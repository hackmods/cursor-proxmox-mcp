"""High Availability (HA) tools for Proxmox MCP."""
from typing import List, Optional
from mcp.types import TextContent as Content
from .base import ProxmoxTool


class HATools(ProxmoxTool):
    """HA status, groups, and resources."""

    def get_ha_status(self) -> List[Content]:
        try:
            status = self.proxmox.cluster.ha.status.current.get()
            return self._format_response(status)
        except Exception as e:
            self._handle_error("get HA status", e)

    def list_ha_groups(self) -> List[Content]:
        try:
            groups = self.proxmox.cluster.ha.groups.get()
            return self._format_response(groups)
        except Exception as e:
            self._handle_error("list HA groups", e)

    def create_ha_group(
        self, group: str, nodes: str, comment: Optional[str] = None
    ) -> List[Content]:
        try:
            params = {"group": group, "nodes": nodes}
            if comment:
                params["comment"] = comment
            result = self.proxmox.cluster.ha.groups.post(**params)
            return [Content(type="text", text=f"HA group '{group}' created\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"create HA group {group}", e)

    def delete_ha_group(self, group: str) -> List[Content]:
        try:
            result = self.proxmox.cluster.ha.groups(group).delete()
            return [Content(type="text", text=f"HA group '{group}' deleted\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"delete HA group {group}", e)

    def list_ha_resources(self) -> List[Content]:
        try:
            resources = self.proxmox.cluster.ha.resources.get()
            return self._format_response(resources)
        except Exception as e:
            self._handle_error("list HA resources", e)

    def create_ha_resource(
        self,
        sid: str,
        group: Optional[str] = None,
        state: str = "started",
        comment: Optional[str] = None,
    ) -> List[Content]:
        try:
            params = {"sid": sid, "state": state}
            if group:
                params["group"] = group
            if comment:
                params["comment"] = comment
            result = self.proxmox.cluster.ha.resources.post(**params)
            return [Content(type="text", text=f"HA resource '{sid}' created\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"create HA resource {sid}", e)

    def update_ha_resource(
        self,
        sid: str,
        group: Optional[str] = None,
        state: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> List[Content]:
        try:
            params = {}
            if group is not None:
                params["group"] = group
            if state is not None:
                params["state"] = state
            if comment is not None:
                params["comment"] = comment
            result = self.proxmox.cluster.ha.resources(sid).put(**params)
            return [Content(type="text", text=f"HA resource '{sid}' updated\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"update HA resource {sid}", e)

    def delete_ha_resource(self, sid: str) -> List[Content]:
        try:
            result = self.proxmox.cluster.ha.resources(sid).delete()
            return [Content(type="text", text=f"HA resource '{sid}' deleted\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"delete HA resource {sid}", e)
