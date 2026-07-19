"""Slice 1: structured ACL denial helpers."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from proxmox_mcp.tools.helpers import acl_denied_message, feature_acl_denied_message
from proxmox_mcp.tools.ha import HATools
from proxmox_mcp.tools.firewall import FirewallTools
from proxmox_mcp.tools.access import AccessTools
from proxmox_mcp.tools.sdn import SDNTools


def test_acl_denied_message_shape():
    msg = acl_denied_message(
        "ha_acl_denied",
        operation="create HA group",
        path="/cluster/ha/groups",
        cause="403 permission denied",
    )
    assert "ha_acl_denied" in msg
    assert "get_token_permissions" in msg
    assert '"path": "/cluster/ha/groups"' in msg


def test_feature_acl_wraps_general():
    msg = feature_acl_denied_message("107", "nesting=1,keyctl=1", cause="403")
    assert "feature_acl_denied" in msg
    assert "recommended_fallback" in msg
    assert "crun" in msg


def test_ha_create_group_acl_denied():
    proxmox = MagicMock()
    proxmox.cluster.ha.groups.post.side_effect = PermissionError("403")
    with pytest.raises(ValueError, match="ha_acl_denied"):
        HATools(proxmox).create_ha_group("g1", "pve")


def test_firewall_set_options_acl_denied():
    proxmox = MagicMock()
    proxmox.cluster.firewall.options.put.side_effect = PermissionError("403")
    with pytest.raises(ValueError, match="firewall_acl_denied"):
        FirewallTools(proxmox).set_cluster_firewall_options(enable=True)


def test_access_update_acl_denied():
    proxmox = MagicMock()
    proxmox.access.acl.put.side_effect = PermissionError("403")
    with pytest.raises(ValueError, match="access_acl_denied"):
        AccessTools(proxmox).update_acl("/vms/100", "PVEVMUser", users="u@pve")


def test_sdn_apply_acl_denied():
    proxmox = MagicMock()
    proxmox.cluster.sdn.put.side_effect = PermissionError("403")
    with pytest.raises(ValueError, match="sdn_acl_denied"):
        SDNTools(proxmox).apply_sdn()
