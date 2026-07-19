"""Unit tests for GuestPowerTools and Phase E LXC/ops helpers."""
from __future__ import annotations

from tests.fakes.proxmox import make_fake_proxmox
from proxmox_mcp.tools.guest_power import GuestPowerTools
from proxmox_mcp.tools.container import ContainerTools
from proxmox_mcp.tools.pool import PoolTools
from proxmox_mcp.tools.replication import ReplicationTools
from proxmox_mcp.tools.backup import BackupTools
from proxmox_mcp.tools.firewall import FirewallTools


def test_start_guest_already_running():
    api = make_fake_proxmox(qemu={"100": {"name": "vm", "status": "running"}})
    tools = GuestPowerTools(api)
    text = tools.start_guest("pve", "100", "qemu")[0].text
    assert "already running" in text


def test_start_guest_lxc():
    api = make_fake_proxmox(lxc={"200": {"hostname": "ct", "status": "stopped"}})
    tools = GuestPowerTools(api)
    text = tools.start_guest("pve", "200", "lxc")[0].text
    assert "start initiated" in text


def test_stop_shutdown_reboot_guest():
    api = make_fake_proxmox(qemu={"100": {"name": "vm", "status": "running"}})
    tools = GuestPowerTools(api)
    assert "stop initiated" in tools.stop_guest("pve", "100")[0].text
    assert "shutdown initiated" in tools.shutdown_guest("pve", "100")[0].text
    assert "reboot initiated" in tools.reboot_guest("pve", "100")[0].text


def test_stop_shutdown_already_stopped():
    api = make_fake_proxmox(qemu={"100": {"name": "vm", "status": "stopped"}})
    tools = GuestPowerTools(api)
    assert "already stopped" in tools.stop_guest("pve", "100")[0].text
    assert "already stopped" in tools.shutdown_guest("pve", "100")[0].text


def test_delete_guest_when_stopped():
    api = make_fake_proxmox(lxc={"200": {"hostname": "ct", "status": "stopped"}})
    tools = GuestPowerTools(api)
    text = tools.delete_guest("pve", "200", "lxc")[0].text
    assert "deletion initiated" in text


def test_reboot_guest_when_stopped():
    api = make_fake_proxmox(qemu={"100": {"name": "vm", "status": "stopped"}})
    tools = GuestPowerTools(api)
    assert "Cannot reboot" in tools.reboot_guest("pve", "100")[0].text


def test_delete_guest_requires_force_when_running():
    api = make_fake_proxmox(qemu={"100": {"name": "vm", "status": "running"}})
    tools = GuestPowerTools(api)
    try:
        tools.delete_guest("pve", "100", "qemu", force=False)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "force=True" in str(e)


def test_delete_guest_force():
    api = make_fake_proxmox(qemu={"100": {"name": "vm", "status": "running"}})
    tools = GuestPowerTools(api)
    text = tools.delete_guest("pve", "100", "qemu", force=True)[0].text
    assert "deletion initiated" in text


def test_get_guest_status_and_pending():
    api = make_fake_proxmox(qemu={"100": {"name": "vm", "status": "stopped"}})
    tools = GuestPowerTools(api)
    assert tools.get_guest_status("pve", "100")[0].text
    assert tools.get_guest_pending("pve", "100")[0].text is not None


def test_move_guest_disk_qemu_and_lxc():
    api = make_fake_proxmox(
        qemu={"100": {"name": "vm", "status": "stopped"}},
        lxc={"200": {"hostname": "ct", "status": "stopped"}},
    )
    tools = GuestPowerTools(api)
    assert "Move" in tools.move_guest_disk("pve", "100", "scsi0", "local-lvm")[0].text
    assert "Move" in tools.move_guest_disk(
        "pve", "200", "rootfs", "local-lvm", guest_type="lxc"
    )[0].text


def test_lxc_suspend_resume_rrd_spice():
    api = make_fake_proxmox(lxc={"200": {"hostname": "ct", "status": "running"}})
    tools = ContainerTools(api)
    assert "CRIU" in tools.suspend_lxc("pve", "200")[0].text
    assert "CRIU" in tools.resume_lxc("pve", "200")[0].text
    assert tools.get_lxc_rrd_data("pve", "200")[0].text is not None
    assert tools.create_spice_ticket("pve", "200")[0].text is not None


def test_update_pool_and_replication_and_backup_jobs():
    api = make_fake_proxmox()
    pool = PoolTools(api)
    assert "updated" in pool.update_pool("p", vms="100")[0].text
    repl = ReplicationTools(api)
    assert "updated" in repl.update_replication_job("100-0", enabled=False)[0].text
    bak = BackupTools(api)
    assert bak.list_backup_jobs()[0].text is not None
    assert "created" in bak.create_backup_job("sun 01:00", "local")[0].text
    assert "deleted" in bak.delete_backup_job("backup-1")[0].text


def test_firewall_ipset_cidrs():
    api = make_fake_proxmox()
    fw = FirewallTools(api)
    assert fw.list_firewall_ipset_cidrs("set1")[0].text is not None
    assert "Added" in fw.add_firewall_ipset_cidr("set1", "10.0.0.0/8")[0].text
    assert "Removed" in fw.delete_firewall_ipset_cidr("set1", "10.0.0.0/8")[0].text
