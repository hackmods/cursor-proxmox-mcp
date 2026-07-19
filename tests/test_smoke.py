"""Smoke tests for package entrypoints and tool inventory integrity."""
import importlib

import pytest

from tests.expected_tools import EXPECTED_TOOLS


def test_expected_tools_floor():
    assert len(EXPECTED_TOOLS) >= 100, f"inventory too small: {len(EXPECTED_TOOLS)}"


def test_server_module_imports():
    mod = importlib.import_module("proxmox_mcp.server")
    assert hasattr(mod, "main")
    assert hasattr(mod, "ProxmoxMCPServer")


def test_all_tool_modules_import():
    modules = [
        "proxmox_mcp.tools.node",
        "proxmox_mcp.tools.vm",
        "proxmox_mcp.tools.container",
        "proxmox_mcp.tools.storage",
        "proxmox_mcp.tools.cluster",
        "proxmox_mcp.tools.tasks",
        "proxmox_mcp.tools.snapshot",
        "proxmox_mcp.tools.backup",
        "proxmox_mcp.tools.migrate",
        "proxmox_mcp.tools.ha",
        "proxmox_mcp.tools.firewall",
        "proxmox_mcp.tools.access",
        "proxmox_mcp.tools.network",
        "proxmox_mcp.tools.replication",
        "proxmox_mcp.tools.acme",
        "proxmox_mcp.tools.sdn",
        "proxmox_mcp.tools.pool",
        "proxmox_mcp.tools.guest",
    ]
    for name in modules:
        importlib.import_module(name)


def test_console_script_entrypoints_registered():
    """Verify pyproject declares console scripts; soft-check installed eps."""
    import re
    from pathlib import Path

    text = Path("pyproject.toml").read_text(encoding="utf-8")
    # Avoid tomllib (3.11+) / tomli so CI works on 3.10 without extra deps
    block = re.search(r"\[project\.scripts\]\s*(.*?)(?:\n\[|\Z)", text, re.S)
    assert block, "missing [project.scripts] in pyproject.toml"
    scripts = dict(re.findall(r'^([A-Za-z0-9_-]+)\s*=\s*"([^"]+)"', block.group(1), re.M))
    assert "cursor-proxmox-mcp" in scripts
    assert "proxmox-mcp" in scripts
    assert "proxmox-mcp-server" in scripts
    for name in ("cursor-proxmox-mcp", "proxmox-mcp", "proxmox-mcp-server"):
        assert scripts[name].endswith(":main")

    from importlib.metadata import entry_points

    eps = entry_points()
    if hasattr(eps, "select"):
        installed = {ep.name: ep for ep in eps.select(group="console_scripts")}
    else:
        installed = {ep.name: ep for ep in eps.get("console_scripts", [])}

    # Soft check only when this package is installed into the active env
    if "cursor-proxmox-mcp" in installed:
        assert installed["cursor-proxmox-mcp"].value.endswith(":main")


def test_main_requires_config_env(monkeypatch):
    monkeypatch.delenv("PROXMOX_MCP_CONFIG", raising=False)
    from proxmox_mcp.server import main

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1


def test_definitions_cover_new_domains():
    from proxmox_mcp.tools import definitions as D

    required = [
        "LIST_REPLICATION_JOBS_DESC",
        "LIST_ACME_PLUGINS_DESC",
        "LIST_SDN_ZONES_DESC",
        "LIST_POOLS_DESC",
        "CREATE_VNC_TICKET_VM_DESC",
        "GET_VERSION_DESC",
        "LIST_FIREWALL_ALIASES_DESC",
        "GET_NODE_SUBSCRIPTION_DESC",
    ]
    for name in required:
        assert hasattr(D, name), f"missing description {name}"
        assert isinstance(getattr(D, name), str)
        assert len(getattr(D, name)) > 5
