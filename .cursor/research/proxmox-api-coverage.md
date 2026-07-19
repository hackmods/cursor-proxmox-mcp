# Proxmox API → MCP coverage matrix

Living inventory for cursor-proxmox-mcp. Status: **done** | **planned** | **excluded**.

Source of truth for registered names: `ProxmoxMCPServer._setup_tools()` and `tests/expected_tools.py`.

**Auth note:** MCP uses API tokens (`config.json`). Proxmox default **Privilege Separation=Yes** requires ACL on `user@realm!tokenid` (not only the user). See `SETUP.md` and decision D8. Some interactive console endpoints are token-incompatible per upstream PVE docs; we mint tickets only.

## Done

| Domain | MCP tools | API (representative) |
|--------|-----------|----------------------|
| Nodes | get_nodes, get_node_status, list_node_networks, subscription, certificates, report, services, time, wakeonlan | /nodes... |
| Cluster | get_cluster_status, get_next_vmid, get_version, get_cluster_resources, get_cluster_log, get_cluster_options | /cluster..., /version |
| Tasks | get_task_status, list_tasks, wait_for_task | /nodes/{n}/tasks... |
| QEMU | full lifecycle + config (ISO/cloud-init/net) + status + rrd + console tickets | /nodes/{n}/qemu... |
| LXC | full lifecycle + config + suspend/resume (CRIU warn) + status + **get_lxc_network** + rrd + VNC/SPICE/termproxy + **exec via SSH/pct** | /nodes/{n}/lxc... + host pct (opt-in ssh) |
| Guest unified | start/stop/shutdown/reboot/delete_guest, get_guest_status/pending, move_guest_disk | qemu\|lxc status + pending + move_disk/move_volume |
| Snapshots | list/create/delete/rollback | .../snapshot |
| Backups | one-shot create/list/restore/delete + scheduled list/create/delete_backup_job | vzdump + /cluster/backup |
| Storage | get/content/list_os_templates/list_isos/delete/download-url + definition CRUD | /storage... |
| Migrate | migrate_guest | .../migrate |
| HA | status, groups, resources CRUD | /cluster/ha... |
| Firewall | cluster+guest rules/options; aliases; ipsets + CIDR members; macros | /cluster/firewall... |
| Access | users, groups, roles, ACL, tokens, get_permissions, get_token_permissions | /access/... |
| Replication | list/status/run/create/update/delete | /cluster/replication, /nodes/{n}/replication |
| ACME | list plugins/accounts/directories (read) | /cluster/acme... |
| SDN | list zones/vnets/controllers/ipams/dns + apply | /cluster/sdn... |
| Pools | list/get/create/update/delete | /pools |

## Planned

### Phase D — Agent QOL (done)

See [next-expansion.md](next-expansion.md). Summary:

| Item | Status |
|------|--------|
| `wait_for_task` (poll UPID) | done |
| ISO/CDROM + boot on create/update VM | done |
| Cloud-init params on create/update | done |
| Net/bridge overrides on create_vm / create_lxc | done |
| `list_os_templates` / `list_isos` | done |
| `get_token_permissions` (privsep ACL smoke) | done |
| PyPI package + publish.yml for `uvx cursor-proxmox-mcp` | done (publish on Release) |

### Phase C — Heavy / deferred

| Area | Reason to defer |
|------|-----------------|
| SDN write CRUD (zones/vnets/subnets) | Multi-object graph + apply orchestration UX |
| ACME account create + order + renew | Multi-step DNS plugin credentials |
| Ceph OSD/MON/MGR create/destroy | Cluster-invasive sequenced ops |
| Cluster join / corosync bootstrap | One-shot, dangerous, no rollback |
| Full VNC/SPICE websocket proxy | Long-lived stream ≠ MCP request/response |
| PBS direct admin | Separate product; use storage.type=pbs |
| Node reboot/shutdown | Physical host power needs extra confirmation UX |

## Excluded

| Area | Reason |
|------|--------|
| Ceph deep admin beyond planned | Prefer native Ceph tooling |
| Subscription write / license upload | Rare; UI-driven |
