"""Shared helpers for QEMU vs LXC guest API routing."""
from typing import Any, Literal

GuestType = Literal["qemu", "lxc"]


def guest_resource(proxmox: Any, node: str, vmid: str, guest_type: GuestType) -> Any:
    """Return the proxmoxer resource for a QEMU VM or LXC container."""
    node_api = proxmox.nodes(node)
    if guest_type == "qemu":
        return node_api.qemu(vmid)
    if guest_type == "lxc":
        return node_api.lxc(vmid)
    raise ValueError(f"guest_type must be 'qemu' or 'lxc', got {guest_type!r}")


def normalize_guest_type(guest_type: str) -> GuestType:
    """Normalize user input to qemu|lxc."""
    value = (guest_type or "").strip().lower()
    if value in ("qemu", "vm", "kvm"):
        return "qemu"
    if value in ("lxc", "ct", "container"):
        return "lxc"
    raise ValueError("guest_type must be 'qemu' or 'lxc'")
