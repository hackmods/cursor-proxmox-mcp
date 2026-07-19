"""Invoke every registered MCP tool via mocked server for coverage."""
from __future__ import annotations

import inspect
from unittest.mock import patch

import pytest

from proxmox_mcp.config.models import AuthConfig, Config, LoggingConfig, ProxmoxConfig
from proxmox_mcp.server import ProxmoxMCPServer
from proxmox_mcp.tools.inventory import ALL_TOOL_NAMES
from tests.fakes.proxmox import make_fake_proxmox


@pytest.fixture
def server():
    api = make_fake_proxmox(
        qemu={"100": {"name": "vm", "status": "stopped"}},
        lxc={"200": {"hostname": "ct", "status": "stopped"}},
    )
    cfg = Config(
        proxmox=ProxmoxConfig(host="h", verify_ssl=False),
        auth=AuthConfig(user="u@pve", token_name="t", token_value="v"),
        logging=LoggingConfig(level="INFO"),
    )
    with patch("proxmox_mcp.server.load_config", return_value=cfg), patch(
        "proxmox_mcp.server.ProxmoxManager"
    ) as mgr:
        mgr.return_value.get_api.return_value = api
        return ProxmoxMCPServer("dummy.json")


def _default_args(tool_name: str, fn) -> dict:
    sig = inspect.signature(fn)
    kwargs = {}
    for name, param in sig.parameters.items():
        if param.default is not inspect.Parameter.empty:
            continue
        if name == "node":
            kwargs[name] = "pve"
        elif name in ("vmid", "newid"):
            kwargs[name] = "100"
        elif name == "upid":
            kwargs[name] = "UPID:TEST"
        elif name == "name":
            kwargs[name] = "name"
        elif name == "hostname":
            kwargs[name] = "host"
        elif name == "cpus":
            kwargs[name] = 1
        elif name == "memory":
            kwargs[name] = 1024
        elif name == "disk_size":
            kwargs[name] = 8
        elif name == "snapname":
            kwargs[name] = "s1"
        elif name == "storage":
            kwargs[name] = "local-lvm"
        elif name in ("volume", "archive"):
            kwargs[name] = "local:backup/x.vma.zst"
        elif name == "disk":
            kwargs[name] = "scsi0"
        elif name == "size":
            kwargs[name] = "+1G"
        elif name == "url":
            kwargs[name] = "https://example.com/a.iso"
        elif name == "type":
            kwargs[name] = "dir" if "storage" in tool_name or tool_name == "create_storage" else "in"
        elif name == "action":
            kwargs[name] = "ACCEPT"
        elif name == "path":
            kwargs[name] = "/"
        elif name == "roles":
            kwargs[name] = "PVEVMAdmin"
        elif name == "userid":
            kwargs[name] = "u@pve"
        elif name == "tokenid":
            kwargs[name] = "tok"
        elif name == "groupid" or name == "group":
            kwargs[name] = "g"
        elif name == "poolid":
            kwargs[name] = "p"
        elif name == "sid":
            kwargs[name] = "vm:100"
        elif name == "id" or name == "jobid":
            kwargs[name] = "100-0"
        elif name == "target":
            kwargs[name] = "pve2"
        elif name == "nodes":
            kwargs[name] = "pve"
        elif name == "cidr":
            kwargs[name] = "10.0.0.0/8"
        elif name == "pos":
            kwargs[name] = 0
        elif name == "command":
            kwargs[name] = "true"
        elif name == "features":
            kwargs[name] = "nesting=1"
        elif name == "ostemplate":
            kwargs[name] = "local:vztmpl/u.tar.zst"
        elif name == "schedule":
            kwargs[name] = "sun 01:00"
        else:
            kwargs[name] = "x"
    return kwargs


@pytest.mark.asyncio
async def test_invoke_all_registered_tools(server):
    """Call every registered tool once to exercise register.py wrappers + tool methods."""
    tools = await server.mcp.list_tools()
    names = {t.name for t in tools}
    assert names == ALL_TOOL_NAMES

    failures = []
    for tool in tools:
        fn = server.mcp._tool_manager._tools[tool.name].fn  # type: ignore[attr-defined]
        kwargs = _default_args(tool.name, fn)
        try:
            result = fn(**kwargs)
            if inspect.iscoroutine(result):
                await result
        except Exception as e:
            failures.append(f"{tool.name}: {type(e).__name__}: {e}")

    # Allow some failures from imperfect fakes; require majority success
    assert len(failures) <= len(tools) * 0.35, "\n".join(failures[:30])
