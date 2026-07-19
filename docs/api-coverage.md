# API coverage guide

Formal **cursor-proxmox-mcp** maps Proxmox VE REST endpoints to MCP tools for Cursor agents.

## Auth

Configure `proxmox-config/config.json` with host + API token. Full first-run guide: [SETUP.md](../SETUP.md).

**Token format in config:** `auth.user` = `user@realm`, `auth.token_name` = token id, `auth.token_value` = secret. Proxmox’s combined id is `user@realm!tokenid`.

**Privilege Separation (Proxmox default = Yes):**

- **Yes:** token needs its own ACL; effective perms = user ∩ token. Best practice.
- **No:** token inherits all user perms. Lab bypass when token ACLs were forgotten; larger leak blast radius.

Many HA/firewall/access and `keyctl` feature changes need privileges beyond a limited token — often `PVEAdmin` / `Sys.Modify` or a carefully scoped dedicated user (prefer that over a `root@pam` token).

After connect, use `get_permissions` to sanity-check what the token can actually do.

## Install (uvx)

Recommended: use the `proxmox-mcp-server` console script via uv so Cursor does not need a hand-managed venv:

```bash
uvx --from /path/to/cursor-proxmox-mcp proxmox-mcp-server
```

Set `PROXMOX_MCP_CONFIG` to your `proxmox-config/config.json`. See [SETUP.md](../SETUP.md) for Cursor JSON snippets, Privilege Separation, and pip/uvx fallbacks.

## Domains

See the living matrix in [`.cursor/research/proxmox-api-coverage.md`](../.cursor/research/proxmox-api-coverage.md).

Quick map:

| Need | Start with |
|------|------------|
| Pick free ID | `get_next_vmid` |
| Find templates/ISOs | `get_storage_content` |
| Create guest | `create_vm` / `create_lxc` |
| Wait for job | `get_task_status` |
| Inspect config | `get_vm_config` / `get_lxc_config` |
| Safety net | `create_snapshot` / `create_backup` |
| Move node | `migrate_guest` |
| HA | `create_ha_resource` |
| Firewall | `create_guest_firewall_rule` / `create_firewall_alias` |
| Users/tokens | `create_user` / `create_token` |
| Replication | `list_replication_jobs` / `run_replication_job` |
| SDN | `list_sdn_zones` / `apply_sdn` |
| Console ticket | `create_vnc_ticket_vm` (mint only) |
| Cluster overview | `get_cluster_resources` / `get_version` |

## Exclusions / planned

**Phase D (next — agent QOL):** `wait_for_task`, richer `create_vm`/`create_lxc` (ISO, cloud-init, net/bridge), token permission smoke, optional PyPI publish. Full table: [next-expansion.md](../.cursor/research/next-expansion.md).

**Phase C (deferred):** SDN write, ACME order/renew, Ceph OSD, cluster join, websocket console proxy, PBS direct admin, node reboot/shutdown — documented as planned, **not** registered as available tools. See [coverage matrix](../.cursor/research/proxmox-api-coverage.md).

## Knowledge pointers

| Topic | File |
|-------|------|
| What to build next | [.cursor/research/next-expansion.md](../.cursor/research/next-expansion.md) |
| API done / planned / excluded | [.cursor/research/proxmox-api-coverage.md](../.cursor/research/proxmox-api-coverage.md) |
| Design decisions (privsep, tickets, uvx, Phase D bias) | [.cursor/research/decisions.md](../.cursor/research/decisions.md) |
| Quirks found while shipping | [.cursor/research/changelog-notes.md](../.cursor/research/changelog-notes.md) |
| First-run auth | [SETUP.md](../SETUP.md) |

## Local CI

```powershell
.\scripts\ci-local.ps1
```

```bash
./scripts/ci-local.sh
```

Runs ruff + pytest + entrypoint smoke. Tool registration must match `tests/expected_tools.py` (≥100 tools).
