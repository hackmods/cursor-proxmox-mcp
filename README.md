# cursor-proxmox-mcp

**Formal Cursor ↔ [Proxmox VE](https://www.proxmox.com/) MCP integration** — 132 tools covering QEMU VMs, LXC, storage admin, cluster/tasks, snapshots, backups, migration, HA, firewall, access control, replication, SDN (read), ACME (read), pools, and console tickets.

**Repo:** [hackmods/cursor-proxmox-mcp](https://github.com/hackmods/cursor-proxmox-mcp)

Docs: [**Setup guide**](SETUP.md) · [API coverage](docs/api-coverage.md) · [Next expansion](.cursor/research/next-expansion.md) · Research matrix: [`.cursor/research/proxmox-api-coverage.md`](.cursor/research/proxmox-api-coverage.md)

## MCP tools

Registered in `ProxmoxMCPServer._setup_tools()` — inventory locked by `tests/expected_tools.py` (CI fails on drift).

| Domain | Tools |
|--------|--------|
| **Nodes** | `get_nodes`, `get_node_status`, `list_node_networks`, `get_node_subscription`, `list_node_certificates`, `get_node_report`, `list_node_services`, `get_node_time`, `wake_node` |
| **Cluster / tasks** | `get_cluster_status`, `get_next_vmid`, `get_task_status`, `list_tasks`, `wait_for_task`, `get_version`, `get_cluster_resources`, `get_cluster_log`, `get_cluster_options` |
| **QEMU** | lifecycle + config (ISO/cloud-init/net on create/update) + `get_vm_status`, `get_vm_rrd_data`, console tickets |
| **LXC** | lifecycle + config (auto ostemplate, bridge/ip/net0) + `get_lxc_status`, console tickets |
| **Snapshots / Backups** | list/create/delete/rollback snapshot; create/list/restore/delete backup |
| **Storage** | list, content, `list_os_templates`, `list_isos`, download-url, definition CRUD |
| **Migrate / HA** | `migrate_guest`; HA groups + resources CRUD |
| **Firewall** | cluster + guest rules/options; aliases, IP sets, macros |
| **Access** | users, groups, roles, ACL, tokens, `get_permissions`, `get_token_permissions` |
| **Replication** | list/status/run/create/delete jobs |
| **SDN** | list zones/vnets/controllers/ipams/dns + `apply_sdn` |
| **ACME** | list plugins/accounts/directories (read) |
| **Pools** | list/get/create/delete |

### Suggested agent flow

1. `get_next_vmid` → `list_os_templates` / `list_isos` → `list_node_networks`
2. `create_lxc` / `create_vm` → `wait_for_task` → start
3. `create_snapshot` before risky changes → `update_*_config` / power tools
4. `migrate_guest` / HA / firewall / access / replication as needed

## Installation

### Prerequisites

- [uv](https://github.com/astral-sh/uv) (recommended) **or** Python 3.10+
- Proxmox API token

### Path 1 — uvx (recommended)

PyPI package name is **`proxmox-mcp-server`** (console scripts: `proxmox-mcp-server` and `proxmox-mcp`).

```bash
# Install uv if needed:  pip install uv   OR   winget install astral-sh.uv

# After PyPI publish (GitHub Release → publish.yml):
uvx proxmox-mcp-server

# From a local checkout (dev / before first publish):
uvx --from . proxmox-mcp-server
```

Cursor MCP (published package — no checkout):

```json
{
  "mcpServers": {
    "proxmox": {
      "command": "uvx",
      "args": ["proxmox-mcp-server"],
      "env": {
        "PROXMOX_MCP_CONFIG": "C:/Users/YOU/proxmox-config/config.json"
      }
    }
  }
}
```

From a local checkout, use `"args": ["--from", "C:/Users/YOU/Projects/cursor-proxmox-mcp", "proxmox-mcp-server"]` instead.

Why uvx: it resolves dependencies into an isolated ephemeral env so Cursor does not depend on a hand-managed venv/`PYTHONPATH`.

### Path 2 — uv from source

```bash
git clone https://github.com/hackmods/cursor-proxmox-mcp.git
cd cursor-proxmox-mcp
uv venv
# Windows: .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
uv pip install -e ".[dev]"
cp proxmox-config/config.example.json proxmox-config/config.json
# Edit host + token, then:
uv run proxmox-mcp-server
```

### Path 3 — pip fallback

```bash
python -m venv .venv
# activate venv
pip install -e ".[dev]"
# optional OpenAPI bridge: pip install -e ".[openapi]"
$env:PROXMOX_MCP_CONFIG="proxmox-config\config.json"   # PowerShell
python -m proxmox_mcp.server
```

Cursor MCP (direct Python — use absolute paths):

```json
{
  "mcpServers": {
    "proxmox": {
      "command": "python",
      "args": ["-m", "proxmox_mcp.server"],
      "cwd": "C:/Users/YOU/Projects/cursor-proxmox-mcp",
      "env": {
        "PROXMOX_MCP_CONFIG": "C:/Users/YOU/Projects/cursor-proxmox-mcp/proxmox-config/config.json",
        "PYTHONPATH": "C:/Users/YOU/Projects/cursor-proxmox-mcp/src"
      }
    }
  }
}
```

Restart the **proxmox** MCP server in Cursor after pulling new tools. `start.bat` is a manual Windows fallback only.

### Verify / local CI

```powershell
.\scripts\ci-local.ps1
```

```bash
./scripts/ci-local.sh
```

Runs: editable install → entrypoint smoke → ruff → pytest → inventory floor (≥100 tools).

### Troubleshooting

| Symptom | Fix |
|---------|-----|
| `spawn uvx ENOENT` | Install uv (`pip install uv` or `winget install astral-sh.uv`), then restart Cursor |
| `ModuleNotFoundError: proxmox_mcp` | Use uvx/`uv run`, or set `PYTHONPATH=.../src` for plain python |
| `PROXMOX_MCP_CONFIG ... must be set` | Point env at `proxmox-config/config.json` (absolute path) |
| Auth OK but empty data / odd 403 | Privilege Separation **Yes** without token ACL — see [SETUP.md](SETUP.md#privilege-separation-the-gotcha) |
| 403 on HA / firewall / `keyctl` | Token needs elevated role; prefer scoped `mcp@pve` over `root@pam` when possible |
| Tools missing in Cursor | Restart MCP server after git pull |

First-time cluster wiring (token, privsep, Cursor JSON, example prompts): **[SETUP.md](SETUP.md)**.

## Configuration

Example `proxmox-config/config.json`:

```json
{
  "proxmox": {
    "host": "PROXMOX_HOST",
    "port": 8006,
    "verify_ssl": false,
    "service": "PVE"
  },
  "auth": {
    "user": "USER@pve",
    "token_name": "TOKEN_NAME",
    "token_value": "TOKEN_VALUE"
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "proxmox_mcp.log"
  }
}
```

Create the token in Proxmox UI: Datacenter → Permissions → API Tokens. See **[SETUP.md — API token & Privilege Separation](SETUP.md#1-create-a-proxmox-api-token)** for the full walkthrough.

**Privilege Separation:** leave **Yes** (default) and grant ACLs to the **token** (`user@realm!tokenid`). Setting it to **No** makes the token inherit the user’s full permissions (common lab shortcut; larger blast radius if leaked). Grant roles matching the tools you use (`PVEAuditor`, `PVEVMAdmin`, `Datastore.*`, `Sys.Audit`/`Sys.Modify` for HA/firewall/access).

## Features

- Token auth via proxmoxer
- Full guest lifecycle, snapshots, vzdump backups
- Storage content + definition CRUD + URL download
- Cluster HA, firewall (rules/aliases/ipsets), access/ACL/tokens
- Replication jobs, SDN read + apply, ACME read, pools
- Console **ticket mint** only (VNC/SPICE/termproxy) — no websocket proxy
- uvx / uv / pip install paths; optional `.[openapi]` for mcpo
- Local + GitHub CI (`ruff` + `pytest` + inventory lock)

### Planned (not implemented yet)

**Phase C — heavy:** SDN write CRUD, ACME order/renew, Ceph OSD/MON admin, cluster join/bootstrap, full VNC/SPICE websocket proxy, PBS direct admin, node reboot/shutdown — see [coverage matrix](.cursor/research/proxmox-api-coverage.md) and [next-expansion.md](.cursor/research/next-expansion.md).

## Development

```powershell
.\scripts\ci-local.ps1
```

After adding a tool: update `definitions.py`, README table, `.cursor/research/proxmox-api-coverage.md`, `.cursor/research/next-expansion.md` (if closing a planned row), and `tests/expected_tools.py`.

## Status

- [x] Formal multi-domain Proxmox API coverage (132 tools)
- [x] Phase B: replication, SDN read, ACME read, certs, console tickets, pools, firewall extras
- [x] Phase D agent QOL: `wait_for_task`, ISO/cloud-init/net create, `list_os_templates`/`list_isos`, `get_token_permissions`
- [x] uvx `proxmox-mcp-server` entrypoint + PyPI publish workflow
- [x] Local + GitHub CI with inventory floor + optional mcpo smoke
- [ ] Phase C heavy/dangerous endpoints (documented only)

## License

MIT

## Acknowledgments

Based on [ProxmoxMCP](https://github.com/RekklesNA/ProxmoxMCP-Plus) / [canvrno/ProxmoxMCP](https://github.com/canvrno/ProxmoxMCP). Extended for Cursor IDE as a formal Proxmox VE integration.
