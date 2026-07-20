# Revision log (living)

Chronological record of meaningful MCP / agent-UX revisions for future Cursor sessions.
Pair with [changelog-notes.md](changelog-notes.md) (research “why”) and root `CHANGELOG.md` (user-facing).

| Date | Rev | Summary | Tools | Key files / decisions |
|------|-----|---------|-------|------------------------|
| 2026-07-19 | r1 | Phase E baseline: LXC parity, `*_guest`, ops completeness | 152 | D1, next-expansion Phase E |
| 2026-07-19 | r2 | Agent feedback: fix LXC exec (SSH+pct), guest IP, QEMU/LXC UX | 153 | D4 revised; `get_lxc_network` |
| 2026-07-19 | r3 | Guest auth: ssh_public_keys, set_lxc_password/keys, honest create | **155** | D21; see agent-feedback-log |
| 2026-07-19 | r4 | Host SSH setup docs (keygen / authorized_keys / reload) | 155 | SETUP + wiki |
| 2026-07-19 | r5 | Post-1.1 QOL sweep: exec exit truth, UPID footers, force-delete wait, hints | **155** | D22, D23; v1.1.3 |
| 2026-07-19 | r4 | Docs: host SSH checklist (authorized_keys, overrides, reload) | 155 | SETUP + proxmox-config README; agent-feedback |
| 2026-07-19 | r6 | Tag v1.2.0: wait_for_task non-OK exitstatus test; first tag since v1.1.0 | **155** | Release; deferred create auto-wait / QEMU IP / Docker bake |
| 2026-07-19 | r7 | Wiki living guide: full tool catalog generator, Recipes, `_Footer.md`, CI lock | **155** | `docs/wiki/` + `scripts/generate-wiki-tools.py` |
| 2026-07-19 | r8 | Phase F LXC day-2: capabilities, prepare_docker, push/pull, paramiko core | **159** | D4 revised; D24; next-expansion Phase F done |
| 2026-07-19 | r9 | Phase F.1: get_vm_network, create wait=, push/pull_vm, deploy_static_nginx, probes | **163** | D25; next-expansion Phase F.1 done; v1.4.0 |
| 2026-07-19 | r10 | Community post tooling + D26 skip Phase C; release.yml Trusted Publisher docs | **163** | scripts/post-community.*; docs/community/; PUBLISHING |
| 2026-07-19 | r11 | Docker LXC Path B: crun fallback, feature_acl_denied, configure_lxc_dns, pct_set_lxc | **165** | D24 revised; prepare docker_mode=auto\|keyctl\|crun |
| 2026-07-19 | r12 | Post-r11: ACL UX, bootstrap_docker_lxc, SSH/status helpers, qm_set_vm, VM tags | **169** | Slices 1–5 roadmap |
| 2026-07-19 | r13 | provision_lxc + create_lxc onboot/tags/description; wget note | **170** | D27; CT110 agent feedback; **v1.5.0** |
| 2026-07-19 | r14 | CT111: deploy_node_app, tip reload footer, quorum lab note, ssh.timeout 120 | **171** | agent-feedback CT111; **v1.5.1** |

## How to update

When shipping a behavior change that agents will feel:

1. Append a row here (`rN`).
2. Add a dated section to `changelog-notes.md`.
3. If feedback-driven, append to `agent-feedback-log.md` (symptoms → root cause → fix → out of scope).
4. Update `proxmox-api-coverage.md` / `next-expansion.md` / `decisions.md` as needed.
5. Keep `tests/expected_tools.py` / `inventory.py` / README tool count in lockstep (D5).
