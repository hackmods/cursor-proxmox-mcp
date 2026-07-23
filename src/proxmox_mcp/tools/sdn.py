"""SDN tools — list, write CRUD for zones/vnets/subnets, and apply."""
from __future__ import annotations

from typing import List, Optional

from mcp.types import TextContent as Content

from .base import ProxmoxTool
from .helpers import destructive_warning, privilege_required_note, privsep_empty_hint

_APPLY_TIP = "💡 Next: apply_sdn to push pending SDN config cluster-wide."


class SDNTools(ProxmoxTool):
    """SDN list + zone/vnet/subnet CRUD + apply."""

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

    def create_sdn_zone(
        self,
        zone: str,
        type: str,
        bridge: Optional[str] = None,
        nodes: Optional[str] = None,
        mtu: Optional[int] = None,
        ipam: Optional[str] = None,
        dns: Optional[str] = None,
        reversedns: Optional[str] = None,
        dnszone: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> List[Content]:
        try:
            params: dict = {"zone": zone, "type": type}
            for key, val in (
                ("bridge", bridge),
                ("nodes", nodes),
                ("mtu", mtu),
                ("ipam", ipam),
                ("dns", dns),
                ("reversedns", reversedns),
                ("dnszone", dnszone),
                ("comment", comment),
            ):
                if val is not None:
                    params[key] = val
            result = self.proxmox.cluster.sdn.zones.post(**params)
            return [
                Content(
                    type="text",
                    text=(
                        f"SDN zone '{zone}' created (type={type})\n"
                        f"Result: {result}\n{_APPLY_TIP}"
                    ),
                )
            ]
        except Exception as e:
            self._handle_mutation_error(
                f"create SDN zone {zone}",
                e,
                code="sdn_acl_denied",
                path="/cluster/sdn/zones",
            )

    def update_sdn_zone(
        self,
        zone: str,
        bridge: Optional[str] = None,
        nodes: Optional[str] = None,
        mtu: Optional[int] = None,
        ipam: Optional[str] = None,
        dns: Optional[str] = None,
        reversedns: Optional[str] = None,
        dnszone: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> List[Content]:
        try:
            params: dict = {}
            for key, val in (
                ("bridge", bridge),
                ("nodes", nodes),
                ("mtu", mtu),
                ("ipam", ipam),
                ("dns", dns),
                ("reversedns", reversedns),
                ("dnszone", dnszone),
                ("comment", comment),
            ):
                if val is not None:
                    params[key] = val
            if not params:
                raise ValueError("Provide at least one field to update")
            result = self.proxmox.cluster.sdn.zones(zone).put(**params)
            return [
                Content(
                    type="text",
                    text=(
                        f"SDN zone '{zone}' updated\nParams: {params}\n"
                        f"Result: {result}\n{_APPLY_TIP}"
                    ),
                )
            ]
        except ValueError:
            raise
        except Exception as e:
            self._handle_mutation_error(
                f"update SDN zone {zone}",
                e,
                code="sdn_acl_denied",
                path=f"/cluster/sdn/zones/{zone}",
            )

    def delete_sdn_zone(self, zone: str) -> List[Content]:
        try:
            result = self.proxmox.cluster.sdn.zones(zone).delete()
            return [
                Content(
                    type="text",
                    text=(
                        f"{destructive_warning('deleted')}\n"
                        f"SDN zone '{zone}' deleted\nResult: {result}\n{_APPLY_TIP}"
                    ),
                )
            ]
        except Exception as e:
            self._handle_mutation_error(
                f"delete SDN zone {zone}",
                e,
                code="sdn_acl_denied",
                path=f"/cluster/sdn/zones/{zone}",
            )

    def create_sdn_vnet(
        self,
        vnet: str,
        zone: str,
        alias: Optional[str] = None,
        tag: Optional[int] = None,
        vlanaware: Optional[bool] = None,
        comment: Optional[str] = None,
    ) -> List[Content]:
        try:
            params: dict = {"vnet": vnet, "zone": zone}
            if alias is not None:
                params["alias"] = alias
            if tag is not None:
                params["tag"] = int(tag)
            if vlanaware is not None:
                params["vlanaware"] = 1 if vlanaware else 0
            if comment is not None:
                params["comment"] = comment
            result = self.proxmox.cluster.sdn.vnets.post(**params)
            return [
                Content(
                    type="text",
                    text=(
                        f"SDN vnet '{vnet}' created in zone '{zone}'\n"
                        f"Result: {result}\n{_APPLY_TIP}"
                    ),
                )
            ]
        except Exception as e:
            self._handle_mutation_error(
                f"create SDN vnet {vnet}",
                e,
                code="sdn_acl_denied",
                path="/cluster/sdn/vnets",
            )

    def update_sdn_vnet(
        self,
        vnet: str,
        alias: Optional[str] = None,
        tag: Optional[int] = None,
        vlanaware: Optional[bool] = None,
        comment: Optional[str] = None,
        zone: Optional[str] = None,
    ) -> List[Content]:
        try:
            params: dict = {}
            if alias is not None:
                params["alias"] = alias
            if tag is not None:
                params["tag"] = int(tag)
            if vlanaware is not None:
                params["vlanaware"] = 1 if vlanaware else 0
            if comment is not None:
                params["comment"] = comment
            if zone is not None:
                params["zone"] = zone
            if not params:
                raise ValueError("Provide at least one field to update")
            result = self.proxmox.cluster.sdn.vnets(vnet).put(**params)
            return [
                Content(
                    type="text",
                    text=(
                        f"SDN vnet '{vnet}' updated\nParams: {params}\n"
                        f"Result: {result}\n{_APPLY_TIP}"
                    ),
                )
            ]
        except ValueError:
            raise
        except Exception as e:
            self._handle_mutation_error(
                f"update SDN vnet {vnet}",
                e,
                code="sdn_acl_denied",
                path=f"/cluster/sdn/vnets/{vnet}",
            )

    def delete_sdn_vnet(self, vnet: str) -> List[Content]:
        try:
            result = self.proxmox.cluster.sdn.vnets(vnet).delete()
            return [
                Content(
                    type="text",
                    text=(
                        f"{destructive_warning('deleted')}\n"
                        f"SDN vnet '{vnet}' deleted\nResult: {result}\n{_APPLY_TIP}"
                    ),
                )
            ]
        except Exception as e:
            self._handle_mutation_error(
                f"delete SDN vnet {vnet}",
                e,
                code="sdn_acl_denied",
                path=f"/cluster/sdn/vnets/{vnet}",
            )

    def list_sdn_subnets(self, vnet: str) -> List[Content]:
        try:
            subnets = self.proxmox.cluster.sdn.vnets(vnet).subnets.get()
            if not subnets:
                return [Content(type="text", text=privsep_empty_hint(f"subnets on {vnet}"))]
            return self._format_response(subnets)
        except Exception as e:
            self._handle_error(f"list SDN subnets on {vnet}", e)

    def create_sdn_subnet(
        self,
        vnet: str,
        subnet: str,
        gateway: Optional[str] = None,
        snat: Optional[bool] = None,
        type: str = "subnet",
        dnszoneprefix: Optional[str] = None,
    ) -> List[Content]:
        try:
            params: dict = {"subnet": subnet, "type": type}
            if gateway is not None:
                params["gateway"] = gateway
            if snat is not None:
                params["snat"] = 1 if snat else 0
            if dnszoneprefix is not None:
                params["dnszoneprefix"] = dnszoneprefix
            result = self.proxmox.cluster.sdn.vnets(vnet).subnets.post(**params)
            return [
                Content(
                    type="text",
                    text=(
                        f"SDN subnet '{subnet}' created on vnet '{vnet}'\n"
                        f"Result: {result}\n{_APPLY_TIP}"
                    ),
                )
            ]
        except Exception as e:
            self._handle_mutation_error(
                f"create SDN subnet {subnet}",
                e,
                code="sdn_acl_denied",
                path=f"/cluster/sdn/vnets/{vnet}/subnets",
            )

    def update_sdn_subnet(
        self,
        vnet: str,
        subnet: str,
        gateway: Optional[str] = None,
        snat: Optional[bool] = None,
        dnszoneprefix: Optional[str] = None,
    ) -> List[Content]:
        try:
            params: dict = {}
            if gateway is not None:
                params["gateway"] = gateway
            if snat is not None:
                params["snat"] = 1 if snat else 0
            if dnszoneprefix is not None:
                params["dnszoneprefix"] = dnszoneprefix
            if not params:
                raise ValueError("Provide at least one field to update")
            # Proxmox encodes CIDR with %2F in path; proxmoxer usually accepts subnet id
            result = self.proxmox.cluster.sdn.vnets(vnet).subnets(subnet).put(**params)
            return [
                Content(
                    type="text",
                    text=(
                        f"SDN subnet '{subnet}' on '{vnet}' updated\n"
                        f"Params: {params}\nResult: {result}\n{_APPLY_TIP}"
                    ),
                )
            ]
        except ValueError:
            raise
        except Exception as e:
            self._handle_mutation_error(
                f"update SDN subnet {subnet}",
                e,
                code="sdn_acl_denied",
                path=f"/cluster/sdn/vnets/{vnet}/subnets/{subnet}",
            )

    def delete_sdn_subnet(self, vnet: str, subnet: str) -> List[Content]:
        try:
            result = self.proxmox.cluster.sdn.vnets(vnet).subnets(subnet).delete()
            return [
                Content(
                    type="text",
                    text=(
                        f"{destructive_warning('deleted')}\n"
                        f"SDN subnet '{subnet}' deleted from '{vnet}'\n"
                        f"Result: {result}\n{_APPLY_TIP}"
                    ),
                )
            ]
        except Exception as e:
            self._handle_mutation_error(
                f"delete SDN subnet {subnet}",
                e,
                code="sdn_acl_denied",
                path=f"/cluster/sdn/vnets/{vnet}/subnets/{subnet}",
            )
