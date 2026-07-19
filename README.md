# cursor-proxmox-mcp

**Formal Cursor ↔ [Proxmox VE](https://www.proxmox.com/) MCP integration** — 85 tools covering QEMU VMs, LXC, storage admin, cluster/tasks, snapshots, backups, migration, HA, firewall, and access control.

**Repo:** [hackmods/cursor-proxmox-mcp](https://github.com/hackmods/cursor-proxmox-mcp)

Docs: [API coverage guide](docs/api-coverage.md) · Research matrix: [`.cursor/research/proxmox-api-coverage.md`](.cursor/research/proxmox-api-coverage.md)

## MCP tools (85)

Registered in `ProxmoxMCPServer._setup_tools()` — inventory locked by `tests/expected_tools.py`.

| Domain | Tools |
|--------|--------|
| **Nodes** | `get_nodes`, `get_node_status`, `list_node_networks` |
| **Cluster / tasks** | `get_cluster_status`, `get_next_vmid`, `get_task_status`, `list_tasks` |
| **QEMU** | `get_vms`, `create_vm`, `get_vm_config`, `update_vm_config`, `execute_vm_command`, `start_vm`, `stop_vm`, `shutdown_vm`, `reset_vm`, `reboot_vm`, `suspend_vm`, `resume_vm`, `delete_vm`, `clone_vm`, `resize_vm_disk`, `convert_vm_to_template` |
| **LXC** | `get_containers`, `create_lxc`, `get_lxc_config`, `update_lxc_config`, `start_lxc`, `stop_lxc`, `shutdown_lxc`, `reboot_lxc`, `delete_lxc`, `update_lxc_features`, `clone_lxc`, `resize_lxc_disk`, `convert_lxc_to_template`, `execute_lxc_command` |
| **Snapshots** | `list_snapshots`, `create_snapshot`, `delete_snapshot`, `rollback_snapshot` (`guest_type=qemu\|lxc`) |
| **Backups** | `create_backup`, `list_backups`, `restore_backup`, `delete_backup` |
| **Storage** | `get_storage`, `get_storage_content`, `delete_storage_content`, `download_url_to_storage`, `create_storage`, `update_storage`, `delete_storage` |
| **Migrate** | `migrate_guest` |
| **HA** | `get_ha_status`, `list_ha_groups`, `create_ha_group`, `delete_ha_group`, `list_ha_resources`, `create_ha_resource`, `update_ha_resource`, `delete_ha_resource` |
| **Firewall** | cluster + guest options/rules CRUD (`get/set/list/create/delete_*_firewall_*`) |
| **Access** | `list_users`, `get_user`, `create_user`, `delete_user`, `list_groups`, `create_group`, `delete_group`, `list_roles`, `list_acl`, `update_acl`, `list_tokens`, `create_token`, `delete_token`, `get_permissions` |

### Suggested agent flow

1. `get_next_vmid` → `get_storage_content` (templates/ISOs) → `list_node_networks`
2. `create_lxc` / `create_vm` → `get_task_status`
3. `create_snapshot` before risky changes → `update_*_config` / power tools
4. `migrate_guest` / HA / firewall / access as needed

## Features

- Token auth to Proxmox via proxmoxer
- Full guest lifecycle (create, power, clone, resize, template, delete)
- Snapshots + vzdump backups/restore
- Storage content browse + storage definition CRUD + URL download
- Cluster HA, firewall, and access/ACL/token admin
- Windows-friendly Cursor `mcp.json` launch; optional OpenAPI via `mcpo`
- Local + GitHub CI (`ruff` + `pytest`)

### Intentionally excluded

SDN, Ceph OSD internals, cluster bootstrap/join, VNC/SPICE websocket consoles — see [coverage matrix](.cursor/research/proxmox-api-coverage.md).

## Built With

- [Cursor](https://cursor.com) · [Proxmoxer](https://github.com/proxmoxer/proxmoxer) · [MCP SDK](https://github.com/modelcontextprotocol/sdk) · [Pydantic](https://www.pydantic.dev/)

## Installation

### Prerequisites

- Python 3.10+
- Proxmox API token
- Optional: [uv](https://github.com/astral-sh/uv)

```bash
git clone https://github.com/hackmods/cursor-proxmox-mcp.git
cd cursor-proxmox-mcp
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
cp proxmox-config/config.example.json proxmox-config/config.json
# Edit proxmox-config/config.json with host + token
```

### Verify

```bash
pytest
# or full local CI:
# Windows: .\scripts\ci-local.ps1
# Unix:    ./scripts/ci-local.sh
```

```bash
# Linux/macOS
PROXMOX_MCP_CONFIG="proxmox-config/config.json" python -m proxmox_mcp.server
# Windows PowerShell
$env:PROXMOX_MCP_CONFIG="proxmox-config\config.json"; python -m proxmox_mcp.server
```

## Configuration

### Proxmox API token

In the Proxmox UI: Datacenter → Permissions → API Tokens → Add. Grant roles appropriate for the tools you use (VM/CT allocate, datastore, Sys.Audit/Modify for HA/firewall/access).

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

### Cursor MCP

Add to Cursor MCP settings (path adjusted):

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

Restart the **proxmox** MCP server after pulling new tools.

`start.bat` is a manual fallback (avoid stdout noise for MCP stdio).

## Development / CI

```powershell
.\scripts\ci-local.ps1
```

GitHub Actions runs the same gate on push/PR (Python 3.10 + 3.12).

- Tests: `pytest`
- Lint: `ruff check src tests`
- After adding a tool: update `definitions.py`, README table, `.cursor/research/proxmox-api-coverage.md`, and `tests/expected_tools.py`

## Status

- [x] Formal multi-domain Proxmox API coverage (85 tools)
- [x] Snapshots, backups, migrate, HA, firewall, access, storage admin
- [x] Discovery QOL (`get_storage_content`, `get_next_vmid`, `get_task_status`)
- [x] Local + GitHub CI

## License

MIT

## Acknowledgments

Based on [ProxmoxMCP](https://github.com/RekklesNA/ProxmoxMCP-Plus) / [canvrno/ProxmoxMCP](https://github.com/canvrno/ProxmoxMCP). Extended for Cursor IDE as a formal Proxmox VE integration.
