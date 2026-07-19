"""Unit tests for new tool modules (mocked Proxmox API)."""
from unittest.mock import Mock

import pytest

from proxmox_mcp.tools.guest import normalize_guest_type, guest_resource
from proxmox_mcp.tools.snapshot import SnapshotTools
from proxmox_mcp.tools.backup import BackupTools
from proxmox_mcp.tools.tasks import TaskTools
from proxmox_mcp.tools.ha import HATools
from proxmox_mcp.tools.access import AccessTools
from proxmox_mcp.tools.storage import StorageTools
from proxmox_mcp.tools.migrate import MigrateTools
from proxmox_mcp.tools.network import NetworkTools
from proxmox_mcp.tools.firewall import FirewallTools
from proxmox_mcp.tools.cluster import ClusterTools
from proxmox_mcp.tools.vm import VMTools
from proxmox_mcp.tools.container import ContainerTools


def test_normalize_guest_type():
    assert normalize_guest_type("vm") == "qemu"
    assert normalize_guest_type("lxc") == "lxc"
    assert normalize_guest_type("CT") == "lxc"
    with pytest.raises(ValueError):
        normalize_guest_type("xen")


def test_guest_resource_routes():
    proxmox = Mock()
    guest_resource(proxmox, "pve", "100", "qemu")
    proxmox.nodes.assert_called_with("pve")
    proxmox.nodes.return_value.qemu.assert_called_with("100")
    guest_resource(proxmox, "pve", "200", "lxc")
    proxmox.nodes.return_value.lxc.assert_called_with("200")


def test_get_next_vmid():
    api = Mock()
    api.cluster.nextid.get.return_value = 305
    tools = ClusterTools(api)
    result = tools.get_next_vmid()
    assert "305" in result[0].text


def test_get_task_status():
    api = Mock()
    api.nodes.return_value.tasks.return_value.status.get.return_value = {
        "status": "stopped",
        "exitstatus": "OK",
    }
    tools = TaskTools(api)
    result = tools.get_task_status("pve", "UPID:pve:1:2:3:qmstart:100:")
    assert "OK" in result[0].text or "stopped" in result[0].text


def test_wait_for_task_success():
    api = Mock()
    api.nodes.return_value.tasks.return_value.status.get.side_effect = [
        {"status": "running"},
        {"status": "stopped", "exitstatus": "OK"},
    ]
    tools = TaskTools(api)
    result = tools.wait_for_task("pve", "UPID:pve:1:2:3:qmcreate:100:", timeout=10, poll_interval=0.5)
    assert "finished" in result[0].text.lower() or "OK" in result[0].text


def test_wait_for_task_timeout():
    api = Mock()
    api.nodes.return_value.tasks.return_value.status.get.return_value = {"status": "running"}
    tools = TaskTools(api)
    with pytest.raises(TimeoutError):
        tools.wait_for_task("pve", "UPID:stuck", timeout=1, poll_interval=0.5)


def test_get_token_permissions():
    api = Mock()
    api.access.permissions.get.return_value = {"/": ["VM.Audit"]}
    tools = AccessTools(api)
    result = tools.get_token_permissions("mcp@pve", "cursor")
    assert "mcp@pve!cursor" in result[0].text
    api.access.permissions.get.assert_called_with(userid="mcp@pve!cursor")


def test_list_os_templates():
    api = Mock()
    api.nodes.return_value.storage.get.return_value = [
        {"storage": "local", "content": "vztmpl,iso"}
    ]
    api.nodes.return_value.storage.return_value.content.get.return_value = [
        {"volid": "local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst"}
    ]
    tools = StorageTools(api)
    result = tools.list_os_templates("pve", filter="ubuntu")
    assert "ubuntu" in result[0].text.lower()


def test_create_vm_iso_and_net():
    api = Mock()
    # VM does not exist
    api.nodes.return_value.qemu.return_value.config.get.side_effect = Exception(
        "Configuration file does not exist"
    )
    api.nodes.return_value.storage.get.return_value = [
        {"storage": "local-lvm", "content": "images", "type": "lvmthin"}
    ]
    api.nodes.return_value.qemu.create.return_value = "UPID:create"
    tools = VMTools(api)
    result = tools.create_vm(
        "pve",
        "150",
        "blank",
        2,
        2048,
        20,
        iso="local:iso/ubuntu.iso",
        bridge="vmbr1",
        ciuser="ubuntu",
        sshkeys="ssh-ed25519 AAAA",
        ipconfig0="ip=dhcp",
    )
    assert "150" in result[0].text
    kwargs = api.nodes.return_value.qemu.create.call_args.kwargs
    assert "ide2" in kwargs
    assert kwargs["net0"] == "virtio,bridge=vmbr1"
    assert kwargs["ciuser"] == "ubuntu"


def test_create_lxc_auto_template():
    api = Mock()
    api.nodes.return_value.lxc.return_value.config.get.side_effect = Exception(
        "Configuration file does not exist"
    )
    api.nodes.return_value.qemu.return_value.config.get.side_effect = Exception(
        "Configuration file does not exist"
    )
    api.nodes.return_value.storage.get.return_value = [
        {"storage": "local-lvm", "content": "rootdir", "type": "lvmthin"},
        {"storage": "local", "content": "vztmpl", "type": "dir"},
    ]
    api.nodes.return_value.storage.return_value.content.get.return_value = [
        {"volid": "local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst"}
    ]
    api.nodes.return_value.lxc.create.return_value = "UPID:lxc"
    tools = ContainerTools(api)
    result = tools.create_lxc(
        node="pve",
        vmid="250",
        hostname="docker-nest",
        features="nesting=1,keyctl=1",
        bridge="vmbr0",
        ip="dhcp",
        ostemplate_filter="debian",
    )
    assert "250" in result[0].text
    kwargs = api.nodes.return_value.lxc.create.call_args.kwargs
    assert "debian" in kwargs["ostemplate"]
    assert "nesting=1" in kwargs["features"]
    assert "bridge=vmbr0" in kwargs["net0"]


def test_create_snapshot():
    api = Mock()
    api.nodes.return_value.qemu.return_value.snapshot.create.return_value = "UPID:snap"
    tools = SnapshotTools(api)
    result = tools.create_snapshot("pve", "100", "before-upgrade")
    assert "before-upgrade" in result[0].text


def test_create_backup():
    api = Mock()
    api.nodes.return_value.vzdump.create.return_value = "UPID:backup"
    tools = BackupTools(api)
    result = tools.create_backup("pve", "100", storage="local")
    assert "100" in result[0].text


def test_get_storage_content():
    api = Mock()
    api.nodes.return_value.storage.return_value.content.get.return_value = [
        {"volid": "local:vztmpl/ubuntu.tar.zst", "content": "vztmpl"}
    ]
    tools = StorageTools(api)
    result = tools.get_storage_content("pve", "local", "vztmpl")
    assert "ubuntu" in result[0].text


def test_migrate_guest():
    api = Mock()
    api.nodes.return_value.qemu.return_value.migrate.post.return_value = "UPID:mig"
    tools = MigrateTools(api)
    result = tools.migrate_guest("pve1", "100", "pve2")
    assert "pve2" in result[0].text


def test_ha_list_groups():
    api = Mock()
    api.cluster.ha.groups.get.return_value = [{"group": "grp1", "nodes": "pve1"}]
    tools = HATools(api)
    result = tools.list_ha_groups()
    assert "grp1" in result[0].text


def test_list_users():
    api = Mock()
    api.access.users.get.return_value = [{"userid": "root@pam"}]
    tools = AccessTools(api)
    result = tools.list_users()
    assert "root@pam" in result[0].text


def test_list_node_networks():
    api = Mock()
    api.nodes.return_value.network.get.return_value = [
        {"iface": "vmbr0", "type": "bridge"}
    ]
    tools = NetworkTools(api)
    result = tools.list_node_networks("pve")
    assert "vmbr0" in result[0].text


def test_list_cluster_firewall_rules():
    api = Mock()
    api.cluster.firewall.rules.get.return_value = [{"action": "ACCEPT", "type": "in"}]
    tools = FirewallTools(api)
    result = tools.list_cluster_firewall_rules()
    assert "ACCEPT" in result[0].text


def test_get_vm_config():
    api = Mock()
    api.nodes.return_value.qemu.return_value.config.get.return_value = {
        "cores": 2,
        "memory": 2048,
        "name": "web",
    }
    tools = VMTools(api)
    result = tools.get_vm_config("pve", "100")
    assert "web" in result[0].text


def test_get_lxc_config():
    api = Mock()
    api.nodes.return_value.lxc.return_value.config.get.return_value = {
        "hostname": "ct1",
        "cores": 1,
    }
    tools = ContainerTools(api)
    result = tools.get_lxc_config("pve", "200")
    assert "ct1" in result[0].text


def test_reboot_vm():
    api = Mock()
    api.nodes.return_value.qemu.return_value.status.current.get.return_value = {
        "status": "running"
    }
    api.nodes.return_value.qemu.return_value.status.reboot.post.return_value = "UPID:rb"
    tools = VMTools(api)
    result = tools.reboot_vm("pve", "100")
    assert "reboot" in result[0].text.lower()
