# Cursor forum — draft post

**Title:** Formal Proxmox VE MCP for Cursor — 153 tools (QEMU, LXC, storage, HA, firewall)

**Body:**

Hi — sharing [hackmods/cursor-proxmox-mcp](https://github.com/hackmods/cursor-proxmox-mcp), a production-oriented MCP server that wires Cursor agents to Proxmox VE.

**Highlights**
- 153 tools: VMs/LXC lifecycle + config, unified `*_guest` power tools, snapshots/backups (incl. scheduled jobs), migrate/HA, firewall (IPSet CIDRs), access/ACL, replication, SDN/ACME (read), pools, console tickets
- Install: `uvx cursor-proxmox-mcp` (PyPI) or `uvx --from <checkout> cursor-proxmox-mcp` / Docker from GHCR
- Config via `PROXMOX_MCP_CONFIG` JSON; secrets via `${ENV}` interpolation
- Security hardening in 1.x: log redaction, typed errors, optional exec allowlist, SSL defaults on

**Setup:** [SETUP.md](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SETUP.md) · [Wiki](https://github.com/hackmods/cursor-proxmox-mcp/wiki)

Feedback welcome — especially around token/privsep patterns and which write APIs you’d want next.
