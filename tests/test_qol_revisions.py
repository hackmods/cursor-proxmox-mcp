"""QOL revision (v1.1.3 / r5) coverage: honesty, UPID footers, hints, destructive echo."""
from __future__ import annotations

from unittest.mock import MagicMock, Mock

import pytest

from proxmox_mcp.formatting.templates import ProxmoxTemplates
from proxmox_mcp.tools.access import AccessTools
from proxmox_mcp.tools.backup import BackupTools
from proxmox_mcp.tools.cluster import ClusterTools
from proxmox_mcp.tools.console.manager import VMConsoleManager
from proxmox_mcp.tools.container import ContainerTools
from proxmox_mcp.tools.helpers import (
    destructive_warning,
    lxc_not_found_message,
    privsep_empty_hint,
    upid_response_footer,
    validate_download_url,
)
from proxmox_mcp.tools.migrate import MigrateTools
from proxmox_mcp.tools.storage import StorageTools
from proxmox_mcp.tools.vm import VMTools
from tests.fakes.proxmox import make_fake_proxmox


@pytest.mark.asyncio
async def test_exec_exit_code_truthfulness():
    mock = Mock()
    mock.nodes.return_value.qemu.return_value.status.current.get.return_value = {
        "status": "running"
    }
    mock.nodes.return_value.qemu.return_value.agent.return_value.post.return_value = {
        "pid": 7
    }
    mock.nodes.return_value.qemu.return_value.agent.return_value.get.return_value = {
        "exited": 1,
        "exitcode": 2,
        "out-data": "",
        "err-data": "boom",
    }
    mgr = VMConsoleManager(mock)
    result = await mgr.execute_command("pve", "100", "false")
    assert result["success"] is False
    assert result["exit_code"] == 2


def test_force_delete_stop_then_wait():
    api = make_fake_proxmox(qemu={"100": {"name": "vm", "status": "running"}})
    tools = VMTools(api)
    out = tools.delete_vm("pve", "100", force=True)
    text = out[0].text
    assert "stop UPID" in text
    assert "wait_for_task" in text
    assert "IRREVERSIBLE" in text
    assert "deletion initiated" in text.lower()


def test_upid_footer_on_clone_and_migrate():
    api = make_fake_proxmox(qemu={"100": {"name": "vm", "status": "stopped"}})
    clone = VMTools(api).clone_vm("pve", "100", "201")
    assert "wait_for_task" in clone[0].text
    mig = MigrateTools(api).migrate_guest("pve", "100", "pve2", guest_type="qemu")
    assert "wait_for_task" in mig[0].text
    footer = upid_response_footer("UPID:x", node="pve")
    assert "Task ID: UPID:x" in footer
    assert "wait_for_task" in footer


def test_lxc_not_found_inverse_hint():
    api = make_fake_proxmox()
    tools = ContainerTools(api)
    with pytest.raises(ValueError, match="get_vms") as exc:
        tools.get_lxc_config("pve", "999")
    assert "LXC" in str(exc.value)
    assert "get_vms" in lxc_not_found_message("999", "pve")


def test_create_vm_async_copy():
    api = make_fake_proxmox()
    out = VMTools(api).create_vm("pve", "210", "n", 1, 512, 4)
    assert "create task started" in out[0].text.lower()
    assert "wait_for_task" in out[0].text


def test_restore_backup_force_and_normalize():
    api = make_fake_proxmox()
    api.nodes("pve").lxc.create.return_value = "UPID:restore"
    out = BackupTools(api).restore_backup(
        "pve", "local:backup/x.vma", "300", force=True, guest_type="ct"
    )
    text = out[0].text
    assert "force=True" in text or "overwrite" in text.lower()
    assert "wait_for_task" in text
    assert "lxc" in text.lower()


def test_destructive_echo_delete_backup():
    api = make_fake_proxmox()
    out = BackupTools(api).delete_backup("pve", "local", "local:backup/x")
    assert "IRREVERSIBLE" in out[0].text
    assert "IRREVERSIBLE" in destructive_warning("deleted")


def test_empty_list_privsep_hints():
    api = make_fake_proxmox()
    users = AccessTools(api).list_users()
    assert "get_token_permissions" in users[0].text
    assert "get_token_permissions" in privsep_empty_hint("x")

    # Direct empty content path
    tools = StorageTools(MagicMock())
    tools.proxmox.nodes.return_value.storage.return_value.content.get.return_value = []
    content = tools.get_storage_content("pve", "local")
    assert "get_token_permissions" in content[0].text


def test_empty_vm_and_container_templates():
    vm_text = ProxmoxTemplates.vm_list([])
    assert "get_containers" in vm_text
    ct_text = ProxmoxTemplates.container_list([])
    assert "get_vms" in ct_text


def test_download_url_validation_and_footer():
    with pytest.raises(ValueError, match="http"):
        validate_download_url("ftp://x")
    api = make_fake_proxmox()
    out = StorageTools(api).download_url_to_storage(
        "pve", "local", "https://example.com/a.iso", verify_certificate=False
    )
    assert "wait_for_task" in out[0].text
    with pytest.raises(ValueError, match="http"):
        StorageTools(api).download_url_to_storage("pve", "local", "file:///etc/passwd")


def test_next_vmid_race_note():
    api = make_fake_proxmox()
    out = ClusterTools(api).get_next_vmid()
    assert "Best-effort" in out[0].text


def test_console_ticket_viewer_hint():
    api = make_fake_proxmox(qemu={"100": {"name": "vm", "status": "stopped"}})
    out = VMTools(api).create_vnc_ticket("pve", "100")
    assert "Ticket only" in out[0].text or "connect externally" in out[0].text.lower()


def test_wait_for_upid_ok_and_fail():
    from proxmox_mcp.tools.helpers import wait_for_upid

    api = MagicMock()
    api.nodes.return_value.tasks.return_value.status.get.return_value = {
        "status": "stopped",
        "exitstatus": "OK",
    }
    assert wait_for_upid(api, "pve", "UPID:1")["exitstatus"] == "OK"

    api.nodes.return_value.tasks.return_value.status.get.return_value = {
        "status": "stopped",
        "exitstatus": "ERROR",
    }
    with pytest.raises(RuntimeError, match="failed"):
        wait_for_upid(api, "pve", "UPID:2")


def test_ha_and_sdn_privilege_copy():
    from proxmox_mcp.tools.ha import HATools
    from proxmox_mcp.tools.sdn import SDNTools

    api = make_fake_proxmox()
    ha = HATools(api).create_ha_group("g1", "pve")
    assert "elevated privileges" in ha[0].text
    groups = HATools(api).list_ha_groups()
    assert "get_token_permissions" in groups[0].text
    sdn = SDNTools(api).apply_sdn()
    assert "elevated privileges" in sdn[0].text


def test_snapshot_destructive_and_footer():
    from proxmox_mcp.tools.snapshot import SnapshotTools

    api = make_fake_proxmox(qemu={"100": {"name": "vm", "status": "stopped"}})
    created = SnapshotTools(api).create_snapshot("pve", "100", "s1")
    assert "wait_for_task" in created[0].text
    deleted = SnapshotTools(api).delete_snapshot("pve", "100", "s1")
    assert "IRREVERSIBLE" in deleted[0].text
    rolled = SnapshotTools(api).rollback_snapshot("pve", "100", "s1")
    assert "IRREVERSIBLE" in rolled[0].text


def test_guest_power_not_found_hint():
    from proxmox_mcp.tools.guest_power import GuestPowerTools

    api = MagicMock()
    api.nodes.return_value.qemu.return_value.status.current.get.side_effect = Exception(
        "VM 999 not found"
    )
    tools = GuestPowerTools(api)
    with pytest.raises(ValueError, match="guest_type"):
        tools.get_guest_status("pve", "999", "qemu")
    with pytest.raises(ValueError, match="guest_type"):
        tools.start_guest("pve", "999", "qemu")
    with pytest.raises(ValueError, match="guest_type"):
        tools.stop_guest("pve", "999", "qemu")
    with pytest.raises(ValueError, match="guest_type"):
        tools.shutdown_guest("pve", "999", "qemu")
    with pytest.raises(ValueError, match="guest_type"):
        tools.reboot_guest("pve", "999", "qemu")
    with pytest.raises(ValueError, match="guest_type"):
        tools.delete_guest("pve", "999", "qemu")


def test_vm_missing_resource_hints():
    api = make_fake_proxmox()
    tools = VMTools(api)
    with pytest.raises(ValueError, match="get_containers"):
        tools.get_vm_config("pve", "999")
    with pytest.raises(ValueError, match="get_containers"):
        tools.get_vm_status("pve", "999")
    with pytest.raises(ValueError, match="get_containers"):
        tools.clone_vm("pve", "999", "1000")
    with pytest.raises(ValueError, match="get_containers"):
        tools.suspend_vm("pve", "999")
    with pytest.raises(ValueError, match="get_containers"):
        tools.resume_vm("pve", "999")
    with pytest.raises(ValueError, match="get_containers"):
        tools.resize_vm_disk("pve", "999", "scsi0", "+1G")
    with pytest.raises(ValueError, match="get_containers"):
        tools.convert_vm_to_template("pve", "999")
    with pytest.raises(ValueError, match="get_containers"):
        tools.create_vnc_ticket("pve", "999")
    with pytest.raises(ValueError, match="get_containers"):
        tools.create_spice_ticket("pve", "999")
    with pytest.raises(ValueError, match="get_containers"):
        tools.create_termproxy_ticket("pve", "999")
    with pytest.raises(ValueError, match="get_containers"):
        tools.get_vm_rrd_data("pve", "999")


def test_lxc_missing_resource_hints_more():
    api = make_fake_proxmox()
    tools = ContainerTools(api)
    with pytest.raises(ValueError, match="get_vms"):
        tools.clone_lxc("pve", "999", "1000")
    with pytest.raises(ValueError, match="get_vms"):
        tools.resize_lxc_disk("pve", "999", "rootfs", "+1G")
    with pytest.raises(ValueError, match="get_vms"):
        tools.convert_lxc_to_template("pve", "999")
    with pytest.raises(ValueError, match="get_vms"):
        tools.create_vnc_ticket("pve", "999")
    with pytest.raises(ValueError, match="get_vms"):
        tools.create_spice_ticket("pve", "999")
    with pytest.raises(ValueError, match="get_vms"):
        tools.create_termproxy_ticket("pve", "999")
    with pytest.raises(ValueError, match="get_vms"):
        tools.get_lxc_status("pve", "999")
    with pytest.raises(ValueError, match="get_vms"):
        tools.get_lxc_network("pve", "999")
    with pytest.raises(ValueError, match="get_vms"):
        tools.get_lxc_rrd_data("pve", "999")
    with pytest.raises(ValueError, match="get_vms"):
        tools.suspend_lxc("pve", "999")
    with pytest.raises(ValueError, match="get_vms"):
        tools.resume_lxc("pve", "999")


def test_access_destructive_and_acl_delete():
    api = make_fake_proxmox()
    tools = AccessTools(api)
    deleted = tools.delete_user("u@pve")
    assert "IRREVERSIBLE" in deleted[0].text
    acl = tools.update_acl("/", "PVEAuditor", users="u@pve", delete=True)
    assert "IRREVERSIBLE" in acl[0].text
    pool_text = __import__(
        "proxmox_mcp.tools.pool", fromlist=["PoolTools"]
    ).PoolTools(api).delete_pool("lab")
    assert "IRREVERSIBLE" in pool_text[0].text
