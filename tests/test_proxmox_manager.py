"""ProxmoxManager unit tests."""
from unittest.mock import MagicMock, patch

import pytest

from proxmox_mcp.config.models import AuthConfig, ProxmoxConfig
from proxmox_mcp.core.proxmox import ProxmoxManager


def test_connect_ok():
    with patch("proxmox_mcp.core.proxmox.ProxmoxAPI") as mock_api:
        inst = MagicMock()
        mock_api.return_value = inst
        inst.version.get.return_value = {"version": "8"}
        mgr = ProxmoxManager(
            ProxmoxConfig(host="h", verify_ssl=True),
            AuthConfig(user="u@pve", token_name="t", token_value="v"),
        )
        assert mgr.get_api() is inst


def test_connect_fail():
    with patch("proxmox_mcp.core.proxmox.ProxmoxAPI") as mock_api:
        mock_api.side_effect = Exception("down")
        with pytest.raises(RuntimeError, match="Failed to connect"):
            ProxmoxManager(
                ProxmoxConfig(host="h"),
                AuthConfig(user="u@pve", token_name="t", token_value="v"),
            )


def test_ssl_off_warns(caplog):
    import logging

    with patch("proxmox_mcp.core.proxmox.ProxmoxAPI") as mock_api:
        inst = MagicMock()
        mock_api.return_value = inst
        inst.version.get.return_value = {}
        with caplog.at_level(logging.WARNING):
            ProxmoxManager(
                ProxmoxConfig(host="h", verify_ssl=False),
                AuthConfig(user="u@pve", token_name="t", token_value="v"),
            )
        assert "DISABLED" in caplog.text or "verification" in caplog.text.lower()
