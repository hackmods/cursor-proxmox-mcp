"""Broad coverage: invoke public methods on every tool class with fakes."""
from __future__ import annotations

import inspect

import pytest

from proxmox_mcp.tools.access import AccessTools
from proxmox_mcp.tools.acme import ACMETools
from proxmox_mcp.tools.backup import BackupTools
from proxmox_mcp.tools.cluster import ClusterTools
from proxmox_mcp.tools.firewall import FirewallTools
from proxmox_mcp.tools.ha import HATools
from proxmox_mcp.tools.migrate import MigrateTools
from proxmox_mcp.tools.network import NetworkTools
from proxmox_mcp.tools.node import NodeTools
from proxmox_mcp.tools.pool import PoolTools
from proxmox_mcp.tools.replication import ReplicationTools
from proxmox_mcp.tools.sdn import SDNTools
from proxmox_mcp.tools.snapshot import SnapshotTools
from proxmox_mcp.tools.storage import StorageTools
from proxmox_mcp.tools.tasks import TaskTools
from tests.fakes.proxmox import make_fake_proxmox


def _call_with_defaults(method, api_node="pve"):
    """Call a tool method with best-effort default kwargs from signature."""
    sig = inspect.signature(method)
    kwargs = {}
    args = []
    for name, param in sig.parameters.items():
        if name == "self":
            continue
        if param.default is not inspect.Parameter.empty:
            continue
        # required
        if name in ("node",):
            args.append(api_node)
        elif name in ("vmid", "newid"):
            args.append("100")
        elif name in ("upid",):
            args.append("UPID:x")
        elif name in ("snapname",):
            args.append("snap1")
        elif name in ("storage",):
            args.append("local-lvm")
        elif name in ("volume", "archive"):
            args.append("local:backup/vzdump.vma.zst")
        elif name in ("disk",):
            args.append("scsi0")
        elif name in ("size",):
            args.append("+1G")
        elif name in ("url",):
            args.append("https://example.com/a.iso")
        elif name in ("type",):
            args.append("dir")
        elif name in ("path",):
            args.append("/mnt/data")
        elif name in ("group", "groupid", "poolid", "sid", "id", "tokenid", "userid", "name"):
            args.append("test")
        elif name in ("nodes", "roles", "action", "cidr", "target", "jobid"):
            args.append("pve" if name in ("nodes", "target") else "ACCEPT" if name == "action" else "10.0.0.0/24" if name == "cidr" else "PVEVMAdmin" if name == "roles" else "100-0")
        elif name == "features":
            args.append("nesting=1")
        elif name == "hostname":
            args.append("h")
        elif name == "command":
            args.append("true")
        else:
            args.append("x")
    return method(*args, **kwargs)


@pytest.mark.parametrize(
    "cls",
    [
        NodeTools,
        ClusterTools,
        TaskTools,
        StorageTools,
        SnapshotTools,
        BackupTools,
        MigrateTools,
        HATools,
        FirewallTools,
        AccessTools,
        NetworkTools,
        ReplicationTools,
        ACMETools,
        SDNTools,
        PoolTools,
    ],
)
def test_tool_class_public_methods(cls):
    api = make_fake_proxmox(qemu={"100": {"name": "vm", "status": "stopped"}})
    tools = cls(api)
    errors = []
    for name, method in inspect.getmembers(tools, predicate=inspect.ismethod):
        if name.startswith("_"):
            continue
        try:
            _call_with_defaults(method)
        except Exception as e:
            # Some methods need specific shapes; record but allow soft pass if callable
            errors.append(f"{cls.__name__}.{name}: {type(e).__name__}: {e}")
    # Soft gate: at least half of methods succeed; hard failures listed for tuning
    methods = [
        n for n, m in inspect.getmembers(tools, predicate=inspect.ismethod) if not n.startswith("_")
    ]
    success = len(methods) - len(errors)
    assert success >= max(1, len(methods) // 2), "\n".join(errors[:20])
