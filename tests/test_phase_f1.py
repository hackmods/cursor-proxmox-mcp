"""Phase F.1 unit tests: VM network/push, create wait, nginx, inventory probes."""
from __future__ import annotations

import base64
from unittest.mock import MagicMock, patch

import pytest

from proxmox_mcp.ssh.pct import PctExecResult
from proxmox_mcp.tools.container import ContainerTools
from proxmox_mcp.tools.helpers import (
    agent_runtime_ipv4_summary,
    parse_agent_network_interfaces,
    parse_qemu_networks,
)
from proxmox_mcp.tools.inventory import ALL_TOOL_NAMES
from proxmox_mcp.tools.vm import VMTools


def test_phase_f1_tools_in_inventory():
    for name in (
        "get_vm_network",
        "push_to_vm",
        "pull_from_vm",
        "deploy_static_nginx",
        "deploy_node_app",
    ):
        assert name in ALL_TOOL_NAMES
    assert len(ALL_TOOL_NAMES) == 211


def test_parse_qemu_networks_virtio_mac():
    nets = parse_qemu_networks(
        {"net0": "virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0,firewall=1"}
    )
    assert len(nets) == 1
    assert nets[0]["model"] == "virtio"
    assert nets[0]["hwaddr"] == "AA:BB:CC:DD:EE:FF"
    assert nets[0]["bridge"] == "vmbr0"


def test_parse_agent_network_and_ipv4():
    raw = {
        "result": [
            {
                "name": "lo",
                "ip-addresses": [{"ip-address": "127.0.0.1", "ip-address-type": "ipv4"}],
            },
            {
                "name": "eth0",
                "hardware-address": "aa:bb:cc:dd:ee:ff",
                "ip-addresses": [
                    {"ip-address": "10.0.0.5", "ip-address-type": "ipv4"},
                    {"ip-address": "fe80::1", "ip-address-type": "ipv6"},
                ],
            },
        ]
    }
    ifaces = parse_agent_network_interfaces(raw)
    assert len(ifaces) == 2
    assert agent_runtime_ipv4_summary(ifaces) == ["10.0.0.5"]


def test_get_vm_network_with_agent():
    api = MagicMock()
    api.nodes.return_value.qemu.return_value.config.get.return_value = {
        "net0": "virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0"
    }
    api.nodes.return_value.qemu.return_value.status.current.get.return_value = {
        "status": "running"
    }
    agent = MagicMock()
    agent.return_value.get.return_value = {
        "result": [
            {
                "name": "eth0",
                "ip-addresses": [{"ip-address": "192.168.1.50"}],
            }
        ]
    }
    api.nodes.return_value.qemu.return_value.agent = agent
    out = VMTools(api).get_vm_network("pve", "100")
    text = out[0].text
    assert "192.168.1.50" in text
    assert "net0" in text


def test_get_vm_network_agent_failure_note():
    api = MagicMock()
    api.nodes.return_value.qemu.return_value.config.get.return_value = {
        "net0": "virtio,bridge=vmbr0"
    }
    api.nodes.return_value.qemu.return_value.status.current.get.return_value = {
        "status": "running"
    }
    agent = MagicMock()
    agent.return_value.get.side_effect = RuntimeError("agent not running")
    api.nodes.return_value.qemu.return_value.agent = agent
    out = VMTools(api).get_vm_network("pve", "100")
    assert "Guest agent" in out[0].text or "agent" in out[0].text.lower()


def test_create_vm_wait_true():
    api = MagicMock()
    api.nodes.return_value.qemu.return_value.config.get.side_effect = Exception(
        "does not exist"
    )
    api.nodes.return_value.storage.get.return_value = [
        {"storage": "local-lvm", "type": "lvmthin", "content": "images"}
    ]
    api.nodes.return_value.qemu.create.return_value = "UPID:pve:000:create"
    with patch("proxmox_mcp.tools.vm.wait_for_upid") as wait:
        wait.return_value = {"status": "stopped", "exitstatus": "OK"}
        with patch("proxmox_mcp.tools.vm.assert_id_absent"):
            out = VMTools(api).create_vm(
                "pve", "210", "n", 1, 512, 4, wait=True
            )
    assert "wait=true" in out[0].text
    wait.assert_called_once()


def test_create_lxc_wait_true():
    api = MagicMock()
    api.nodes.return_value.storage.get.return_value = [
        {"storage": "local-lvm", "type": "lvmthin", "content": "rootdir,vztmpl"}
    ]
    api.nodes.return_value.lxc.create.return_value = "UPID:pve:000:create"
    tools = ContainerTools(api)
    with patch("proxmox_mcp.tools.container.wait_for_upid") as wait:
        wait.return_value = {"status": "stopped", "exitstatus": "OK"}
        with patch("proxmox_mcp.tools.container.assert_id_absent"):
            with patch.object(
                tools, "_resolve_ostemplate", return_value="local:vztmpl/u.tar.zst"
            ):
                with patch.object(tools, "_hostname_collision_warning", return_value=None):
                    out = tools.create_lxc(
                        "pve", "122", "lab", wait=True
                    )
    assert "wait=true" in out[0].text
    wait.assert_called_once()


def test_push_to_vm_base64():
    api = MagicMock()
    api.nodes.return_value.qemu.return_value.status.current.get.return_value = {
        "status": "running"
    }
    agent = MagicMock()
    api.nodes.return_value.qemu.return_value.agent = agent
    payload = base64.b64encode(b"hello").decode("ascii")
    out = VMTools(api).push_to_vm(
        "pve", "100", "/tmp/x.txt", content_base64=payload
    )
    assert "Pushed 5 bytes" in out[0].text
    agent.assert_called_with("file-write")
    agent.return_value.post.assert_called_once()


def test_get_containers_probes_opt_in():
    api = MagicMock()
    api.nodes.get.return_value = [{"node": "pve"}]
    api.nodes.return_value.lxc.get.return_value = [
        {"vmid": 122, "status": "running", "name": "lab", "mem": 1, "maxmem": 2}
    ]
    api.nodes.return_value.lxc.return_value.config.get.return_value = {
        "hostname": "lab",
        "cores": 1,
        "net0": "name=eth0,bridge=vmbr0,ip=dhcp",
    }
    tools = ContainerTools(api)
    pct = MagicMock()
    pct.execute.side_effect = [
        PctExecResult(True, "yes\n", "", 0, "docker"),
        PctExecResult(True, "no\n", "", 0, "port"),
    ]
    tools._pct = pct
    out = tools.get_containers(probes=True)
    text = out[0].text
    assert "Probes:" in text or "probe" in text.lower()
    assert "docker=yes" in text or "docker=yes" in text.replace(" ", "")


def test_pull_from_vm_returns_base64():
    api = MagicMock()
    api.nodes.return_value.qemu.return_value.status.current.get.return_value = {
        "status": "running"
    }
    agent = MagicMock()
    agent.return_value.get.return_value = {
        "result": base64.b64encode(b"payload").decode("ascii")
    }
    api.nodes.return_value.qemu.return_value.agent = agent
    out = VMTools(api).pull_from_vm("pve", "100", "/tmp/x.txt")
    text = out[0].text
    assert "content_base64" in text or "cGF5bG9hZA" in text  # base64 of payload


def test_get_vm_network_stopped():
    api = MagicMock()
    api.nodes.return_value.qemu.return_value.config.get.return_value = {
        "net0": "virtio,bridge=vmbr0"
    }
    api.nodes.return_value.qemu.return_value.status.current.get.return_value = {
        "status": "stopped"
    }
    out = VMTools(api).get_vm_network("pve", "100")
    assert "not running" in out[0].text.lower()


def test_push_to_vm_requires_one_source():
    api = MagicMock()
    with pytest.raises(ValueError, match="exactly one"):
        VMTools(api).push_to_vm("pve", "100", "/tmp/x")


def test_deploy_static_nginx_tarball():
    api = MagicMock()
    api.nodes.return_value.lxc.return_value.status.current.get.return_value = {
        "status": "running"
    }
    tools = ContainerTools(api)
    pct = MagicMock()
    pct.execute.return_value = PctExecResult(True, "", "", 0, "cmd")
    tools._pct = pct
    # minimal gzip header + fake name so lower.endswith .tar.gz works via src_name
    data = b"not-a-real-tar"
    with patch.object(tools, "get_lxc_network", return_value=[]):
        # content_base64 alone uses payload.bin — force tar via local_path name
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as fh:
            fh.write(data)
            path = fh.name
        try:
            out = tools.deploy_static_nginx("pve", "122", local_path=path)
        finally:
            os.unlink(path)
    assert "extracted" in out[0].text.lower() or "deploy_static_nginx" in out[0].text
    assert pct.push_to_guest.called


def test_pull_from_vm_to_local_path(tmp_path):
    api = MagicMock()
    api.nodes.return_value.qemu.return_value.status.current.get.return_value = {
        "status": "running"
    }
    agent = MagicMock()
    agent.return_value.get.return_value = {"result": "hello-plain"}
    api.nodes.return_value.qemu.return_value.agent = agent
    dest = tmp_path / "out.bin"
    out = VMTools(api).pull_from_vm("pve", "100", "/tmp/x.txt", local_path=str(dest))
    assert "Pulled" in out[0].text
    assert dest.exists()


def test_deploy_static_nginx_install_only():
    api = MagicMock()
    api.nodes.return_value.lxc.return_value.status.current.get.return_value = {
        "status": "running"
    }
    tools = ContainerTools(api)
    pct = MagicMock()
    pct.execute.return_value = PctExecResult(True, "", "", 0, "cmd")
    tools._pct = pct
    with patch.object(tools, "get_lxc_network", side_effect=RuntimeError("no net")):
        out = tools.deploy_static_nginx("pve", "122")
    assert "default nginx index" in out[0].text
    assert "get_lxc_network" in out[0].text


def test_deploy_static_nginx_tar():
    api = MagicMock()
    api.nodes.return_value.lxc.return_value.status.current.get.return_value = {
        "status": "running"
    }
    tools = ContainerTools(api)
    pct = MagicMock()
    pct.execute.return_value = PctExecResult(True, "", "", 0, "cmd")
    tools._pct = pct
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".tar", delete=False) as fh:
        fh.write(b"x")
        path = fh.name
    try:
        with patch.object(tools, "get_lxc_network", return_value=[]):
            out = tools.deploy_static_nginx("pve", "122", local_path=path)
    finally:
        os.unlink(path)
    assert "extracted" in out[0].text.lower()


def test_deploy_node_app_install_only():
    api = MagicMock()
    api.nodes.return_value.lxc.return_value.status.current.get.return_value = {
        "status": "running"
    }
    tools = ContainerTools(api)
    pct = MagicMock()
    pct.execute.return_value = PctExecResult(True, "", "", 0, "cmd")
    tools._pct = pct
    with patch.object(tools, "get_lxc_network", side_effect=RuntimeError("no net")):
        out = tools.deploy_node_app("pve", "111")
    assert "deploy_node_app" in out[0].text
    assert "Node installed only" in out[0].text
    assert "wget -qO-" in out[0].text


def test_deploy_node_app_tarball():
    api = MagicMock()
    api.nodes.return_value.lxc.return_value.status.current.get.return_value = {
        "status": "running"
    }
    tools = ContainerTools(api)
    pct = MagicMock()

    def _exec(node, vmid, command, timeout=None):
        # nest check returns empty → workdir = remote_dir
        if "find . -mindepth 1" in command:
            return PctExecResult(True, "", "", 0, command)
        return PctExecResult(True, "", "", 0, command)

    pct.execute.side_effect = _exec
    tools._pct = pct
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as fh:
        fh.write(b"fake")
        path = fh.name
    try:
        with patch.object(tools, "get_lxc_network", return_value=[]):
            out = tools.deploy_node_app(
                "pve",
                "111",
                local_path=path,
                service_name="behind7proxies",
                port=3000,
            )
    finally:
        os.unlink(path)
    assert "deploy_node_app" in out[0].text
    assert "build OK" in out[0].text
    assert pct.push_to_guest.called
    assert "behind7proxies" in out[0].text


def test_probe_container_skipped_stopped():
    tools = ContainerTools(MagicMock())
    tools._pct = MagicMock()
    out = tools._probe_container("pve", "1", "stopped")
    assert out["probe_note"] == "skipped (not running)"


def test_probe_container_skipped_no_ssh():
    tools = ContainerTools(MagicMock())
    tools._pct = None
    out = tools._probe_container("pve", "1", "running")
    assert "SSH" in (out["probe_note"] or "")
