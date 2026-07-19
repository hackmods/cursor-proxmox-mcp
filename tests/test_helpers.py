"""Helpers unit tests."""
import pytest

from proxmox_mcp.tools.helpers import (
    assert_id_absent,
    is_missing_resource_error,
    pick_storage,
)
from tests.fakes.proxmox import make_fake_proxmox


def test_is_missing():
    assert is_missing_resource_error(Exception("does not exist"))
    assert not is_missing_resource_error(Exception("other"))


def test_pick_storage_preferred():
    stores = [
        {"storage": "other", "content": "images", "type": "dir"},
        {"storage": "local-lvm", "content": "images,rootdir", "type": "lvmthin"},
    ]
    assert pick_storage(stores, content="images", preferred=["local-lvm"]) == "local-lvm"


def test_pick_storage_explicit_bad():
    with pytest.raises(ValueError, match="not found"):
        pick_storage([], content="images", explicit="nope")


def test_assert_id_absent_ok():
    api = make_fake_proxmox()
    assert_id_absent(api, "pve", "999", "qemu")


def test_assert_id_absent_exists():
    api = make_fake_proxmox(qemu={"100": {"name": "x", "status": "stopped"}})
    with pytest.raises(ValueError, match="already exists"):
        assert_id_absent(api, "pve", "100", "qemu")
