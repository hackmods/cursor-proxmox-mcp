# cursor-proxmox-mcp

Formal **Cursor ↔ [Proxmox VE](https://www.proxmox.com/)** MCP connector — a living guide for operators and agents.

| | |
|--|--|
| **Version** | [v1.9.0](https://github.com/hackmods/cursor-proxmox-mcp/releases/tag/v1.9.0) |
| **Tools** | **212** (CI-locked inventory) |
| **Package** | [`cursor-proxmox-mcp`](https://pypi.org/project/cursor-proxmox-mcp/) on PyPI · [GHCR](https://github.com/hackmods/cursor-proxmox-mcp/pkgs/container/cursor-proxmox-mcp) |

Covers QEMU VMs (incl. `provision_vm`), LXC day-2 deploy, unified guest power, storage, cluster/tasks, snapshots, backups, migration, HA, firewall, access control, replication, SDN write, ACME, Ceph (gated OSD), pools, console tickets, and optional **dual-credential elevated mode** (`auth_write`).

## Wiki map

| Page | What it’s for |
|------|----------------|
| [Setup](Setup) | Cursor `mcp.json`, auth/privsep, host SSH for `pct`, reload checklist |
| [Elevated mode](Elevated-mode) | **`auth_write`**, dual MCP servers, Cursor `permissions.json` auto-approve, deploy pipeline |
| [Example prompts](Example-prompts) | Copy-paste starters + DevOps prompts for Cursor workflows |
| [Tools](Tools) | **Every** registered tool with description (generated from inventory) |
| [Recipes](Recipes) | Agent playbooks (create → wait → start, Docker-in-LXC, VM ISO, ACL smoke) |
| [Troubleshooting](Troubleshooting) | Symptom → fix table |

**Repo deep-links:** full [SETUP.md](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SETUP.md) · [README](https://github.com/hackmods/cursor-proxmox-mcp#readme) · [CHANGELOG](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/CHANGELOG.md) · [PUBLISHING.md](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/PUBLISHING.md) · [API coverage](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/docs/api-coverage.md)

## Quick install

```bash
# Published package (recommended):
uvx cursor-proxmox-mcp

# Local checkout (dev):
uvx --from /path/to/cursor-proxmox-mcp cursor-proxmox-mcp
```

Set `PROXMOX_MCP_CONFIG` to an **absolute** path to `config.json` (see [Setup](Setup)).

> **Package name:** always install **`cursor-proxmox-mcp`**. The unrelated PyPI project `proxmox-mcp-server` is a different codebase.

## Suggested agent flow

1. `get_next_vmid` → `list_os_templates` / `list_isos` → `list_node_networks`
2. `provision_lxc` / `provision_vm` (preferred) or `create_lxc` / `create_vm` → **`wait_for_task`** → start
3. After config edits: `get_guest_pending` → reboot if needed
4. `create_snapshot` before risky changes

Elevated write / fewer approval prompts: [Elevated mode](Elevated-mode). More: [Recipes](Recipes).

## Design highlights (agents)

- **Create ≠ ready:** async UPID first; failures (missing template, etc.) surface on `wait_for_task`.
- **LXC create ≠ app deploy:** OS template only — nesting ≠ Docker installed.
- **QEMU vs LXC:** empty `get_vms` does not mean “no guests” if only containers exist.
- **Privsep:** empty lists often mean missing ACL on `user@realm!tokenid` — use `get_token_permissions`.
- **Elevated mode:** optional `auth_write` or dual MCP servers — see [Elevated mode](Elevated-mode).

## Source of truth

Registered tools: `src/proxmox_mcp/tools/register.py` + `inventory.py` (CI-locked). This wiki is mirrored from [`docs/wiki/`](https://github.com/hackmods/cursor-proxmox-mcp/tree/main/docs/wiki) — regenerate tools with `python scripts/generate-wiki-tools.py`, then sync with `scripts/sync-wiki.ps1` or `scripts/sync-wiki.sh`.
