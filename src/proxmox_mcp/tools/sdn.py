"""SDN (Software Defined Network) read + apply tools."""
from typing import List
from mcp.types import TextContent as Content
from .base import ProxmoxTool
from .helpers import privilege_required_note, privsep_empty_hint


class SDNTools(ProxmoxTool):
    """List SDN objects and apply pending config (no zone/vnet CRUD — Phase C)."""

    def list_sdn_zones(self) -> List[Content]:
        try:
            zones = self.proxmox.cluster.sdn.zones.get()
            if not zones:
                return [Content(type="text", text=privsep_empty_hint("SDN zones"))]
            return self._format_response(zones)
        except Exception as e:
            self._handle_error("list SDN zones", e)

    def list_sdn_vnets(self) -> List[Content]:
        try:
            vnets = self.proxmox.cluster.sdn.vnets.get()
            if not vnets:
                return [Content(type="text", text=privsep_empty_hint("SDN vnets"))]
            return self._format_response(vnets)
        except Exception as e:
            self._handle_error("list SDN vnets", e)

    def list_sdn_controllers(self) -> List[Content]:
        try:
            controllers = self.proxmox.cluster.sdn.controllers.get()
            return self._format_response(controllers)
        except Exception as e:
            self._handle_error("list SDN controllers", e)

    def list_sdn_ipams(self) -> List[Content]:
        try:
            ipams = self.proxmox.cluster.sdn.ipams.get()
            return self._format_response(ipams)
        except Exception as e:
            self._handle_error("list SDN IPAMs", e)

    def list_sdn_dns(self) -> List[Content]:
        try:
            dns = self.proxmox.cluster.sdn.dns.get()
            return self._format_response(dns)
        except Exception as e:
            self._handle_error("list SDN DNS", e)

    def apply_sdn(self) -> List[Content]:
        """Apply pending SDN configuration cluster-wide."""
        try:
            result = self.proxmox.cluster.sdn.put()
            return [
                Content(
                    type="text",
                    text=(
                        f"SDN apply initiated\nResult: {result}\n"
                        f"{privilege_required_note('SDN apply')}"
                    ),
                )
            ]
        except Exception as e:
            self._handle_mutation_error(
                "apply SDN", e, code="sdn_acl_denied", path="/cluster/sdn"
            )
