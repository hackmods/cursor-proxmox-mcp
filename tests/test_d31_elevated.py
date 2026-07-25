"""D31 dual auth + provision_vm + capability tiers."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from proxmox_mcp.config.loader import load_config
from proxmox_mcp.config.models import AuthConfig, ProxmoxConfig
from proxmox_mcp.core.proxmox import ProxmoxManager
from proxmox_mcp.tools.base import ProxmoxTool
from proxmox_mcp.tools.capabilities import CapabilitiesTools, DAY2_TOOLS
from proxmox_mcp.tools.inventory import (
    ALL_TOOL_NAMES,
    DESTRUCTIVE_TOOLS,
    SAFE_DAY2_TOOLS,
    TYPED_CONFIRM_TOOLS,
)
from proxmox_mcp.tools.vm import VMTools


def test_provision_vm_in_inventory():
    assert "provision_vm" in ALL_TOOL_NAMES
    assert "provision_vm" in DAY2_TOOLS
    assert "provision_vm" in SAFE_DAY2_TOOLS
    assert len(ALL_TOOL_NAMES) == 212


def test_typed_confirm_subset_of_destructive():
    assert TYPED_CONFIRM_TOOLS <= DESTRUCTIVE_TOOLS


def test_load_config_with_auth_write(tmp_path, monkeypatch):
    monkeypatch.setenv("TOK", "secret-read")
    monkeypatch.setenv("TOKW", "secret-write")
    cfg = {
        "proxmox": {"host": "10.0.0.1", "port": 8006, "verify_ssl": True, "service": "PVE"},
        "auth": {"user": "mcp@pve", "token_name": "audit", "token_value": "${TOK}"},
        "auth_write": {
            "user": "mcp@pve",
            "token_name": "write",
            "token_value": "${TOKW}",
        },
        "logging": {"level": "INFO"},
    }
    path = tmp_path / "c.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    loaded = load_config(str(path))
    assert loaded.auth.token_name == "audit"
    assert loaded.auth_write is not None
    assert loaded.auth_write.token_value == "secret-write"


def test_proxmox_manager_dual_auth_routing():
    read_api = MagicMock(name="read_api")
    write_api = MagicMock(name="write_api")
    read_api.version.get.return_value = {"version": "8"}
    write_api.version.get.return_value = {"version": "8"}

    with patch("proxmox_mcp.core.proxmox.ProxmoxAPI") as api_cls:
        api_cls.side_effect = [read_api, write_api]
        mgr = ProxmoxManager(
            ProxmoxConfig(host="10.0.0.1"),
            AuthConfig(user="mcp@pve", token_name="audit", token_value="r"),
            auth_write=AuthConfig(user="mcp@pve", token_name="write", token_value="w"),
        )
    assert mgr.dual_auth is True
    assert mgr.get_api() is read_api
    assert mgr.get_write_api() is write_api
    summary = mgr.auth_summary()
    assert summary["dual_auth"] is True
    assert summary["mutating_api"] == "write"
    assert "mcp@pve!audit" in summary["auth_identity"]
    assert "mcp@pve!write" in summary["auth_write_identity"]


def test_proxmox_manager_single_auth():
    api = MagicMock()
    api.version.get.return_value = {"version": "8"}
    with patch("proxmox_mcp.core.proxmox.ProxmoxAPI", return_value=api):
        mgr = ProxmoxManager(
            ProxmoxConfig(host="10.0.0.1"),
            AuthConfig(user="mcp@pve", token_name="cursor", token_value="x"),
        )
    assert mgr.dual_auth is False
    assert mgr.get_api() is mgr.get_write_api()
    assert mgr.auth_summary()["mutating_api"] == "primary"


def test_api_for_mutating():
    read_api = MagicMock(name="read")
    write_api = MagicMock(name="write")
    tool = ProxmoxTool(read_api, proxmox_write_api=write_api, proxmox_read_api=read_api)
    assert tool.api_for(mutating=False) is read_api
    assert tool.api_for(mutating=True) is write_api


def test_capabilities_reports_dual_auth():
    api = MagicMock()
    caps = CapabilitiesTools(
        api,
        auth_summary={
            "dual_auth": True,
            "auth_identity": "mcp@pve!audit",
            "auth_write_identity": "mcp@pve!write",
            "mutating_api": "write",
        },
    )
    text = caps.get_mcp_capabilities()[0].text
    assert "dual_auth: True" in text
    assert "mcp@pve!write" in text
    assert "typed_confirm_tools:" in text
    assert "safe_day2_tools_count:" in text


def test_provision_vm_create_path_mocked():
    proxmox = MagicMock()
    proxmox.cluster.nextid.get.return_value = 200
    proxmox.nodes.return_value.qemu.return_value.status.current.get.return_value = {
        "status": "stopped"
    }
    proxmox.nodes.return_value.qemu.return_value.status.start.post.return_value = "UPID:start"
    tools = VMTools(proxmox)

    with patch.object(tools, "create_vm", return_value=[MagicMock(text="created")]) as create:
        with patch.object(
            tools,
            "get_vm_network",
            return_value=[MagicMock(text=json.dumps({"runtime_ips": ["10.0.0.5/24"]}))],
        ):
            with patch("proxmox_mcp.tools.vm.wait_for_upid"):
                text = tools.provision_vm(
                    "pve",
                    "lab-vm",
                    sshkeys="ssh-ed25519 AAAA",
                    timeout=5,
                )[0].text

    assert "provision_vm complete" in text
    create.assert_called_once()
    assert create.call_args.kwargs.get("wait") is True
    body = json.loads(text.split("\n", 1)[1])
    assert body["vmid"] == "200"
    assert body["ip"] == "10.0.0.5"
    assert body["mode"] == "create"


def test_provision_vm_clone_delegates():
    tools = VMTools(MagicMock())
    with patch.object(
        tools,
        "bootstrap_cloudinit_vm",
        return_value=[MagicMock(text="bootstrap_cloudinit_vm complete\n{}")],
    ) as boot:
        text = tools.provision_vm("pve", "lab", clone_from="9000")[0].text
    boot.assert_called_once()
    assert "provision_vm complete" in text
