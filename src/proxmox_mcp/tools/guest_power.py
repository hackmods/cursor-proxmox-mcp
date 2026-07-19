"""Unified guest power / status / pending / disk-move tools (qemu|lxc)."""
from typing import List

from mcp.types import TextContent as Content

from .base import ProxmoxTool
from .guest import guest_resource, normalize_guest_type


class GuestPowerTools(ProxmoxTool):
    """Additive guest_type wrappers; parallel *_vm / *_lxc tools remain."""

    def start_guest(self, node: str, vmid: str, guest_type: str = "qemu") -> List[Content]:
        try:
            gtype = normalize_guest_type(guest_type)
            status = guest_resource(self.proxmox, node, vmid, gtype).status.current.get()
            if status.get("status") == "running":
                return [Content(type="text", text=f"🟢 {gtype} {vmid} is already running")]
            task = guest_resource(self.proxmox, node, vmid, gtype).status.start.post()
            return [
                Content(
                    type="text",
                    text=f"🚀 {gtype} {vmid} start initiated\nTask ID: {task}",
                )
            ]
        except Exception as e:
            self._handle_error(f"start {guest_type} {vmid}", e)

    def stop_guest(self, node: str, vmid: str, guest_type: str = "qemu") -> List[Content]:
        try:
            gtype = normalize_guest_type(guest_type)
            status = guest_resource(self.proxmox, node, vmid, gtype).status.current.get()
            if status.get("status") == "stopped":
                return [Content(type="text", text=f"🔴 {gtype} {vmid} is already stopped")]
            task = guest_resource(self.proxmox, node, vmid, gtype).status.stop.post()
            return [
                Content(
                    type="text",
                    text=f"🛑 {gtype} {vmid} stop initiated\nTask ID: {task}",
                )
            ]
        except Exception as e:
            self._handle_error(f"stop {guest_type} {vmid}", e)

    def shutdown_guest(self, node: str, vmid: str, guest_type: str = "qemu") -> List[Content]:
        try:
            gtype = normalize_guest_type(guest_type)
            status = guest_resource(self.proxmox, node, vmid, gtype).status.current.get()
            if status.get("status") == "stopped":
                return [Content(type="text", text=f"🔴 {gtype} {vmid} is already stopped")]
            task = guest_resource(self.proxmox, node, vmid, gtype).status.shutdown.post()
            return [
                Content(
                    type="text",
                    text=f"💤 {gtype} {vmid} shutdown initiated\nTask ID: {task}",
                )
            ]
        except Exception as e:
            self._handle_error(f"shutdown {guest_type} {vmid}", e)

    def reboot_guest(self, node: str, vmid: str, guest_type: str = "qemu") -> List[Content]:
        try:
            gtype = normalize_guest_type(guest_type)
            status = guest_resource(self.proxmox, node, vmid, gtype).status.current.get()
            if status.get("status") == "stopped":
                return [
                    Content(
                        type="text",
                        text=f"⚠️ Cannot reboot {gtype} {vmid}: currently stopped\nUse start_guest first",
                    )
                ]
            task = guest_resource(self.proxmox, node, vmid, gtype).status.reboot.post()
            return [
                Content(
                    type="text",
                    text=f"🔄 {gtype} {vmid} reboot initiated\nTask ID: {task}",
                )
            ]
        except Exception as e:
            self._handle_error(f"reboot {guest_type} {vmid}", e)

    def delete_guest(
        self, node: str, vmid: str, guest_type: str = "qemu", force: bool = False
    ) -> List[Content]:
        try:
            gtype = normalize_guest_type(guest_type)
            resource = guest_resource(self.proxmox, node, vmid, gtype)
            status = resource.status.current.get()
            current = status.get("status")
            name = status.get("name") or status.get("hostname") or f"{gtype}-{vmid}"
            prefix = ""
            if current == "running":
                if not force:
                    raise ValueError(
                        f"{gtype} {vmid} ({name}) is running. "
                        f"Stop it first or use force=True to stop and delete."
                    )
                resource.status.stop.post()
                prefix = f"🛑 Stopping {gtype} {vmid} ({name}) before deletion...\n"
            else:
                prefix = f"🗑️ Deleting {gtype} {vmid} ({name})...\n"
            task = resource.delete()
            return [
                Content(
                    type="text",
                    text=(
                        f"{prefix}🗑️ {gtype} {vmid} ({name}) deletion initiated\n"
                        f"⚠️ IRREVERSIBLE: config, disks/rootfs, and snapshots will be removed.\n"
                        f"Task ID: {task}"
                    ),
                )
            ]
        except ValueError:
            raise
        except Exception as e:
            self._handle_error(f"delete {guest_type} {vmid}", e)

    def get_guest_status(
        self, node: str, vmid: str, guest_type: str = "qemu"
    ) -> List[Content]:
        try:
            gtype = normalize_guest_type(guest_type)
            status = guest_resource(self.proxmox, node, vmid, gtype).status.current.get()
            return self._format_response(status)
        except Exception as e:
            self._handle_error(f"get status for {guest_type} {vmid}", e)

    def get_guest_pending(
        self, node: str, vmid: str, guest_type: str = "qemu"
    ) -> List[Content]:
        try:
            gtype = normalize_guest_type(guest_type)
            pending = guest_resource(self.proxmox, node, vmid, gtype).pending.get()
            return self._format_response(pending)
        except Exception as e:
            self._handle_error(f"get pending config for {guest_type} {vmid}", e)

    def move_guest_disk(
        self,
        node: str,
        vmid: str,
        disk: str,
        storage: str,
        guest_type: str = "qemu",
        delete: bool = True,
    ) -> List[Content]:
        try:
            gtype = normalize_guest_type(guest_type)
            resource = guest_resource(self.proxmox, node, vmid, gtype)
            params = {"storage": storage, "delete": 1 if delete else 0}
            if gtype == "qemu":
                params["disk"] = disk
                result = resource.move_disk.post(**params)
            else:
                params["volume"] = disk
                result = resource.move_volume.post(**params)
            return [
                Content(
                    type="text",
                    text=(
                        f"Move {disk} on {gtype} {vmid} → storage '{storage}' initiated\n"
                        f"Task ID: {result}"
                    ),
                )
            ]
        except Exception as e:
            self._handle_error(f"move disk on {guest_type} {vmid}", e)
