"""
Main server implementation for Proxmox MCP.

Formal Cursor ↔ Proxmox VE integration: VMs, LXC, storage, cluster, HA,
firewall, access control, backups, snapshots, migration, and tasks.
"""
from __future__ import annotations

import os
import sys
import signal
from typing import Optional

from mcp.server.fastmcp import FastMCP

from .config.loader import load_config
from .core.logging import setup_logging
from .core.proxmox import ProxmoxManager
from .tools.node import NodeTools
from .tools.vm import VMTools
from .tools.container import ContainerTools
from .tools.storage import StorageTools
from .tools.cluster import ClusterTools
from .tools.tasks import TaskTools
from .tools.snapshot import SnapshotTools
from .tools.backup import BackupTools
from .tools.migrate import MigrateTools
from .tools.ha import HATools
from .tools.firewall import FirewallTools
from .tools.access import AccessTools
from .tools.network import NetworkTools
from .tools.replication import ReplicationTools
from .tools.acme import ACMETools
from .tools.sdn import SDNTools
from .tools.pool import PoolTools


class ProxmoxMCPServer:
    """Main server class for Proxmox MCP."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = load_config(config_path)
        self.logger = setup_logging(self.config.logging)

        self.proxmox_manager = ProxmoxManager(self.config.proxmox, self.config.auth)
        self.proxmox = self.proxmox_manager.get_api()

        self.node_tools = NodeTools(self.proxmox)
        self.vm_tools = VMTools(self.proxmox)
        self.container_tools = ContainerTools(self.proxmox)
        self.storage_tools = StorageTools(self.proxmox)
        self.cluster_tools = ClusterTools(self.proxmox)
        self.task_tools = TaskTools(self.proxmox)
        self.snapshot_tools = SnapshotTools(self.proxmox)
        self.backup_tools = BackupTools(self.proxmox)
        self.migrate_tools = MigrateTools(self.proxmox)
        self.ha_tools = HATools(self.proxmox)
        self.firewall_tools = FirewallTools(self.proxmox)
        self.access_tools = AccessTools(self.proxmox)
        self.network_tools = NetworkTools(self.proxmox)
        self.replication_tools = ReplicationTools(self.proxmox)
        self.acme_tools = ACMETools(self.proxmox)
        self.sdn_tools = SDNTools(self.proxmox)
        self.pool_tools = PoolTools(self.proxmox)

        self.mcp = FastMCP("ProxmoxMCP")
        self._setup_tools()

    def _setup_tools(self) -> None:
        """Register all MCP tools via tools.register.register_all."""
        from .tools.register import register_all

        register_all(self)

    def start(self) -> None:
        import anyio

        def signal_handler(signum, frame):
            self.logger.info("Received signal to shutdown...")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            self.logger.info("Starting MCP server...")
            anyio.run(self.mcp.run_stdio_async)
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            sys.exit(1)


def main() -> None:
    config_path = os.getenv("PROXMOX_MCP_CONFIG")
    if not config_path:
        print("PROXMOX_MCP_CONFIG environment variable must be set")
        sys.exit(1)
    try:
        server = ProxmoxMCPServer(config_path)
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
