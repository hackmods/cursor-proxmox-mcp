# cursor-proxmox-mcp

Formal **Cursor ↔ Proxmox VE** MCP server — **153 tools** for QEMU VMs, LXC, storage, HA, firewall, access, replication, SDN (read), ACME (read), pools, and console tickets.

| Doc | Link |
|-----|------|
| Setup (first run) | [Setup](Setup) · full guide in repo [`SETUP.md`](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SETUP.md) |
| Tool map | [Tools](Tools) · [`docs/api-coverage.md`](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/docs/api-coverage.md) |
| Troubleshooting | [Troubleshooting](Troubleshooting) |
| Publishing | [`PUBLISHING.md`](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/PUBLISHING.md) |

## Quick install

```bash
# After PyPI publish:
uvx cursor-proxmox-mcp

# From a local checkout (dev):
uvx --from /path/to/cursor-proxmox-mcp cursor-proxmox-mcp
```

Set `PROXMOX_MCP_CONFIG` to an absolute path to `config.json` (see Setup).

**Package name:** always install **`cursor-proxmox-mcp`**. The unrelated PyPI project `proxmox-mcp-server` is a different codebase.

## Suggested agent flow

1. `get_next_vmid` → `list_os_templates` / `list_isos` → `list_node_networks`
2. `create_lxc` / `create_vm` → `wait_for_task` → start (`start_lxc` / `start_vm`, or `start_guest` with `guest_type`)
3. After config edits: `get_guest_pending` → reboot if needed
4. `create_snapshot` before risky changes

## Source of truth

Registered tools live in `tools/register.py` / `tools/inventory.py` (CI-locked). This wiki is mirrored from [`docs/wiki/`](https://github.com/hackmods/cursor-proxmox-mcp/tree/main/docs/wiki) in the repo — sync with `scripts/sync-wiki.ps1` or `scripts/sync-wiki.sh`.
