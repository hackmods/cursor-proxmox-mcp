"""
Logging configuration for the Proxmox MCP server.
"""
from __future__ import annotations

import logging
import os

from ..config.models import LoggingConfig
from .log_filters import RedactingFilter


def setup_logging(config: LoggingConfig) -> logging.Logger:
    """Configure logging with optional file handler and secret redaction."""
    log_file = config.file
    if log_file and not os.path.isabs(log_file):
        log_file = os.path.join(os.getcwd(), log_file)

    handlers: list[logging.Handler] = []

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, config.level.upper()))
        handlers.append(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    handlers.append(console_handler)

    formatter = logging.Formatter(config.format)
    redactor = RedactingFilter()
    for handler in handlers:
        handler.setFormatter(formatter)
        handler.addFilter(redactor)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.level.upper()))

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    for handler in handlers:
        root_logger.addHandler(handler)

    return logging.getLogger("proxmox-mcp")
