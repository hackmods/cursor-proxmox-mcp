"""Node network list + CRUD + reload (apply pending ifaces)."""
from __future__ import annotations

from typing import List, Optional

from mcp.types import TextContent as Content

from .base import ProxmoxTool
from .helpers import destructive_warning


_RELOAD_TIP = "💡 Next: reload_node_network to apply pending iface config on the node."


class NetworkTools(ProxmoxTool):
    """Node network interface discovery and mutation."""

    def list_node_networks(self, node: str) -> List[Content]:
        try:
            networks = self.proxmox.nodes(node).network.get()
            return self._format_response(networks)
        except Exception as e:
            self._handle_error(f"list networks on {node}", e)

    def create_node_network(
        self,
        node: str,
        iface: str,
        type: str,
        bridge_ports: Optional[str] = None,
        bridge_stp: Optional[bool] = None,
        bridge_fd: Optional[int] = None,
        address: Optional[str] = None,
        netmask: Optional[str] = None,
        gateway: Optional[str] = None,
        cidr: Optional[str] = None,
        autostart: bool = True,
        comments: Optional[str] = None,
        mtu: Optional[int] = None,
        slaves: Optional[str] = None,
        bond_mode: Optional[str] = None,
        vlan_id: Optional[int] = None,
        vlan_raw_device: Optional[str] = None,
    ) -> List[Content]:
        try:
            params: dict = {"iface": iface, "type": type}
            if bridge_ports is not None:
                params["bridge_ports"] = bridge_ports
            if bridge_stp is not None:
                params["bridge_stp"] = "on" if bridge_stp else "off"
            if bridge_fd is not None:
                params["bridge_fd"] = int(bridge_fd)
            if address is not None:
                params["address"] = address
            if netmask is not None:
                params["netmask"] = netmask
            if gateway is not None:
                params["gateway"] = gateway
            if cidr is not None:
                params["cidr"] = cidr
            params["autostart"] = 1 if autostart else 0
            if comments is not None:
                params["comments"] = comments
            if mtu is not None:
                params["mtu"] = int(mtu)
            if slaves is not None:
                params["slaves"] = slaves
            if bond_mode is not None:
                params["bond_mode"] = bond_mode
            if vlan_id is not None:
                params["vlan-id"] = int(vlan_id)
            if vlan_raw_device is not None:
                params["vlan-raw-device"] = vlan_raw_device
            result = self.proxmox.nodes(node).network.post(**params)
            return [
                Content(
                    type="text",
                    text=(
                        f"Network iface '{iface}' ({type}) created on {node}\n"
                        f"Result: {result}\n{_RELOAD_TIP}"
                    ),
                )
            ]
        except Exception as e:
            self._handle_mutation_error(
                f"create network {iface} on {node}",
                e,
                code="network_acl_denied",
                path=f"/nodes/{node}/network",
            )

    def update_node_network(
        self,
        node: str,
        iface: str,
        bridge_ports: Optional[str] = None,
        bridge_stp: Optional[bool] = None,
        bridge_fd: Optional[int] = None,
        address: Optional[str] = None,
        netmask: Optional[str] = None,
        gateway: Optional[str] = None,
        cidr: Optional[str] = None,
        autostart: Optional[bool] = None,
        comments: Optional[str] = None,
        mtu: Optional[int] = None,
        slaves: Optional[str] = None,
        bond_mode: Optional[str] = None,
        delete: Optional[str] = None,
    ) -> List[Content]:
        try:
            params: dict = {}
            if bridge_ports is not None:
                params["bridge_ports"] = bridge_ports
            if bridge_stp is not None:
                params["bridge_stp"] = "on" if bridge_stp else "off"
            if bridge_fd is not None:
                params["bridge_fd"] = int(bridge_fd)
            if address is not None:
                params["address"] = address
            if netmask is not None:
                params["netmask"] = netmask
            if gateway is not None:
                params["gateway"] = gateway
            if cidr is not None:
                params["cidr"] = cidr
            if autostart is not None:
                params["autostart"] = 1 if autostart else 0
            if comments is not None:
                params["comments"] = comments
            if mtu is not None:
                params["mtu"] = int(mtu)
            if slaves is not None:
                params["slaves"] = slaves
            if bond_mode is not None:
                params["bond_mode"] = bond_mode
            if delete is not None:
                params["delete"] = delete
            if not params:
                raise ValueError("Provide at least one field to update")
            result = self.proxmox.nodes(node).network(iface).put(**params)
            return [
                Content(
                    type="text",
                    text=(
                        f"Network iface '{iface}' updated on {node}\n"
                        f"Params: {params}\nResult: {result}\n{_RELOAD_TIP}"
                    ),
                )
            ]
        except ValueError:
            raise
        except Exception as e:
            self._handle_mutation_error(
                f"update network {iface} on {node}",
                e,
                code="network_acl_denied",
                path=f"/nodes/{node}/network/{iface}",
            )

    def delete_node_network(self, node: str, iface: str) -> List[Content]:
        try:
            result = self.proxmox.nodes(node).network(iface).delete()
            return [
                Content(
                    type="text",
                    text=(
                        f"{destructive_warning('deleted')}\n"
                        f"Network iface '{iface}' deleted on {node}\n"
                        f"Result: {result}\n{_RELOAD_TIP}"
                    ),
                )
            ]
        except Exception as e:
            self._handle_mutation_error(
                f"delete network {iface} on {node}",
                e,
                code="network_acl_denied",
                path=f"/nodes/{node}/network/{iface}",
            )

    def reload_node_network(self, node: str) -> List[Content]:
        """Apply pending network configuration on a node (ifupdown2 reload)."""
        try:
            result = self.proxmox.nodes(node).network.put()
            return [
                Content(
                    type="text",
                    text=(
                        f"⚠️ Network reload initiated on {node}\n"
                        f"Result: {result}\n"
                        "Incorrect config can disconnect the host — verify list_node_networks."
                    ),
                )
            ]
        except Exception as e:
            self._handle_mutation_error(
                f"reload network on {node}",
                e,
                code="network_acl_denied",
                path=f"/nodes/{node}/network",
            )
