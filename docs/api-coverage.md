# API coverage guide

Formal **cursor-proxmox-mcp** maps Proxmox VE REST endpoints to MCP tools for Cursor agents.

## Auth

Configure `proxmox-config/config.json` with host + API token (`user@realm!tokenid`). Many HA/firewall/access and `keyctl` feature changes require privileges beyond a limited token — often `root@pam` or a role with `Sys.Modify` / `VM.Allocate` / `Datastore.*`.

## Install (uvx)

Recommended: use the `proxmox-mcp-server` console script via uv so Cursor does not need a hand-managed venv:

```bash
uvx --from /path/to/cursor-proxmox-mcp proxmox-mcp-server
```

Set `PROXMOX_MCP_CONFIG` to your `proxmox-config/config.json`. See README for Cursor JSON snippets and pip fallback.

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

Phase C (SDN write, ACME order, Ceph OSD, cluster join, websocket console proxy) is documented as planned — not registered as available tools.

## Local CI

```powershell
.\scripts\ci-local.ps1
```

```bash
./scripts/ci-local.sh
```

Runs ruff + pytest + entrypoint smoke. Tool registration must match `tests/expected_tools.py` (≥100 tools).
