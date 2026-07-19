"""Firewall tools for cluster and per-guest rules."""
from typing import List, Optional
from mcp.types import TextContent as Content
from .base import ProxmoxTool
from .guest import guest_resource, normalize_guest_type


class FirewallTools(ProxmoxTool):
    """Cluster and guest firewall management."""

    def get_cluster_firewall_options(self) -> List[Content]:
        try:
            options = self.proxmox.cluster.firewall.options.get()
            return self._format_response(options)
        except Exception as e:
            self._handle_error("get cluster firewall options", e)

    def set_cluster_firewall_options(self, enable: Optional[bool] = None, policy_in: Optional[str] = None, policy_out: Optional[str] = None) -> List[Content]:
        try:
            params = {}
            if enable is not None:
                params["enable"] = 1 if enable else 0
            if policy_in is not None:
                params["policy_in"] = policy_in
            if policy_out is not None:
                params["policy_out"] = policy_out
            result = self.proxmox.cluster.firewall.options.put(**params)
            return [Content(type="text", text=f"Cluster firewall options updated\nResult: {result}")]
        except Exception as e:
            self._handle_error("set cluster firewall options", e)

    def list_cluster_firewall_rules(self) -> List[Content]:
        try:
            rules = self.proxmox.cluster.firewall.rules.get()
            return self._format_response(rules)
        except Exception as e:
            self._handle_error("list cluster firewall rules", e)

    def create_cluster_firewall_rule(
        self,
        action: str,
        type: str,
        enable: bool = True,
        source: Optional[str] = None,
        dest: Optional[str] = None,
        proto: Optional[str] = None,
        dport: Optional[str] = None,
        sport: Optional[str] = None,
        comment: Optional[str] = None,
        pos: Optional[int] = None,
    ) -> List[Content]:
        try:
            params = {
                "action": action,
                "type": type,
                "enable": 1 if enable else 0,
            }
            if source is not None:
                params["source"] = source
            if dest is not None:
                params["dest"] = dest
            if proto is not None:
                params["proto"] = proto
            if dport is not None:
                params["dport"] = dport
            if sport is not None:
                params["sport"] = sport
            if comment is not None:
                params["comment"] = comment
            if pos is not None:
                params["pos"] = pos
            result = self.proxmox.cluster.firewall.rules.post(**params)
            return [Content(type="text", text=f"Cluster firewall rule created\nResult: {result}")]
        except Exception as e:
            self._handle_error("create cluster firewall rule", e)

    def delete_cluster_firewall_rule(self, pos: int) -> List[Content]:
        try:
            result = self.proxmox.cluster.firewall.rules(pos).delete()
            return [Content(type="text", text=f"Cluster firewall rule at pos {pos} deleted\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"delete cluster firewall rule {pos}", e)

    def list_guest_firewall_rules(
        self, node: str, vmid: str, guest_type: str = "qemu"
    ) -> List[Content]:
        try:
            gtype = normalize_guest_type(guest_type)
            rules = guest_resource(self.proxmox, node, vmid, gtype).firewall.rules.get()
            return self._format_response(rules)
        except Exception as e:
            self._handle_error(f"list firewall rules for {guest_type} {vmid}", e)

    def create_guest_firewall_rule(
        self,
        node: str,
        vmid: str,
        action: str,
        type: str,
        guest_type: str = "qemu",
        enable: bool = True,
        source: Optional[str] = None,
        dest: Optional[str] = None,
        proto: Optional[str] = None,
        dport: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> List[Content]:
        try:
            gtype = normalize_guest_type(guest_type)
            params = {
                "action": action,
                "type": type,
                "enable": 1 if enable else 0,
            }
            if source is not None:
                params["source"] = source
            if dest is not None:
                params["dest"] = dest
            if proto is not None:
                params["proto"] = proto
            if dport is not None:
                params["dport"] = dport
            if comment is not None:
                params["comment"] = comment
            result = guest_resource(self.proxmox, node, vmid, gtype).firewall.rules.post(**params)
            return [Content(type="text", text=f"Guest firewall rule created\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"create firewall rule for {guest_type} {vmid}", e)

    def delete_guest_firewall_rule(
        self, node: str, vmid: str, pos: int, guest_type: str = "qemu"
    ) -> List[Content]:
        try:
            gtype = normalize_guest_type(guest_type)
            result = guest_resource(self.proxmox, node, vmid, gtype).firewall.rules(pos).delete()
            return [Content(type="text", text=f"Guest firewall rule at pos {pos} deleted\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"delete firewall rule {pos}", e)

    def get_guest_firewall_options(
        self, node: str, vmid: str, guest_type: str = "qemu"
    ) -> List[Content]:
        try:
            gtype = normalize_guest_type(guest_type)
            options = guest_resource(self.proxmox, node, vmid, gtype).firewall.options.get()
            return self._format_response(options)
        except Exception as e:
            self._handle_error(f"get firewall options for {guest_type} {vmid}", e)

    def set_guest_firewall_options(
        self,
        node: str,
        vmid: str,
        guest_type: str = "qemu",
        enable: Optional[bool] = None,
        dhcp: Optional[bool] = None,
        ipfilter: Optional[bool] = None,
    ) -> List[Content]:
        try:
            gtype = normalize_guest_type(guest_type)
            params = {}
            if enable is not None:
                params["enable"] = 1 if enable else 0
            if dhcp is not None:
                params["dhcp"] = 1 if dhcp else 0
            if ipfilter is not None:
                params["ipfilter"] = 1 if ipfilter else 0
            result = guest_resource(self.proxmox, node, vmid, gtype).firewall.options.put(**params)
            return [Content(type="text", text=f"Guest firewall options updated\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"set firewall options for {guest_type} {vmid}", e)

    def list_firewall_aliases(self) -> List[Content]:
        try:
            aliases = self.proxmox.cluster.firewall.aliases.get()
            return self._format_response(aliases)
        except Exception as e:
            self._handle_error("list firewall aliases", e)

    def create_firewall_alias(
        self, name: str, cidr: str, comment: Optional[str] = None
    ) -> List[Content]:
        try:
            params = {"name": name, "cidr": cidr}
            if comment is not None:
                params["comment"] = comment
            result = self.proxmox.cluster.firewall.aliases.post(**params)
            return [Content(type="text", text=f"Firewall alias '{name}' created\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"create firewall alias {name}", e)

    def delete_firewall_alias(self, name: str) -> List[Content]:
        try:
            result = self.proxmox.cluster.firewall.aliases(name).delete()
            return [Content(type="text", text=f"Firewall alias '{name}' deleted\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"delete firewall alias {name}", e)

    def list_firewall_ipsets(self) -> List[Content]:
        try:
            ipsets = self.proxmox.cluster.firewall.ipset.get()
            return self._format_response(ipsets)
        except Exception as e:
            self._handle_error("list firewall IP sets", e)

    def create_firewall_ipset(
        self, name: str, comment: Optional[str] = None
    ) -> List[Content]:
        try:
            params = {"name": name}
            if comment is not None:
                params["comment"] = comment
            result = self.proxmox.cluster.firewall.ipset.post(**params)
            return [Content(type="text", text=f"Firewall IP set '{name}' created\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"create firewall IP set {name}", e)

    def delete_firewall_ipset(self, name: str) -> List[Content]:
        try:
            result = self.proxmox.cluster.firewall.ipset(name).delete()
            return [Content(type="text", text=f"Firewall IP set '{name}' deleted\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"delete firewall IP set {name}", e)

    def list_firewall_ipset_cidrs(self, name: str) -> List[Content]:
        try:
            members = self.proxmox.cluster.firewall.ipset(name).get()
            return self._format_response(members)
        except Exception as e:
            self._handle_error(f"list IP set '{name}' CIDRs", e)

    def add_firewall_ipset_cidr(
        self,
        name: str,
        cidr: str,
        comment: Optional[str] = None,
        nomatch: bool = False,
    ) -> List[Content]:
        try:
            params = {"cidr": cidr}
            if comment is not None:
                params["comment"] = comment
            if nomatch:
                params["nomatch"] = 1
            result = self.proxmox.cluster.firewall.ipset(name).post(**params)
            return [
                Content(
                    type="text",
                    text=f"Added '{cidr}' to IP set '{name}'\nResult: {result}",
                )
            ]
        except Exception as e:
            self._handle_error(f"add CIDR to IP set {name}", e)

    def delete_firewall_ipset_cidr(self, name: str, cidr: str) -> List[Content]:
        try:
            # Proxmox encodes CIDR in the path; proxmoxer accepts the cidr segment
            result = self.proxmox.cluster.firewall.ipset(name)(cidr).delete()
            return [
                Content(
                    type="text",
                    text=f"Removed '{cidr}' from IP set '{name}'\nResult: {result}",
                )
            ]
        except Exception as e:
            self._handle_error(f"delete CIDR from IP set {name}", e)

    def list_firewall_macros(self) -> List[Content]:
        try:
            macros = self.proxmox.cluster.firewall.macros.get()
            return self._format_response(macros)
        except Exception as e:
            self._handle_error("list firewall macros", e)
