<!-- channel: cursor-forum -->
<!-- version: 1.7.0 -->
<!-- tools: 207 -->

# Cursor forum — draft post

**Title:** Formal Proxmox VE MCP for Cursor — 207 tools (SDN write, ACME, Ceph, PBS)

**Body:**

Hi — sharing [hackmods/cursor-proxmox-mcp](https://github.com/hackmods/cursor-proxmox-mcp), a production-oriented MCP server that wires Cursor agents to Proxmox VE.

**Highlights**
- 207 tools (v1.7.0): VMs/LXC lifecycle + day-2 helpers, SDN **write** + apply, ACME order/renew, Ceph status + pool CRUD, PBS storage plugin + status, node network CRUD, `get_console_connection` (tickets only — D6), HA/firewall/access/replication/pools
- Install: `uvx cursor-proxmox-mcp` (PyPI) or `uvx --from <checkout> cursor-proxmox-mcp` / Docker from GHCR
- Config via `PROXMOX_MCP_CONFIG` JSON; secrets via `${ENV}` interpolation; opt-in host SSH for LXC `pct` day-2
- Security hardening in 1.x: log redaction, typed errors, optional exec allowlist, SSL defaults on

**Setup:** [SETUP.md](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SETUP.md) · [Wiki](https://github.com/hackmods/cursor-proxmox-mcp/wiki)

Feedback welcome — especially around token/privsep patterns.
