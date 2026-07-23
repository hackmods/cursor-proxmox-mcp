# Changelog / research notes

## 2026-07-23 — Phase C light + QEMU/cloud-init (rev r16) — 179 tools

**Why:** Roadmap leftovers requested: QEMU agent stretch, `bootstrap_cloudinit_vm`, host reboot/shutdown, cluster join — while keeping SDN/ACME/Ceph/VNC/PBS deferred.

**Shipped:** `get_vm_guest_info`, `fsfreeze_vm`, `fsthaw_vm`; `bootstrap_cloudinit_vm` (clone_from required); `reboot_node`/`shutdown_node` (`confirm==node`); `get_cluster_join_info`/`join_cluster` (`confirm=JOIN`); D29 typed confirm; D26 revised.

**Out of scope:** SDN write, ACME write, Ceph, VNC proxy, PBS, node network CRUD, cloud-image download/import, default-on create wait.

## 2026-07-23 — Tool-call audit + logging QOL (rev r15) — 171 tools

**Why:** `podcast-shorts-factory/proxmox_mcp.log` showed only MCP handshake (ListTools/ListResources) across three startups — zero `CallToolRequest` lines — so usage reviews could not drive enhancements. Root cause: no structured tool invocation logging; DEBUG also drowned in urllib3/asyncio/MCP framework noise.

**Shipped:** Wrap FastMCP `ToolManager.call_tool` → `tool_call name=… ok=… duration_ms=…` (+ safe identity args); `LoggingConfig.verbose` / `tool_calls` / `console_level` / `quiet_libraries` / `http_debug`; env overrides `PROXMOX_MCP_VERBOSE` / `LOG_LEVEL` / `TOOL_CALLS` / `CONSOLE_LEVEL`; capabilities reports logging; D28.

**Out of scope:** Logging full command bodies / file contents by default; raising console above ERROR by default; changing tool inventory.

## 2026-07-19 — CT111 hygiene + deploy_node_app (rev r14) — 171 tools

**Why:** CT111 behind7proxies Next.js deploy — stale Cursor catalog made Phase F tip names look like ghost tools; private git clone failed; no Node recipe; quorum NOT OK on 1-node lab; ssh.timeout 30 opaque for apt/npm.

**Shipped:** `deploy_node_app`; create_lxc tip reload footer + private→push + password-optional; curl→wget on deploy tips; single-node quorum lab note; default `ssh.timeout` 120; `__version__` align.

**Out of scope:** Auto-wait on create; free-form host shell; baking Node into create_lxc; git-token clone helper; returning create passwords.

## 2026-07-19 — provision_lxc + create knobs (rev r13) — 170 tools

**Why:** CT110 lab feedback — create→start→SSH→IP took ~8 tool calls; password at create ≠ SSH login (Debian `prohibit-password`); create lacked tags/onboot/description; curl missing on stock Debian.

**Shipped:** `provision_lxc` (create wait → start wait → optional `configure_lxc_ssh` → runtime IP JSON); `create_lxc` `onboot`/`description`/`tags`; execute_lxc_command wget tip; D27.

**Out of scope:** Returning create password in output; folding Docker into provision; default-on create wait; `http_check_lxc` tool.

## 2026-07-19 — Post-r11 expansion slices 1–5 (rev r12) — 169 tools

**Why:** Close remaining FeedForge-style agent gaps after crun Path B: structured ACL UX everywhere mutations fail, one-shot Docker LXC orchestrator, SSH/status helpers, QEMU host escape hatch, VM tag/description/onboot parity.

**Shipped:** `acl_denied_message` + `_handle_mutation_error` (HA/firewall/access/SDN/VM); `configure_lxc_ssh`, `get_docker_lxc_status`, `bootstrap_docker_lxc`; `qm_set_vm`; create/update VM `onboot`/`description`/`tags`.

**Out of scope:** Phase C; free-form host shell; `bootstrap_cloudinit_vm`; privileged CT.

## 2026-07-19 — Docker LXC crun Path B (rev r11) — 165 tools

**Why:** FeedForge CT107 lab — `keyctl=1` 403 under privsep token; stock runc fails without keyctl (`ip_unprivileged_port_start`); gateway DNS/IPv6 flaky; no host `pct set` escape hatch for agents.

**Shipped:** `prepare_lxc_for_docker(docker_mode=auto|keyctl|crun)` with pinned crun 1.21 default-runtime; structured `feature_acl_denied` on `update_lxc_features` / prepare; `configure_lxc_dns`; allowlisted `pct_set_lxc`; `create_lxc` `nameserver`/`searchdomain` + docker_ready keyctl→nesting retry (`needs_crun`); D24 Path A/B.

**Out of scope:** `bootstrap_docker_lxc` orchestrator; free-form `execute_host_command`; privileged CT happy path; auto-install Docker on create.

## 2026-07-19 — Community announce tooling (rev r10) — 163 tools

**Why:** Make release announcements repeatable; keep Phase C deferred (D26).

**Shipped:** `docs/community/` normalized drafts + README; `scripts/community_drafts.py` + `post-community.ps1`/`.sh` (`-Check` / `-Open` / `-CreateDiscussion`); PUBLISHING community section; D26.

**Operator:** ~~add PyPI Trusted Publisher for `release.yml` + `pypi`~~ — **done** 2026-07-19. `publish.yml` remains registered for manual retry.

## 2026-07-19 — Phase F.1 VM parity + create wait (rev r9 / v1.4.0) — 163 tools

**Why:** Close Lumon/F.1 deferrals — VM network parity, optional create wait, guest-agent file push, static nginx recipe, opt-in inventory probes.

**Shipped:** `get_vm_network`; `push_to_vm`/`pull_from_vm`; `deploy_static_nginx`; `create_vm`/`create_lxc` `wait=` (default false, D25); `get_containers(probes=true)`.

**Out of scope:** default-on wait; default-on probes; richer QEMU agent beyond network/file.

## 2026-07-19 — Phase F LXC day-2 god mode (rev r8 / v1.3.0) — 159 tools

**Why:** Lumon CT122 lab: pct exec + password SSH worked; Docker CE installed but `docker run` failed (`ip_unprivileged_port_start`); no MCP push/prepare; paramiko optional extra + stale MCP friction.

**Shipped:** paramiko core; `get_mcp_capabilities`; `prepare_lxc_for_docker` (D24); `push_to_lxc`/`pull_from_lxc`; `docker_ready` on create; SSH/exec QOL (timeouts, output/error aliases, startup warning); SETUP/Recipes rewrite.

**Out of scope (~~Phase F.1~~ shipped r9):** was `get_vm_network`, create `wait=`, `push_to_vm`, `deploy_static_nginx`, inventory probes.

## 2026-07-19 — Phase F / F.1 pipeline queued (planning)

**Why:** First successful Cursor↔Proxmox MCP lab deploy (Lumon CT122) proved pct exec + password SSH, then hit Docker-in-LXC AppArmor/CVE gap and missing push/prepare tools. Sized deferred parity items for the expansion pipeline.

**Queued (not shipped):**

- ~~**Phase F**~~ — **shipped r8 / v1.3.0**
- ~~**Phase F.1**~~ — **shipped r9 / v1.4.0**

**Insights locked:** Docker `--privileged`/`--sysctl` do not fix `ip_unprivileged_port_start`; prefer host `lxc-pve ≥ 6.0.5-2`; unpatched hosts need **both** AppArmor workaround lines + stop/start; bare `unconfined` overrides nesting.

**Out of scope (kept):** default-on create auto-wait; default-on inventory probes.

## 2026-07-19 — Wiki living guide (rev r7) — 155 tools

**Why:** Wiki only summarized domains; agents/operators needed a durable guide with every tool listed and a site-wide git footer.

**Shipped:** `scripts/generate-wiki-tools.py`; full `Tools.md` inventory; `Recipes.md`; `_Footer.md`; expanded Home/Setup/Troubleshooting; `tests/test_wiki_tools.py`; sync via `scripts/sync-wiki.*`.

**Out of scope:** New MCP tools; auto-wait / QEMU IP / Docker-in-create.

## 2026-07-19 — Release v1.2.0 (rev r6) — 155 tools

**Why:** 1.1.1–1.1.3 landed on `main` but were never tagged; PyPI/GHCR still at v1.1.0. Ship a tagged 1.2.0 that includes that line plus a `wait_for_task` non-OK `exitstatus` unit test.

**Shipped:** Version bump (`pyproject.toml`, `__init__.py`, `server.json`); CHANGELOG/README; `test_wait_for_task_non_ok_exitstatus`.

**Out of scope (unchanged):** auto-wait inside `create_*`; QEMU IP on `get_vms`; baking Docker into create.

## 2026-07-19 — Post-1.1 QOL sweep (rev r5 / v1.1.3) — 155 tools

**Why:** After LXC P0/P1 fixes (r2/r3), a full-tool audit found the same honesty/UX patterns across ~150 tools that were never lab-exercised: false SUCCESS on guest exec, force-delete races, missing `wait_for_task` copy, asymmetric VM/LXC hints, soft destructive responses, empty-list ACL silence.

**Shipped:**
- P0: `execute_vm_command` honors guest-agent exit code
- Force-delete: stop → `wait_for_upid` → delete
- Shared helpers: `upid_response_footer`, `lxc_not_found_message`, `destructive_warning`, `privsep_empty_hint`, `validate_download_url`
- D22 / D23; additive `download_url_to_storage` verify/checksum params

**Out of scope:** auto-wait inside create; QEMU IP on `get_vms`; Phase C SDN/HA CRUD expansion.

## 2026-07-19 — Host SSH setup docs (rev r4) — 155 tools

**Why:** Lab operator enabled `ssh` + `host_overrides` in config but still could not use host `pct exec` — missing public key on the node and no MCP reload after config change. Docs described the schema, not the end-to-end trust loop.

**Shipped (docs only):** Full SETUP SSH checklist (keygen, node `authorized_keys`, worked `host_overrides`, verify `pct version`, reload MCP); host-trust in `proxmox-config/README.md`; README + wiki Troubleshooting/Setup; agent-feedback entry.

**Out of scope:** Auto-install of host keys; `SSHConfig` schema changes.

## 2026-07-19 — LXC guest auth + honest bootstrap (rev r3 / v1.1.2) — 155 tools

**Why:** Agents set `password=` on create but guest SSH still failed; still saw 501 `/exec`; empty nesting CT mistaken for deployed Docker host; no post-create password/key path.

**Root causes:**
- Create-time password is applied by Proxmox, but stock templates often use `PermitRootLogin prohibit-password` — password SSH fails even when password is correct
- No REST to reset password/keys after create; no `ssh-public-keys` on MCP create before this rev
- 501 = Cursor still on pre-1.1.1 REST `/exec` client OR misunderstanding; current code never calls that path
- Create success text oversold Docker readiness

**Shipped:** `ssh_public_keys` on create; `set_lxc_password` / `set_lxc_ssh_keys`; hostname collision warning; honest Next steps; D21; Docker recipe in SETUP; agent-feedback + revisions updates

**Out of scope:** Auto-install Docker on create; auto-wait on create; guest SSH without host pct when keys weren’t injected at create and ssh config is off

## 2026-07-19 — Agent LXC UX (rev r2 / v1.1.1) — 153 tools

**Why:** Lab agent hit 501 on `execute_lxc_command`, could not discover DHCP IP, confused `get_vms` vs LXC, raced create UPID, and misused `*_vm` on CT IDs.

**Root cause:** Fake REST `/lxc/{vmid}/exec` does not exist upstream; only `pct exec` on the node. IP/list gaps and soft docs amplified the failure.

**Shipped:**
- Opt-in `ssh` config + `PctExecutor` (`paramiko` optional extra)
- Rewrite `execute_lxc_command`; allowlist parity with VM exec
- `get_lxc_network`; configured IP on `get_containers` / `get_lxc_status`
- QEMU-not-found hints; louder create → `wait_for_task`
- Living trackers: `revisions.md`, `agent-feedback-log.md`; D4 revised

**Out of scope (logged):** auto-wait on create; merge get_vms; silent guest auto-detect; DHCP lease scraping; QEMU agent network helper.

**Quirks:**
- Without SSH, LXC exec and runtime IP remain unavailable by design
- keyctl still privilege-gated; we do not strip flags
- Reload Cursor MCP after pull to see 153 tools / new descriptions

## 2026-07-19 — Release v1.1.0

Tagged release: 152-tool Phase E + wiki/docs polish. PyPI Trusted Publisher + MCP/Glama submissions already in place.

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
