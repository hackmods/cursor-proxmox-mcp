"""Structured MCP tool-call audit logging.

Wraps FastMCP's ToolManager so every CallToolRequest emits a single-line
``tool_call`` record (name, ok, duration, safe identity args). Secrets are
never logged; ``verbose`` adds truncated previews for non-sensitive fields.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Callable, Optional

from ..config.models import LoggingConfig

logger = logging.getLogger("proxmox-mcp.tools")

# Always include when present (safe identity / routing knobs).
_IDENTITY_KEYS = frozenset(
    {
        "node",
        "vmid",
        "guest_type",
        "storage",
        "content",
        "volume",
        "type",
        "probes",
        "wait",
        "snapname",
        "force",
        "purge",
        "group",
        "sid",
        "pos",
        "enable",
        "action",
        "bridge",
        "hostname",
        "ostemplate",
        "cores",
        "memory",
        "swap",
        "disk",
        "pool",
        "target",
        "online",
        "jobid",
        "id",
        "name",
        "path",
        "scope",
        "macro",
        "probe_node",
        "docker_mode",
        "runtime",
        "service_name",
        "port",
        "build_cmd",
        "start_cmd",
        "node_major",
        "template",
        "full",
        "newid",
        "description",
        "tags",
        "onboot",
        "bwlimit",
        "format",
        "compress",
        "mode",
        "remove",
        "timeout",
        "max_entries",
        "userid",
        "role",
        "propagate",
        "confirm",
        "clone_from",
        "fingerprint",
        "sections",
        "votes",
        "nodeid",
        "ciuser",
        "ipconfig0",
    }
)

_SENSITIVE_SUBSTR = (
    "password",
    "secret",
    "token",
    "private_key",
    "ssh_public",
    "api_key",
    "passphrase",
)


def _is_sensitive_key(key: str) -> bool:
    kl = key.lower()
    return any(s in kl for s in _SENSITIVE_SUBSTR)


def _truncate(value: Any, max_len: int) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, (list, tuple)):
        return f"(list,len={len(value)})"
    if isinstance(value, dict):
        return f"(dict,keys={len(value)})"
    text = str(value)
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def summarize_tool_args(
    arguments: Optional[dict[str, Any]],
    *,
    verbose: bool = False,
) -> dict[str, Any]:
    """Return a redacted, size-bounded dict suitable for log lines."""
    if not arguments:
        return {}
    out: dict[str, Any] = {}
    max_len = 120 if verbose else 64
    for key, value in arguments.items():
        if _is_sensitive_key(key):
            if value is None or value == "":
                out[key] = "(empty)"
            else:
                out[key] = f"(redacted,len={len(str(value))})"
            continue
        if key == "command":
            text = str(value) if value is not None else ""
            out["command_len"] = len(text)
            if verbose and text:
                out["command_preview"] = _truncate(text, 80)
            continue
        if key in ("local_path", "remote_path", "url", "filename"):
            if value is None or value == "":
                out[key] = "(empty)"
            elif verbose:
                out[key] = _truncate(value, max_len)
            else:
                out[f"has_{key}"] = True
            continue
        if key in _IDENTITY_KEYS or verbose:
            out[key] = _truncate(value, max_len)
    return out


def format_arg_suffix(safe_args: dict[str, Any]) -> str:
    """Space-prefixed ``k=v`` pairs for appending to a log message."""
    if not safe_args:
        return ""
    parts = []
    for key, value in safe_args.items():
        if isinstance(value, str) and (" " in value or "=" in value):
            parts.append(f'{key}="{value}"')
        else:
            parts.append(f"{key}={value}")
    return " " + " ".join(parts)


def _short_error(exc: BaseException, limit: int = 160) -> str:
    text = str(exc).replace("\n", " ").strip()
    if len(text) > limit:
        return text[: limit - 1] + "…"
    return text


def install_tool_call_audit(mcp: Any, config: LoggingConfig) -> None:
    """Wrap ``mcp._tool_manager.call_tool`` with structured audit logging.

    FastMCP registers ``self.call_tool`` at construction time, so patching the
    ToolManager method (which ``call_tool`` delegates to) is the reliable hook.
    """
    if not getattr(config, "tool_calls", True):
        logger.debug("tool_call audit disabled (logging.tool_calls=false)")
        return

    tool_manager = getattr(mcp, "_tool_manager", None)
    if tool_manager is None:
        logger.warning("Cannot install tool_call audit: FastMCP has no _tool_manager")
        return

    original: Callable[..., Any] = tool_manager.call_tool
    verbose = bool(config.verbose)

    async def call_tool_audited(
        name: str,
        arguments: dict[str, Any],
        context: Any = None,
        convert_result: bool = False,
    ) -> Any:
        started = time.perf_counter()
        safe = summarize_tool_args(arguments, verbose=verbose)
        suffix = format_arg_suffix(safe)
        try:
            result = await original(
                name, arguments, context=context, convert_result=convert_result
            )
            duration_ms = int((time.perf_counter() - started) * 1000)
            logger.info(
                "tool_call name=%s ok=true duration_ms=%d%s",
                name,
                duration_ms,
                suffix,
            )
            if verbose:
                logger.debug(
                    "tool_call_detail name=%s args=%s",
                    name,
                    safe,
                )
            return result
        except Exception as exc:
            duration_ms = int((time.perf_counter() - started) * 1000)
            logger.error(
                "tool_call name=%s ok=false duration_ms=%d error=%s: %s%s",
                name,
                duration_ms,
                type(exc).__name__,
                _short_error(exc),
                suffix,
            )
            raise

    tool_manager.call_tool = call_tool_audited  # type: ignore[method-assign]
    logger.debug("tool_call audit installed on ToolManager")
