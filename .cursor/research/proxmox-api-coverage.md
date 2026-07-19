# Proxmox API → MCP coverage matrix

Living inventory for cursor-proxmox-mcp. Status: **done** | **excluded**.

Source of truth for registered names: `ProxmoxMCPServer._setup_tools()` and `tests/expected_tools.py`.

## Done

| Domain | MCP tools | API (representative) |
|--------|-----------|----------------------|
| Nodes | get_nodes, get_node_status, list_node_networks | /nodes, /nodes/{n}/status, /nodes/{n}/network |
| Cluster | get_cluster_status, get_next_vmid | /cluster/status, /cluster/nextid |
| Tasks | get_task_status, list_tasks | /nodes/{n}/tasks... |
| QEMU lifecycle | get_vms, create_vm, start/stop/shutdown/reset/reboot/suspend/resume_vm, delete_vm | /nodes/{n}/qemu... |
| QEMU config | get_vm_config, update_vm_config, resize_vm_disk, convert_vm_to_template, clone_vm | config, resize, template, clone |
| QEMU agent | execute_vm_command | /agent/exec |
| LXC lifecycle | get_containers, create_lxc, power suite, delete_lxc, update_lxc_features | /nodes/{n}/lxc... |
| LXC config | get_lxc_config, update_lxc_config, resize_lxc_disk, convert_lxc_to_template, clone_lxc | config, resize, template, clone |
| LXC exec | execute_lxc_command | /lxc/{vmid}/exec (version-dependent) |
| Snapshots | list/create/delete/rollback_snapshot | .../snapshot |
| Backups | create/list/restore/delete_backup | vzdump + storage content |
| Storage | get_storage, get_storage_content, delete_storage_content, download_url_to_storage, create/update/delete_storage | /storage, content, download-url |
| Migrate | migrate_guest | .../migrate |
| HA | get_ha_status, list/create/delete_ha_group, list/create/update/delete_ha_resource | /cluster/ha... |
| Firewall | cluster + guest options/rules CRUD | /cluster/firewall, guest firewall |
| Access | users, groups, roles, ACL, tokens, permissions | /access/... |

## Excluded (with reason)

| Area | Reason |
|------|--------|
| SDN / zones / VNets | Large nested surface; niche for Cursor agents |
| Ceph OSD/MON/MGR admin | Ops-heavy; use Ceph tooling |
| Cluster join / corosync bootstrap | Dangerous one-shot ops |
| VNC/SPICE websocket console | Needs long-lived proxy; poor MCP fit |
| Subscription / ACME full lifecycle | Low day-to-day agent value |
| Replication job orchestration | Beyond list/status for now |
