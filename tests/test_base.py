"""Base tool error/format tests."""
import pytest

from proxmox_mcp.errors import ProxmoxNotFoundError
from proxmox_mcp.tools.base import ProxmoxTool
from tests.fakes.proxmox import make_fake_proxmox


def test_format_json_fallback():
    tool = ProxmoxTool(make_fake_proxmox())
    out = tool._format_response({"a": 1})
    assert "a" in out[0].text


def test_handle_error_raises_typed():
    tool = ProxmoxTool(make_fake_proxmox())
    with pytest.raises(ProxmoxNotFoundError):
        tool._handle_error("get", Exception("not found"))
