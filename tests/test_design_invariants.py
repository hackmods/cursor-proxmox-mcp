"""Design-invariant / architecture locks."""
from __future__ import annotations

import ast
from pathlib import Path


from proxmox_mcp.tools.inventory import (
    ALL_TOOL_NAMES,
    DESTRUCTIVE_TOOLS,
    all_tool_specs,
)
from proxmox_mcp.tools.vm import VMTools
from proxmox_mcp.tools.container import ContainerTools
from proxmox_mcp.tools.snapshot import SnapshotTools
from proxmox_mcp.tools.migrate import MigrateTools
from proxmox_mcp.tools.firewall import FirewallTools
from tests.expected_tools import EXPECTED_TOOLS
from tests.fakes.proxmox import make_fake_proxmox


def test_expected_tools_equals_inventory():
    assert EXPECTED_TOOLS == ALL_TOOL_NAMES
    assert len(ALL_TOOL_NAMES) >= 100


def test_all_tool_specs_cover_inventory():
    specs = all_tool_specs()
    names = {s.name for s in specs}
    assert names == ALL_TOOL_NAMES
    for s in specs:
        assert isinstance(s.description, str) and len(s.description) > 5


def test_destructive_descriptions_warn():
    by_name = {s.name: s.description for s in all_tool_specs()}
    for name in DESTRUCTIVE_TOOLS:
        desc = by_name[name].upper()
        assert "IRREVERSIBLE" in desc or "WARNING" in desc, name


def test_server_uses_core_logging_only():
    server_src = Path("src/proxmox_mcp/server.py").read_text(encoding="utf-8")
    assert "from .core.logging import setup_logging" in server_src
    assert "utils.logging" not in server_src
    assert "utils.auth" not in server_src


def test_dead_utils_modules_removed():
    root = Path("src/proxmox_mcp/utils")
    assert not (root / "auth.py").exists()
    assert not (root / "logging.py").exists()


def test_guest_modules_use_guest_helpers():
    for mod in (SnapshotTools, MigrateTools, FirewallTools):
        path = Path("src") / Path(*mod.__module__.split("."))
        path = path.with_suffix(".py")
        text = path.read_text(encoding="utf-8")
        assert "guest_resource" in text or "normalize_guest_type" in text


def test_tool_classes_injectable():
    api = make_fake_proxmox()
    VMTools(api)
    ContainerTools(api)


def test_register_module_exists():
    from proxmox_mcp.tools.register import register_all

    assert callable(register_all)


def test_no_bare_except_in_tools():
    tools_root = Path("src/proxmox_mcp/tools")
    offenders = []
    for path in tools_root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                offenders.append(f"{path}:{node.lineno}")
    assert not offenders, offenders
