# Reddit — draft post

Suggested subs: `r/Proxmox`, `r/homelab`, `r/mcp` (and Cursor-related communities if appropriate). Keep one primary post; cross-post sparingly.

**Title:** Open-source Cursor MCP for Proxmox VE (132 tools) — uvx install

**Body:**

I maintain [cursor-proxmox-mcp](https://github.com/hackmods/cursor-proxmox-mcp) — an MCP server so Cursor (and other MCP clients) can manage Proxmox VE: QEMU/LXC, storage, snapshots/backups, HA, firewall, ACLs, etc.

```bash
uvx cursor-proxmox-mcp
```

Point `PROXMOX_MCP_CONFIG` at a JSON config with host + API token (privsep recommended). Full setup: https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SETUP.md

Note: PyPI package name is **`cursor-proxmox-mcp`** (there is a differently named `proxmox-mcp-server` package that is not this project).

Happy to take feedback from homelab / ops folks using agent tooling against their clusters.
