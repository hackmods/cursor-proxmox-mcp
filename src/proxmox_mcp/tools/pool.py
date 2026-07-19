"""Resource pool tools for Proxmox MCP."""
from typing import List, Optional
from mcp.types import TextContent as Content
from .base import ProxmoxTool


class PoolTools(ProxmoxTool):
    """List and manage resource pools."""

    def list_pools(self) -> List[Content]:
        try:
            pools = self.proxmox.pools.get()
            return self._format_response(pools)
        except Exception as e:
            self._handle_error("list pools", e)

    def get_pool(self, poolid: str) -> List[Content]:
        try:
            pool = self.proxmox.pools(poolid).get()
            return self._format_response(pool)
        except Exception as e:
            self._handle_error(f"get pool {poolid}", e)

    def create_pool(self, poolid: str, comment: Optional[str] = None) -> List[Content]:
        try:
            params = {"poolid": poolid}
            if comment is not None:
                params["comment"] = comment
            result = self.proxmox.pools.post(**params)
            return [Content(type="text", text=f"Pool '{poolid}' created\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"create pool {poolid}", e)

    def update_pool(
        self,
        poolid: str,
        comment: Optional[str] = None,
        vms: Optional[str] = None,
        storage: Optional[str] = None,
        delete: bool = False,
    ) -> List[Content]:
        """Add or remove pool members (vms/storage comma-separated)."""
        try:
            params = {}
            if comment is not None:
                params["comment"] = comment
            if vms is not None:
                params["vms"] = vms
            if storage is not None:
                params["storage"] = storage
            if delete:
                params["delete"] = 1
            if not params:
                raise ValueError("Provide comment, vms, and/or storage to update")
            result = self.proxmox.pools(poolid).put(**params)
            action = "removed from" if delete else "updated on"
            return [
                Content(
                    type="text",
                    text=f"Pool '{poolid}' {action}\nParams: {params}\nResult: {result}",
                )
            ]
        except ValueError:
            raise
        except Exception as e:
            self._handle_error(f"update pool {poolid}", e)

    def delete_pool(self, poolid: str) -> List[Content]:
        try:
            result = self.proxmox.pools(poolid).delete()
            return [Content(type="text", text=f"Pool '{poolid}' deleted\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"delete pool {poolid}", e)
