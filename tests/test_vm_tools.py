"""VMTools critical-path and method coverage."""
from __future__ import annotations

import inspect

import pytest

from proxmox_mcp.tools.vm import VMTools
from tests.fakes.proxmox import make_fake_proxmox


@pytest.fixture
def vm_tools():
    return VMTools(make_fake_proxmox())


@pytest.fixture
def vm_tools_running():
    return VMTools(make_fake_proxmox(qemu={"100": {"name": "vm100", "status": "running"}}))


@pytest.fixture
def vm_tools_stopped():
    return VMTools(make_fake_proxmox(qemu={"100": {"name": "vm100", "status": "stopped"}}))


def test_get_vms(vm_tools_stopped):
    out = vm_tools_stopped.get_vms()
    assert out and out[0].text


def test_create_vm_success(vm_tools):
    out = vm_tools.create_vm("pve", "200", "new", 1, 1024, 8)
    assert "created" in out[0].text.lower() or "successfully" in out[0].text.lower()


def test_create_vm_duplicate(vm_tools_stopped):
    with pytest.raises(ValueError, match="already exists"):
        vm_tools_stopped.create_vm("pve", "100", "dup", 1, 1024, 8)


def test_delete_vm_stopped(vm_tools_stopped):
    out = vm_tools_stopped.delete_vm("pve", "100")
    assert "delete" in out[0].text.lower()


def test_delete_vm_running_requires_force(vm_tools_running):
    with pytest.raises(ValueError, match="running"):
        vm_tools_running.delete_vm("pve", "100", force=False)


def test_delete_vm_force(vm_tools_running):
    out = vm_tools_running.delete_vm("pve", "100", force=True)
    assert out


@pytest.mark.asyncio
async def test_execute_vm_command(vm_tools_running):
    out = await vm_tools_running.execute_command("pve", "100", "echo hi")
    assert out[0].text


@pytest.mark.asyncio
async def test_execute_vm_not_running(vm_tools_stopped):
    with pytest.raises(Exception):
        await vm_tools_stopped.execute_command("pve", "100", "echo hi")


def test_power_and_config_methods(vm_tools_stopped, vm_tools_running):
    vm_tools_stopped.start_vm("pve", "100")
    vm_tools_running.stop_vm("pve", "100")
    vm_tools_running.shutdown_vm("pve", "100")
    vm_tools_running.reset_vm("pve", "100")
    vm_tools_running.reboot_vm("pve", "100")
    vm_tools_running.suspend_vm("pve", "100")
    vm_tools_running.resume_vm("pve", "100")
    vm_tools_stopped.get_vm_config("pve", "100")
    vm_tools_stopped.update_vm_config("pve", "100", cores=2)
    vm_tools_stopped.clone_vm("pve", "100", "201")
    vm_tools_stopped.resize_vm_disk("pve", "100", "scsi0", "+1G")
    vm_tools_stopped.convert_vm_to_template("pve", "100")
    vm_tools_stopped.get_vm_status("pve", "100")
    vm_tools_stopped.get_vm_rrd_data("pve", "100")
    vm_tools_stopped.create_vnc_ticket("pve", "100")
    vm_tools_stopped.create_spice_ticket("pve", "100")
    vm_tools_stopped.create_termproxy_ticket("pve", "100")


def test_all_public_methods_exist():
    methods = [
        n
        for n, m in inspect.getmembers(VMTools, predicate=inspect.isfunction)
        if not n.startswith("_")
    ]
    assert "create_vm" in methods
    assert "delete_vm" in methods
