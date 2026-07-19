"""Storage replication tools for Proxmox MCP."""
from typing import List, Optional
from mcp.types import TextContent as Content
from .base import ProxmoxTool


class ReplicationTools(ProxmoxTool):
    """List, inspect, and trigger guest storage replication jobs."""

    def list_replication_jobs(self) -> List[Content]:
        try:
            jobs = self.proxmox.cluster.replication.get()
            return self._format_response(jobs)
        except Exception as e:
            self._handle_error("list replication jobs", e)

    def get_replication_status(self, node: str, jobid: str) -> List[Content]:
        try:
            status = self.proxmox.nodes(node).replication(jobid).status.get()
            return self._format_response(status)
        except Exception as e:
            self._handle_error(f"get replication status {jobid}", e)

    def run_replication_job(self, node: str, jobid: str) -> List[Content]:
        try:
            result = self.proxmox.nodes(node).replication(jobid).schedule_now.post()
            return [
                Content(
                    type="text",
                    text=f"Replication job '{jobid}' scheduled now on {node}\nResult: {result}",
                )
            ]
        except Exception as e:
            self._handle_error(f"run replication job {jobid}", e)

    def create_replication_job(
        self,
        id: str,
        target: str,
        schedule: Optional[str] = None,
        comment: Optional[str] = None,
        enabled: bool = True,
    ) -> List[Content]:
        """Create a cluster replication job (id like '100-0')."""
        try:
            params = {"id": id, "target": target, "enabled": 1 if enabled else 0}
            if schedule is not None:
                params["schedule"] = schedule
            if comment is not None:
                params["comment"] = comment
            result = self.proxmox.cluster.replication.post(**params)
            return [Content(type="text", text=f"Replication job '{id}' created\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"create replication job {id}", e)

    def delete_replication_job(self, id: str) -> List[Content]:
        try:
            result = self.proxmox.cluster.replication(id).delete()
            return [Content(type="text", text=f"Replication job '{id}' deleted\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"delete replication job {id}", e)
