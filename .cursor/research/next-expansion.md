# Next expansion phases

Living Cursor note for what to build after the current **128-tool** baseline.
Update this file when priorities change; keep [proxmox-api-coverage.md](proxmox-api-coverage.md), [README.md](../../README.md), and [docs/api-coverage.md](../../docs/api-coverage.md) in sync.

**Baseline (done):** Formal Cursor ↔ Proxmox MCP — guest lifecycle, storage, HA, firewall, access, replication, SDN read, ACME read, pools, console tickets, inventory-locked CI.

---

## Phase D — Agent QOL (do next)

Highest leverage for Cursor agents. Not “more API surface for its own sake” — fixes friction in create/wait/config loops.

| Priority | Item | Why | Notes / APIs |
|----------|------|-----|----------------|
| P0 | `wait_for_task` | Agents race after create/clone/migrate | Poll `GET /nodes/{n}/tasks/{upid}/status` until `stopped`; optional timeout |
| P0 | ISO / CDROM + boot on `create_vm` / `update_vm_config` | Blank VMs still need manual ISO | `ide2`/`sata` CDROM + `boot` order |
| P0 | Cloud-init params | Provision without guest-agent dance | `ciuser`, `sshkeys`, `ipconfig0`, `cipassword` |
| P1 | Net/bridge params on create | Still hardcodes `vmbr0` / DHCP | `net0` string or bridge/ip helpers on create_vm/create_lxc |
| P1 | Create-flow template discovery | Agents still guess `ostemplate` | Soft-guide: call `get_storage_content` first; optional helper tool |
| P1 | Token ACL helper | Privsep empty-result trap (D8) | `get_token_permissions` or document `get_permissions` smoke in SETUP prompts |
| P2 | Publish to PyPI | True `uvx proxmox-mcp-server` without `--from` | Packaging/release workflow |
| P2 | SETUP example prompts | Nested Docker LXC, snap→upgrade→rollback | Docs-only QOL |

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

## Soft DX (docs / CI — anytime)

- Cursor MCP reload checklist after `git pull` (SETUP / README troubleshooting)
- Optional `mcpo` OpenAPI smoke in CI (`.[openapi]`)
- Example agent prompts for common lab flows

---

## Knowledge to keep in mind (reference these files)

| Insight | Where captured | Reminder |
|---------|----------------|----------|
| Privsep=Yes needs ACL on `user@realm!tokenid` | D8, SETUP.md, proxmox-auth rule | Empty lists ≠ “no VMs” — check token ACL first |
| SETUP.md is first-run SoT | D9 | README stays inventory + short install |
| Console = ticket mint only | D6 | No websocket proxy in MCP |
| uvx / `proxmox-mcp-server` preferred | D7 | Avoid fragile system Python + PYTHONPATH |
| Inventory lock | D5, `tests/expected_tools.py` | Every new tool updates README + coverage + expected_tools |
| LXC `/exec` version-dependent | D4, changelog | Fail clearly; don’t pretend QGA |
| `create_*` hardcodes net/bridge today | This note + coverage Planned/Phase D | Fix in Phase D before more exotic APIs |
| HA/firewall/keyctl often need elevated roles | SETUP, api-coverage Auth | Document role expectations, don’t widen token by default |
| Destructive ops need force + warnings | D2 | Keep pattern for new delete/power tools |

---

## Suggested implementation order

```text
1. wait_for_task (+ unit test with mocked UPID lifecycle)
2. create_vm / update_vm_config: ISO + boot + cloud-init + net overrides
3. create_lxc: bridge/ip/net0 overrides (features already covered)
4. Token permission smoke helper or SETUP prompt block
5. PyPI publish (optional parallel track)
6. Only then: SDN write or ACME write if a real use case appears
```

When shipping any row above: update this file’s status, coverage matrix, changelog-notes, README Planned section, and `expected_tools.py` in the same change (api-coverage + keep-docs-aligned rules).
