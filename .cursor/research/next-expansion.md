# Next expansion phases

Living Cursor note for what to build after the current **153-tool** baseline.
Update this file when priorities change; keep [proxmox-api-coverage.md](proxmox-api-coverage.md), [README.md](../../README.md), and [docs/api-coverage.md](../../docs/api-coverage.md) in sync.

**Baseline (done):** Formal Cursor ↔ Proxmox MCP — guest lifecycle, storage, HA, firewall, access, replication, SDN read, ACME read, pools, console tickets, inventory-locked CI.

**Phase D (done):** Agent QOL — `wait_for_task`, ISO/cloud-init/net on create, template/ISO helpers, token ACL helper, SETUP reload + nested Docker prompts, mcpo CI smoke, PyPI publish workflow.

**Phase E (done):** LXC↔VM parity + unified guest power + ops completeness — RRD/SPICE/suspend LXC, `*_guest` aliases, pending, pool membership, IPSet CIDRs, move disk, replication update, backup jobs.

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
| QEMU agent helpers beyond exec | Low–med | Low | Richer guest introspection |

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
| Guest IP: configured netN always; runtime via pct | get_lxc_network | DHCP without SSH → static ip or enable SSH |
| LXC `/exec` version-dependent | ~~obsolete~~ | Superseded by D4 revision 2026-07-19 |

| LXC suspend/resume is CRIU best-effort | Phase E | Prefer shutdown; warn in tool text |
| Parallel `*_vm`/`*_lxc` + additive `*_guest` | D1 | Do not rename power tools in minor releases |
| Destructive ops need force + warnings | D2 | Keep pattern for new delete/power tools |

---

## Suggested next work

```text
1. Operator: enable config ssh + paramiko for lab LXC exec / DHCP IP workflows
2. Configure PyPI Trusted Publisher for `cursor-proxmox-mcp` → re-run publish.yml (see PUBLISHING.md)
3. Official MCP registry: `mcp-publisher publish` after PyPI upload
4. Glama submit + community drafts in docs/community/
5. Only then: SDN write or ACME write if a real use case appears (Phase C)
6. Soft: QEMU agent/network-get-interfaces (parity with get_lxc_network)
```

When shipping any new tool: update this file’s status, coverage matrix, changelog-notes, README, and `expected_tools.py` in the same change (api-coverage + keep-docs-aligned rules).
