# Agent feedback log

Captured feedback from agents (or humans driving agents) using this MCP in real Proxmox labs.
Use this to avoid re-learning the same failures across sessions.

---

## 2026-07-19 — LXC create / DHCP / wrong-tool family

**Session context:** Agent created LXC, tried to discover DHCP IP and run guest commands; hit blockers and workarounds (static IP).

### Symptoms reported

| Symptom | Agent impact |
|---------|----------------|
| `execute_lxc_command` → HTTP 501 | Could not read DHCP IP or run install scripts inside CT |
| `get_lxc_status` / `get_containers` / `get_cluster_resources` no IPv4 | Forced static `net0` + reboot |
| `get_vms` empty while CTs exist | Assumed “nothing there” |
| `start_vm` / `execute_vm_command` / `delete_vm` on CT ID | “VM not found” / missing qemu-server conf |
| `create_lxc` returned success + UPID immediately | Race before vzcreate finished; needed `wait_for_task` |
| `features=nesting=1,keyctl=1` with non-root token | Proxmox rejects keyctl (“only allowed for root@pam”) |

### Root causes (codebase)

| Item | Cause |
|------|--------|
| LXC exec 501 | Implementation called non-existent REST `POST /nodes/{n}/lxc/{vmid}/exec`. Official Proxmox has **no** LXC shell REST API; only host `pct exec`. D4 previously understated this as “version-dependent.” |
| No guest IP | List/status formatters never parsed `netN`; DHCP lease IP is not in REST without host/guest exec |
| `get_vms` empty | By design QEMU-only (`/qemu`); under-documented for agents |
| Wrong-tool family | Parallel `*_vm` / `*_lxc` (D1/D13); no auto-detect; errors lacked LXC hint |
| Create vs ready | Fire-and-forget UPID (same as `create_vm`); `wait_for_task` exists but under-emphasized |
| keyctl | Privilege / role limitation — not a missing MCP feature |

### What worked (keep)

`get_lxc_status`, `start_lxc`, `reboot_lxc`, `update_lxc_config`, `get_lxc_config`, `get_containers`, `list_node_networks`; static net0 + reboot → reachable IP.

### Fixes shipped (rev r2 / v1.1.1)

1. Opt-in SSH + `pct exec` for `execute_lxc_command` (revise D4).
2. `get_lxc_network` + configured IP on list/status; runtime IP when SSH enabled.
3. Louder create → `wait_for_task` copy; QEMU-not-found hints; docs for QEMU vs LXC.
4. keyctl: document only (do not silently strip flags).

### Explicitly out of scope (do not reopen without new decision)

| Item | Why |
|------|-----|
| Auto-wait inside `create_*` | Changes response contract; D10 prefers separate `wait_for_task` |
| Merge LXC into `get_vms` | Fights D1/D13 parallel naming; use `get_containers` or `get_cluster_resources(type=vm)` |
| Silent guest-type auto-detect on `*_vm` | Surprising; prefer clear errors + `*_guest` + `guest_type` |
| Host DHCP lease file scraping | Fragile across setups; prefer static IP or `pct exec` |
| QEMU `agent/network-get-interfaces` tool | Soft Phase C; separate from this LXC P0 |

### Knowledge for future agents

- After `create_lxc` / `create_vm`: **always** `wait_for_task` before start or config assumptions.
- Guest type unknown → `get_cluster_resources(type="vm")` or `*_guest` with explicit `guest_type`.
- DHCP CT without SSH: set static `ip=` at create/update, or enable SSH for `get_lxc_network` / exec.
- Docker-in-LXC: `nesting=1` default; `keyctl=1` needs elevated privileges — expect failures on narrow tokens.
- Stale Cursor catalog (~14 tools / missing `*_guest`): reload MCP / quit Cursor; prefer `uvx --from <checkout>`.
