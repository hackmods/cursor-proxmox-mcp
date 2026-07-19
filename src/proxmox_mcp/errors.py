"""Typed exceptions for Proxmox MCP operations."""
from __future__ import annotations

import re
from typing import Optional


_SENSITIVE_PATTERNS = [
    re.compile(r"(token[_-]?value\s*[=:]\s*)\S+", re.I),
    re.compile(r"(password\s*[=:]\s*)\S+", re.I),
    re.compile(r"(PVEAPIToken=[^\s,]+)", re.I),
    re.compile(r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})", re.I),
]


def sanitize_error_message(message: str) -> str:
    """Strip secrets and token-like UUIDs from error strings."""
    text = message or ""
    for pattern in _SENSITIVE_PATTERNS:
        text = pattern.sub(r"\1***", text)
    return text


class ProxmoxMCPError(Exception):
    """Base error for Proxmox MCP."""

    def __init__(self, message: str, *, cause: Optional[BaseException] = None):
        self.raw_message = message
        safe = sanitize_error_message(message)
        super().__init__(safe)
        self.__cause__ = cause


class ProxmoxNotFoundError(ProxmoxMCPError, ValueError):
    """Resource missing."""


class ProxmoxAuthError(ProxmoxMCPError, ValueError):
    """Authentication or permission failure."""


class ProxmoxPermissionError(ProxmoxMCPError, ValueError):
    """Permission denied."""


class ProxmoxAPIError(ProxmoxMCPError, RuntimeError):
    """Unexpected API / transport failure."""


def classify_proxmox_error(operation: str, error: BaseException) -> ProxmoxMCPError:
    """Map a raw exception into a typed, sanitized ProxmoxMCPError."""
    msg = str(error)
    lower = msg.lower()
    wrapped = f"Failed to {operation}: {msg}"

    if "not found" in lower or "does not exist" in lower:
        return ProxmoxNotFoundError(f"Resource not found: {msg}", cause=error)
    if "permission denied" in lower or "403" in lower:
        return ProxmoxPermissionError(f"Permission denied: {msg}", cause=error)
    if "401" in lower or "authentication" in lower or "unauthorized" in lower:
        return ProxmoxAuthError(f"Authentication failed: {msg}", cause=error)
    if "invalid" in lower:
        return ProxmoxNotFoundError(f"Invalid input: {msg}", cause=error)
    return ProxmoxAPIError(wrapped, cause=error)
