"""Backup (vzdump) tools for Proxmox MCP."""
from typing import List, Optional
from mcp.types import TextContent as Content
from .base import ProxmoxTool
from .guest import normalize_guest_type
from .helpers import destructive_warning, privsep_empty_hint, upid_response_footer


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
            return [
                Content(
                    type="text",
                    text=(
                        f"Backup of {vmid} initiated\n"
                        f"{upid_response_footer(result, node=node)}"
                    ),
                )
            ]
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
            if not content:
                return [Content(type="text", text=privsep_empty_hint("backups"))]
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
            gtype = normalize_guest_type(guest_type)
            params = {"archive": archive, "force": 1 if force else 0}
            if storage:
                params["storage"] = storage
            if gtype == "lxc":
                result = self.proxmox.nodes(node).lxc.create(vmid=vmid, **params)
            else:
                result = self.proxmox.nodes(node).qemu.create(vmid=vmid, **params)
            lines = [
                f"Restore of archive to {gtype} {vmid} initiated",
            ]
            if force:
                lines.append(
                    "⚠️ WARNING: force=True — existing guest disks/config may be overwritten."
                )
            lines.append(upid_response_footer(result, node=node))
            return [Content(type="text", text="\n".join(lines))]
        except Exception as e:
            self._handle_error(f"restore backup to {vmid}", e)

    def delete_backup(self, node: str, storage: str, volume: str) -> List[Content]:
        try:
            result = self.proxmox.nodes(node).storage(storage).content(volume).delete()
            return [
                Content(
                    type="text",
                    text=(
                        f"{destructive_warning('deleted')}\n"
                        f"Deleted backup volume {volume}\nResult: {result}"
                    ),
                )
            ]
        except Exception as e:
            self._handle_error(f"delete backup {volume}", e)

    def list_backup_jobs(self) -> List[Content]:
        """List scheduled cluster backup jobs."""
        try:
            jobs = self.proxmox.cluster.backup.get()
            if not jobs:
                return [Content(type="text", text=privsep_empty_hint("backup jobs"))]
            return self._format_response(jobs)
        except Exception as e:
            self._handle_error("list backup jobs", e)

    def create_backup_job(
        self,
        schedule: str,
        storage: str,
        vmid: Optional[str] = None,
        mode: str = "snapshot",
        compress: str = "zstd",
        enabled: bool = True,
        comment: Optional[str] = None,
        mailto: Optional[str] = None,
        mailnotification: Optional[str] = None,
        all: bool = False,
    ) -> List[Content]:
        """Create a scheduled /cluster/backup job."""
        try:
            params = {
                "schedule": schedule,
                "storage": storage,
                "mode": mode,
                "compress": compress,
                "enabled": 1 if enabled else 0,
                "all": 1 if all else 0,
            }
            if vmid is not None:
                params["vmid"] = vmid
            if comment is not None:
                params["comment"] = comment
            if mailto is not None:
                params["mailto"] = mailto
            if mailnotification is not None:
                params["mailnotification"] = mailnotification
            result = self.proxmox.cluster.backup.post(**params)
            return [
                Content(
                    type="text",
                    text=f"Backup job created\nParams: {params}\nResult: {result}",
                )
            ]
        except Exception as e:
            self._handle_error("create backup job", e)

    def delete_backup_job(self, id: str) -> List[Content]:
        try:
            result = self.proxmox.cluster.backup(id).delete()
            return [
                Content(
                    type="text",
                    text=(
                        f"{destructive_warning('deleted')}\n"
                        f"Backup job '{id}' deleted\nResult: {result}"
                    ),
                )
            ]
        except Exception as e:
            self._handle_error(f"delete backup job {id}", e)
