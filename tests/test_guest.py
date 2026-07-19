"""Guest helper tests."""
import pytest

from proxmox_mcp.tools.guest import guest_resource, normalize_guest_type
from tests.fakes.proxmox import make_fake_proxmox


def test_normalize():
    assert normalize_guest_type("VM") == "qemu"
    assert normalize_guest_type("ct") == "lxc"
    with pytest.raises(ValueError):
        normalize_guest_type("foo")


def test_guest_resource():
    api = make_fake_proxmox()
    guest_resource(api, "pve", "100", "qemu")
    guest_resource(api, "pve", "200", "lxc")
