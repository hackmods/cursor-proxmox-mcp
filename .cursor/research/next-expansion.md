# Next expansion phases

Living Cursor note for what to build after the current **132-tool** baseline.
Update this file when priorities change; keep [proxmox-api-coverage.md](proxmox-api-coverage.md), [README.md](../../README.md), and [docs/api-coverage.md](../../docs/api-coverage.md) in sync.

**Baseline (done):** Formal Cursor ↔ Proxmox MCP — guest lifecycle, storage, HA, firewall, access, replication, SDN read, ACME read, pools, console tickets, inventory-locked CI.

**Phase D (done):** Agent QOL — `wait_for_task`, ISO/cloud-init/net on create, template/ISO helpers, token ACL helper, SETUP reload + nested Docker prompts, mcpo CI smoke, PyPI publish workflow.

---

## Phase D — Agent QOL (shipped)

| Priority | Item | Status |
|----------|------|--------|
| P0 | `wait_for_task` | done |
| P0 | ISO / CDROM + boot on `create_vm` / `update_vm_config` | done |
| P0 | Cloud-init params (`ciuser`, `sshkeys`, `ipconfig0`, `cipassword`) | done |
| P1 | Net/bridge params on create_vm / create_lxc | done |
| P1 | `list_os_templates` / `list_isos` + auto ostemplate | done |
| P1 | `get_token_permissions` (privsep D8) | done |
| P2 | PyPI package `cursor-proxmox-mcp` + publish.yml | done (name collision fix in 1.0.1; needs Trusted Publisher) |
| P2 | SETUP nested Docker LXC prompts + MCP reload checklist | done |

**Success criteria:** Agent can discover media → pick nextid → create with ISO/cloud-init/net → `wait_for_task` → verify — without guessing paths or sleeping blindly.

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

---

## Soft DX (docs / CI)

| Item | Status |
|------|--------|
| Cursor MCP reload checklist after `git pull` | done (SETUP.md) |
| Optional `mcpo` OpenAPI smoke in CI | done |
| Example agent prompts (nested Docker LXC, ISO VM) | done (SETUP.md) |

---

## Knowledge to keep in mind (reference these files)

| Insight | Where captured | Reminder |
|---------|----------------|----------|
| Privsep=Yes needs ACL on `user@realm!tokenid` | D8, SETUP.md, `get_token_permissions` | Empty lists ≠ “no VMs” — check token ACL first |
| SETUP.md is first-run SoT | D9 | README stays inventory + short install |
| Console = ticket mint only | D6 | No websocket proxy in MCP |
| uvx / `cursor-proxmox-mcp` preferred | D7 / D20 | PyPI name matches console script; avoid colliding `proxmox-mcp-server` |
| Inventory lock | D5, `tests/expected_tools.py` | Every new tool updates README + coverage + expected_tools |
| LXC `/exec` version-dependent | D4, changelog | Fail clearly; don’t pretend QGA |
| Destructive ops need force + warnings | D2 | Keep pattern for new delete/power tools |

---

## Suggested next work

```text
1. Configure PyPI Trusted Publisher for `cursor-proxmox-mcp` → re-run publish.yml (see PUBLISHING.md)
2. Official MCP registry: `mcp-publisher publish` after PyPI upload
3. Glama submit + community drafts in docs/community/
4. Only then: SDN write or ACME write if a real use case appears (Phase C)
```

When shipping any new tool: update this file’s status, coverage matrix, changelog-notes, README, and `expected_tools.py` in the same change (api-coverage + keep-docs-aligned rules).
