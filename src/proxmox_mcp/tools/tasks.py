"""Async task status tools for Proxmox MCP."""
import time
from typing import List, Optional
from mcp.types import TextContent as Content
from .base import ProxmoxTool


class TaskTools(ProxmoxTool):
    """Tools for inspecting and waiting on Proxmox task (UPID) status."""

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

    def wait_for_task(
        self,
        node: str,
        upid: str,
        timeout: int = 300,
        poll_interval: float = 2.0,
    ) -> List[Content]:
        """Poll a task UPID until it stops or timeout (seconds) is reached."""
        try:
            if timeout < 1:
                raise ValueError("timeout must be >= 1 second")
            if poll_interval < 0.5:
                poll_interval = 0.5

            deadline = time.time() + timeout
            last: Optional[dict] = None
            while time.time() < deadline:
                last = self.proxmox.nodes(node).tasks(upid).status.get()
                status = (last or {}).get("status", "")
                if status == "stopped":
                    exitstatus = (last or {}).get("exitstatus", "unknown")
                    ok = str(exitstatus).upper() in ("OK", "WARNING")
                    return [
                        Content(
                            type="text",
                            text=(
                                f"{'✅' if ok else '❌'} Task finished\n"
                                f"UPID: {upid}\n"
                                f"Node: {node}\n"
                                f"Exit: {exitstatus}\n"
                                f"Detail: {last}"
                            ),
                        )
                    ]
                time.sleep(poll_interval)

            raise TimeoutError(
                f"Task {upid} still running after {timeout}s. Last status: {last}"
            )
        except (ValueError, TimeoutError):
            raise
        except Exception as e:
            self._handle_error(f"wait for task {upid}", e)
