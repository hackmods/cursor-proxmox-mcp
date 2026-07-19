"""Shared helpers for guest/storage operations."""
from __future__ import annotations

from typing import Any, List, Optional

# Lab defaults (public create params for bridge/IP remain Phase D — D11/D18)
DEFAULT_BRIDGE = "vmbr0"
DEFAULT_LXC_FEATURES = "nesting=1"
DEFAULT_NET0 = f"virtio,bridge={DEFAULT_BRIDGE}"


def is_missing_resource_error(error: BaseException) -> bool:
    """True if proxmoxer/API error indicates the resource does not exist."""
    text = str(error).lower()
    return "does not exist" in text or "not found" in text


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
