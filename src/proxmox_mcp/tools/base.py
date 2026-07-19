"""
Base classes and utilities for Proxmox MCP tools.
"""
from __future__ import annotations

import json
import logging
from typing import Any, List, Optional

from mcp.types import TextContent as Content
from proxmoxer import ProxmoxAPI

from ..errors import classify_proxmox_error
from ..formatting import ProxmoxTemplates
from .helpers import acl_denied_message, is_permission_denied_error


class ProxmoxTool:
    """Base class for Proxmox MCP tools."""

    def __init__(self, proxmox_api: ProxmoxAPI):
        self.proxmox = proxmox_api
        self.logger = logging.getLogger(f"proxmox-mcp.{self.__class__.__name__.lower()}")

    def _format_response(self, data: Any, resource_type: Optional[str] = None) -> List[Content]:
        if resource_type == "nodes":
            formatted = ProxmoxTemplates.node_list(data)
        elif resource_type == "node_status":
            if isinstance(data, tuple) and len(data) == 2:
                formatted = ProxmoxTemplates.node_status(data[0], data[1])
            else:
                formatted = ProxmoxTemplates.node_status("unknown", data)
        elif resource_type == "vms":
            formatted = ProxmoxTemplates.vm_list(data)
        elif resource_type == "storage":
            formatted = ProxmoxTemplates.storage_list(data)
        elif resource_type == "containers":
            formatted = ProxmoxTemplates.container_list(data)
        elif resource_type == "cluster":
            formatted = ProxmoxTemplates.cluster_status(data)
        else:
            formatted = json.dumps(data, indent=2)

        return [Content(type="text", text=formatted)]

    def _handle_error(self, operation: str, error: Exception) -> None:
        """Log and raise a typed, sanitized error (still ValueError/RuntimeError subclasses)."""
        classified = classify_proxmox_error(operation, error)
        self.logger.error("%s", classified)
        raise classified

    def _handle_mutation_error(
        self,
        operation: str,
        error: Exception,
        *,
        code: str = "acl_denied",
        path: Optional[str] = None,
        mcp_fallback: Optional[str] = None,
    ) -> None:
        """Like ``_handle_error`` but emit structured ACL denial on 403."""
        if is_permission_denied_error(error):
            msg = acl_denied_message(
                code,
                operation=operation,
                path=path,
                mcp_fallback=mcp_fallback,
                cause=str(error),
            )
            self.logger.error("%s", msg)
            raise ValueError(msg) from error
        self._handle_error(operation, error)