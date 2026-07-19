"""Phase F unit tests: SSH/pct helpers, capabilities, prepare/push."""
from __future__ import annotations

import base64
from unittest.mock import MagicMock, patch

import pytest

from proxmox_mcp.ssh.pct import (
    APPARMOR_NULL_BIND,
    APPARMOR_UNCONFINED,
    PctExecError,
    PctExecutor,
    lxc_pve_is_patched,
    parse_lxc_pve_version,
    require_host_ssh_message,
)
from proxmox_mcp.tools.capabilities import CapabilitiesTools, package_version
from proxmox_mcp.tools.container import ContainerTools
from proxmox_mcp.tools.inventory import ALL_TOOL_NAMES


def test_parse_lxc_pve_version_patched():
    assert parse_lxc_pve_version("6.0.5-2") == (6, 0, 5, 2)
    assert lxc_pve_is_patched(parse_lxc_pve_version("6.0.5-2")) is True
    assert lxc_pve_is_patched(parse_lxc_pve_version("6.0.5-1")) is False
    assert lxc_pve_is_patched(parse_lxc_pve_version("5.0.0-1")) is False


def test_require_host_ssh_message_no_pip_install_ssh():
    msg = require_host_ssh_message()
    assert "reload MCP" in msg
    assert "[ssh]" not in msg
    assert "pip install" not in msg


def test_phase_f_tools_in_inventory():
    for name in (
        "get_mcp_capabilities",
        "prepare_lxc_for_docker",
        "configure_lxc_dns",
        "pct_set_lxc",
        "push_to_lxc",
        "pull_from_lxc",
    ):
        assert name in ALL_TOOL_NAMES
    assert len(ALL_TOOL_NAMES) == 165


def test_package_version_nonzero():
    assert package_version()


def test_capabilities_ssh_off():
    tools = CapabilitiesTools(MagicMock(), ssh_config=None, proxmox_host="192.168.0.1")
    text = tools.get_mcp_capabilities()[0].text
    assert "ssh.enabled: False" in text
    assert "prepare_lxc_for_docker" in text
    assert "Host SSH off" in text


def test_capabilities_ssh_on_no_key_warn():
    ssh = MagicMock()
    ssh.enabled = True
    ssh.private_key_path = None
    tools = CapabilitiesTools(MagicMock(), ssh_config=ssh, proxmox_host="192.168.0.1")
    text = tools.get_mcp_capabilities()[0].text
    assert "ssh.enabled: True" in text
    assert "without private_key_path" in text


def test_apply_apparmor_idempotent_adds_both_lines():
    pct = PctExecutor(MagicMock(enabled=True, timeout=30, user="root"), "host")
    conf = "arch: amd64\nhostname: lab\nfeatures: nesting=1\n"
    with patch.object(pct, "read_lxc_conf", return_value=conf):
        with patch.object(pct, "write_lxc_conf") as write:
            applied = pct.apply_docker_apparmor_workaround("pve", "122")
    assert any("unconfined" in a for a in applied)
    assert any("apparmor/parameters/enabled" in a for a in applied)
    written = write.call_args[0][2]
    assert APPARMOR_UNCONFINED in written
    assert APPARMOR_NULL_BIND in written


def test_strip_apparmor_removes_workaround():
    pct = PctExecutor(MagicMock(enabled=True, timeout=30, user="root"), "host")
    conf = (
        "arch: amd64\n"
        f"{APPARMOR_UNCONFINED}\n"
        f"{APPARMOR_NULL_BIND}\n"
        "features: nesting=1,keyctl=1\n"
    )
    with patch.object(pct, "read_lxc_conf", return_value=conf):
        with patch.object(pct, "write_lxc_conf") as write:
            removed = pct.strip_docker_apparmor_workaround("pve", "122")
    assert len(removed) == 2
    written = write.call_args[0][2]
    assert "unconfined" not in written
    assert "apparmor/parameters/enabled" not in written


def test_push_size_limit():
    pct = PctExecutor(MagicMock(enabled=True, timeout=30, user="root"), "host")
    with pytest.raises(PctExecError, match="exceeds"):
        pct.push_to_guest("pve", "100", b"x" * (32 * 1024 * 1024 + 1), "/tmp/x")


def test_execute_lxc_command_field_aliases():
    proxmox = MagicMock()
    proxmox.nodes.return_value.lxc.return_value.status.current.get.return_value = {
        "status": "running"
    }
    ssh = MagicMock()
    ssh.enabled = True
    ssh.timeout = 30
    ssh.user = "root"
    ssh.private_key_path = "/tmp/key"
    ssh.host_overrides = {}
    ssh.pct_path = "/usr/sbin/pct"
    tools = ContainerTools(proxmox, ssh_config=ssh, proxmox_host="192.168.0.1")
    mock_result = MagicMock(
        success=True, command="uname", exit_code=0, stdout="Linux\n", stderr=""
    )
    with patch.object(tools._pct, "execute", return_value=mock_result):
        content = tools.execute_lxc_command("pve", "100", "uname")
    text = content[0].text
    assert "stdout" in text or "Linux" in text
    # formatted response should include aliases
    assert "output" in text.lower() or "Linux" in text


def test_require_pct_message():
    tools = ContainerTools(MagicMock(), ssh_config=None, proxmox_host="h")
    with pytest.raises(ValueError, match="reload MCP"):
        tools._require_pct()


def test_push_to_lxc_base64():
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
    payload = b"hello"
    with patch.object(tools._pct, "push_to_guest") as push:
        out = tools.push_to_lxc(
            "pve",
            "122",
            "/tmp/app.tar",
            content_base64=base64.b64encode(payload).decode(),
        )
    push.assert_called_once()
    assert push.call_args[0][2] == payload
    assert "Pushed" in out[0].text


def test_prepare_patched_host_strips_workaround():
    proxmox = MagicMock()
    proxmox.nodes.return_value.lxc.return_value.config.get.return_value = {
        "features": "nesting=1,keyctl=1"
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
        tools._pct, "probe_lxc_pve_version", return_value=("6.0.5-2", (6, 0, 5, 2), True)
    ):
        with patch.object(
            tools._pct, "strip_docker_apparmor_workaround", return_value=["removed x"]
        ) as strip:
            text = tools.prepare_lxc_for_docker("pve", "122")[0].text
    strip.assert_called_once()
    assert "host_patch_status: ok" in text
    assert "restart_required: True" in text


def test_prepare_unpatched_applies_workaround():
    proxmox = MagicMock()
    proxmox.nodes.return_value.lxc.return_value.config.get.return_value = {
        "features": "nesting=1"
    }
    proxmox.nodes.return_value.lxc.return_value.config.put.return_value = "ok"
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
        tools._pct, "probe_lxc_pve_version", return_value=("6.0.4-1", (6, 0, 4, 1), False)
    ):
        with patch.object(
            tools._pct,
            "apply_docker_apparmor_workaround",
            return_value=["added unconfined", "added bind"],
        ):
            text = tools.prepare_lxc_for_docker("pve", "122")[0].text
    assert "unpatched" in text
    assert "restart_required: True" in text
    assert "stop_lxc" in text


def test_run_host_and_execute_timeout_env(monkeypatch):
    monkeypatch.setenv("PROXMOX_MCP_EXEC_TIMEOUT", "99")
    ssh = MagicMock(
        enabled=True,
        timeout=30,
        user="root",
        private_key_path=None,
        host_overrides={},
        pct_path="/usr/sbin/pct",
    )
    pct = PctExecutor(ssh, "10.0.0.1")
    assert pct.timeout == 99

    fake_client = MagicMock()
    stdout = MagicMock()
    stdout.channel.recv_exit_status.return_value = 0
    stdout.read.return_value = b"ok"
    stderr = MagicMock()
    stderr.read.return_value = b""
    fake_client.exec_command.return_value = (MagicMock(), stdout, stderr)

    with patch.object(pct, "_connect", return_value=(fake_client, "10.0.0.1", 99)):
        r = pct.run_host("pve", "echo hi")
        assert r.success and r.stdout == "ok"
        r2 = pct.execute("pve", "100", "true")
        assert r2.command == "true"


def test_probe_lxc_pve_version():
    ssh = MagicMock(
        enabled=True,
        timeout=30,
        user="root",
        private_key_path="/k",
        host_overrides={},
        pct_path="/usr/sbin/pct",
    )
    pct = PctExecutor(ssh, "h")
    with patch.object(
        pct,
        "run_host",
        return_value=MagicMock(success=True, stdout="6.0.5-2\n", stderr="", exit_code=0),
    ):
        raw, _parsed, patched = pct.probe_lxc_pve_version("pve")
    assert raw == "6.0.5-2"
    assert patched is True


def test_push_pull_guest_helpers():
    ssh = MagicMock(
        enabled=True,
        timeout=30,
        user="root",
        private_key_path="/k",
        host_overrides={},
        pct_path="/usr/sbin/pct",
    )
    pct = PctExecutor(ssh, "h")
    with patch.object(pct, "_sftp_put_bytes") as put:
        with patch.object(
            pct,
            "run_host",
            return_value=MagicMock(success=True, stdout="", stderr="", exit_code=0),
        ):
            pct.push_to_guest("pve", "1", b"abc", "/tmp/x")
    put.assert_called_once()
    with patch.object(
        pct,
        "run_host",
        return_value=MagicMock(success=True, stdout="", stderr="", exit_code=0),
    ):
        with patch.object(pct, "_sftp_get_bytes", return_value=b"xyz"):
            data = pct.pull_from_guest("pve", "1", "/tmp/x")
    assert data == b"xyz"


def test_capabilities_probe_ok():
    ssh = MagicMock(enabled=True, private_key_path="/k")
    tools = CapabilitiesTools(MagicMock(), ssh_config=ssh, proxmox_host="h")
    with patch.object(
        tools._pct,
        "probe_pct_version",
        return_value=MagicMock(success=True, stdout="pct 8.0\n", stderr="", exit_code=0),
    ):
        text = tools.get_mcp_capabilities(probe_node="pve")[0].text
    assert "pct probe (pve): OK" in text


def test_pull_from_lxc_base64():
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
    with patch.object(tools._pct, "pull_from_guest", return_value=b"data"):
        out = tools.pull_from_lxc("pve", "122", "/tmp/f")
    assert "content_base64" in out[0].text or "ZGF0YQ==" in out[0].text


def test_server_warn_ssh_off(tmp_path, monkeypatch):
    cfg = tmp_path / "c.json"
    cfg.write_text(
        '{"proxmox":{"host":"h","port":8006,"verify_ssl":false,"service":"PVE"},'
        '"auth":{"user":"u@pve","token_name":"t","token_value":"v"},'
        '"logging":{"level":"INFO"}}',
        encoding="utf-8",
    )
    with patch("proxmox_mcp.server.ProxmoxManager") as mgr:
        mgr.return_value.get_api.return_value = MagicMock()
        from proxmox_mcp.server import ProxmoxMCPServer

        server = ProxmoxMCPServer(str(cfg))
        assert server.capabilities_tools is not None


def test_read_write_conf_and_features():
    ssh = MagicMock(
        enabled=True,
        timeout=30,
        user="root",
        private_key_path="/k",
        host_overrides={"pve": "1.2.3.4"},
        pct_path="/usr/sbin/pct",
    )
    pct = PctExecutor(ssh, "default")
    assert pct.resolve_host("pve") == "1.2.3.4"
    assert pct.resolve_host("other") == "default"
    with patch.object(
        pct,
        "run_host",
        return_value=MagicMock(
            success=True, stdout="hostname: x\n", stderr="", exit_code=0, command="cat"
        ),
    ):
        assert "hostname" in pct.read_lxc_conf("pve", "10")
    with patch.object(pct, "_sftp_put_bytes"):
        with patch.object(
            pct,
            "run_host",
            return_value=MagicMock(success=True, stdout="", stderr="", exit_code=0),
        ):
            pct.write_lxc_conf("pve", "10", "hostname: y\n")
    with patch.object(
        pct,
        "run_host",
        return_value=MagicMock(success=True, stdout="", stderr="", exit_code=0),
    ) as rh:
        pct.ensure_features("pve", "10", "nesting=1,keyctl=1")
        assert "features" in rh.call_args[0][1]
    with patch.object(
        pct,
        "run_host",
        return_value=MagicMock(success=True, stdout="v\n", stderr="", exit_code=0),
    ):
        assert pct.probe_pct_version("pve").success


def test_apply_apparmor_already_present():
    pct = PctExecutor(MagicMock(enabled=True, timeout=30, user="root"), "host")
    conf = f"arch: amd64\n{APPARMOR_UNCONFINED}\n{APPARMOR_NULL_BIND}\n"
    with patch.object(pct, "read_lxc_conf", return_value=conf):
        with patch.object(pct, "write_lxc_conf") as write:
            applied = pct.apply_docker_apparmor_workaround("pve", "122")
    assert applied == []
    write.assert_not_called()


def test_feature_acl_denied_message():
    from proxmox_mcp.tools.helpers import (
        crun_daemon_json,
        feature_acl_denied_message,
        normalize_docker_mode,
        parse_feature_flags,
    )

    assert parse_feature_flags("nesting=1,keyctl=1") == {"nesting", "keyctl"}
    msg = feature_acl_denied_message("107", "nesting=1,keyctl=1", cause="403")
    assert "feature_acl_denied" in msg
    assert "recommended_fallback" in msg
    assert '"crun"' in msg
    assert normalize_docker_mode("AUTO") == "auto"
    with pytest.raises(ValueError):
        normalize_docker_mode("privileged")
    body = crun_daemon_json()
    assert '"default-runtime": "crun"' in body


def test_prepare_auto_falls_back_to_crun_on_keyctl_deny():
    proxmox = MagicMock()
    proxmox.nodes.return_value.lxc.return_value.config.get.return_value = {
        "features": "nesting=1"
    }
    proxmox.nodes.return_value.lxc.return_value.config.put.side_effect = [
        PermissionError("403 changing feature flags only allowed for root@pam"),
        "ok",  # nesting-only fallback
    ]
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
        "ensure_features",
        return_value=MagicMock(
            success=False, stdout="", stderr="denied", exit_code=1
        ),
    ):
        with patch.object(
            tools._pct,
            "probe_lxc_pve_version",
            return_value=("6.0.5-2", (6, 0, 5, 2), True),
        ):
            with patch.object(
                tools._pct, "strip_docker_apparmor_workaround", return_value=[]
            ):
                text = tools.prepare_lxc_for_docker(
                    "pve", "107", docker_mode="auto"
                )[0].text
    assert "docker_path: crun" in text
    assert "keyctl_denied_used_crun_fallback" in text


def test_update_lxc_features_structured_acl_error():
    proxmox = MagicMock()
    proxmox.nodes.return_value.lxc.return_value.config.get.return_value = {
        "features": "nesting=1"
    }
    proxmox.nodes.return_value.lxc.return_value.config.put.side_effect = PermissionError(
        "403 only allowed for root@pam"
    )
    tools = ContainerTools(proxmox)
    with pytest.raises(ValueError) as ei:
        tools.update_lxc_features("pve", "107", "nesting=1,keyctl=1")
    assert "feature_acl_denied" in str(ei.value)


def test_pct_set_lxc_rejects_empty_and_runs_allowlisted():
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
    with pytest.raises(ValueError, match="at least one"):
        tools.pct_set_lxc("pve", "107")
    with patch.object(
        tools._pct,
        "pct_set",
        return_value=MagicMock(
            success=True, stdout="", stderr="", exit_code=0, command="pct set"
        ),
    ) as ps:
        text = tools.pct_set_lxc("pve", "107", features="nesting=1")[0].text
    ps.assert_called_once_with("pve", "107", features="nesting=1")
    assert "pct_set_lxc" in text


def test_configure_lxc_dns_rest():
    proxmox = MagicMock()
    proxmox.nodes.return_value.lxc.return_value.config.put.return_value = "ok"
    proxmox.nodes.return_value.lxc.return_value.status.current.get.return_value = {
        "status": "stopped"
    }
    tools = ContainerTools(proxmox)
    text = tools.configure_lxc_dns("pve", "107", nameserver="8.8.8.8 9.9.9.9")[0].text
    assert "REST nameserver" in text


def test_prepare_crun_mode_install_and_smoke():
    proxmox = MagicMock()
    proxmox.nodes.return_value.lxc.return_value.config.get.return_value = {
        "features": "nesting=1"
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

    def _exec(_node, _vmid, command, timeout=None):
        out = "crun\ndocker compose version 2.0"
        if "hello-world" in command:
            return MagicMock(success=True, stdout="Hello", stderr="", exit_code=0)
        if "get.docker.com" in command or "docker --version" in command:
            return MagicMock(success=True, stdout="Docker version 29", stderr="", exit_code=0)
        if "crun" in command or "daemon.json" in command or "DefaultRuntime" in command:
            return MagicMock(success=True, stdout=out, stderr="", exit_code=0)
        return MagicMock(success=True, stdout=out, stderr="", exit_code=0)

    with patch.object(
        tools._pct,
        "probe_lxc_pve_version",
        return_value=("6.0.5-2", (6, 0, 5, 2), True),
    ):
        with patch.object(tools._pct, "strip_docker_apparmor_workaround", return_value=[]):
            with patch.object(tools._pct, "execute", side_effect=_exec):
                text = tools.prepare_lxc_for_docker(
                    "pve",
                    "107",
                    docker_mode="crun",
                    install_docker=True,
                    smoke_test=True,
                )[0].text
    assert "docker_path: crun" in text
    assert "smoke_test" in text.lower() or "hello-world" in text


def test_create_lxc_docker_ready_retries_without_keyctl():
    proxmox = MagicMock()
    proxmox.nodes.return_value.storage.get.return_value = [
        {"storage": "local-lvm", "type": "lvmthin", "content": "rootdir,images"}
    ]
    create = MagicMock(
        side_effect=[
            PermissionError("403 only allowed for root@pam"),
            "UPID:pve:000:create",
        ]
    )
    proxmox.nodes.return_value.lxc.create = create
    tools = ContainerTools(proxmox)
    with patch("proxmox_mcp.tools.container.assert_id_absent"):
        with patch.object(
            tools,
            "_resolve_ostemplate",
            return_value="local:vztmpl/ubuntu-24.04-standard_amd64.tar.zst",
        ):
            with patch.object(tools, "_hostname_collision_warning", return_value=None):
                text = tools.create_lxc(
                    "pve",
                    "107",
                    "feedforge",
                    docker_ready=True,
                    nameserver="8.8.8.8 9.9.9.9",
                )[0].text
    assert "needs_crun" in text
    assert create.call_count == 2
    assert create.call_args_list[1].kwargs["features"] == "nesting=1"
    assert create.call_args_list[1].kwargs["nameserver"] == "8.8.8.8 9.9.9.9"


def test_pct_set_helper_builds_command():
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
        pct.pct_set("pve", "107", nameserver="8.8.8.8", onboot=1)
    cmd = rh.call_args[0][1]
    assert "set" in cmd and "107" in cmd and "nameserver" in cmd


def test_configure_lxc_dns_pct_fallback_and_gai():
    proxmox = MagicMock()
    proxmox.nodes.return_value.lxc.return_value.config.put.side_effect = PermissionError(
        "403"
    )
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
        "pct_set",
        return_value=MagicMock(success=True, stdout="", stderr="", exit_code=0),
    ):
        with patch.object(
            tools._pct,
            "execute",
            return_value=MagicMock(
                success=True, stdout="gai applied", stderr="", exit_code=0
            ),
        ):
            text = tools.configure_lxc_dns(
                "pve", "107", nameserver="1.1.1.1", searchdomain="lab", prefer_ipv4=True
            )[0].text
    assert "pct set nameserver" in text
    assert "gai.conf" in text


def test_prepare_keyctl_mode_raises_on_deny():
    proxmox = MagicMock()
    proxmox.nodes.return_value.lxc.return_value.config.get.return_value = {
        "features": "nesting=1"
    }
    proxmox.nodes.return_value.lxc.return_value.config.put.side_effect = PermissionError(
        "403 root@pam"
    )
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
        "ensure_features",
        return_value=MagicMock(success=False, stdout="", stderr="no", exit_code=1),
    ):
        with pytest.raises(ValueError, match="feature_acl_denied"):
            tools.prepare_lxc_for_docker("pve", "107", docker_mode="keyctl")


def test_pct_set_lxc_all_keys():
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
        tools._pct,
        "pct_set",
        return_value=MagicMock(
            success=True, stdout="ok", stderr="", exit_code=0, command="pct set"
        ),
    ) as ps:
        tools.pct_set_lxc(
            "pve",
            "107",
            features="nesting=1",
            nameserver="8.8.8.8",
            searchdomain="lan",
            onboot=1,
            description="docker",
            tags="docker;lab",
        )
    assert ps.call_args.kwargs["onboot"] == 1
    assert ps.call_args.kwargs["tags"] == "docker;lab"
