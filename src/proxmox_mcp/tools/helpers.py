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


def is_missing_resource_error(error: BaseException) -> bool:
    """True if proxmoxer/API error indicates the resource does not exist."""
    text = str(error).lower()
    return "does not exist" in text or "not found" in text


def qemu_not_found_message(vmid: str, node: str) -> str:
    """Clear error when a QEMU-only tool is used against a missing/wrong guest."""
    return f"VM {vmid} not found on node {node}\n{QEMU_NOT_FOUND_HINT}"


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
