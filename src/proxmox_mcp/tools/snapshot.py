"""Snapshot management tools for QEMU VMs and LXC containers."""
from typing import List, Optional
from mcp.types import TextContent as Content
from .base import ProxmoxTool
from .guest import guest_resource, normalize_guest_type


class SnapshotTools(ProxmoxTool):
    """Create, list, delete, and rollback guest snapshots."""

    def list_snapshots(self, node: str, vmid: str, guest_type: str = "qemu") -> List[Content]:
        try:
            gtype = normalize_guest_type(guest_type)
            snaps = guest_resource(self.proxmox, node, vmid, gtype).snapshot.get()
            return self._format_response(snaps)
        except Exception as e:
            self._handle_error(f"list snapshots for {guest_type} {vmid}", e)

    def create_snapshot(
        self,
        node: str,
        vmid: str,
        snapname: str,
        guest_type: str = "qemu",
        description: Optional[str] = None,
        vmstate: bool = False,
    ) -> List[Content]:
        try:
            gtype = normalize_guest_type(guest_type)
            params = {"snapname": snapname}
            if description:
                params["description"] = description
            if gtype == "qemu" and vmstate:
                params["vmstate"] = 1
            result = guest_resource(self.proxmox, node, vmid, gtype).snapshot.create(**params)
            return [Content(type="text", text=f"Snapshot '{snapname}' create initiated\nTask ID: {result}")]
        except Exception as e:
            self._handle_error(f"create snapshot {snapname}", e)

    def delete_snapshot(
        self, node: str, vmid: str, snapname: str, guest_type: str = "qemu"
    ) -> List[Content]:
        try:
            gtype = normalize_guest_type(guest_type)
            result = guest_resource(self.proxmox, node, vmid, gtype).snapshot(snapname).delete()
            return [Content(type="text", text=f"Snapshot '{snapname}' delete initiated\nTask ID: {result}")]
        except Exception as e:
            self._handle_error(f"delete snapshot {snapname}", e)

    def rollback_snapshot(
        self, node: str, vmid: str, snapname: str, guest_type: str = "qemu"
    ) -> List[Content]:
        try:
            gtype = normalize_guest_type(guest_type)
            result = guest_resource(self.proxmox, node, vmid, gtype).snapshot(snapname).rollback.post()
            return [
                Content(
                    type="text",
                    text=(
                        f"⚠️ Rollback to '{snapname}' initiated for {gtype} {vmid}\n"
                        f"Task ID: {result}"
                    ),
                )
            ]
        except Exception as e:
            self._handle_error(f"rollback snapshot {snapname}", e)
