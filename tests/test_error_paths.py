"""Force error paths through _handle_error for coverage."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from proxmox_mcp.errors import ProxmoxAPIError, ProxmoxNotFoundError
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


@pytest.mark.parametrize(
    "factory,call",
    [
        (NodeTools, lambda t: t.get_nodes()),
        (ClusterTools, lambda t: t.get_cluster_status()),
        (ClusterTools, lambda t: t.get_version()),
        (ClusterTools, lambda t: t.get_next_vmid()),
        (ClusterTools, lambda t: t.get_cluster_resources()),
        (ClusterTools, lambda t: t.get_cluster_log()),
        (ClusterTools, lambda t: t.get_cluster_options()),
        (TaskTools, lambda t: t.list_tasks("pve")),
        (TaskTools, lambda t: t.get_task_status("pve", "UPID")),
        (StorageTools, lambda t: t.get_storage()),
        (StorageTools, lambda t: t.get_storage_content("pve", "local")),
        (NetworkTools, lambda t: t.list_node_networks("pve")),
        (HATools, lambda t: t.get_ha_status()),
        (HATools, lambda t: t.list_ha_groups()),
        (HATools, lambda t: t.list_ha_resources()),
        (ACMETools, lambda t: t.list_acme_plugins()),
        (ACMETools, lambda t: t.list_acme_accounts()),
        (ACMETools, lambda t: t.get_acme_directories()),
        (SDNTools, lambda t: t.list_sdn_zones()),
        (SDNTools, lambda t: t.list_sdn_vnets()),
        (SDNTools, lambda t: t.list_sdn_controllers()),
        (SDNTools, lambda t: t.list_sdn_ipams()),
        (SDNTools, lambda t: t.list_sdn_dns()),
        (SDNTools, lambda t: t.apply_sdn()),
        (PoolTools, lambda t: t.list_pools()),
        (PoolTools, lambda t: t.get_pool("p")),
        (PoolTools, lambda t: t.create_pool("p")),
        (PoolTools, lambda t: t.delete_pool("p")),
        (AccessTools, lambda t: t.list_users()),
        (AccessTools, lambda t: t.list_groups()),
        (AccessTools, lambda t: t.list_roles()),
        (AccessTools, lambda t: t.list_acl()),
        (AccessTools, lambda t: t.get_permissions()),
        (FirewallTools, lambda t: t.get_cluster_firewall_options()),
        (FirewallTools, lambda t: t.list_cluster_firewall_rules()),
        (FirewallTools, lambda t: t.list_firewall_aliases()),
        (FirewallTools, lambda t: t.list_firewall_ipsets()),
        (FirewallTools, lambda t: t.list_firewall_macros()),
        (SnapshotTools, lambda t: t.list_snapshots("pve", "100")),
        (BackupTools, lambda t: t.list_backups("pve", "local")),
        (ReplicationTools, lambda t: t.list_replication_jobs()),
        (MigrateTools, lambda t: t.migrate_guest("pve", "100", "pve2")),
    ],
)
def test_api_error_paths(factory, call):
    api = MagicMock()
    # Make everything raise
    api.nodes.get.side_effect = Exception("boom")
    api.nodes.side_effect = Exception("boom")
    api.cluster.status.get.side_effect = Exception("boom")
    api.cluster.nextid.get.side_effect = Exception("boom")
    api.cluster.resources.get.side_effect = Exception("boom")
    api.cluster.log.get.side_effect = Exception("boom")
    api.cluster.options.get.side_effect = Exception("boom")
    api.version.get.side_effect = Exception("boom")
    api.storage.get.side_effect = Exception("boom")
    api.cluster.ha.status.current.get.side_effect = Exception("boom")
    api.cluster.ha.groups.get.side_effect = Exception("boom")
    api.cluster.ha.resources.get.side_effect = Exception("boom")
    api.cluster.acme.plugins.get.side_effect = Exception("boom")
    api.cluster.acme.account.get.side_effect = Exception("boom")
    api.cluster.acme.directories.get.side_effect = Exception("boom")
    api.cluster.sdn.zones.get.side_effect = Exception("boom")
    api.cluster.sdn.vnets.get.side_effect = Exception("boom")
    api.cluster.sdn.controllers.get.side_effect = Exception("boom")
    api.cluster.sdn.ipams.get.side_effect = Exception("boom")
    api.cluster.sdn.dns.get.side_effect = Exception("boom")
    api.cluster.sdn.put.side_effect = Exception("boom")
    api.cluster.sdn.apply.put.side_effect = Exception("boom")
    api.pools.get.side_effect = Exception("boom")
    api.pools.post.side_effect = Exception("boom")
    api.pools.side_effect = Exception("boom")
    api.access.users.get.side_effect = Exception("boom")
    api.access.groups.get.side_effect = Exception("boom")
    api.access.roles.get.side_effect = Exception("boom")
    api.access.acl.get.side_effect = Exception("boom")
    api.access.permissions.get.side_effect = Exception("boom")
    api.cluster.firewall.options.get.side_effect = Exception("boom")
    api.cluster.firewall.rules.get.side_effect = Exception("boom")
    api.cluster.firewall.aliases.get.side_effect = Exception("boom")
    api.cluster.firewall.ipset.get.side_effect = Exception("boom")
    api.cluster.firewall.macros.get.side_effect = Exception("boom")
    api.cluster.replication.get.side_effect = Exception("boom")

    tools = factory(api)
    with pytest.raises((ProxmoxAPIError, ProxmoxNotFoundError, RuntimeError, ValueError)):
        call(tools)
