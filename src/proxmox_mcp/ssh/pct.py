"""SSH + ``pct`` helpers for LXC guest/host operations.

Proxmox has no REST endpoint for LXC shell exec. Official mechanism is
host-side ``pct exec`` (lxc-attach). File transfer uses ``pct push``/``pct pull``.
Raw AppArmor lines for Docker-in-LXC use host conf edits (D24).
"""
from __future__ import annotations

import logging
import os
import shlex
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Union

logger = logging.getLogger("proxmox-mcp.ssh.pct")

# Dual AppArmor workaround for unpatched hosts (CVE-2025-52881 / nested Docker).
# Never apply profile unconfined without the /dev/null AppArmor bind (D24).
APPARMOR_UNCONFINED = "lxc.apparmor.profile: unconfined"
APPARMOR_NULL_BIND = (
    "lxc.mount.entry: /dev/null sys/module/apparmor/parameters/enabled none bind 0 0"
)
DOCKER_APPARMOR_LINES = (APPARMOR_UNCONFINED, APPARMOR_NULL_BIND)

MIN_LXC_PVE_PATCHED = (6, 0, 5, 2)  # lxc-pve >= 6.0.5-2
MAX_PUSH_BYTES = 32 * 1024 * 1024


class PctExecError(RuntimeError):
    """Raised when SSH/pct operations fail or are unavailable."""


def ssh_configured(ssh_config: Optional[Any]) -> bool:
    """True when optional SSH config is present and enabled."""
    if ssh_config is None:
        return False
    return bool(getattr(ssh_config, "enabled", False))


def require_host_ssh_message(*, context: str = "This operation") -> str:
    """Shared tip when host SSH/pct is required but not configured (D4)."""
    return (
        f"{context} requires opt-in SSH config for host-side `pct` "
        "(Proxmox has no REST LXC shell / push API). "
        "Add `ssh` to PROXMOX_MCP_CONFIG with enabled=true and private_key_path "
        "(public key must be in the node's authorized_keys), then **reload MCP** "
        "(Disable/Enable the proxmox server — config is process-start only). "
        "If you still see HTTP 501 on /lxc/.../exec, Cursor is running a stale pre-1.1.1 build."
    )


def parse_lxc_pve_version(raw: str) -> Optional[tuple]:
    """Parse ``dpkg`` version like ``6.0.5-2`` → comparable tuple."""
    text = (raw or "").strip().splitlines()[0].strip() if raw else ""
    if not text or text.lower() in ("", "none"):
        return None
    # Strip epoch and debian revision extras: 1:6.0.5-2 → 6.0.5-2
    if ":" in text:
        text = text.split(":", 1)[1]
    main, _, deb = text.partition("-")
    parts = main.split(".")
    try:
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        rev = int("".join(c for c in deb if c.isdigit()) or "0")
        return (major, minor, patch, rev)
    except ValueError:
        return None


def lxc_pve_is_patched(version_tuple: Optional[tuple]) -> bool:
    if version_tuple is None:
        return False
    return version_tuple >= MIN_LXC_PVE_PATCHED


@dataclass
class PctExecResult:
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    command: str


class PctExecutor:
    """Run ``pct`` (and related host commands) on a Proxmox node over SSH."""

    def __init__(self, ssh_config: Any, proxmox_host: str):
        self.ssh = ssh_config
        self.default_host = proxmox_host
        self.pct_path = getattr(ssh_config, "pct_path", None) or "/usr/sbin/pct"
        self.timeout = self._resolve_default_timeout(ssh_config)

    @staticmethod
    def _resolve_default_timeout(ssh_config: Any) -> int:
        env = os.environ.get("PROXMOX_MCP_EXEC_TIMEOUT")
        if env:
            try:
                return max(1, int(env))
            except ValueError:
                pass
        return int(getattr(ssh_config, "timeout", 30) or 30)

    def resolve_host(self, node: str) -> str:
        overrides = getattr(self.ssh, "host_overrides", None) or {}
        if isinstance(overrides, dict) and node in overrides:
            return str(overrides[node])
        return self.default_host

    def _connect(self, node: str, timeout: Optional[int] = None):
        import paramiko

        host = self.resolve_host(node)
        user = self.ssh.user
        key_path = self.ssh.private_key_path
        port = int(getattr(self.ssh, "port", 22) or 22)
        to = int(timeout if timeout is not None else self.timeout)

        client = paramiko.SSHClient()
        # Lab nodes often use self-signed/unknown host keys; operator opts into ssh config.
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # noqa: S507
        connect_kwargs: Dict[str, Any] = {
            "hostname": host,
            "port": port,
            "username": user,
            "timeout": to,
            "allow_agent": True,
            "look_for_keys": True,
        }
        if key_path:
            connect_kwargs["key_filename"] = key_path
        client.connect(**connect_kwargs)
        return client, host, to

    def run_host(
        self,
        node: str,
        command: Union[str, Sequence[str]],
        *,
        timeout: Optional[int] = None,
    ) -> PctExecResult:
        """Run a command on the Proxmox host (not inside a CT)."""
        if isinstance(command, (list, tuple)):
            remote = " ".join(shlex.quote(str(c)) for c in command)
            display = " ".join(str(c) for c in command)
        else:
            remote = str(command)
            display = remote

        truncated = display if len(display) <= 120 else display[:117] + "..."
        logger.warning("SSH host cmd (node=%s): %s", node, truncated)

        try:
            client, host, to = self._connect(node, timeout)
        except Exception as e:
            raise PctExecError(
                f"SSH connect failed (node={node}): {e}"
            ) from e

        try:
            _stdin, stdout, stderr = client.exec_command(remote, timeout=to)
            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode("utf-8", errors="replace")
            err = stderr.read().decode("utf-8", errors="replace")
            return PctExecResult(
                success=exit_code == 0,
                stdout=out,
                stderr=err,
                exit_code=exit_code,
                command=display,
            )
        except PctExecError:
            raise
        except Exception as e:
            raise PctExecError(f"SSH host command failed (node={node}, host={host}): {e}") from e
        finally:
            client.close()

    def execute(
        self,
        node: str,
        vmid: str,
        command: str,
        *,
        timeout: Optional[int] = None,
    ) -> PctExecResult:
        """Run ``pct exec`` inside a guest CT."""
        guest_shell = f"sh -c {shlex.quote(command)}"
        remote = f"{shlex.quote(self.pct_path)} exec {shlex.quote(str(vmid))} -- {guest_shell}"
        truncated = command if len(command) <= 120 else command[:117] + "..."
        logger.warning(
            "SSH pct exec on CT %s (node=%s): %s", vmid, node, truncated
        )
        result = self.run_host(node, remote, timeout=timeout)
        return PctExecResult(
            success=result.success,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            command=command,
        )

    def probe_pct_version(self, node: str) -> PctExecResult:
        return self.run_host(node, f"{shlex.quote(self.pct_path)} version")

    def probe_lxc_pve_version(self, node: str) -> tuple[Optional[str], Optional[tuple], bool]:
        """Return (raw_version, parsed_tuple, is_patched)."""
        result = self.run_host(
            node,
            "dpkg-query -W -f='${Version}' lxc-pve 2>/dev/null || true",
        )
        raw = (result.stdout or "").strip()
        parsed = parse_lxc_pve_version(raw)
        return raw or None, parsed, lxc_pve_is_patched(parsed)

    def pct_set(
        self,
        node: str,
        vmid: str,
        **options: Any,
    ) -> PctExecResult:
        """``pct set VMID -key value ...`` for allowlisted CT options.

        Allowed keys are enforced by callers (``PCT_SET_ALLOWED_KEYS``).
        """
        if not options:
            raise PctExecError("pct_set requires at least one option")
        parts = [
            shlex.quote(self.pct_path),
            "set",
            shlex.quote(str(vmid)),
        ]
        for key, value in options.items():
            parts.append(f"-{key}")
            parts.append(shlex.quote(str(value)))
        return self.run_host(node, " ".join(parts))

    def ensure_features(
        self, node: str, vmid: str, features: str
    ) -> PctExecResult:
        """``pct set VMID -features ...`` on the host."""
        return self.pct_set(node, vmid, features=features)

    def read_lxc_conf(self, node: str, vmid: str) -> str:
        path = f"/etc/pve/lxc/{vmid}.conf"
        result = self.run_host(node, f"cat {shlex.quote(path)}")
        if not result.success:
            raise PctExecError(
                f"Failed to read {path}: {result.stderr or result.stdout}"
            )
        return result.stdout

    def write_lxc_conf(self, node: str, vmid: str, content: str) -> None:
        """Atomically replace CT conf via host temp + mv (cluster filesystem)."""
        path = f"/etc/pve/lxc/{vmid}.conf"
        tmp = f"/tmp/proxmox-mcp-{vmid}-{uuid.uuid4().hex}.conf"  # noqa: S108
        # Upload via SFTP then mv into place
        data = content.encode("utf-8")
        self._sftp_put_bytes(node, data, tmp)
        mv = self.run_host(
            node,
            f"mv {shlex.quote(tmp)} {shlex.quote(path)} && chmod 640 {shlex.quote(path)}",
        )
        if not mv.success:
            self.run_host(node, f"rm -f {shlex.quote(tmp)}", timeout=10)
            raise PctExecError(
                f"Failed to write {path}: {mv.stderr or mv.stdout}"
            )

    def apply_docker_apparmor_workaround(self, node: str, vmid: str) -> List[str]:
        """Ensure both AppArmor workaround lines exist. Returns list of applied changes."""
        conf = self.read_lxc_conf(node, vmid)
        lines = conf.splitlines()
        applied: List[str] = []
        for needed in DOCKER_APPARMOR_LINES:
            key = needed.split(":", 1)[0].strip()
            if any(ln.strip().startswith(key) for ln in lines):
                # Ensure exact value for these allowlisted keys
                updated = False
                new_lines = []
                for ln in lines:
                    if ln.strip().startswith(key):
                        if ln.strip() != needed:
                            new_lines.append(needed)
                            updated = True
                        else:
                            new_lines.append(ln)
                    else:
                        new_lines.append(ln)
                if updated:
                    lines = new_lines
                    applied.append(f"updated {needed}")
                continue
            lines.append(needed)
            applied.append(f"added {needed}")
        if applied:
            # Preserve trailing newline
            body = "\n".join(lines)
            if not body.endswith("\n"):
                body += "\n"
            self.write_lxc_conf(node, vmid, body)
        return applied

    def strip_docker_apparmor_workaround(self, node: str, vmid: str) -> List[str]:
        """Remove allowlisted AppArmor workaround lines (patched host)."""
        conf = self.read_lxc_conf(node, vmid)
        lines = conf.splitlines()
        keys = {ln.split(":", 1)[0].strip() for ln in DOCKER_APPARMOR_LINES}
        kept = []
        removed: List[str] = []
        for ln in lines:
            key = ln.strip().split(":", 1)[0].strip() if ":" in ln else ""
            if key in keys and any(
                ln.strip() == full or ln.strip().startswith(key)
                for full in DOCKER_APPARMOR_LINES
            ):
                # Only strip our known workaround keys
                if key in ("lxc.apparmor.profile", "lxc.mount.entry") and (
                    "unconfined" in ln
                    or "apparmor/parameters/enabled" in ln
                ):
                    removed.append(ln.strip())
                    continue
            kept.append(ln)
        if removed:
            body = "\n".join(kept)
            if body and not body.endswith("\n"):
                body += "\n"
            self.write_lxc_conf(node, vmid, body or "\n")
        return [f"removed {r}" for r in removed]

    def _sftp_put_bytes(self, node: str, data: bytes, remote_path: str) -> None:
        try:
            client, host, _to = self._connect(node)
        except Exception as e:
            raise PctExecError(f"SSH connect failed for SFTP (node={node}): {e}") from e
        try:
            sftp = client.open_sftp()
            try:
                with sftp.file(remote_path, "wb") as rf:
                    rf.write(data)
            finally:
                sftp.close()
        except Exception as e:
            raise PctExecError(f"SFTP put failed (host={host}, path={remote_path}): {e}") from e
        finally:
            client.close()

    def _sftp_get_bytes(self, node: str, remote_path: str) -> bytes:
        try:
            client, host, _to = self._connect(node)
        except Exception as e:
            raise PctExecError(f"SSH connect failed for SFTP (node={node}): {e}") from e
        try:
            sftp = client.open_sftp()
            try:
                with sftp.file(remote_path, "rb") as rf:
                    return rf.read()
            finally:
                sftp.close()
        except Exception as e:
            raise PctExecError(f"SFTP get failed (host={host}, path={remote_path}): {e}") from e
        finally:
            client.close()

    def push_to_guest(
        self,
        node: str,
        vmid: str,
        data: bytes,
        guest_path: str,
        *,
        timeout: Optional[int] = None,
    ) -> None:
        """Upload bytes to host temp, ``pct push`` into CT, unlink temp."""
        if len(data) > MAX_PUSH_BYTES:
            raise PctExecError(
                f"Payload {len(data)} bytes exceeds {MAX_PUSH_BYTES} byte limit"
            )
        tmp = f"/tmp/proxmox-mcp-push-{vmid}-{uuid.uuid4().hex}"  # noqa: S108
        self._sftp_put_bytes(node, data, tmp)
        try:
            cmd = (
                f"{shlex.quote(self.pct_path)} push {shlex.quote(str(vmid))} "
                f"{shlex.quote(tmp)} {shlex.quote(guest_path)}"
            )
            result = self.run_host(node, cmd, timeout=timeout)
            if not result.success:
                raise PctExecError(
                    f"pct push failed: {result.stderr or result.stdout}"
                )
        finally:
            self.run_host(node, f"rm -f {shlex.quote(tmp)}", timeout=15)

    def pull_from_guest(
        self,
        node: str,
        vmid: str,
        guest_path: str,
        *,
        timeout: Optional[int] = None,
    ) -> bytes:
        """``pct pull`` to host temp, download bytes, unlink temp."""
        tmp = f"/tmp/proxmox-mcp-pull-{vmid}-{uuid.uuid4().hex}"  # noqa: S108
        try:
            cmd = (
                f"{shlex.quote(self.pct_path)} pull {shlex.quote(str(vmid))} "
                f"{shlex.quote(guest_path)} {shlex.quote(tmp)}"
            )
            result = self.run_host(node, cmd, timeout=timeout)
            if not result.success:
                raise PctExecError(
                    f"pct pull failed: {result.stderr or result.stdout}"
                )
            return self._sftp_get_bytes(node, tmp)
        finally:
            self.run_host(node, f"rm -f {shlex.quote(tmp)}", timeout=15)
