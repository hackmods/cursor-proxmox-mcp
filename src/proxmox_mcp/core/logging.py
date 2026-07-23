"""
Logging configuration for the Proxmox MCP server.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from ..config.models import LoggingConfig
from .log_filters import RedactingFilter

# Third-party loggers that drown useful MCP/tool lines when root is DEBUG.
_NOISY_LOGGERS = (
    "urllib3",
    "urllib3.connectionpool",
    "asyncio",
    "httpcore",
    "httpx",
    "mcp.server.lowlevel",
    "mcp.server.lowlevel.server",
    "mcp.server.fastmcp",
    "mcp.server.fastmcp.resources",
    "paramiko",
    "paramiko.transport",
)


def _env_bool(name: str) -> Optional[bool]:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return None
    return raw.strip().lower() in ("1", "true", "yes", "on")


def resolve_logging_config(config: LoggingConfig) -> LoggingConfig:
    """Apply env overrides for QOL without editing config.json.

    - ``PROXMOX_MCP_LOG_LEVEL`` — overrides ``logging.level``
    - ``PROXMOX_MCP_VERBOSE=1`` — sets ``verbose=true`` (and DEBUG if still INFO)
    - ``PROXMOX_MCP_TOOL_CALLS=0`` — disables structured tool_call audit lines
    - ``PROXMOX_MCP_CONSOLE_LEVEL`` — overrides ``logging.console_level``
    """
    updates: dict = {}
    env_level = os.environ.get("PROXMOX_MCP_LOG_LEVEL")
    if env_level:
        updates["level"] = env_level.strip().upper()

    verbose_env = _env_bool("PROXMOX_MCP_VERBOSE")
    if verbose_env is True:
        updates["verbose"] = True

    tool_calls_env = _env_bool("PROXMOX_MCP_TOOL_CALLS")
    if tool_calls_env is not None:
        updates["tool_calls"] = tool_calls_env

    console_env = os.environ.get("PROXMOX_MCP_CONSOLE_LEVEL")
    if console_env:
        updates["console_level"] = console_env.strip().upper()

    resolved = config.model_copy(update=updates) if updates else config.model_copy()

    # verbose ⇒ at least DEBUG for our package loggers (file handler).
    if resolved.verbose and resolved.level.upper() == "INFO":
        resolved = resolved.model_copy(update={"level": "DEBUG"})

    return resolved


def setup_logging(config: LoggingConfig) -> logging.Logger:
    """Configure logging with optional file handler, console level, and redaction.

    Prefer passing a config already run through ``resolve_logging_config``.
    This function still resolves env overrides so direct callers stay correct.

    Noisy third-party loggers stay at WARNING unless ``http_debug`` is true so
    ``DEBUG`` / ``verbose`` stays useful for Proxmox MCP diagnostics.
    """
    config = resolve_logging_config(config)
    level_name = config.level.upper()
    console_level_name = (config.console_level or "ERROR").upper()
    level = getattr(logging, level_name, logging.INFO)
    console_level = getattr(logging, console_level_name, logging.ERROR)

    log_file = config.file
    if log_file and not os.path.isabs(log_file):
        log_file = os.path.join(os.getcwd(), log_file)

    handlers: list[logging.Handler] = []

    if log_file:
        parent = os.path.dirname(log_file)
        if parent:
            os.makedirs(parent, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        handlers.append(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    handlers.append(console_handler)

    formatter = logging.Formatter(config.format)
    redactor = RedactingFilter()
    for handler in handlers:
        handler.setFormatter(formatter)
        handler.addFilter(redactor)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    for handler in handlers:
        root_logger.addHandler(handler)

    if config.quiet_libraries and not config.http_debug:
        for name in _NOISY_LOGGERS:
            logging.getLogger(name).setLevel(logging.WARNING)
    elif config.http_debug:
        logging.getLogger("urllib3").setLevel(logging.DEBUG)
        logging.getLogger("urllib3.connectionpool").setLevel(logging.DEBUG)

    package_logger = logging.getLogger("proxmox-mcp")
    package_logger.info(
        "logging configured level=%s verbose=%s tool_calls=%s console_level=%s file=%s",
        level_name,
        config.verbose,
        config.tool_calls,
        console_level_name,
        log_file or "(none)",
    )
    return package_logger
