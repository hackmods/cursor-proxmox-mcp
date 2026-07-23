<!-- channel: reddit -->
<!-- version: 1.7.0 -->
<!-- tools: 207 -->

# Reddit — draft post

**Subreddit ideas:** r/Proxmox, r/selfhosted, r/cursor (where allowed)

**Title:** Cursor MCP for Proxmox VE — 207 tools (SDN/ACME/Ceph/PBS + day-2 LXC)

**Body:**

Built [cursor-proxmox-mcp](https://github.com/hackmods/cursor-proxmox-mcp) so Cursor agents can operate a Proxmox lab end-to-end without leaving chat.

- **207 tools** (v1.7.0): QEMU + LXC lifecycle, guest-agent helpers, `provision_lxc` + Docker-in-LXC + deploy recipes, SDN zone/vnet/subnet write + apply, ACME account/plugin + order/renew, Ceph status/pools, PBS as PVE storage + status, node network CRUD/reload, console ticket helper (no websocket proxy), HA/firewall/access/replication
- Install with `uvx cursor-proxmox-mcp` once on PyPI, or `uvx --from` a checkout / GHCR image
- First-run: [SETUP.md](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SETUP.md) (token + Privilege Separation notes + host SSH for LXC exec)

Happy to take feedback on ACL/token patterns. Ceph OSD create and full PBS product admin stay intentionally out of scope.
