"""Node network listing tools."""
from typing import List
from mcp.types import TextContent as Content
from .base import ProxmoxTool


class NetworkTools(ProxmoxTool):
    """Node network interface discovery."""

    def list_node_networks(self, node: str) -> List[Content]:
        try:
            networks = self.proxmox.nodes(node).network.get()
            return self._format_response(networks)
        except Exception as e:
            self._handle_error(f"list networks on {node}", e)
