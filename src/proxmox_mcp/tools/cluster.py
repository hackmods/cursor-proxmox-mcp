"""
Cluster-related tools for Proxmox MCP.

This module provides tools for monitoring and managing Proxmox clusters:
- Retrieving overall cluster health status
- Monitoring quorum status and node count
- Tracking cluster resources and configuration
- Checking cluster-wide service availability

The tools provide essential information for maintaining
cluster health and ensuring proper operation.
"""
from typing import List, Optional
from mcp.types import TextContent as Content
from .base import ProxmoxTool

class ClusterTools(ProxmoxTool):
    """Tools for managing Proxmox cluster.
    
    Provides functionality for:
    - Monitoring cluster health and status
    - Tracking quorum and node membership
    - Managing cluster-wide resources
    - Verifying cluster configuration
    
    Essential for maintaining cluster health and ensuring
    proper operation of the Proxmox environment.
    """

    def get_cluster_status(self) -> List[Content]:
        """Get overall Proxmox cluster health and configuration status.

        Retrieves comprehensive cluster information including:
        - Cluster name and identity
        - Quorum status (essential for cluster operations)
        - Active node count and health
        - Resource distribution and status
        
        This information is critical for:
        - Ensuring cluster stability
        - Monitoring node membership
        - Verifying resource availability
        - Detecting potential issues

        Returns:
            List of Content objects containing formatted cluster status:
            {
                "name": "cluster-name",
                "quorum": true/false,
                "nodes": count,
                "resources": [
                    {
                        "type": "resource-type",
                        "status": "status"
                    }
                ]
            }

        Raises:
            RuntimeError: If cluster status query fails due to:
                        - Network connectivity issues
                        - Authentication problems
                        - API endpoint failures
        """
        try:
            result = self.proxmox.cluster.status.get()

            first_item = result[0] if result and len(result) > 0 else {}
            status = {
                "name": first_item.get("name") if first_item else None,
                "quorum": first_item.get("quorate") if first_item else None,
                "nodes": len([node for node in result if node.get("type") == "node"]) if result else 0,
                "resources": [res for res in result if res.get("type") == "resource"] if result else []
            }
            return self._format_response(status, "cluster")
        except Exception as e:
            self._handle_error("get cluster status", e)

    def get_next_vmid(self) -> List[Content]:
        """Return the next free VM/CT ID from the cluster."""
        try:
            nextid = self.proxmox.cluster.nextid.get()
            return [
                Content(
                    type="text",
                    text=(
                        f"Next free VMID: {nextid}\n"
                        f"💡 Best-effort — another create can take this ID before yours; "
                        f"create_vm / create_lxc will fail if it is already used."
                    ),
                )
            ]
        except Exception as e:
            self._handle_error("get next VMID", e)

    def get_version(self) -> List[Content]:
        """Get Proxmox VE API/version info."""
        try:
            version = self.proxmox.version.get()
            return self._format_response(version)
        except Exception as e:
            self._handle_error("get version", e)

    def get_cluster_resources(self, type: Optional[str] = None) -> List[Content]:
        """List cluster resources (vms, storage, node, sdn). Optional type filter."""
        try:
            params = {}
            if type:
                params["type"] = type
            resources = self.proxmox.cluster.resources.get(**params)
            return self._format_response(resources)
        except Exception as e:
            self._handle_error("get cluster resources", e)

    def get_cluster_log(self, max_entries: int = 50) -> List[Content]:
        """Get recent cluster log entries."""
        try:
            log = self.proxmox.cluster.log.get(max=max_entries)
            return self._format_response(log)
        except Exception as e:
            self._handle_error("get cluster log", e)

    def get_cluster_options(self) -> List[Content]:
        """Get cluster-wide options."""
        try:
            options = self.proxmox.cluster.options.get()
            return self._format_response(options)
        except Exception as e:
            self._handle_error("get cluster options", e)

    def get_cluster_join_info(self, node: Optional[str] = None) -> List[Content]:
        """Read join information from an existing cluster member."""
        try:
            params = {}
            if node:
                params["node"] = node
            info = self.proxmox.cluster.config.join.get(**params)
            return self._format_response(info)
        except Exception as e:
            self._handle_error("get cluster join info", e)

    def join_cluster(
        self,
        hostname: str,
        fingerprint: str,
        password: str,
        confirm: str,
        nodeid: Optional[int] = None,
        votes: Optional[int] = None,
        force: bool = False,
    ) -> List[Content]:
        """Join THIS API host into an existing cluster (must target the joining node)."""
        try:
            if confirm != "JOIN":
                raise ValueError(
                    "confirm must be the literal string 'JOIN' "
                    f"(got {confirm!r}). Refusing cluster join."
                )
            if not hostname or not fingerprint or not password:
                raise ValueError("hostname, fingerprint, and password are required")

            params: dict = {
                "hostname": hostname,
                "fingerprint": fingerprint,
                "password": password,
            }
            if nodeid is not None:
                params["nodeid"] = int(nodeid)
            if votes is not None:
                params["votes"] = int(votes)
            if force:
                params["force"] = 1

            result = self.proxmox.cluster.config.join.post(**params)
            return [
                Content(
                    type="text",
                    text=(
                        "⚠️ IRREVERSIBLE: cluster join initiated on THIS API host\n"
                        f"Peer: {hostname}\n"
                        f"Fingerprint: {fingerprint}\n"
                        f"Result/UPID: {result}\n"
                        "💡 Point MCP at the standalone node being joined — not an "
                        "existing cluster member. After join, verify with get_cluster_status."
                    ),
                )
            ]
        except ValueError:
            raise
        except Exception as e:
            self._handle_error("join cluster", e)
