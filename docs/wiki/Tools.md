# Tools overview

Inventory is locked at **155** tools (`tools/inventory.py`). Domain summary:

| Domain | Highlights |
|--------|------------|
| Nodes / cluster / tasks | status, networks, `wait_for_task`, version, resources, log |
| QEMU | lifecycle, ISO/cloud-init/net, status, RRD, VNC/SPICE/termproxy |
| LXC | lifecycle, features, suspend/resume (CRIU warn), status, **network**, RRD, console tickets, exec via SSH/`pct` |
| Guest (unified) | `start/stop/shutdown/reboot/delete_guest`, `get_guest_status`, `get_guest_pending`, `move_guest_disk` — pass `guest_type=qemu\|lxc` |
| Snapshots / backups | snapshot CRUD; one-shot vzdump; scheduled `*_backup_job` |
| Storage | content, templates/ISOs, download-url, definition CRUD |
| Migrate / HA | `migrate_guest`; HA groups + resources |
| Firewall | cluster + guest rules; aliases; IP sets + **CIDR members**; macros |
| Access | users, groups, roles, ACL, tokens, permissions |
| Replication | list/status/run/create/**update**/delete |
| SDN / ACME | read (+ `apply_sdn`); ACME directories/accounts/plugins read |
| Pools | list/get/create/**update**/delete |

## Naming

- Parallel power tools: `*_vm` / `*_lxc` (stable for existing Cursor prompts).
- Prefer **`*_guest` + `guest_type`** when the agent does not know QEMU vs LXC.
- Cross-cutting tools (snapshots, migrate, guest firewall, pending, move disk) already use `guest_type`.

## Coverage matrix

Living matrix: [`.cursor/research/proxmox-api-coverage.md`](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/.cursor/research/proxmox-api-coverage.md) and [`docs/api-coverage.md`](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/docs/api-coverage.md).
