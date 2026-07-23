<!-- channel: github -->
<!-- version: 1.5.2 -->
<!-- tools: 171 -->

# GitHub Discussion — draft (Announcements)

**Title:** cursor-proxmox-mcp — 171 tools (deploy_node_app + CT111 hygiene)

**Body:**

## Summary

**[cursor-proxmox-mcp](https://github.com/hackmods/cursor-proxmox-mcp)** is on [PyPI](https://pypi.org/project/cursor-proxmox-mcp/) and GHCR (`ghcr.io/hackmods/cursor-proxmox-mcp`).

**171 tools** covering QEMU/LXC lifecycle, guest-agent network + file push/pull, LXC `provision_lxc` / `bootstrap_docker_lxc` (keyctl or crun), `deploy_static_nginx` / `deploy_node_app`, `configure_lxc_dns`/`configure_lxc_ssh`, `pct_set_lxc`/`qm_set_vm`, structured ACL denials, optional create `wait=`, snapshots/backups/jobs, migrate/HA, firewall + IPSets, access/ACL, replication, SDN/ACME (read), pools, and console tickets.

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
- [Release notes](https://github.com/hackmods/cursor-proxmox-mcp/releases/tag/v1.5.2)

Feedback welcome on token/privsep patterns and which write APIs to prioritize next (Phase C stays deferred).
