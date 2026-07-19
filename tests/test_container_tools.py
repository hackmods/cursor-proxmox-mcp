"""ContainerTools critical-path tests."""
from __future__ import annotations

import pytest

from proxmox_mcp.tools.container import ContainerTools
from tests.fakes.proxmox import make_fake_proxmox


@pytest.fixture
def ct_tools():
    return ContainerTools(make_fake_proxmox())


@pytest.fixture
def ct_stopped():
    return ContainerTools(
        make_fake_proxmox(lxc={"200": {"hostname": "ct200", "status": "stopped"}})
    )


@pytest.fixture
def ct_running():
    return ContainerTools(
        make_fake_proxmox(lxc={"200": {"hostname": "ct200", "status": "running"}})
    )


def test_get_containers(ct_stopped):
    assert ct_stopped.get_containers()


def test_create_lxc(ct_tools):
    out = ct_tools.create_lxc(
        "pve", "300", "newct", ostemplate="local:vztmpl/ubuntu.tar.zst", cpus=1, memory=512, disk_size=4
    )
    assert "created" in out[0].text.lower() or "successfully" in out[0].text.lower()


def test_create_lxc_duplicate(ct_stopped):
    with pytest.raises(ValueError, match="already exists"):
        ct_stopped.create_lxc(
            "pve", "200", "x", ostemplate="local:vztmpl/u.tar.zst", cpus=1, memory=512, disk_size=4
        )


def test_delete_lxc(ct_stopped):
    assert ct_stopped.delete_lxc("pve", "200")


def test_delete_running_requires_force(ct_running):
    with pytest.raises(ValueError):
        ct_running.delete_lxc("pve", "200", force=False)


def test_lifecycle(ct_stopped, ct_running):
    ct_stopped.start_lxc("pve", "200")
    ct_running.stop_lxc("pve", "200")
    ct_running.shutdown_lxc("pve", "200")
    ct_running.reboot_lxc("pve", "200")
    ct_stopped.get_lxc_config("pve", "200")
    ct_stopped.update_lxc_config("pve", "200", cores=2)
    ct_stopped.update_lxc_features("pve", "200", "nesting=1,keyctl=1")
    ct_stopped.clone_lxc("pve", "200", "301")
    ct_stopped.resize_lxc_disk("pve", "200", "rootfs", "+1G")
    ct_stopped.convert_lxc_to_template("pve", "200")
    ct_stopped.get_lxc_status("pve", "200")
    ct_stopped.create_vnc_ticket("pve", "200")
    ct_stopped.create_termproxy_ticket("pve", "200")
