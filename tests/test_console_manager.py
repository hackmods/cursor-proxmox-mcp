"""Console manager polling / allowlist tests."""
import pytest

from proxmox_mcp.tools.console.manager import VMConsoleManager
from tests.fakes.proxmox import make_fake_proxmox


@pytest.mark.asyncio
async def test_execute_success():
    api = make_fake_proxmox(qemu={"100": {"name": "v", "status": "running"}})
    mgr = VMConsoleManager(api)
    result = await mgr.execute_command("pve", "100", "echo hi")
    assert result["success"] is True
    assert result["output"] == "hello"


@pytest.mark.asyncio
async def test_execute_not_running():
    api = make_fake_proxmox(qemu={"100": {"name": "v", "status": "stopped"}})
    mgr = VMConsoleManager(api)
    with pytest.raises(ValueError, match="not running"):
        await mgr.execute_command("pve", "100", "echo hi")


@pytest.mark.asyncio
async def test_allowlist_blocks(monkeypatch):
    monkeypatch.setenv("PROXMOX_MCP_EXEC_ALLOWLIST", r"^echo ")
    api = make_fake_proxmox(qemu={"100": {"name": "v", "status": "running"}})
    mgr = VMConsoleManager(api)
    with pytest.raises(ValueError, match="ALLOWLIST"):
        await mgr.execute_command("pve", "100", "rm -rf /")
