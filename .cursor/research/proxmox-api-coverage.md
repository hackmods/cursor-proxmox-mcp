# Proxmox API → MCP coverage matrix

Living inventory for cursor-proxmox-mcp. Status: **done** | **planned** | **excluded**.

Source of truth for registered names: `ProxmoxMCPServer._setup_tools()` and `tests/expected_tools.py`.

**Auth note:** MCP uses API tokens (`config.json`). Proxmox default **Privilege Separation=Yes** requires ACL on `user@realm!tokenid` (not only the user). See `SETUP.md` and decision D8. Some interactive console endpoints are token-incompatible per upstream PVE docs; we mint tickets only.

## Done

| Domain | MCP tools | API (representative) |
|--------|-----------|----------------------|
| Nodes | get_nodes, get_node_status, list_node_networks, subscription, certificates, report, services, time, wakeonlan | /nodes... |
| LXC | full lifecycle + config + suspend/resume (CRIU warn) + status + **get_lxc_network** + rrd + VNC/SPICE/termproxy + **exec/password/keys via SSH/pct** + **prepare_lxc_for_docker (keyctl\|crun)** + **configure_lxc_dns** + **pct_set_lxc** + **push/pull** + **provision_lxc** + **deploy_static_nginx** + **deploy_node_app** + **ssh_public_keys / docker_ready / nameserver / onboot / description / tags on create** | /nodes/{n}/lxc... + host pct (opt-in ssh) |
| Cluster | get_cluster_status, get_next_vmid, get_version, **get_mcp_capabilities**, get_cluster_resources, get_cluster_log, get_cluster_options | /cluster..., /version + MCP self-check |
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

### Phase F — LXC day-2 (done / v1.3.0)

| Item | Status |
|------|--------|
| `get_mcp_capabilities` | done |
| `prepare_lxc_for_docker` | done |
| `configure_lxc_dns` | done |
| `pct_set_lxc` | done (allowlisted host pct set) |
| `configure_lxc_ssh` | done |
| `get_docker_lxc_status` | done |
| `bootstrap_docker_lxc` | done |
| `provision_lxc` | done |
| `qm_set_vm` | done (allowlisted host qm set) |
| `push_to_lxc` / `pull_from_lxc` | done |
| paramiko core + SSH/exec QOL | done |
| `create_lxc(docker_ready=…)` tip/features only | done |

### Phase F.1 — done / v1.4.0

| Item | Effort | Status |
|------|--------|--------|
| `get_vm_network` (agent network-get-interfaces) | S ~0.5d | done |
| `create_vm`/`create_lxc` optional `wait=` (default false) | S ~0.5d | done |
| `push_to_vm` / `pull_from_vm` (agent file-write/read) | M ~1–1.5d | done |
| `deploy_static_nginx` | M ~0.5–1d | done |
| `get_containers` probes (docker/`:80`, opt-in only) | M ~0.5–1d | done |
| `deploy_node_app` (Node LTS → build → systemd) | M ~0.5d | done (r14) |

### Phase C light — done / v1.6.0

| Item | Status |
|------|--------|
| `get_vm_guest_info` / `fsfreeze_vm` / `fsthaw_vm` | done |
| `bootstrap_cloudinit_vm` | done |
| `reboot_node` / `shutdown_node` (confirm=node) | done |
| `get_cluster_join_info` / `join_cluster` (confirm=JOIN) | done |

### Phase C — Heavy / deferred

| Area | Reason to defer |
|------|-----------------|
| SDN write CRUD (zones/vnets/subnets) | Multi-object graph + apply orchestration UX |
| ACME account create + order + renew | Multi-step DNS plugin credentials |
| Ceph OSD/MON/MGR create/destroy | Cluster-invasive sequenced ops |
| Full VNC/SPICE websocket proxy | Long-lived stream ≠ MCP request/response |
| PBS direct admin | Separate product; use storage.type=pbs |
| Node network create/update/reload | Bridge automation labs |

## Excluded

| Area | Reason |
|------|--------|
| Ceph deep admin beyond planned | Prefer native Ceph tooling |
| Subscription write / license upload | Rare; UI-driven |
