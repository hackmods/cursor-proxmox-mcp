"""Tests for LXC exec (SSH/pct), network helpers, and agent UX."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from proxmox_mcp.config.models import SSHConfig
from proxmox_mcp.ssh.pct import PctExecutor, ssh_configured
from proxmox_mcp.tools.container import ContainerTools
from proxmox_mcp.tools.helpers import (
    check_exec_allowlist,
    configured_ipv4_summary,
    parse_lxc_networks,
    parse_net_kv,
    qemu_not_found_message,
)
from tests.fakes.proxmox import make_fake_proxmox


def test_parse_net_kv_static():
    parsed = parse_net_kv("name=eth0,bridge=vmbr0,ip=192.168.0.121/24,gw=192.168.0.1")
    assert parsed["bridge"] == "vmbr0"
    assert parsed["ip"] == "192.168.0.121/24"
    assert parsed["gw"] == "192.168.0.1"


def test_parse_lxc_networks_dhcp():
    nets = parse_lxc_networks(
        {"net0": "name=eth0,bridge=vmbr0,ip=dhcp,hwaddr=BC:24:11:00:00:01"}
    )
    assert len(nets) == 1
    assert nets[0]["mode"] == "dhcp"
    assert nets[0]["hwaddr"] == "BC:24:11:00:00:01"
    assert configured_ipv4_summary(nets) == "dhcp"


def test_qemu_not_found_hint():
    msg = qemu_not_found_message("121", "pve1")
    assert "121" in msg
    assert "get_containers" in msg
    assert "guest_type=lxc" in msg


def test_check_exec_allowlist(monkeypatch):
    monkeypatch.setenv("PROXMOX_MCP_EXEC_ALLOWLIST", r"^echo ")
    check_exec_allowlist("echo hi")
    with pytest.raises(ValueError, match="ALLOWLIST"):
        check_exec_allowlist("rm -rf /")


def test_ssh_configured():
    assert not ssh_configured(None)
    assert not ssh_configured(SSHConfig(enabled=False))
    assert ssh_configured(SSHConfig(enabled=True, user="root"))


def test_execute_lxc_requires_ssh():
    api = make_fake_proxmox(lxc={"121": {"name": "ct", "status": "running"}})
    tools = ContainerTools(api)
    with pytest.raises(ValueError, match="opt-in SSH"):
        tools.execute_lxc_command("pve", "121", "hostname")


def test_execute_lxc_via_pct():
    api = make_fake_proxmox(lxc={"121": {"name": "ct", "status": "running"}})
    ssh = SSHConfig(enabled=True, user="root", private_key_path="/var/keys/test.key")
    tools = ContainerTools(api, ssh_config=ssh, proxmox_host="10.0.0.1")
    fake_result = MagicMock(
        success=True, command="hostname", exit_code=0, stdout="ct\n", stderr=""
    )
    with patch.object(tools._pct, "execute", return_value=fake_result) as mock_exec:
        out = tools.execute_lxc_command("pve", "121", "hostname")
    mock_exec.assert_called_once_with("pve", "121", "hostname")
    text = out[0].text
    assert "hostname" in text
    assert '"exit_code": 0' in text or "exit_code" in text


def test_get_lxc_network_configured_only():
    api = make_fake_proxmox(
        lxc={
            "121": {
                "hostname": "ct",
                "status": "running",
                "net0": "name=eth0,bridge=vmbr0,ip=192.168.0.121/24",
            }
        }
    )
    tools = ContainerTools(api)
    out = tools.get_lxc_network("pve", "121", resolve_runtime=True)
    text = out[0].text
    assert "192.168.0.121/24" in text
    assert "Runtime IP requires" in text or "runtime_note" in text


def test_get_containers_includes_ip():
    api = make_fake_proxmox(
        lxc={
            "121": {
                "hostname": "ct",
                "status": "running",
                "cores": 2,
                "net0": "name=eth0,bridge=vmbr0,ip=10.0.0.5/24",
            }
        }
    )
    tools = ContainerTools(api)
    out = tools.get_containers()
    assert "10.0.0.5/24" in out[0].text


def test_pct_resolve_host_override():
    ssh = SSHConfig(
        enabled=True,
        user="root",
        host_overrides={"pve1": "192.168.1.10"},
    )
    ex = PctExecutor(ssh, "10.0.0.1")
    assert ex.resolve_host("pve1") == "192.168.1.10"
    assert ex.resolve_host("pve2") == "10.0.0.1"


def test_load_config_with_ssh(tmp_path, monkeypatch):
    import json

    from proxmox_mcp.config.loader import load_config

    monkeypatch.setenv("TOK", "secret")
    cfg = {
        "proxmox": {"host": "10.0.0.1", "port": 8006, "verify_ssl": True, "service": "PVE"},
        "auth": {"user": "u@pve", "token_name": "t", "token_value": "${TOK}"},
        "logging": {"level": "INFO"},
        "ssh": {"enabled": True, "user": "root", "private_key_path": "/keys/id"},
    }
    path = tmp_path / "c.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    loaded = load_config(str(path))
    assert loaded.ssh is not None
    assert loaded.ssh.enabled is True
    assert loaded.ssh.private_key_path == "/keys/id"


def test_create_lxc_passes_ssh_public_keys_and_password():
    from unittest.mock import Mock

    api = Mock()
    api.nodes.get.return_value = [{"node": "pve"}]
    api.nodes.return_value.lxc.get.return_value = []
    api.nodes.return_value.storage.get.return_value = [
        {"storage": "local-lvm", "type": "lvmthin", "content": "images,rootdir"},
        {"storage": "local", "type": "dir", "content": "iso,vztmpl,backup"},
    ]
    api.nodes.return_value.lxc.create.return_value = "UPID:lxc"
    # qemu/lxc config miss for assert_id_absent
    api.nodes.return_value.qemu.return_value.config.get.side_effect = Exception(
        "does not exist"
    )
    api.nodes.return_value.lxc.return_value.config.get.side_effect = Exception(
        "does not exist"
    )
    tools = ContainerTools(api)
    out = tools.create_lxc(
        "pve",
        "301",
        "app1",
        ostemplate="local:vztmpl/ubuntu.tar.zst",
        password="SecretPass1",
        ssh_public_keys="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITest comment",
    )
    kwargs = api.nodes.return_value.lxc.create.call_args.kwargs
    assert kwargs["password"] == "SecretPass1"
    assert "ssh-public-keys" in kwargs
    assert "ssh-ed25519" in kwargs["ssh-public-keys"]
    text = out[0].text
    assert "SecretPass1" not in text
    assert "SSH public keys" in text
    assert "wait_for_task" in text


def test_create_lxc_hostname_collision_warning():
    api = make_fake_proxmox(
        lxc={"121": {"hostname": "lumon-docker", "status": "running"}}
    )
    tools = ContainerTools(api)
    out = tools.create_lxc(
        "pve",
        "122",
        "lumon-docker",
        ostemplate="local:vztmpl/ubuntu.tar.zst",
    )
    assert "already used" in out[0].text
    assert "121" in out[0].text


def test_set_lxc_password_requires_ssh():
    api = make_fake_proxmox(lxc={"122": {"hostname": "ct", "status": "running"}})
    tools = ContainerTools(api)
    with pytest.raises(ValueError, match="opt-in SSH"):
        tools.set_lxc_password("pve", "122", "NewPass123")


def test_set_lxc_password_via_pct():
    api = make_fake_proxmox(lxc={"122": {"hostname": "ct", "status": "running"}})
    ssh = SSHConfig(enabled=True, user="root", private_key_path="/var/keys/test.key")
    tools = ContainerTools(api, ssh_config=ssh, proxmox_host="10.0.0.1")
    fake = MagicMock(success=True, exit_code=0, stdout="", stderr="", command="x")
    with patch.object(tools._pct, "execute", return_value=fake) as mock_exec:
        out = tools.set_lxc_password("pve", "122", "NewPass123", enable_password_ssh=True)
    assert mock_exec.called
    cmd = mock_exec.call_args[0][2]
    assert "chpasswd" in cmd
    assert "PermitRootLogin yes" in cmd
    assert "NewPass123" not in out[0].text


def test_set_lxc_ssh_keys_via_pct():
    api = make_fake_proxmox(lxc={"122": {"hostname": "ct", "status": "running"}})
    ssh = SSHConfig(enabled=True, user="root", private_key_path="/var/keys/test.key")
    tools = ContainerTools(api, ssh_config=ssh, proxmox_host="10.0.0.1")
    fake = MagicMock(success=True, exit_code=0, stdout="", stderr="", command="x")
    key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITest"
    with patch.object(tools._pct, "execute", return_value=fake) as mock_exec:
        out = tools.set_lxc_ssh_keys("pve", "122", key, mode="replace")
    assert "authorized_keys" in mock_exec.call_args[0][2]
    assert "1 SSH public key" in out[0].text
