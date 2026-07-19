"""ACME (Let's Encrypt) read tools for Proxmox MCP."""
from typing import List
from mcp.types import TextContent as Content
from .base import ProxmoxTool


class ACMETools(ProxmoxTool):
    """Read ACME plugins and accounts (no order/renew — Phase C)."""

    def list_acme_plugins(self) -> List[Content]:
        try:
            plugins = self.proxmox.cluster.acme.plugins.get()
            return self._format_response(plugins)
        except Exception as e:
            self._handle_error("list ACME plugins", e)

    def list_acme_accounts(self) -> List[Content]:
        try:
            accounts = self.proxmox.cluster.acme.account.get()
            return self._format_response(accounts)
        except Exception as e:
            self._handle_error("list ACME accounts", e)

    def get_acme_directories(self) -> List[Content]:
        try:
            dirs = self.proxmox.cluster.acme.directories.get()
            return self._format_response(dirs)
        except Exception as e:
            self._handle_error("get ACME directories", e)
