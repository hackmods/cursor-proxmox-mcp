# Changelog / research notes

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
