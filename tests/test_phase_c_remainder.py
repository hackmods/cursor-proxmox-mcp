"""Phase C remainder (v1.7.0): SDN write, ACME, Ceph, console helper, PBS, node net."""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from proxmox_mcp.tools.acme import ACMETools
from proxmox_mcp.tools.ceph import CephTools
from proxmox_mcp.tools.guest_power import GuestPowerTools
from proxmox_mcp.tools.inventory import ALL_TOOL_NAMES, DESTRUCTIVE_TOOLS
from proxmox_mcp.tools.network import NetworkTools
from proxmox_mcp.tools.sdn import SDNTools
from proxmox_mcp.tools.storage import StorageTools


NEW_TOOLS = (
    "create_node_network",
    "update_node_network",
    "delete_node_network",
    "reload_node_network",
    "get_console_connection",
    "get_pbs_storage_status",
    "create_acme_account",
    "create_acme_plugin",
    "delete_acme_plugin",
    "order_acme_certificate",
    "renew_acme_certificate",
    "create_sdn_zone",
    "update_sdn_zone",
    "delete_sdn_zone",
    "create_sdn_vnet",
    "update_sdn_vnet",
    "delete_sdn_vnet",
    "list_sdn_subnets",
    "create_sdn_subnet",
    "update_sdn_subnet",
    "delete_sdn_subnet",
    "get_ceph_status",
    "list_ceph_pools",
    "list_ceph_osds",
    "list_ceph_mons",
    "list_ceph_mgrs",
    "create_ceph_pool",
    "delete_ceph_pool",
)


def test_v17_tools_in_inventory():
    for name in NEW_TOOLS:
        assert name in ALL_TOOL_NAMES
    assert len(ALL_TOOL_NAMES) == 207
    for name in (
        "delete_sdn_zone",
        "delete_sdn_vnet",
        "delete_sdn_subnet",
        "delete_acme_plugin",
        "delete_ceph_pool",
        "delete_node_network",
        "reload_node_network",
    ):
        assert name in DESTRUCTIVE_TOOLS


def test_create_sdn_zone_tips_apply():
    api = MagicMock()
    api.cluster.sdn.zones.post.return_value = "ok"
    text = SDNTools(api).create_sdn_zone("lab", "simple")[0].text
    assert "lab" in text
    assert "apply_sdn" in text
    api.cluster.sdn.zones.post.assert_called_once()


def test_create_acme_plugin_never_echoes_data():
    api = MagicMock()
    api.cluster.acme.plugins.post.return_value = "ok"
    text = ACMETools(api).create_acme_plugin(
        "cf", "dns", api="cloudflare", data="SECRET_TOKEN"
    )[0].text
    assert "SECRET_TOKEN" not in text
    assert "not echoed" in text.lower() or "was not echoed" in text
    kwargs = api.cluster.acme.plugins.post.call_args.kwargs
    assert kwargs["data"] == "SECRET_TOKEN"


def test_order_acme_certificate_upid():
    api = MagicMock()
    api.nodes.return_value.certificates.acme.certificate.post.return_value = (
        "UPID:pve:000:acme:"
    )
    text = ACMETools(api).order_acme_certificate("pve")[0].text
    assert "order" in text.lower()
    assert "wait_for_task" in text or "UPID" in text


def test_delete_ceph_pool_requires_confirm():
    api = MagicMock()
    tools = CephTools(api)
    with pytest.raises(ValueError, match="confirm must equal"):
        tools.delete_ceph_pool("rbd", confirm="wrong")
    api.cluster.ceph.pool.return_value.delete.assert_not_called()

    api.cluster.ceph.pool.return_value.delete.return_value = "ok"
    text = tools.delete_ceph_pool("rbd", confirm="rbd")[0].text
    assert "IRREVERSIBLE" in text
    api.cluster.ceph.pool.assert_called_with("rbd")


def test_get_ceph_status():
    api = MagicMock()
    api.cluster.ceph.status.get.return_value = {"health": {"status": "HEALTH_OK"}}
    text = CephTools(api).get_ceph_status()[0].text
    data = json.loads(text)
    assert data["health"]["status"] == "HEALTH_OK"


def test_create_node_network_tips_reload():
    api = MagicMock()
    api.nodes.return_value.network.post.return_value = "ok"
    text = NetworkTools(api).create_node_network("pve", "vmbr99", "bridge")[0].text
    assert "vmbr99" in text
    assert "reload_node_network" in text


def test_get_pbs_storage_status_rejects_non_pbs():
    api = MagicMock()
    api.storage.get.return_value = [{"storage": "local", "type": "dir"}]
    with pytest.raises(ValueError, match="not pbs"):
        StorageTools(api).get_pbs_storage_status("pve", "local")


def test_get_pbs_storage_status_ok():
    api = MagicMock()
    api.storage.get.return_value = [{"storage": "pbs1", "type": "pbs"}]
    api.nodes.return_value.storage.return_value.status.get.return_value = {
        "active": 1,
        "type": "pbs",
    }
    text = StorageTools(api).get_pbs_storage_status("pve", "pbs1")[0].text
    data = json.loads(text)
    assert data["storage"] == "pbs1"
    assert data["type"] == "pbs"
    assert "PBS product admin" in data["note"]


def test_create_storage_pbs_params():
    api = MagicMock()
    api.storage.post.return_value = "ok"
    text = StorageTools(api).create_storage(
        "pbs1",
        "pbs",
        content="backup",
        server="pbs.local",
        username="user@pbs",
        password="secret",
        datastore="store1",
        fingerprint="AA:BB",
        port=8007,
    )[0].text
    assert "secret" not in text or "password" not in text.lower()
    kwargs = api.storage.post.call_args.kwargs
    assert kwargs["datastore"] == "store1"
    assert kwargs["fingerprint"] == "AA:BB"
    assert kwargs["port"] == 8007
    assert "get_pbs_storage_status" in text


def test_get_console_connection_vnc():
    api = MagicMock()
    resource = MagicMock()
    resource.vncproxy.post.return_value = {
        "ticket": "TICKET",
        "port": "5900",
        "user": "root@pam",
    }
    # guest_resource path: nodes(node).qemu(vmid) or similar
    api.nodes.return_value.qemu.return_value = resource
    text = GuestPowerTools(api).get_console_connection(
        "pve", "100", guest_type="qemu", console="vnc", host="pve.local"
    )[0].text
    assert "VNC" in text
    assert "TICKET" in text or "ticket" in text.lower()
    assert "websocket" in text.lower() or "no" in text.lower() or "proxy" in text.lower()
    resource.vncproxy.post.assert_called_once()


def test_get_console_connection_spice_and_term():
    api = MagicMock()
    resource = MagicMock()
    resource.spiceproxy.post.return_value = {"spice": "SPICE_TICKET"}
    resource.termproxy.post.return_value = {"ticket": "TERM"}
    api.nodes.return_value.qemu.return_value = resource
    tools = GuestPowerTools(api)
    spice = tools.get_console_connection("pve", "100", console="spice")[0].text
    assert "SPICE" in spice
    term = tools.get_console_connection("pve", "100", console="termproxy")[0].text
    assert "termproxy" in term.lower()
    with pytest.raises(ValueError, match="console must be"):
        tools.get_console_connection("pve", "100", console="rdp")


def test_node_network_update_delete_reload():
    api = MagicMock()
    api.nodes.return_value.network.return_value.put.return_value = "ok"
    api.nodes.return_value.network.return_value.delete.return_value = "ok"
    api.nodes.return_value.network.put.return_value = "ok"
    tools = NetworkTools(api)
    with pytest.raises(ValueError, match="at least one"):
        tools.update_node_network("pve", "vmbr0")
    upd = tools.update_node_network("pve", "vmbr0", address="10.0.0.1", mtu=1500)[0].text
    assert "updated" in upd
    assert "reload_node_network" in upd
    deleted = tools.delete_node_network("pve", "vmbr99")[0].text
    assert "IRREVERSIBLE" in deleted or "deleted" in deleted.lower()
    reloaded = tools.reload_node_network("pve")[0].text
    assert "reload" in reloaded.lower()


def test_create_acme_account_and_renew():
    api = MagicMock()
    api.cluster.acme.account.post.return_value = "ok"
    api.nodes.return_value.certificates.acme.certificate.post.return_value = (
        "UPID:pve:000:renew:"
    )
    tools = ACMETools(api)
    acct = tools.create_acme_account("le", "ops@example.com")[0].text
    assert "le" in acct
    assert "order_acme_certificate" in acct
    renew = tools.renew_acme_certificate("pve", force=True)[0].text
    assert "renew" in renew.lower()
    call_kwargs = api.nodes.return_value.certificates.acme.certificate.post.call_args.kwargs
    assert call_kwargs.get("force") == 1


def test_create_ceph_pool_and_lists():
    api = MagicMock()
    api.cluster.ceph.pool.post.return_value = "ok"
    api.cluster.ceph.pool.get.return_value = [{"pool_name": "rbd"}]
    api.cluster.ceph.osd.get.return_value = [{"osd": 0}]
    api.cluster.ceph.mon.get.return_value = [{"name": "pve"}]
    api.cluster.ceph.mgr.get.return_value = [{"name": "pve"}]
    tools = CephTools(api)
    created = tools.create_ceph_pool("lab", size=3, min_size=2, pg_num=16, application="rbd")[0].text
    assert "lab" in created
    assert "out of MCP scope" in created
    assert "rbd" in json.loads(tools.list_ceph_pools()[0].text)[0]["pool_name"]
    assert tools.list_ceph_osds()[0].text
    assert tools.list_ceph_mons()[0].text
    assert tools.list_ceph_mgrs()[0].text


def test_sdn_vnet_subnet_crud():
    api = MagicMock()
    api.cluster.sdn.vnets.post.return_value = "ok"
    api.cluster.sdn.vnets.return_value.put.return_value = "ok"
    api.cluster.sdn.vnets.return_value.delete.return_value = "ok"
    api.cluster.sdn.vnets.return_value.subnets.get.return_value = [{"subnet": "10.0.0.0/24"}]
    api.cluster.sdn.vnets.return_value.subnets.post.return_value = "ok"
    api.cluster.sdn.vnets.return_value.subnets.return_value.put.return_value = "ok"
    api.cluster.sdn.vnets.return_value.subnets.return_value.delete.return_value = "ok"
    api.cluster.sdn.zones.return_value.put.return_value = "ok"
    api.cluster.sdn.zones.return_value.delete.return_value = "ok"
    tools = SDNTools(api)
    assert "apply_sdn" in tools.create_sdn_vnet("vnet1", "zone1")[0].text
    assert "updated" in tools.update_sdn_vnet("vnet1", alias="lab")[0].text.lower() or "vnet1" in tools.update_sdn_vnet("vnet1", alias="lab")[0].text
    assert "deleted" in tools.delete_sdn_vnet("vnet1")[0].text.lower()
    assert "10.0.0.0/24" in tools.list_sdn_subnets("vnet1")[0].text
    assert "apply_sdn" in tools.create_sdn_subnet("vnet1", "10.0.0.0/24", gateway="10.0.0.1")[0].text
    assert "apply_sdn" in tools.update_sdn_subnet("vnet1", "10.0.0.0/24", snat=True)[0].text
    assert "deleted" in tools.delete_sdn_subnet("vnet1", "10.0.0.0/24")[0].text.lower()
    assert "apply_sdn" in tools.update_sdn_zone("zone1", mtu=1400)[0].text
    assert "deleted" in tools.delete_sdn_zone("zone1")[0].text.lower()
