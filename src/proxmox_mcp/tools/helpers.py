"""Shared helpers for guest/storage operations."""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

# Lab defaults (public create params for bridge/IP remain Phase D — D11/D18)
DEFAULT_BRIDGE = "vmbr0"
DEFAULT_LXC_FEATURES = "nesting=1"
DEFAULT_NET0 = f"virtio,bridge={DEFAULT_BRIDGE}"

# Appended when *_vm tools miss a guest that may be an LXC
QEMU_NOT_FOUND_HINT = (
    "💡 Next: if this ID is an LXC, use get_containers / start_lxc / "
    "start_guest(guest_type=lxc) — get_vms is QEMU-only."
)

# Appended when *_lxc tools miss a guest that may be a QEMU VM
LXC_NOT_FOUND_HINT = (
    "💡 Next: if this ID is a QEMU VM, use get_vms / start_vm / "
    "start_guest(guest_type=qemu) — get_containers is LXC-only."
)

# Appended when guest_type-routed tools miss a guest
GUEST_NOT_FOUND_HINT = (
    "💡 Next: confirm guest_type (qemu|lxc) and node; "
    "use get_cluster_resources(type=vm) if unsure."
)

WAIT_FOR_TASK_HINT = (
    "💡 Next: wait_for_task(node, upid) until stopped — "
    "this call returned a task UPID, not a finished result."
)

PRIVSEP_EMPTY_HINT = (
    "💡 If this looks wrong: with Privilege Separation=Yes, empty lists often mean "
    "missing token ACL — check get_token_permissions / get_permissions."
)


def is_missing_resource_error(error: BaseException) -> bool:
    """True if proxmoxer/API error indicates the resource does not exist."""
    text = str(error).lower()
    return "does not exist" in text or "not found" in text


def qemu_not_found_message(vmid: str, node: str) -> str:
    """Clear error when a QEMU-only tool is used against a missing/wrong guest."""
    return f"VM {vmid} not found on node {node}\n{QEMU_NOT_FOUND_HINT}"


def lxc_not_found_message(vmid: str, node: str) -> str:
    """Clear error when an LXC-only tool is used against a missing/wrong guest."""
    return f"LXC {vmid} not found on node {node}\n{LXC_NOT_FOUND_HINT}"


def guest_not_found_message(vmid: str, node: str, guest_type: str) -> str:
    """Clear error when a guest_type-routed tool misses a guest."""
    label = "VM" if guest_type == "qemu" else "LXC"
    return f"{label} {vmid} not found on node {node} (guest_type={guest_type})\n{GUEST_NOT_FOUND_HINT}"


def upid_response_footer(upid: Any, *, node: Optional[str] = None) -> str:
    """Standard footer for tools that return a Proxmox task UPID (D22)."""
    lines = [f"Task ID: {upid}"]
    if node:
        lines.append(f"Node: {node}")
    lines.append(WAIT_FOR_TASK_HINT)
    return "\n".join(lines)


def destructive_warning(action: str = "deleted") -> str:
    """⚠️ IRREVERSIBLE line for destructive tool responses (D23 / D2)."""
    return f"⚠️ IRREVERSIBLE: resource {action}"


def privsep_empty_hint(resource: str = "results") -> str:
    """Hint when a list tool returns empty (may be ACL/privsep)."""
    return f"No {resource} found.\n{PRIVSEP_EMPTY_HINT}"


def console_ticket_footer(kind: str = "VNC") -> str:
    """Note that console tools only mint tickets (D6)."""
    return (
        f"💡 Ticket only — connect externally with a {kind} client "
        "(noVNC / virt-viewer / termproxy). This MCP does not proxy the console."
    )


def privilege_required_note(context: str = "this operation") -> str:
    """Note that elevated Proxmox privileges are typically required."""
    return (
        f"💡 Note: {context} often requires elevated privileges "
        "(e.g. Sys.Modify / root@pam). A 403 usually means token ACL, not a missing tool."
    )


def validate_download_url(url: str) -> str:
    """Allow only http/https URLs for download_url_to_storage (SSRF soft guard)."""
    cleaned = (url or "").strip()
    if not cleaned:
        raise ValueError("url is required")
    lower = cleaned.lower()
    if not (lower.startswith("http://") or lower.startswith("https://")):
        raise ValueError(
            "url must start with http:// or https:// "
            "(file:// and other schemes are rejected)"
        )
    return cleaned


def wait_for_upid(
    proxmox: Any,
    node: str,
    upid: Any,
    *,
    timeout: float = 120.0,
    poll_interval: float = 1.0,
) -> dict:
    """Block until a task UPID stops (used by force-delete stop-then-delete).

    Returns the final status dict. Raises TimeoutError or RuntimeError on failure.
    """
    import time

    deadline = time.time() + timeout
    last: Optional[dict] = None
    while time.time() < deadline:
        last = proxmox.nodes(node).tasks(upid).status.get()
        if (last or {}).get("status") == "stopped":
            exitstatus = str((last or {}).get("exitstatus", "unknown"))
            if exitstatus.upper() not in ("OK", "WARNING"):
                raise RuntimeError(
                    f"Task {upid} failed with exitstatus={exitstatus}: {last}"
                )
            return last or {}
        time.sleep(poll_interval)
    raise TimeoutError(
        f"Task {upid} still running after {timeout}s. Last status: {last}"
    )


def check_exec_allowlist(command: str) -> None:
    """Enforce optional PROXMOX_MCP_EXEC_ALLOWLIST regex (shared by VM + LXC exec)."""
    pattern = os.environ.get("PROXMOX_MCP_EXEC_ALLOWLIST", "").strip()
    if not pattern:
        return
    if not re.search(pattern, command):
        raise ValueError(
            f"Command blocked by PROXMOX_MCP_EXEC_ALLOWLIST (pattern={pattern!r})"
        )


def parse_net_kv(net_value: str) -> Dict[str, str]:
    """Parse a Proxmox netN config string into a dict of key=value pairs."""
    result: Dict[str, str] = {}
    if not net_value:
        return result
    for part in str(net_value).split(","):
        part = part.strip()
        if not part:
            continue
        if "=" in part:
            key, val = part.split("=", 1)
            result[key.strip()] = val.strip()
        else:
            # e.g. virtio / e1000 bare model token on QEMU nets
            result.setdefault("model", part)
    return result


def parse_lxc_networks(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract structured network interfaces from an LXC config dict."""
    networks: List[Dict[str, Any]] = []
    if not isinstance(config, dict):
        return networks
    for key, raw in sorted(config.items()):
        if not re.fullmatch(r"net\d+", str(key)):
            continue
        parsed = parse_net_kv(str(raw))
        ip_val = parsed.get("ip") or parsed.get("ip6")
        mode = "unknown"
        if ip_val:
            mode = "dhcp" if str(ip_val).lower() == "dhcp" else "static"
        networks.append(
            {
                "iface": key,
                "name": parsed.get("name"),
                "bridge": parsed.get("bridge"),
                "hwaddr": parsed.get("hwaddr") or parsed.get("mac"),
                "ip": ip_val,
                "gw": parsed.get("gw") or parsed.get("gw6"),
                "mode": mode,
                "raw": raw,
            }
        )
    return networks


def configured_ipv4_summary(networks: List[Dict[str, Any]]) -> Optional[str]:
    """Best-effort configured IPv4 string for list views (static CIDR or 'dhcp')."""
    for net in networks:
        ip = net.get("ip")
        if not ip:
            continue
        # Prefer IPv4-looking values
        if ":" in str(ip) and "." not in str(ip):
            continue
        return str(ip)
    return None


def assert_id_absent(proxmox: Any, node: str, vmid: str, kind: str) -> None:
    """Raise ValueError if a guest already occupies ``vmid``.

    Args:
        kind: ``qemu`` (QEMU only), ``lxc`` (LXC only), or ``any`` (both;
            used by create_lxc to refuse IDs already taken by a VM).
    """
    if kind in ("qemu", "any"):
        try:
            proxmox.nodes(node).qemu(vmid).config.get()
            if kind == "any":
                raise ValueError(
                    f"VM ID {vmid} is already used by a QEMU VM on node {node}"
                )
            raise ValueError(f"VM {vmid} already exists on node {node}")
        except ValueError:
            raise
        except Exception as e:
            if not is_missing_resource_error(e):
                raise

    if kind in ("lxc", "any"):
        try:
            proxmox.nodes(node).lxc(vmid).config.get()
            if kind == "any":
                raise ValueError(
                    f"VM ID {vmid} is already used by an LXC container on node {node}"
                )
            raise ValueError(f"LXC container {vmid} already exists on node {node}")
        except ValueError:
            raise
        except Exception as e:
            if not is_missing_resource_error(e):
                raise


def pick_storage(
    storage_list: List[dict],
    *,
    content: str,
    preferred: Optional[List[str]] = None,
    explicit: Optional[str] = None,
) -> str:
    """Pick a storage id that supports ``content`` (e.g. images, rootdir)."""
    storage_info = {s["storage"]: s for s in storage_list}

    if explicit is not None:
        if explicit not in storage_info:
            raise ValueError(f"Storage '{explicit}' not found")
        if content not in storage_info[explicit].get("content", ""):
            raise ValueError(f"Storage '{explicit}' does not support {content}")
        return explicit

    for name in preferred or []:
        s = storage_info.get(name)
        if s and content in s.get("content", ""):
            return name

    for s in storage_list:
        if content in s.get("content", ""):
            return s["storage"]

    raise ValueError(f"No suitable storage found for {content}")
