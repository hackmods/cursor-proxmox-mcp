"""Unit tests for Phase B and QOL tool modules (mocked Proxmox API)."""
from unittest.mock import Mock

from proxmox_mcp.tools.acme import ACMETools
from proxmox_mcp.tools.cluster import ClusterTools
from proxmox_mcp.tools.container import ContainerTools
from proxmox_mcp.tools.firewall import FirewallTools
from proxmox_mcp.tools.node import NodeTools
from proxmox_mcp.tools.pool import PoolTools
from proxmox_mcp.tools.replication import ReplicationTools
from proxmox_mcp.tools.sdn import SDNTools
from proxmox_mcp.tools.vm import VMTools


def test_list_replication_jobs():
    api = Mock()
    api.cluster.replication.get.return_value = [{"id": "100-0", "target": "pve2"}]
    result = ReplicationTools(api).list_replication_jobs()
    assert "100-0" in result[0].text


def test_run_replication_job():
    api = Mock()
    api.nodes.return_value.replication.return_value.schedule_now.post.return_value = "OK"
    result = ReplicationTools(api).run_replication_job("pve1", "100-0")
    assert "100-0" in result[0].text


def test_create_delete_replication_job():
    api = Mock()
    api.cluster.replication.post.return_value = None
    api.cluster.replication.return_value.delete.return_value = None
    tools = ReplicationTools(api)
    assert "created" in tools.create_replication_job("100-0", "pve2")[0].text.lower()
    assert "deleted" in tools.delete_replication_job("100-0")[0].text.lower()


def test_acme_lists():
    api = Mock()
    api.cluster.acme.plugins.get.return_value = [{"plugin": "standalone"}]
    api.cluster.acme.account.get.return_value = [{"name": "default"}]
    api.cluster.acme.directories.get.return_value = [{"name": "Let's Encrypt V2"}]
    tools = ACMETools(api)
    assert "standalone" in tools.list_acme_plugins()[0].text
    assert "default" in tools.list_acme_accounts()[0].text
    assert "Encrypt" in tools.get_acme_directories()[0].text


def test_sdn_lists_and_apply():
    api = Mock()
    api.cluster.sdn.zones.get.return_value = [{"zone": "zone1"}]
    api.cluster.sdn.vnets.get.return_value = [{"vnet": "vnet1"}]
    api.cluster.sdn.controllers.get.return_value = []
    api.cluster.sdn.ipams.get.return_value = []
    api.cluster.sdn.dns.get.return_value = []
    api.cluster.sdn.put.return_value = "UPID:sdn"
    tools = SDNTools(api)
    assert "zone1" in tools.list_sdn_zones()[0].text
    assert "vnet1" in tools.list_sdn_vnets()[0].text
    assert "apply" in tools.apply_sdn()[0].text.lower()


def test_pools():
    api = Mock()
    api.pools.get.return_value = [{"poolid": "lab"}]
    api.pools.return_value.get.return_value = {"poolid": "lab", "members": []}
    api.pools.post.return_value = None
    api.pools.return_value.delete.return_value = None
    tools = PoolTools(api)
    assert "lab" in tools.list_pools()[0].text
    assert "lab" in tools.get_pool("lab")[0].text
    assert "created" in tools.create_pool("lab")[0].text.lower()
    assert "deleted" in tools.delete_pool("lab")[0].text.lower()


def test_node_subscription_certs_services():
    api = Mock()
    api.nodes.return_value.subscription.get.return_value = {"status": "Active"}
    api.nodes.return_value.certificates.info.get.return_value = [{"filename": "pveproxy-ssl.pem"}]
    api.nodes.return_value.services.get.return_value = [{"service": "pveproxy", "state": "running"}]
    api.nodes.return_value.time.get.return_value = {"timezone": "UTC"}
    api.nodes.return_value.report.get.return_value = "ok"
    api.nodes.return_value.wakeonlan.post.return_value = "OK"
    tools = NodeTools(api)
    assert "Active" in tools.get_node_subscription("pve")[0].text
    assert "pveproxy" in tools.list_node_certificates("pve")[0].text
    assert "pveproxy" in tools.list_node_services("pve")[0].text
    assert "UTC" in tools.get_node_time("pve")[0].text
    assert "Wake" in tools.wake_node("pve")[0].text


def test_firewall_aliases_ipsets_macros():
    api = Mock()
    api.cluster.firewall.aliases.get.return_value = [{"name": "office", "cidr": "10.0.0.0/24"}]
    api.cluster.firewall.aliases.post.return_value = None
    api.cluster.firewall.aliases.return_value.delete.return_value = None
    api.cluster.firewall.ipset.get.return_value = [{"name": "blocklist"}]
    api.cluster.firewall.ipset.post.return_value = None
    api.cluster.firewall.ipset.return_value.delete.return_value = None
    api.cluster.firewall.macros.get.return_value = [{"macro": "HTTP"}]
    tools = FirewallTools(api)
    assert "office" in tools.list_firewall_aliases()[0].text
    assert "created" in tools.create_firewall_alias("office", "10.0.0.0/24")[0].text.lower()
    assert "deleted" in tools.delete_firewall_alias("office")[0].text.lower()
    assert "blocklist" in tools.list_firewall_ipsets()[0].text
    assert "HTTP" in tools.list_firewall_macros()[0].text


def test_vm_console_tickets_and_status():
    api = Mock()
    api.nodes.return_value.qemu.return_value.vncproxy.post.return_value = {
        "ticket": "TICKET",
        "port": 5900,
    }
    api.nodes.return_value.qemu.return_value.spiceproxy.post.return_value = {"type": "spice"}
    api.nodes.return_value.qemu.return_value.termproxy.post.return_value = {"port": 5901}
    api.nodes.return_value.qemu.return_value.status.current.get.return_value = {
        "status": "running",
        "name": "web",
    }
    api.nodes.return_value.qemu.return_value.rrddata.get.return_value = [{"cpu": 0.1}]
    tools = VMTools(api)
    assert "TICKET" in tools.create_vnc_ticket("pve", "100")[0].text
    assert "spice" in tools.create_spice_ticket("pve", "100")[0].text.lower()
    assert "5901" in tools.create_termproxy_ticket("pve", "100")[0].text
    assert "running" in tools.get_vm_status("pve", "100")[0].text
    assert "cpu" in tools.get_vm_rrd_data("pve", "100")[0].text


def test_lxc_console_and_status():
    api = Mock()
    api.nodes.return_value.lxc.return_value.vncproxy.post.return_value = {"ticket": "LXC"}
    api.nodes.return_value.lxc.return_value.termproxy.post.return_value = {"port": 5902}
    api.nodes.return_value.lxc.return_value.status.current.get.return_value = {
        "status": "running",
        "name": "ct1",
    }
    tools = ContainerTools(api)
    assert "LXC" in tools.create_vnc_ticket("pve", "200")[0].text
    assert "5902" in tools.create_termproxy_ticket("pve", "200")[0].text
    assert "running" in tools.get_lxc_status("pve", "200")[0].text


def test_cluster_version_resources_log():
    api = Mock()
    api.version.get.return_value = {"version": "8.2", "release": "1"}
    api.cluster.resources.get.return_value = [{"type": "qemu", "vmid": 100}]
    api.cluster.log.get.return_value = [{"msg": "hello"}]
    api.cluster.options.get.return_value = {"keyboard": "en-us"}
    tools = ClusterTools(api)
    assert "8.2" in tools.get_version()[0].text
    assert "100" in tools.get_cluster_resources()[0].text
    assert "hello" in tools.get_cluster_log()[0].text
    assert "keyboard" in tools.get_cluster_options()[0].text
