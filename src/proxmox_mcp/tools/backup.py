"""Backup (vzdump) tools for Proxmox MCP."""
from typing import List, Optional
from mcp.types import TextContent as Content
from .base import ProxmoxTool


class BackupTools(ProxmoxTool):
    """Create, list, restore, and delete vzdump backups."""

    def create_backup(
        self,
        node: str,
        vmid: str,
        storage: Optional[str] = None,
        mode: str = "snapshot",
        compress: str = "zstd",
        notes: Optional[str] = None,
    ) -> List[Content]:
        try:
            params = {
                "vmid": vmid,
                "mode": mode,
                "compress": compress,
            }
            if storage:
                params["storage"] = storage
            if notes:
                params["notes-template"] = notes
            result = self.proxmox.nodes(node).vzdump.create(**params)
            return [Content(type="text", text=f"Backup of {vmid} initiated\nTask ID: {result}")]
        except Exception as e:
            self._handle_error(f"create backup for {vmid}", e)

    def list_backups(
        self, node: str, storage: str, vmid: Optional[str] = None
    ) -> List[Content]:
        try:
            params = {"content": "backup"}
            content = self.proxmox.nodes(node).storage(storage).content.get(**params)
            if vmid:
                content = [
                    item
                    for item in content
                    if str(item.get("vmid", "")) == str(vmid)
                    or str(vmid) in str(item.get("volid", ""))
                ]
            return self._format_response(content)
        except Exception as e:
            self._handle_error(f"list backups on {storage}", e)

    def restore_backup(
        self,
        node: str,
        archive: str,
        vmid: str,
        storage: Optional[str] = None,
        force: bool = False,
        guest_type: str = "qemu",
    ) -> List[Content]:
        try:
            params = {"archive": archive, "force": 1 if force else 0}
            if storage:
                params["storage"] = storage
            gtype = guest_type.strip().lower()
            if gtype in ("lxc", "ct", "container"):
                result = self.proxmox.nodes(node).lxc.create(vmid=vmid, **params)
            else:
                result = self.proxmox.nodes(node).qemu.create(vmid=vmid, **params)
            return [
                Content(
                    type="text",
                    text=f"Restore of archive to {guest_type} {vmid} initiated\nTask ID: {result}",
                )
            ]
        except Exception as e:
            self._handle_error(f"restore backup to {vmid}", e)

    def delete_backup(self, node: str, storage: str, volume: str) -> List[Content]:
        try:
            result = self.proxmox.nodes(node).storage(storage).content(volume).delete()
            return [Content(type="text", text=f"Deleted backup volume {volume}\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"delete backup {volume}", e)
