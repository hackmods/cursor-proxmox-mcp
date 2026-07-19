# Changelog / research notes

## 2026-07-19 — Phase B + uvx QOL

**Why:** Document the real local install path (`uvx` / `proxmox-mcp-server`) and close remaining safe/read-heavy API gaps (replication, SDN read, ACME read, certs, console tickets, pools, firewall aliases/ipsets).

**Shipped:**
- Console scripts: `proxmox-mcp` + `proxmox-mcp-server` (alias); optional `.[openapi]` extra
- New modules: `replication`, `acme`, `sdn`, `pool`
- Extended: node (subscription/certs/report/services/time/wol), firewall (aliases/ipsets/macros), vm/lxc (status, tickets, RRD), cluster (version/resources/log/options)
- Tests: `test_phase_b_tools.py`, `test_smoke.py`; CI inventory floor ≥100 + entrypoint smoke
- README install paths: uvx → uv → pip + troubleshooting

**API quirks:**
- Console tools mint tickets only — clients must open VNC/SPICE themselves
- SDN `apply_sdn` is PUT `/cluster/sdn` (applies pending; does not create zones)
- Replication job ids look like `100-0` (vmid-jobindex)
- ACME order/renew deferred (DNS plugin secrets)

## 2026-07-19 — Formal API expansion

**Why:** Promote this fork from a personal VM/LXC toolkit to a formal Cursor ↔ Proxmox VE MCP covering reasonable API surface (migrate, HA, firewall, access, storage admin) plus QOL discovery tools.

**Shipped:**
- New modules: tasks, snapshot, backup, migrate, ha, firewall, access, network, guest helper
- Expanded: storage (content + CRUD + download-url), cluster (nextid), vm/container (config, clone, resize, template, reboot/suspend)
- CI: GitHub Actions + `scripts/ci-local.ps1` / `ci-local.sh`
- Inventory lock: `tests/expected_tools.py`

**API quirks found:**
- LXC `/exec` availability varies by PVE version
- HA and firewall often need elevated privileges beyond typical API tokens
- Storage create params are type-specific (dir vs nfs vs rbd)
- vzdump restore routes through qemu/lxc create with `archive=`

**False docs removed:** README previously claimed snapshot capabilities without tools.
