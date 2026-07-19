# Next expansion phases

Living Cursor note for what to build after the current **163-tool** baseline.
Update this file when priorities change; keep [proxmox-api-coverage.md](proxmox-api-coverage.md), [README.md](../../README.md), and [docs/api-coverage.md](../../docs/api-coverage.md) in sync.

**Baseline (done):** Formal Cursor ↔ Proxmox MCP — guest lifecycle, storage, HA, firewall, access, replication, SDN read, ACME read, pools, console tickets, inventory-locked CI.

**Phase D (done):** Agent QOL — `wait_for_task`, ISO/cloud-init/net on create, template/ISO helpers, token ACL helper, SETUP reload + nested Docker prompts, mcpo CI smoke, PyPI publish workflow.

**Phase E (done):** LXC↔VM parity + unified guest power + ops completeness — RRD/SPICE/suspend LXC, `*_guest` aliases, pending, pool membership, IPSet CIDRs, move disk, replication update, backup jobs.

**Phase F (done / v1.3.0):** LXC day-2 god mode — paramiko core, `get_mcp_capabilities`, `prepare_lxc_for_docker`, `push_to_lxc`/`pull_from_lxc`, SSH/exec QOL. Lab source: [agent-feedback-log.md](agent-feedback-log.md) (Lumon deploy).

**Phase F.1 (done / v1.4.0):** VM network + create `wait=` + guest-agent push/pull + `deploy_static_nginx` + opt-in container probes.

---

## Phase E — Agent ops completeness (shipped)

| Priority | Item | Status |
|----------|------|--------|
| P0 | Cursor MCP wiring (`uvx --from` checkout; kill wrong `proxmox-mcp-server` package) | done (operator reload) |
| P0 | `get_lxc_rrd_data`, `create_spice_ticket_lxc` | done |
| P0 | `suspend_lxc` / `resume_lxc` (CRIU warnings) | done |
| P0 | Additive `*_guest` power tools + `get_guest_status` | done |
| P1 | `get_guest_pending`, `move_guest_disk` | done |
| P1 | `update_pool`, IPSet CIDR CRUD | done |
| P1 | `update_replication_job`, `list/create/delete_backup_job` | done |

---

## Phase C — Heavy / deferred endpoints

Keep **out of Available Tools** until deliberately implemented. Full table also in [proxmox-api-coverage.md](proxmox-api-coverage.md).

| Area | Effort | Risk | When to pull forward |
|------|--------|------|----------------------|
| SDN write CRUD (zones/vnets/subnets) | Medium | Medium | Homelab SDN from chat; always pair with existing `apply_sdn` |
| ACME account create + order + renew | High | Secrets | Need DNS plugin creds in config — never log |
| Ceph OSD/MON/MGR create/destroy | High | Cluster-invasive | Prefer Ceph tooling unless operator insists |
| Cluster join / corosync bootstrap | High | No rollback | Almost never from MCP |
| Full VNC/SPICE websocket proxy | High | Poor MCP fit | Tickets only (D6) unless a client needs proxy |
| PBS direct admin | Medium | Separate product | Use `storage.type=pbs` until needed |
| Node reboot / shutdown | Low code, high risk | Host power | Needs explicit confirmation UX |
| Node network create/update/reload | Medium | Med | Bridge automation labs |
| QEMU agent helpers beyond exec | Low–med | Low | **F.1 shipped** network + file; richer agent APIs stay here |

---

## Phase F — LXC day-2 god mode (shipped v1.3.0)

| Priority | Item | Status |
|----------|------|--------|
| P0 | paramiko core dep + `[ssh]` alias; shared `require_host_ssh` | done |
| P0 | `get_mcp_capabilities` + boot warning | done |
| P0 | `PctExecutor` host cmds (`run_host`, push/pull, `pct set`/conf) | done |
| P0 | `prepare_lxc_for_docker` (host `lxc-pve` gate + dual AppArmor workaround) | done |
| P0 | `create_lxc(docker_ready=…)` tip only (D21 honest) | done |
| P1 | `push_to_lxc` / `pull_from_lxc` | done |
| P1 | Exec/SSH QOL: timeouts, field aliases, features pending footer | done |
| Docs | SETUP/Recipes success = `docker run`, not `docker --version` | done |

**Docker-in-LXC (D24):** CVE-2025-52881 / runc + nested AppArmor → prefer host `lxc-pve ≥ 6.0.5-2`; else dual raw lines via host conf + stop/start; never bare `unconfined`; Docker `--privileged`/`--sysctl` do not fix.

---

## Phase F.1 — VM parity + create wait + app helpers (shipped v1.4.0)

| Priority | Item | Effort | Risk / notes | Status |
|----------|------|--------|--------------|--------|
| P0 | `get_vm_network` (QEMU agent `network-get-interfaces`) | **S ~0.5d** | Best cheap VM↔LXC parity; fail clearly if agent down | done |
| P1 | `create_vm` / `create_lxc` optional `wait=true` (default **false**) | **S ~0.5d** | Preserves D10 UPID contract (D25) | done |
| P1 | `push_to_vm` / `pull_from_vm` (guest-agent file-write/read) | **M ~1–1.5d** | 32 MiB limit; agent required | done |
| P2 | `deploy_static_nginx` (LXC recipe) | **M ~0.5–1d** | Thin wrap over push + pct; Lumon unblocker | done |
| P2 | `get_containers` docker/`:80` probes | **M ~0.5–1d** | Opt-in `probes=true` only | done |

**Not done / deferred:** default-on create wait; default-on inventory probes; richer QEMU agent (fsfreeze, guest-info beyond network/file).

**Explicitly still out:** auto-wait default-on; merge LXC into `get_vms`; DHCP lease scraping; free-form raw LXC config; privileged CT / containerd downgrade as happy path.

---

## Soft DX (docs / CI)

| Item | Status |
|------|--------|
| Cursor MCP reload checklist after `git pull` | done (SETUP.md) — includes stale ~14-tool catalog symptom |
| Optional `mcpo` OpenAPI smoke in CI | done |
| Example agent prompts (nested Docker LXC, ISO VM) | done (SETUP.md) |

---

## Knowledge to keep in mind (reference these files)

| Insight | Where captured | Reminder |
|---------|----------------|----------|
| Privsep=Yes needs ACL on `user@realm!tokenid` | D8, SETUP.md, `get_token_permissions` | Empty lists ≠ “no VMs” — check token ACL first |
| SETUP.md is first-run SoT | D9 | README stays inventory + short install |
| Console = ticket mint only | D6 | No websocket proxy in MCP |
| uvx / `cursor-proxmox-mcp` preferred | D7 / D20 | Wrong PyPI name `proxmox-mcp-server` is a different project |
| Inventory lock | D5, `tests/expected_tools.py` | Every new tool updates README + coverage + expected_tools |
| LXC exec requires opt-in SSH + `pct exec` (no REST) | D4, agent-feedback-log, SETUP | Fail clearly without ssh; never call fake `/lxc/.../exec` |
| Guest IP: configured netN always; runtime via pct / agent | get_lxc_network / get_vm_network | DHCP without SSH → static IP or enable SSH; VM needs qemu-guest-agent |
| LXC `/exec` version-dependent | ~~obsolete~~ | Superseded by D4 revision 2026-07-19 |
| Docker-in-LXC AppArmor / CVE-2025-52881 | Phase F / D24 | Host `lxc-pve` patch first; dual workaround only if unpatched |
| Create returns UPID immediately | D10 / D22 / D25 | Default: `wait_for_task`; optional `wait=true` on create (default false) |
| LXC suspend/resume is CRIU best-effort | Phase E | Prefer shutdown; warn in tool text |
| Parallel `*_vm`/`*_lxc` + additive `*_guest` | D1 | Do not rename power tools in minor releases |
| Destructive ops need force + warnings | D2 | Keep pattern for new delete/power tools |

---

## Suggested next work

```text
1. Configure PyPI Trusted Publisher for cursor-proxmox-mcp → re-run publish.yml (see PUBLISHING.md)
2. Official MCP registry: mcp-publisher publish after PyPI upload
3. Glama submit + community drafts in docs/community/
4. Only then: SDN write or ACME write if a real use case appears (Phase C)
```

When shipping any new tool: update this file’s status, coverage matrix, changelog-notes, README, and `expected_tools.py` in the same change (api-coverage + keep-docs-aligned rules).
