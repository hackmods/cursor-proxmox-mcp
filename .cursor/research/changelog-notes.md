# Changelog / research notes

## 2026-07-19 — Polish for next version bump (docs/wiki + QOL)

**Why:** Prepare repo surface for a user-cut 1.1.0 without bumping `pyproject.toml` yet.

**Shipped:**
- `docs/wiki/` Home/Setup/Tools/Troubleshooting/_Sidebar + sync scripts
- Community drafts + Cursor MCP example + GitHub repo description → 152 tools
- Config-update responses hint `get_guest_pending` + reboot
- README guest-type guidance; CONTRIBUTING/PUBLISHING wiki sync steps
- Extra formatter / guest_power unit tests

**Operator:** Create first GitHub wiki page in the UI once, then `scripts/sync-wiki.ps1`.

## 2026-07-19 — Phase E LXC parity + guest power + ops APIs (152 tools)

**Why:** Cursor’s live MCP catalog was stuck at ~14 tools while the checkout already had full LXC lifecycle; agents also lacked LXC RRD/SPICE, unified `guest_type` power aliases, pending config, pool membership, IPSet CIDRs, disk move, replication update, and scheduled backup jobs.

**Shipped:**
- Operator wiring: `~/.cursor/mcp.json` → `uvx --from <checkout> cursor-proxmox-mcp` + `PROXMOX_MCP_CONFIG` only; kill leftover Gethos `uvx proxmox-mcp-server`
- LXC: `suspend_lxc` / `resume_lxc` (CRIU warnings), `get_lxc_rrd_data`, `create_spice_ticket_lxc`
- Additive guest tools: `start/stop/shutdown/reboot/delete_guest`, `get_guest_status`, `get_guest_pending`, `move_guest_disk`
- Ops: `update_pool`, IPSet CIDR list/add/delete, `update_replication_job`, `list/create/delete_backup_job`
- D1 updated: parallel `*_vm`/`*_lxc` retained; `*_guest` is additive

**Quirks:**
- Cursor may keep a stale tool snapshot until Disable/Enable or full quit — SETUP checklist documents the ~14-tool symptom
- LXC suspend/resume is not production-grade CRIU; prefer shutdown
- `reset_lxc` intentionally omitted (use `reboot_lxc`)

## 2026-07-19 — v1.0.1 publish QoL (PyPI name collision)

**Why:** `proxmox-mcp-server` on PyPI is owned by another project; v1.0.0 Trusted Publish failed (`invalid-publisher`) and bare `uvx proxmox-mcp-server` would install the wrong package.

**Shipped:**
- Package rename to `cursor-proxmox-mcp` + console script of the same name
- Single PyPI path via `publish.yml` + `environment: pypi`; `release.yml` only GHCR + GitHub Release
- `server.json` / `glama.json` / `PUBLISHING.md` / community drafts; README `mcp-name` marker
- Decision D20

**Still manual:** configure PyPI Trusted Publisher claims; `mcp-publisher login github && publish`; submit Glama; post community drafts; enable branch protection.

## 2026-07-19 — Phase D agent QOL + Soft DX

**Why:** Agents raced UPIDs, guessed templates, and hit privsep empty-maps; create paths hardcoded vmbr0/DHCP.

**Shipped tools/params:**
- `wait_for_task` — poll UPID until stopped
- `create_vm` / `update_vm_config` — ISO/CDROM, boot, cloud-init, bridge/net0
- `create_lxc` — optional ostemplate (auto-pick), bridge/ip/gw/net0, `ostemplate_filter`
- `list_os_templates`, `list_isos`, `get_token_permissions`
- Soft DX: SETUP MCP reload checklist, nested Docker LXC prompt, mcpo CI smoke
- PyPI: package rename to `proxmox-mcp-server` v0.3.0 + `publish.yml`

**Quirks:**
- Privsep=Yes empty perms → ACL `user@realm!tokenid` (use `get_token_permissions`)
- Cloud-init drive + pure LVM: API may accept ci* keys; drive placement best-effort
- First bare `uvx cursor-proxmox-mcp` needs a GitHub Release + PyPI Trusted Publishing

## 2026-07-19 — Next-expansion roadmap note

**Why:** Capture post-128-tool priorities so agents don’t invent scope. Prefer Phase D create/wait QOL over Phase C heavy admin.

**Shipped docs:**
- `.cursor/research/next-expansion.md` — Phase D + Phase C + knowledge index + implementation order
- `.cursor/rules/next-expansion.mdc` — point agents at the roadmap
- Decisions D10 (Phase D bias), D11 (create hardcodes)
- README / docs/api-coverage / coverage matrix Planned sections updated

## 2026-07-19 — Setup guide + Privilege Separation depth

**Why:** First-run auth is the #1 footgun. Virtualization Howto–style walkthroughs and this fork’s JSON config differ; operators often disable Privilege Separation without knowing why.

**Shipped docs:**
- `SETUP.md` — token/user/ACL walkthrough, privsep Yes vs No, realms, verify/`get_permissions`, network/SSL, config mistakes, project vs user `mcp.json`, rotation
- `proxmox-config/README.md` — config field reference next to the example JSON
- `.cursor/rules/proxmox-auth.mdc` — keep auth docs and `create_token` defaults aligned
- Decisions D8 (privsep), D9 (SETUP as first-run SoT)

**Operator quirk:** privsep=Yes + ACL only on the **user** → token auth “works” but returns empty/`403`. Fix = ACL the **token** (`user@realm!tokenid`), not disable privsep (unless lab shortcut).

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
