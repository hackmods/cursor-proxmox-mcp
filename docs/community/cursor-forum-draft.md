# Cursor forum — draft post

**Title:** Formal Proxmox VE MCP for Cursor — 132 tools (QEMU, LXC, storage, HA, firewall)

**Body:**

Hi — sharing [hackmods/cursor-proxmox-mcp](https://github.com/hackmods/cursor-proxmox-mcp), a production-oriented MCP server that wires Cursor agents to Proxmox VE.

**Highlights**
- 132 tools: VMs/LXC lifecycle + config, snapshots/backups, migrate/HA, firewall, access/ACL, replication, SDN/ACME (read), pools, console tickets
- Install: `uvx cursor-proxmox-mcp` (PyPI) or Docker from GHCR
- Config via `PROXMOX_MCP_CONFIG` JSON; secrets via `${ENV}` interpolation
- Security hardening in 1.x: log redaction, typed errors, optional exec allowlist, SSL defaults on

**Setup:** [SETUP.md](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SETUP.md)

Feedback welcome — especially around token/privsep patterns and which write APIs you’d want next.
