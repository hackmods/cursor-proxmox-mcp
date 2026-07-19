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

---

## 2026-07-19 — Guest password SSH + empty Docker host (day-2 deploy)

### Symptoms

| Symptom | Impact |
|---------|--------|
| `password=` on create but `ssh root@ct` → Authentication failed | Cannot bootstrap without console |
| `execute_lxc_command` still 501 `/exec` | Stale MCP pre-1.1.1 and/or ssh not enabled |
| Nesting LXC up but nothing on :80 / no Docker | Agent treated create as “app deployed” |
| No post-create password or SSH key tools | Stuck after bad/missing auth |
| Duplicate hostname `lumon-docker` on 121+122 | Confusing listings |

### Root causes / fixes (rev r3 / v1.1.2)

| Item | Cause | Fix |
|------|--------|-----|
| Password SSH fails | Template `PermitRootLogin prohibit-password` (password may still be in shadow) | Prefer `ssh_public_keys` at create; `set_lxc_password(enable_password_ssh=true)` via pct |
| No post-create password API | Proxmox limitation | `set_lxc_password` / `set_lxc_ssh_keys` via pct |
| No key injection | Missing MCP param | `ssh_public_keys` → API `ssh-public-keys` |
| Create ≠ deploy | Product gap | Honest messaging + SETUP Docker recipe |
| Duplicate hostname | Allowed by PVE | Soft warning on create |
| Persistent 501 | Stale Cursor MCP build | Document reload; current code never POSTs `/exec` |

### Out of scope

- Baking Docker into `create_lxc`
- REST password change (does not exist upstream)
- Guest SSH without keys/pct when host ssh config is off

---

## 2026-07-19 — Post-1.1 codebase QOL sweep (proactive audit)

**Session context:** After r2/r3 LXC fixes, review remaining 155 tools for the same issue classes (no full live lab coverage).

### Patterns found / fixed (rev r5 / v1.1.3)

| Pattern | Examples | Fix |
|---------|----------|-----|
| False SUCCESS | `execute_vm_command` always `success: True` | Honor exitcode |
| Force-delete race | stop then immediate delete | `wait_for_upid` after stop |
| Missing wait copy | clone/migrate/backup/download/... | `upid_response_footer` |
| One-sided family hints | `*_lxc` 404 without QEMU hint | `lxc_not_found_message` |
| Soft destructive text | delete_backup / delete_user | Echo ⚠️ IRREVERSIBLE |
| Empty ACL silence | list_users / get_vms empty | privsep / get_containers hints |

### Out of scope

- Auto-wait inside create_*
- QEMU guest-agent network IP on get_vms
- Baking Docker into create_lxc

---

## 2026-07-19 — Host SSH setup gap (config alone not enough)

**Session context:** Operator set `ssh.enabled`, `private_key_path`, and `host_overrides.pve` in `config.json`, but host SSH for `pct exec` still was not usable.

### Symptoms

| Symptom | Impact |
|---------|--------|
| Config has `ssh.enabled: true` + key path + overrides | Tools still fail or MCP process ignores new block |
| New keypair generated locally | No access until public key is on the node |
| Running MCP still on old config | Edits to `config.json` not picked up without reload |

### Root causes

| Item | Cause |
|------|--------|
| Missing host trust | Docs listed schema / “create a key-restricted user” but never spelled out installing the **public** key into node `authorized_keys` |
| Weak reload guidance | Error strings said “reload MCP”; SETUP reload checklist was framed as post-`git pull` / tool count, not “after enabling SSH” |
| Host vs guest confusion | Easy to mix host `authorized_keys` with LXC `ssh_public_keys` / `set_lxc_ssh_keys` |

### Fix (docs only)

Expanded SETUP SSH checklist (keygen → node `authorized_keys` → `host_overrides` example → verify `pct version` → reload MCP); host-trust section in `proxmox-config/README.md`; README + wiki Troubleshooting/Setup pointers.

### Out of scope

- Automating public-key install on the Proxmox host
- Schema / `SSHConfig` field changes
