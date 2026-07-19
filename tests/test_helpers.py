"""Helpers unit tests."""
import pytest

from proxmox_mcp.tools.helpers import (
    assert_id_absent,
    console_ticket_footer,
    destructive_warning,
    guest_not_found_message,
    is_missing_resource_error,
    lxc_not_found_message,
    pick_storage,
    privilege_required_note,
    privsep_empty_hint,
    qemu_not_found_message,
    upid_response_footer,
    validate_download_url,
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


def test_parse_net_static_summary():
    from proxmox_mcp.tools.helpers import configured_ipv4_summary, parse_lxc_networks

    nets = parse_lxc_networks({"net0": "name=eth0,bridge=vmbr0,ip=1.2.3.4/24"})
    assert configured_ipv4_summary(nets) == "1.2.3.4/24"


def test_qemu_and_lxc_not_found_hints():
    q = qemu_not_found_message("100", "pve")
    assert "get_containers" in q
    lxc_msg = lxc_not_found_message("101", "pve")
    assert "get_vms" in lxc_msg
    g = guest_not_found_message("102", "pve", "qemu")
    assert "guest_type" in g


def test_upid_response_footer():
    text = upid_response_footer("UPID:pve:1", node="pve")
    assert "Task ID: UPID:pve:1" in text
    assert "wait_for_task" in text
    assert "Node: pve" in text


def test_destructive_and_privsep_helpers():
    assert "IRREVERSIBLE" in destructive_warning("deleted")
    assert "get_token_permissions" in privsep_empty_hint("users")
    assert "Ticket only" in console_ticket_footer("SPICE")
    assert "elevated privileges" in privilege_required_note("HA")


def test_validate_download_url():
    assert validate_download_url("https://example.com/a.iso") == "https://example.com/a.iso"
    with pytest.raises(ValueError, match="http"):
        validate_download_url("file:///etc/passwd")
    with pytest.raises(ValueError, match="required"):
        validate_download_url("")
