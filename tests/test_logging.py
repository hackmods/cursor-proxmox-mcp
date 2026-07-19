"""Logging / redaction tests."""
import logging

from proxmox_mcp.config.models import LoggingConfig
from proxmox_mcp.core.log_filters import RedactingFilter
from proxmox_mcp.core.logging import setup_logging


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
