<!-- channel: reddit -->
<!-- version: 1.5.0 -->
<!-- tools: 170 -->

# Reddit — draft post

**Subreddit ideas:** r/Proxmox, r/selfhosted, r/cursor (where allowed)

**Title:** Cursor MCP for Proxmox VE — 170 tools (VM/LXC day-2, HA, firewall, backups)

**Body:**

Built [cursor-proxmox-mcp](https://github.com/hackmods/cursor-proxmox-mcp) so Cursor agents can operate a Proxmox lab end-to-end without leaving chat.

- **170 tools** (v1.5.0): QEMU + LXC lifecycle, guest-agent network/file helpers, `provision_lxc` + Docker-in-LXC bootstrap (keyctl/crun) + DNS + SSH + allowlisted `pct`/`qm set`, optional create `wait=`, snapshots/backups/jobs, migrate/HA, firewall + IPSets, users/tokens/ACL, replication, SDN/ACME read, pools, console tickets
- Install with `uvx cursor-proxmox-mcp` once on PyPI, or `uvx --from` a checkout / GHCR image
- First-run: [SETUP.md](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SETUP.md) (token + Privilege Separation notes + host SSH for LXC exec)

Happy to take feedback on ACL/token patterns and which heavy write APIs (SDN/ACME/Ceph) are worth exposing next.
