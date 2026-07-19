"""Migration tools for QEMU VMs and LXC containers."""
from typing import List
from mcp.types import TextContent as Content
from .base import ProxmoxTool
from .guest import guest_resource, normalize_guest_type


class MigrateTools(ProxmoxTool):
    """Migrate guests between cluster nodes."""

    def migrate_guest(
        self,
        node: str,
        vmid: str,
        target: str,
        guest_type: str = "qemu",
        online: bool = True,
        with_local_disks: bool = False,
    ) -> List[Content]:
        try:
            gtype = normalize_guest_type(guest_type)
            params = {"target": target}
            if gtype == "qemu":
                params["online"] = 1 if online else 0
                if with_local_disks:
                    params["with-local-disks"] = 1
            else:
                params["online"] = 1 if online else 0
                if with_local_disks:
                    params["restart"] = 1
            result = guest_resource(self.proxmox, node, vmid, gtype).migrate.post(**params)
            return [
                Content(
                    type="text",
                    text=(
                        f"Migration of {gtype} {vmid} from {node} → {target} initiated\n"
                        f"Task ID: {result}"
                    ),
                )
            ]
        except Exception as e:
            self._handle_error(f"migrate {guest_type} {vmid} to {target}", e)
