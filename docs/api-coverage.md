# API coverage guide

Formal **cursor-proxmox-mcp** maps Proxmox VE REST endpoints to MCP tools for Cursor agents.

## Auth

Configure `proxmox-config/config.json` with host + API token (`user@realm!tokenid`). Many HA/firewall/access and `keyctl` feature changes require privileges beyond a limited token — often `root@pam` or a role with `Sys.Modify` / `VM.Allocate` / `Datastore.*`.

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
| Firewall | `create_guest_firewall_rule` |
| Users/tokens | `create_user` / `create_token` |

## Exclusions

SDN, Ceph internals, cluster bootstrap, VNC/SPICE proxies — documented as excluded in the coverage matrix.

## Local CI

```powershell
.\scripts\ci-local.ps1
```

```bash
./scripts/ci-local.sh
```

Runs ruff + pytest. Tool registration must match `tests/expected_tools.py`.
