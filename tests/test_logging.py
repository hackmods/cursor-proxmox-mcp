"""Logging / redaction / tool-call audit tests."""
from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from proxmox_mcp.config.models import LoggingConfig
from proxmox_mcp.core.log_filters import RedactingFilter
from proxmox_mcp.core.logging import resolve_logging_config, setup_logging
from proxmox_mcp.core.tool_audit import (
    format_arg_suffix,
    install_tool_call_audit,
    summarize_tool_args,
)


def test_redacting_filter():
    f = RedactingFilter()
    record = logging.LogRecord(
        "t", logging.INFO, __file__, 1, "token_value=supersecret", (), None
    )
    assert f.filter(record) is True
    assert "supersecret" not in record.getMessage()
    assert "***" in record.getMessage()


def test_setup_logging_returns_logger(tmp_path):
    log_file = tmp_path / "t.log"
    logger = setup_logging(
        LoggingConfig(level="INFO", file=str(log_file))
    )
    assert logger.name == "proxmox-mcp"
    logger.info("token_value=should-redact")
    text = log_file.read_text(encoding="utf-8")
    assert "should-redact" not in text
    assert "logging configured" in text


def test_summarize_redacts_password_and_keeps_identity():
    safe = summarize_tool_args(
        {
            "node": "pve",
            "vmid": "114",
            "password": "hunter2",
            "command": "apt-get update && apt-get install -y nginx",
        }
    )
    assert safe["node"] == "pve"
    assert safe["vmid"] == "114"
    assert "hunter2" not in str(safe)
    assert safe["password"].startswith("(redacted")
    assert safe["command_len"] == len("apt-get update && apt-get install -y nginx")
    assert "command_preview" not in safe


def test_summarize_verbose_includes_command_preview():
    safe = summarize_tool_args(
        {"command": "echo hello world", "local_path": "C:/src/app"},
        verbose=True,
    )
    assert safe["command_preview"] == "echo hello world"
    assert safe["local_path"] == "C:/src/app"


def test_format_arg_suffix_quotes_spaces():
    assert 'node=pve' in format_arg_suffix({"node": "pve"})
    assert 'hostname="my host"' in format_arg_suffix({"hostname": "my host"})


def test_resolve_verbose_env_bumps_level(monkeypatch):
    monkeypatch.setenv("PROXMOX_MCP_VERBOSE", "1")
    monkeypatch.delenv("PROXMOX_MCP_LOG_LEVEL", raising=False)
    resolved = resolve_logging_config(LoggingConfig(level="INFO", verbose=False))
    assert resolved.verbose is True
    assert resolved.level == "DEBUG"


def test_resolve_tool_calls_env_off(monkeypatch):
    monkeypatch.setenv("PROXMOX_MCP_TOOL_CALLS", "0")
    resolved = resolve_logging_config(LoggingConfig(tool_calls=True))
    assert resolved.tool_calls is False


def test_logging_config_rejects_bad_level():
    with pytest.raises(ValueError, match=r"logging\.level"):
        LoggingConfig(level="TRACE")


@pytest.mark.asyncio
async def test_install_tool_call_audit_logs_success(caplog):
    mcp = MagicMock()
    original = AsyncMock(return_value="ok")
    mcp._tool_manager = MagicMock()
    mcp._tool_manager.call_tool = original

    install_tool_call_audit(mcp, LoggingConfig(tool_calls=True, verbose=False))

    with caplog.at_level(logging.INFO, logger="proxmox-mcp.tools"):
        result = await mcp._tool_manager.call_tool(
            "get_containers",
            {"probes": False},
            context=None,
            convert_result=True,
        )

    assert result == "ok"
    assert any(
        "tool_call name=get_containers ok=true" in r.getMessage()
        for r in caplog.records
    )
    original.assert_awaited_once()


@pytest.mark.asyncio
async def test_install_tool_call_audit_logs_failure(caplog):
    mcp = MagicMock()
    original = AsyncMock(side_effect=ValueError("boom secret=nope"))
    mcp._tool_manager = MagicMock()
    mcp._tool_manager.call_tool = original

    install_tool_call_audit(mcp, LoggingConfig(tool_calls=True))

    with caplog.at_level(logging.ERROR, logger="proxmox-mcp.tools"):
        with pytest.raises(ValueError, match="boom"):
            await mcp._tool_manager.call_tool("start_lxc", {"node": "pve", "vmid": "1"})

    assert any(
        "tool_call name=start_lxc ok=false" in r.getMessage() and "node=pve" in r.getMessage()
        for r in caplog.records
    )


def test_quiet_libraries_keeps_urllib3_quiet(tmp_path, monkeypatch):
    monkeypatch.delenv("PROXMOX_MCP_VERBOSE", raising=False)
    monkeypatch.delenv("PROXMOX_MCP_LOG_LEVEL", raising=False)
    setup_logging(
        LoggingConfig(
            level="DEBUG",
            file=str(tmp_path / "d.log"),
            quiet_libraries=True,
            http_debug=False,
            verbose=False,
        )
    )
    assert logging.getLogger("urllib3").level == logging.WARNING
    assert logging.getLogger("asyncio").level == logging.WARNING
