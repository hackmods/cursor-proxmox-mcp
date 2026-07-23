"""Post-r11 slices 2–5 unit smoke."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from proxmox_mcp.tools.container import ContainerTools
from proxmox_mcp.tools.vm import VMTools
from proxmox_mcp.tools.inventory import ALL_TOOL_NAMES


def test_new_tools_in_inventory():
    for name in (
        "configure_lxc_ssh",
        "get_docker_lxc_status",
        "bootstrap_docker_lxc",
        "provision_lxc",
        "qm_set_vm",
    ):
        assert name in ALL_TOOL_NAMES
    assert len(ALL_TOOL_NAMES) == 207


def test_create_lxc_with_tags_description_onboot():
    proxmox = MagicMock()
    proxmox.nodes.get.return_value = [{"node": "pve"}]
    proxmox.nodes.return_value.lxc.get.return_value = []
    proxmox.nodes.return_value.storage.get.return_value = [
        {"storage": "local-lvm", "type": "lvmthin", "content": "images,rootdir"},
        {"storage": "local", "type": "dir", "content": "iso,vztmpl,backup"},
    ]
    create = MagicMock(return_value="UPID:lxc")
    proxmox.nodes.return_value.lxc.create = create
    with patch("proxmox_mcp.tools.container.assert_id_absent"):
        text = ContainerTools(proxmox).create_lxc(
            "pve",
            "110",
            "lab-ct",
            ostemplate="local:vztmpl/debian.tar.zst",
            onboot=True,
            description="helper scripts host",
            tags="proxmox-helper-scripts",
        )[0].text
    assert create.call_args.kwargs["onboot"] == 1
    assert create.call_args.kwargs["tags"] == "proxmox-helper-scripts"
    assert create.call_args.kwargs["description"] == "helper scripts host"
    assert "Onboot: 1" in text
    assert "proxmox-helper-scripts" in text


def test_provision_lxc_happy_path_mocked():
    proxmox = MagicMock()
    ssh = MagicMock(
        enabled=True,
        timeout=30,
        user="root",
        private_key_path="/k",
        host_overrides={},
        pct_path="/usr/sbin/pct",
    )
    tools = ContainerTools(proxmox, ssh_config=ssh, proxmox_host="h")
    proxmox.nodes.return_value.lxc.return_value.status.current.get.return_value = {
        "status": "stopped"
    }
    proxmox.nodes.return_value.lxc.return_value.status.start.post.return_value = (
        "UPID:start"
    )
    with patch.object(
        tools, "create_lxc", return_value=[MagicMock(text="created")]
    ):
        with patch(
            "proxmox_mcp.tools.container.wait_for_upid",
            return_value={"status": "stopped", "exitstatus": "OK"},
        ):
            with patch.object(
                tools,
                "configure_lxc_ssh",
                return_value=[MagicMock(text="ssh ok")],
            ) as mock_ssh:
                with patch.object(
                    tools,
                    "get_lxc_network",
                    return_value=[
                        MagicMock(
                            text=json.dumps({"runtime_ips": ["192.168.0.174"]})
                        )
                    ],
                ):
                    text = tools.provision_lxc(
                        "pve",
                        "ct110",
                        vmid="110",
                        ssh_public_keys="ssh-ed25519 AAAA",
                        tags="lab",
                        onboot=True,
                    )[0].text
    assert "provision_lxc complete" in text
    assert "192.168.0.174" in text
    assert "110" in text
    assert "ssh root@192.168.0.174" in text
    mock_ssh.assert_called_once()
    assert "Secret" not in text


def test_provision_lxc_requires_ssh():
    tools = ContainerTools(MagicMock())
    with pytest.raises(ValueError, match="opt-in SSH"):
        tools.provision_lxc("pve", "ct")


def test_get_docker_lxc_status_stopped():
    proxmox = MagicMock()
    proxmox.nodes.return_value.lxc.return_value.config.get.return_value = {
        "features": "nesting=1"
    }
    proxmox.nodes.return_value.lxc.return_value.status.current.get.return_value = {
        "status": "stopped"
    }
    tools = ContainerTools(proxmox)
    data = json.loads(tools.get_docker_lxc_status("pve", "107")[0].text)
    assert data["docker_ok"] is False
    assert data["features"] == "nesting=1"


def test_configure_lxc_ssh_reports_listening():
    proxmox = MagicMock()
    proxmox.nodes.return_value.lxc.return_value.status.current.get.return_value = {
        "status": "running"
    }
    ssh = MagicMock(
        enabled=True,
        timeout=30,
        user="root",
        private_key_path="/k",
        host_overrides={},
        pct_path="/usr/sbin/pct",
    )
    tools = ContainerTools(proxmox, ssh_config=ssh, proxmox_host="h")
    with patch.object(
        tools._pct,
        "execute",
        side_effect=[
            MagicMock(success=True, stdout="ok", stderr="", exit_code=0),
            MagicMock(success=True, stdout="LISTEN 0 128 *:22", stderr="", exit_code=0),
        ],
    ):
        text = tools.configure_lxc_ssh("pve", "107")[0].text
    assert "sshd_listening" in text
    assert "true" in text.lower()


def test_qm_set_vm_allowlist():
    proxmox = MagicMock()
    ssh = MagicMock(
        enabled=True,
        timeout=30,
        user="root",
        private_key_path="/k",
        host_overrides={},
        pct_path="/usr/sbin/pct",
    )
    tools = VMTools(proxmox, ssh_config=ssh, proxmox_host="h")
    with pytest.raises(ValueError, match="at least one"):
        tools.qm_set_vm("pve", "100")
    with patch.object(
        tools._pct,
        "qm_set",
        return_value=MagicMock(success=True, stdout="", stderr="", exit_code=0),
    ) as qs:
        text = tools.qm_set_vm("pve", "100", onboot=1, tags="lab")[0].text
    qs.assert_called_once()
    assert "qm_set_vm" in text


def test_update_vm_config_acl_denied():
    proxmox = MagicMock()
    proxmox.nodes.return_value.qemu.return_value.config.put.side_effect = PermissionError(
        "403"
    )
    with pytest.raises(ValueError, match="vm_acl_denied"):
        VMTools(proxmox).update_vm_config("pve", "100", tags="x")


def test_create_vm_with_tags_description_onboot():
    proxmox = MagicMock()
    proxmox.nodes.return_value.storage.get.return_value = [
        {"storage": "local-lvm", "type": "lvmthin", "content": "images"}
    ]
    create = MagicMock(return_value="UPID:x")
    proxmox.nodes.return_value.qemu.create = create
    with patch("proxmox_mcp.tools.vm.assert_id_absent"):
        text = VMTools(proxmox).create_vm(
            "pve",
            "200",
            "lab",
            2,
            2048,
            20,
            onboot=True,
            description="test",
            tags="lab;docker",
        )[0].text
    assert "200" in text
    assert create.call_args.kwargs["onboot"] == 1
    assert create.call_args.kwargs["tags"] == "lab;docker"
    assert create.call_args.kwargs["description"] == "test"


def test_bootstrap_docker_lxc_happy_path_mocked():
    proxmox = MagicMock()
    ssh = MagicMock(
        enabled=True,
        timeout=30,
        user="root",
        private_key_path="/k",
        host_overrides={},
        pct_path="/usr/sbin/pct",
    )
    tools = ContainerTools(proxmox, ssh_config=ssh, proxmox_host="h")
    with patch.object(
        tools,
        "create_lxc",
        return_value=[MagicMock(text="created needs_crun")],
    ):
        with patch.object(tools, "start_lxc", return_value=[MagicMock(text="started")]):
            with patch.object(
                tools, "configure_lxc_dns", return_value=[MagicMock(text="dns")]
            ):
                with patch.object(
                    tools, "configure_lxc_ssh", return_value=[MagicMock(text="ssh")]
                ):
                    with patch.object(
                        tools,
                        "prepare_lxc_for_docker",
                        return_value=[
                            MagicMock(
                                text='prepare\n"docker_path": "crun"\nsmoke_test: OK\nrestart_required: False'
                            )
                        ],
                    ):
                        with patch.object(
                            tools,
                            "get_docker_lxc_status",
                            return_value=[
                                MagicMock(
                                    text=json.dumps(
                                        {
                                            "features": "nesting=1",
                                            "runtime_ips": ["192.168.0.50"],
                                        }
                                    )
                                )
                            ],
                        ):
                            with patch.object(
                                tools,
                                "get_lxc_network",
                                return_value=[
                                    MagicMock(
                                        text=json.dumps(
                                            {"runtime_ips": ["192.168.0.50"]}
                                        )
                                    )
                                ],
                            ):
                                text = tools.bootstrap_docker_lxc(
                                    "pve",
                                    "dock",
                                    vmid="150",
                                    ssh_public_keys="ssh-ed25519 AAAA",
                                )[0].text
    assert "bootstrap_docker_lxc complete" in text
    assert "docker_path" in text
    assert "150" in text


def test_handle_mutation_error_non_acl_falls_through():
    from proxmox_mcp.tools.base import ProxmoxTool
    from proxmox_mcp.errors import ProxmoxAPIError

    tools = ProxmoxTool(MagicMock())
    with pytest.raises(ProxmoxAPIError):
        tools._handle_mutation_error("op", RuntimeError("boom"), code="x")


def test_qm_set_host_command_and_pct_set():
    from proxmox_mcp.ssh.pct import PctExecutor

    ssh = MagicMock(
        enabled=True,
        timeout=30,
        user="root",
        private_key_path="/k",
        host_overrides={},
        pct_path="/usr/sbin/pct",
    )
    pct = PctExecutor(ssh, "host")
    with patch.object(
        pct,
        "run_host",
        return_value=MagicMock(success=True, stdout="", stderr="", exit_code=0),
    ) as rh:
        pct.qm_set("pve", "100", onboot=1, tags="a")
        pct.pct_set("pve", "107", nameserver="8.8.8.8", description="d")
    assert rh.call_count == 2
    assert "qm" in rh.call_args_list[0][0][1]
    assert "pct" in rh.call_args_list[1][0][1]


def test_get_docker_lxc_status_running_with_pct():
    proxmox = MagicMock()
    proxmox.nodes.return_value.lxc.return_value.config.get.return_value = {
        "features": "nesting=1,keyctl=1",
        "net0": "name=eth0,bridge=vmbr0,ip=192.168.0.10/24",
    }
    proxmox.nodes.return_value.lxc.return_value.status.current.get.return_value = {
        "status": "running"
    }
    ssh = MagicMock(
        enabled=True,
        timeout=30,
        user="root",
        private_key_path="/k",
        host_overrides={},
        pct_path="/usr/sbin/pct",
    )
    tools = ContainerTools(proxmox, ssh_config=ssh, proxmox_host="h")

    def _exec(_n, _v, command, timeout=None):
        if "DefaultRuntime" in command:
            out = "crun"
        elif "compose" in command:
            out = "Docker Compose version v2"
        elif "df" in command:
            out = "/dev/root 20G 5G 15G 25%"
        elif "hostname" in command:
            out = "192.168.0.10"
        else:
            out = "Docker version 29"
        return MagicMock(success=True, stdout=out, stderr="", exit_code=0)

    with patch.object(tools._pct, "execute", side_effect=_exec):
        data = json.loads(tools.get_docker_lxc_status("pve", "107")[0].text)
    assert data["default_runtime"] == "crun"
    assert data["runtime_ips"] == ["192.168.0.10"]


def test_access_create_user_acl():
    from proxmox_mcp.tools.access import AccessTools

    proxmox = MagicMock()
    proxmox.access.users.post.side_effect = PermissionError("403")
    with pytest.raises(ValueError, match="access_acl_denied"):
        AccessTools(proxmox).create_user("u@pve")


def test_ha_delete_resource_acl():
    from proxmox_mcp.tools.ha import HATools

    proxmox = MagicMock()
    proxmox.cluster.ha.resources.return_value.delete.side_effect = PermissionError("403")
    with pytest.raises(ValueError, match="ha_acl_denied"):
        HATools(proxmox).delete_ha_resource("vm:100")
