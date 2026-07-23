<!-- channel: github -->
<!-- version: 1.7.0 -->
<!-- tools: 207 -->

# GitHub Discussion — draft (Announcements)

**Title:** cursor-proxmox-mcp — 207 tools (Phase C: SDN / ACME / Ceph / PBS / node net)

**Body:**

## Summary

**[cursor-proxmox-mcp](https://github.com/hackmods/cursor-proxmox-mcp)** is on [PyPI](https://pypi.org/project/cursor-proxmox-mcp/) and GHCR (`ghcr.io/hackmods/cursor-proxmox-mcp`).

**207 tools** covering QEMU/LXC lifecycle, guest-agent helpers, LXC day-2 (`provision_lxc` / Docker Path B / deploy recipes), SDN **write** + apply, ACME account/plugin + order/renew, Ceph status + pool CRUD, PBS as PVE storage + status, node network CRUD/reload, `get_console_connection` (ticket hints — no websocket proxy), plus HA/firewall/access/replication/pools.

## Install

```bash
uvx cursor-proxmox-mcp
# or checkout:
uvx --from /path/to/cursor-proxmox-mcp cursor-proxmox-mcp
```

Set `PROXMOX_MCP_CONFIG` to your config JSON. Day-2 LXC (`pct` exec / prepare / push) needs opt-in host SSH — see [SETUP.md](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SETUP.md).

## Docs

- [SETUP.md](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SETUP.md)
- [Wiki](https://github.com/hackmods/cursor-proxmox-mcp/wiki)
- [Release notes](https://github.com/hackmods/cursor-proxmox-mcp/releases/tag/v1.7.0)

Feedback welcome — Ceph OSD/MON create and full PBS product admin stay out of scope on purpose.
