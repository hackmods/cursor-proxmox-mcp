<!-- channel: github -->
<!-- version: 1.4.0 -->
<!-- tools: 163 -->

# GitHub Discussion — draft (Announcements)

**Title:** cursor-proxmox-mcp v1.4.0 — 163 tools (LXC day-2 + VM network/push)

**Body:**

## Summary

**[cursor-proxmox-mcp](https://github.com/hackmods/cursor-proxmox-mcp)** v1.4.0 is on [PyPI](https://pypi.org/project/cursor-proxmox-mcp/1.4.0/) and GHCR (`ghcr.io/hackmods/cursor-proxmox-mcp:1.4.0`).

**163 tools** covering QEMU/LXC lifecycle, guest-agent network + file push/pull, LXC prepare-Docker / `pct` push / `deploy_static_nginx`, optional create `wait=`, snapshots/backups/jobs, migrate/HA, firewall + IPSets, access/ACL, replication, SDN/ACME (read), pools, and console tickets.

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
- [Release notes](https://github.com/hackmods/cursor-proxmox-mcp/releases/tag/v1.4.0)

Feedback welcome on token/privsep patterns and which write APIs to prioritize next (Phase C stays deferred).
