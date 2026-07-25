"""MCP self-check / capabilities (Phase F + D31)."""
from __future__ import annotations

import importlib.metadata
from typing import Any, Dict, List, Optional

from mcp.types import TextContent as Content

from ..ssh import PctExecutor, ssh_configured
from .base import ProxmoxTool
from .inventory import (
    ALL_TOOL_NAMES,
    SAFE_DAY2_TOOLS,
    TYPED_CONFIRM_TOOLS,
)


DAY2_TOOLS = frozenset(
    {
        "get_mcp_capabilities",
        "prepare_lxc_for_docker",
        "configure_lxc_dns",
        "pct_set_lxc",
        "configure_lxc_ssh",
        "get_docker_lxc_status",
        "bootstrap_docker_lxc",
        "provision_lxc",
        "provision_vm",
        "push_to_lxc",
        "pull_from_lxc",
        "deploy_static_nginx",
        "deploy_node_app",
        "bootstrap_cloudinit_vm",
        "execute_lxc_command",
        "set_lxc_password",
        "set_lxc_ssh_keys",
        "qm_set_vm",
    }
)


def package_version() -> str:
    try:
        return importlib.metadata.version("cursor-proxmox-mcp")
    except importlib.metadata.PackageNotFoundError:
        try:
            from proxmox_mcp import __version__

            return __version__
        except Exception:
            return "unknown"


class CapabilitiesTools(ProxmoxTool):
    """Report MCP package / SSH / day-2 / dual-auth readiness."""

    def __init__(
        self,
        proxmox_api: Any,
        *,
        ssh_config: Optional[Any] = None,
        proxmox_host: Optional[str] = None,
        logging_config: Optional[Any] = None,
        auth_summary: Optional[Dict[str, Any]] = None,
        proxmox_write_api: Optional[Any] = None,
        proxmox_read_api: Optional[Any] = None,
    ):
        super().__init__(
            proxmox_api,
            proxmox_write_api=proxmox_write_api,
            proxmox_read_api=proxmox_read_api,
        )
        self.ssh_config = ssh_config
        self.proxmox_host = proxmox_host
        self.logging_config = logging_config
        self.auth_summary = auth_summary or {"dual_auth": False, "mutating_api": "primary"}
        self._pct: Optional[PctExecutor] = None
        if ssh_configured(ssh_config) and proxmox_host:
            self._pct = PctExecutor(ssh_config, proxmox_host)

    def get_mcp_capabilities(
        self, probe_node: Optional[str] = None
    ) -> List[Content]:
        """Self-check: version, ssh, dual auth, tool tiers, optional pct probe."""
        ver = package_version()
        ssh_on = ssh_configured(self.ssh_config)
        key_path = getattr(self.ssh_config, "private_key_path", None) if self.ssh_config else None
        key_set = bool(key_path)
        log_cfg = self.logging_config
        auth = self.auth_summary

        try:
            import paramiko  # noqa: F401

            paramiko_ok = True
            paramiko_detail = "importable"
        except ImportError as e:
            paramiko_ok = False
            paramiko_detail = f"NOT importable: {e}"

        day2_present = sorted(DAY2_TOOLS & ALL_TOOL_NAMES)
        day2_missing = sorted(DAY2_TOOLS - ALL_TOOL_NAMES)
        safe_present = sorted(SAFE_DAY2_TOOLS & ALL_TOOL_NAMES)
        typed_confirm = sorted(TYPED_CONFIRM_TOOLS & ALL_TOOL_NAMES)

        lines = [
            "MCP capabilities (cursor-proxmox-mcp)",
            f"  • package_version: {ver}",
            f"  • tool_inventory_count: {len(ALL_TOOL_NAMES)}",
            f"  • dual_auth: {auth.get('dual_auth', False)}",
            f"  • auth_identity: {auth.get('auth_identity', '(unknown)')}",
        ]
        if auth.get("dual_auth"):
            lines.append(
                f"  • auth_write_identity: {auth.get('auth_write_identity', '(unknown)')}"
            )
            lines.append(f"  • mutating_api: {auth.get('mutating_api', 'write')}")
        else:
            lines.append("  • mutating_api: primary (single token)")
        lines.extend(
            [
                f"  • ssh.enabled: {ssh_on}",
                f"  • ssh.private_key_path set: {key_set}",
                f"  • paramiko: {paramiko_detail}",
                f"  • day2_tools_present: {', '.join(day2_present) or '(none)'}",
                f"  • safe_day2_tools_count: {len(safe_present)} "
                "(Cursor mcpAllowlist candidates — see permissions.example.json)",
                f"  • typed_confirm_tools: {', '.join(typed_confirm)} "
                "(never auto-bypass confirm=)",
            ]
        )
        if log_cfg is not None:
            lines.append(
                "  • logging: "
                f"level={getattr(log_cfg, 'level', '?')} "
                f"verbose={getattr(log_cfg, 'verbose', False)} "
                f"tool_calls={getattr(log_cfg, 'tool_calls', True)} "
                f"file={getattr(log_cfg, 'file', None) or '(none)'}"
            )
        if day2_missing:
            lines.append(
                f"  • day2_tools_MISSING (stale catalog?): {', '.join(day2_missing)}"
            )
            lines.append(
                "  • Tip: reload MCP (Disable/Enable) or quit Cursor — stale builds miss new tools."
            )

        if ssh_on and not key_set:
            lines.append(
                "  • ⚠️ ssh.enabled without private_key_path — agent/default keys only; "
                "prefer an explicit key."
            )

        if not ssh_on:
            lines.append(
                "  • ⚠️ Host SSH off — execute_lxc_command / prepare / push unavailable. "
                "Set ssh.enabled=true + private_key_path, put pubkey in node authorized_keys, "
                "**reload MCP**."
            )
        elif not paramiko_ok:
            lines.append(
                "  • ⚠️ paramiko missing — reinstall package (paramiko is a core dep since 1.3.0)."
            )
        elif self._pct and probe_node:
            try:
                probe = self._pct.probe_pct_version(probe_node)
                if probe.success:
                    lines.append(
                        f"  • pct probe ({probe_node}): OK — {(probe.stdout or '').strip()[:80]}"
                    )
                else:
                    lines.append(
                        f"  • pct probe ({probe_node}): FAILED exit={probe.exit_code} "
                        f"{(probe.stderr or probe.stdout or '')[:120]}"
                    )
                    lines.append(
                        "  • Tip: check host_overrides, authorized_keys, firewall 22/tcp, reload MCP."
                    )
            except Exception as e:
                lines.append(f"  • pct probe ({probe_node}): ERROR — {e}")
                lines.append(
                    "  • Tip: check host_overrides, authorized_keys, firewall 22/tcp, reload MCP."
                )
        elif self._pct:
            lines.append(
                "  • pct probe: skipped (pass probe_node= to live-check, e.g. your node name)"
            )

        return [Content(type="text", text="\n".join(lines))]
