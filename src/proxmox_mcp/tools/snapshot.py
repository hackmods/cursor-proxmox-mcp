"""Snapshot management tools for QEMU VMs and LXC containers."""
from typing import List, Optional
from mcp.types import TextContent as Content
from .base import ProxmoxTool
from .guest import guest_resource, normalize_guest_type
from .helpers import (
    destructive_warning,
    guest_not_found_message,
    is_missing_resource_error,
    upid_response_footer,
)


class SnapshotTools(ProxmoxTool):
    """Create, list, delete, and rollback guest snapshots."""

    def _not_found(self, node: str, vmid: str, guest_type: str, error: Exception) -> None:
        if is_missing_resource_error(error):
            raise ValueError(
                guest_not_found_message(vmid, node, normalize_guest_type(guest_type))
            ) from error

    def list_snapshots(self, node: str, vmid: str, guest_type: str = "qemu") -> List[Content]:
        try:
            gtype = normalize_guest_type(guest_type)
            snaps = guest_resource(self.proxmox, node, vmid, gtype).snapshot.get()
            return self._format_response(snaps)
        except ValueError:
            raise
        except Exception as e:
            self._not_found(node, vmid, guest_type, e)
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
            return [
                Content(
                    type="text",
                    text=(
                        f"Snapshot '{snapname}' create initiated\n"
                        f"{upid_response_footer(result, node=node)}"
                    ),
                )
            ]
        except ValueError:
            raise
        except Exception as e:
            self._not_found(node, vmid, guest_type, e)
            self._handle_error(f"create snapshot {snapname}", e)

    def delete_snapshot(
        self, node: str, vmid: str, snapname: str, guest_type: str = "qemu"
    ) -> List[Content]:
        try:
            gtype = normalize_guest_type(guest_type)
            result = guest_resource(self.proxmox, node, vmid, gtype).snapshot(snapname).delete()
            return [
                Content(
                    type="text",
                    text=(
                        f"{destructive_warning('deleted')}\n"
                        f"Snapshot '{snapname}' delete initiated\n"
                        f"{upid_response_footer(result, node=node)}"
                    ),
                )
            ]
        except ValueError:
            raise
        except Exception as e:
            self._not_found(node, vmid, guest_type, e)
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
                        f"{destructive_warning('rolled back')}\n"
                        f"⚠️ Rollback to '{snapname}' initiated for {gtype} {vmid}\n"
                        f"{upid_response_footer(result, node=node)}"
                    ),
                )
            ]
        except ValueError:
            raise
        except Exception as e:
            self._not_found(node, vmid, guest_type, e)
            self._handle_error(f"rollback snapshot {snapname}", e)
