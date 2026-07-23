"""Phase C light + QEMU agent / cloud-init bootstrap (v1.6.0) tests."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from proxmox_mcp.tools.cluster import ClusterTools
from proxmox_mcp.tools.inventory import ALL_TOOL_NAMES, DESTRUCTIVE_TOOLS
from proxmox_mcp.tools.node import NodeTools
from proxmox_mcp.tools.vm import VMTools


NEW_TOOLS = (
    "get_vm_guest_info",
    "fsfreeze_vm",
    "fsthaw_vm",
    "bootstrap_cloudinit_vm",
    "reboot_node",
    "shutdown_node",
    "get_cluster_join_info",
    "join_cluster",
)


def test_v16_tools_in_inventory():
    for name in NEW_TOOLS:
        assert name in ALL_TOOL_NAMES
    assert len(ALL_TOOL_NAMES) == 179
    for name in ("reboot_node", "shutdown_node", "join_cluster"):
        assert name in DESTRUCTIVE_TOOLS


def test_get_vm_guest_info_soft_fail_per_section():
    api = MagicMock()
    status = MagicMock()
    status.get.return_value = {"status": "running"}
    api.nodes.return_value.qemu.return_value.status.current = status

    def agent_factory(cmd):
        ep = MagicMock()
        if cmd == "get-osinfo":
            ep.get.return_value = {"result": {"id": "ubuntu"}}
        elif cmd == "get-fsinfo":
            ep.get.side_effect = RuntimeError("no fs")
        else:
            ep.get.return_value = {"result": "ok"}
        return ep

    api.nodes.return_value.qemu.return_value.agent = agent_factory

    tools = VMTools(api)
    text = tools.get_vm_guest_info("pve", "100", sections="os,fs")[0].text
    data = json.loads(text)
    assert data["sections"]["os"]["id"] == "ubuntu"
    assert any("fs" in n for n in data["notes"])


def test_fsfreeze_and_thaw():
    api = MagicMock()
    status = MagicMock()
    status.get.return_value = {"status": "running"}
    api.nodes.return_value.qemu.return_value.status.current = status

    calls = []

    def agent_factory(cmd):
        calls.append(cmd)
        ep = MagicMock()
        ep.post.return_value = {"result": 0}
        ep.get.return_value = {"result": "frozen" if "freeze" in cmd else "thawed"}
        return ep

    api.nodes.return_value.qemu.return_value.agent = agent_factory
    tools = VMTools(api)
    freeze_text = tools.fsfreeze_vm("pve", "100")[0].text
    assert "fsfreeze-freeze" in freeze_text
    assert "fsthaw_vm" in freeze_text
    thaw_text = tools.fsthaw_vm("pve", "100")[0].text
    assert "fsfreeze-thaw" in thaw_text
    assert "fsfreeze-freeze" in calls
    assert "fsfreeze-thaw" in calls


def test_fsfreeze_requires_running():
    api = MagicMock()
    api.nodes.return_value.qemu.return_value.status.current.get.return_value = {
        "status": "stopped"
    }
    tools = VMTools(api)
    with pytest.raises(ValueError, match="not running"):
        tools.fsfreeze_vm("pve", "100")


def test_reboot_node_confirm_gate():
    api = MagicMock()
    tools = NodeTools(api)
    with pytest.raises(ValueError, match="confirm must equal"):
        tools.reboot_node("pve", confirm="wrong")
    text = tools.reboot_node("pve", confirm="pve")[0].text
    assert "IRREVERSIBLE" in text
    api.nodes.return_value.status.post.assert_called_once_with(command="reboot")


def test_shutdown_node_confirm_gate():
    api = MagicMock()
    tools = NodeTools(api)
    with pytest.raises(ValueError, match="confirm must equal"):
        tools.shutdown_node("pve", confirm="PVE")
    text = tools.shutdown_node("pve", confirm="pve")[0].text
    assert "IRREVERSIBLE" in text
    api.nodes.return_value.status.post.assert_called_once_with(command="shutdown")


def test_join_cluster_confirm_join():
    api = MagicMock()
    api.cluster.config.join.post.return_value = "UPID:join"
    tools = ClusterTools(api)
    with pytest.raises(ValueError, match="literal string 'JOIN'"):
        tools.join_cluster("192.168.0.23", "fp", "secret", confirm="yes")
    text = tools.join_cluster(
        "192.168.0.23", "AA:BB", "secret", confirm="JOIN"
    )[0].text
    assert "IRREVERSIBLE" in text
    api.cluster.config.join.post.assert_called_once()
    kwargs = api.cluster.config.join.post.call_args.kwargs
    assert kwargs["hostname"] == "192.168.0.23"
    assert kwargs["password"] == "secret"


def test_get_cluster_join_info():
    api = MagicMock()
    api.cluster.config.join.get.return_value = {
        "preferred_node": "pve",
        "nodelist": [{"name": "pve", "pve_fp": "AA"}],
    }
    tools = ClusterTools(api)
    text = tools.get_cluster_join_info()[0].text
    assert "preferred_node" in text or "pve" in text


@patch("proxmox_mcp.tools.vm.wait_for_upid")
def test_bootstrap_cloudinit_vm(mock_wait):
    api = MagicMock()
    api.cluster.nextid.get.return_value = 200
    api.nodes.return_value.qemu.return_value.clone.post.return_value = "UPID:clone"
    api.nodes.return_value.qemu.return_value.status.start.post.return_value = "UPID:start"
    api.nodes.return_value.qemu.return_value.status.current.get.return_value = {
        "status": "running"
    }
    api.nodes.return_value.qemu.return_value.config.get.return_value = {
        "net0": "virtio,bridge=vmbr0"
    }

    agent_ep = MagicMock()
    agent_ep.get.return_value = {
        "result": [
            {
                "name": "eth0",
                "ip-addresses": [
                    {"ip-address-type": "ipv4", "ip-address": "192.168.0.200"}
                ],
            }
        ]
    }
    api.nodes.return_value.qemu.return_value.agent = MagicMock(return_value=agent_ep)

    tools = VMTools(api)
    text = tools.bootstrap_cloudinit_vm(
        node="pve",
        name="ci-test",
        clone_from="9000",
        sshkeys="ssh-ed25519 AAAA",
        ipconfig0="ip=dhcp",
    )[0].text
    assert "bootstrap_cloudinit_vm complete" in text
    payload = json.loads(text.split("\n", 1)[1])
    assert payload["vmid"] == "200"
    assert payload["name"] == "ci-test"
    assert mock_wait.call_count >= 2


def test_bootstrap_requires_clone_from():
    tools = VMTools(MagicMock())
    with pytest.raises(ValueError, match="clone_from"):
        tools.bootstrap_cloudinit_vm(node="pve", name="x", clone_from="")
