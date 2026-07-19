"""
Storage-related tools for Proxmox MCP.

This module provides tools for managing and monitoring Proxmox storage:
- Listing all storage pools across the cluster
- Retrieving detailed storage information including:
  * Storage type and content types
  * Usage statistics and capacity
  * Availability status
  * Node assignments

The tools implement fallback mechanisms for scenarios where
detailed storage information might be temporarily unavailable.
"""
from typing import List, Optional
from mcp.types import TextContent as Content
from .base import ProxmoxTool


class StorageTools(ProxmoxTool):
    """Tools for managing Proxmox storage pools and content."""

    def get_storage(self) -> List[Content]:
        """List storage pools across the cluster with detailed status."""
        try:
            result = self.proxmox.storage.get()
            storage = []

            for store in result:
                try:
                    status = self.proxmox.nodes(store.get("node", "localhost")).storage(
                        store["storage"]
                    ).status.get()
                    storage.append({
                        "storage": store["storage"],
                        "type": store["type"],
                        "content": store.get("content", []),
                        "status": "online" if store.get("enabled", True) else "offline",
                        "used": status.get("used", 0),
                        "total": status.get("total", 0),
                        "available": status.get("avail", 0),
                    })
                except Exception:
                    storage.append({
                        "storage": store["storage"],
                        "type": store["type"],
                        "content": store.get("content", []),
                        "status": "online" if store.get("enabled", True) else "offline",
                        "used": 0,
                        "total": 0,
                        "available": 0,
                    })

            return self._format_response(storage, "storage")
        except Exception as e:
            self._handle_error("get storage", e)

    def get_storage_content(
        self, node: str, storage: str, content: Optional[str] = None
    ) -> List[Content]:
        """List content on a storage (iso, vztmpl, backup, images, etc.)."""
        try:
            params = {}
            if content:
                params["content"] = content
            items = self.proxmox.nodes(node).storage(storage).content.get(**params)
            return self._format_response(items)
        except Exception as e:
            self._handle_error(f"get storage content on {storage}", e)

    def delete_storage_content(self, node: str, storage: str, volume: str) -> List[Content]:
        """Delete a volume from storage (ISO, backup, disk image, etc.)."""
        try:
            result = self.proxmox.nodes(node).storage(storage).content(volume).delete()
            return [
                Content(
                    type="text",
                    text=f"⚠️ Deleted storage volume {volume} from {storage}\nResult: {result}",
                )
            ]
        except Exception as e:
            self._handle_error(f"delete storage content {volume}", e)

    def download_url_to_storage(
        self,
        node: str,
        storage: str,
        url: str,
        filename: Optional[str] = None,
        content: str = "iso",
    ) -> List[Content]:
        """Download a file from URL into storage (ISO/vztmpl)."""
        try:
            params = {"url": url, "content": content}
            if filename:
                params["filename"] = filename
            result = self.proxmox.nodes(node).storage(storage)("download-url").post(**params)
            return [
                Content(
                    type="text",
                    text=f"Download to {storage} initiated\nURL: {url}\nTask ID: {result}",
                )
            ]
        except Exception as e:
            self._handle_error(f"download URL to {storage}", e)

    def create_storage(
        self,
        storage: str,
        type: str,
        content: Optional[str] = None,
        path: Optional[str] = None,
        server: Optional[str] = None,
        export: Optional[str] = None,
        vgname: Optional[str] = None,
        pool: Optional[str] = None,
        monhost: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        nodes: Optional[str] = None,
        disable: bool = False,
    ) -> List[Content]:
        """Create a cluster storage definition."""
        try:
            params = {"storage": storage, "type": type}
            if content is not None:
                params["content"] = content
            if path is not None:
                params["path"] = path
            if server is not None:
                params["server"] = server
            if export is not None:
                params["export"] = export
            if vgname is not None:
                params["vgname"] = vgname
            if pool is not None:
                params["pool"] = pool
            if monhost is not None:
                params["monhost"] = monhost
            if username is not None:
                params["username"] = username
            if password is not None:
                params["password"] = password
            if nodes is not None:
                params["nodes"] = nodes
            if disable:
                params["disable"] = 1
            result = self.proxmox.storage.post(**params)
            return [Content(type="text", text=f"Storage '{storage}' created\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"create storage {storage}", e)

    def update_storage(
        self,
        storage: str,
        content: Optional[str] = None,
        nodes: Optional[str] = None,
        disable: Optional[bool] = None,
    ) -> List[Content]:
        """Update a cluster storage definition."""
        try:
            params = {}
            if content is not None:
                params["content"] = content
            if nodes is not None:
                params["nodes"] = nodes
            if disable is not None:
                params["disable"] = 1 if disable else 0
            result = self.proxmox.storage(storage).put(**params)
            return [Content(type="text", text=f"Storage '{storage}' updated\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"update storage {storage}", e)

    def delete_storage(self, storage: str) -> List[Content]:
        """Delete a cluster storage definition (does not wipe underlying data by default)."""
        try:
            result = self.proxmox.storage(storage).delete()
            return [
                Content(
                    type="text",
                    text=f"⚠️ Storage definition '{storage}' deleted\nResult: {result}",
                )
            ]
        except Exception as e:
            self._handle_error(f"delete storage {storage}", e)
