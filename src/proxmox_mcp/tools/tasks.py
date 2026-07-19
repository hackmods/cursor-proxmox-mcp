"""Async task status tools for Proxmox MCP."""
from typing import List
from mcp.types import TextContent as Content
from .base import ProxmoxTool


class TaskTools(ProxmoxTool):
    """Tools for inspecting Proxmox task (UPID) status."""

    def get_task_status(self, node: str, upid: str) -> List[Content]:
        """Get status for a task UPID on a node."""
        try:
            status = self.proxmox.nodes(node).tasks(upid).status.get()
            return self._format_response(status)
        except Exception as e:
            self._handle_error(f"get task status {upid}", e)

    def list_tasks(self, node: str) -> List[Content]:
        """List recent tasks on a node."""
        try:
            tasks = self.proxmox.nodes(node).tasks.get()
            return self._format_response(tasks)
        except Exception as e:
            self._handle_error(f"list tasks on {node}", e)
