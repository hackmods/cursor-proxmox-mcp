"""SSH + ``pct exec`` for LXC guest commands.

Proxmox has no REST endpoint for LXC shell exec. Official mechanism is
host-side ``pct exec`` (lxc-attach). This module is opt-in via config ``ssh``.
"""
from __future__ import annotations

import logging
import shlex
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger("proxmox-mcp.ssh.pct")


class PctExecError(RuntimeError):
    """Raised when SSH/pct exec fails or is unavailable."""


def ssh_configured(ssh_config: Optional[Any]) -> bool:
    """True when optional SSH config is present and enabled."""
    if ssh_config is None:
        return False
    return bool(getattr(ssh_config, "enabled", False))


@dataclass
class PctExecResult:
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    command: str


class PctExecutor:
    """Run ``pct exec`` on a Proxmox node over SSH."""

    def __init__(self, ssh_config: Any, proxmox_host: str):
        self.ssh = ssh_config
        self.default_host = proxmox_host
        self.pct_path = getattr(ssh_config, "pct_path", None) or "/usr/sbin/pct"
        self.timeout = int(getattr(ssh_config, "timeout", 30) or 30)

    def resolve_host(self, node: str) -> str:
        overrides = getattr(self.ssh, "host_overrides", None) or {}
        if isinstance(overrides, dict) and node in overrides:
            return str(overrides[node])
        return self.default_host

    def execute(self, node: str, vmid: str, command: str) -> PctExecResult:
        try:
            import paramiko
        except ImportError as e:
            raise PctExecError(
                "SSH LXC exec requires the 'paramiko' package. "
                "Install with: pip install 'cursor-proxmox-mcp[ssh]' "
                "or: pip install paramiko"
            ) from e

        host = self.resolve_host(node)
        user = self.ssh.user
        key_path = self.ssh.private_key_path
        port = int(getattr(self.ssh, "port", 22) or 22)

        # Quote the guest command for `pct exec vmid -- sh -c '...'`
        guest_shell = f"sh -c {shlex.quote(command)}"
        remote = f"{shlex.quote(self.pct_path)} exec {shlex.quote(str(vmid))} -- {guest_shell}"

        truncated = command if len(command) <= 120 else command[:117] + "..."
        logger.warning(
            "SSH pct exec on CT %s (node=%s host=%s): %s", vmid, node, host, truncated
        )

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            connect_kwargs: Dict[str, Any] = {
                "hostname": host,
                "port": port,
                "username": user,
                "timeout": self.timeout,
                "allow_agent": True,
                "look_for_keys": True,
            }
            if key_path:
                connect_kwargs["key_filename"] = key_path
            client.connect(**connect_kwargs)
            _stdin, stdout, stderr = client.exec_command(remote, timeout=self.timeout)
            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode("utf-8", errors="replace")
            err = stderr.read().decode("utf-8", errors="replace")
            return PctExecResult(
                success=exit_code == 0,
                stdout=out,
                stderr=err,
                exit_code=exit_code,
                command=command,
            )
        except PctExecError:
            raise
        except Exception as e:
            raise PctExecError(f"SSH pct exec failed (node={node}, host={host}): {e}") from e
        finally:
            client.close()
