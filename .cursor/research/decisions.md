# Design decisions

## D1 — guest_type for cross-cutting tools

Snapshots, backups (restore), migrate, guest firewall, pending config, and disk move use `guest_type=qemu|lxc` instead of doubling every tool name. Parallel power tools stay as `*_vm` / `*_lxc` for Cursor workflow compatibility.

Additive unified aliases (`start_guest`, `stop_guest`, `shutdown_guest`, `reboot_guest`, `delete_guest`, `get_guest_status`) also take `guest_type` and must not replace or deprecate the parallel names in a minor release.

## D2 — Destructive ops

Delete VM/LXC/storage/backup/snapshot/user require clear warning text in tool descriptions and responses. Running guests need `force=True` to delete (stop then delete).

## D3 — Token secrets

`create_token` returns the secret in the tool response once. Do not log secrets at INFO; callers must store immediately.

## D4 — LXC exec

Proxmox has **no REST API** for LXC guest shell (unlike QEMU guest-agent `/agent/exec`). Official mechanism is host-side `pct exec` (lxc-attach). File push/pull uses `pct push`/`pct pull`.

Day-2 LXC tools (`execute_lxc_command`, `set_lxc_password` / `set_lxc_ssh_keys`, `prepare_lxc_for_docker`, `push_to_lxc` / `pull_from_lxc`, runtime IP in `get_lxc_network`) require **opt-in** config `ssh` (`enabled`, user, key). **paramiko is a core dependency** since 1.3.0 (`[ssh]` extra is an empty back-compat alias). Without SSH, tools return a clear actionable error (reload MCP after config change) — they must **not** call a fake `/lxc/{vmid}/exec` path (that yields 501 Not Implemented on real clusters). HTTP 501 from agents usually means Cursor is still on a pre-1.1.1 MCP build — reload/`uvx --from` checkout.

Runtime IP discovery in `get_lxc_network` uses the same SSH/`pct` path when configured; otherwise only configured `netN` (static CIDR or `dhcp`) is returned.

## D21 — LXC guest auth (password / SSH keys)

Proxmox applies `password` and `ssh-public-keys` **only at create** (rootfs provisioning). There is **no** REST API to change LXC root password or authorized_keys afterward.

MCP stance:
- Expose `password` + `ssh_public_keys` on `create_lxc`.
- Post-create: `set_lxc_password` / `set_lxc_ssh_keys` via host SSH + `pct exec` (same gate as D4).
- Many stock templates set `PermitRootLogin prohibit-password` — create-time password alone often fails guest SSH. Prefer keys at create, or `set_lxc_password(enable_password_ssh=true)` after start.
- `update_lxc_config` must not pretend to set password/keys.
- `create_lxc` success text must not claim Docker/app readiness; nesting ≠ installed runtime.

## D5 — Docs / inventory lockstep

`tests/expected_tools.py` must equal registered tool names. CI fails on drift. README + coverage matrix update in the same change.

## D6 — VNC/SPICE ticket-only, no proxy

MCP request/response does not fit long-lived websocket console streams. Tools mint `vncproxy` / `spiceproxy` / `termproxy` tickets and return JSON; external viewers connect. Full proxy remains Phase C / excluded.

## D7 — uvx as recommended install path

Cursor MCP reliability improved when using `uvx` (or `uv run`) with console script `cursor-proxmox-mcp` instead of a fragile system Python + manual `PYTHONPATH`. Keep `python -m proxmox_mcp.server` as documented fallback. Scripts `cursor-proxmox-mcp`, `proxmox-mcp`, and `proxmox-mcp-server` all map to `server:main`.

## D8 — API tokens default to Privilege Separation

Proxmox creates tokens with **Privilege Separation = Yes** (`privsep=1`). Separated tokens start with **no** ACLs; effective permissions are the intersection of user ACLs and token ACLs. Disabling privsep (`privsep=0`) makes the token inherit the user’s full permission set — a common lab “make it work” bypass when operators forget to ACL the token, but a larger blast radius if the secret leaks.

**Project stance:** Document privsep=Yes + explicit token ACL as best practice in `SETUP.md` / `proxmox-auth` rule. Document privsep=No as an explicit lab shortcut, not the recommended default. `create_token` keeps `privsep=True` by default to match Proxmox.

Operators hitting empty results after a “successful” token create should check token ACLs (`pveum user token permissions …` / UI Permissions for `user@realm!tokenid`) before disabling privsep.

## D9 — Setup guide is first-run source of truth

`SETUP.md` is the primary first-run path (token, Cursor `mcp.json`, prompts, security). README stays the inventory + short install reference and links into SETUP for auth depth. `proxmox-config/README.md` covers the config file only.

## D10 — Prefer Phase D QOL over Phase C surface

After the 128-tool baseline, expand create/wait paths before exotic admin APIs. Agents lose more time to racing UPIDs and hardcoded `vmbr0`/missing ISO/cloud-init than to missing SDN zone CRUD. Roadmap: `.cursor/research/next-expansion.md`.

## D11 — Create tools should not hardcode lab assumptions forever

`create_vm` / `create_lxc` default to `vmbr0` / DHCP when omitted, but accept bridge/IP/`net0`, ISO/boot, and cloud-init params. Prefer discovery tools (`list_os_templates`, `list_isos`) over guessing volids.

## D12 — PyPI package name matches uvx entrypoint

Publish as **`cursor-proxmox-mcp`** so `uvx cursor-proxmox-mcp` resolves without `--from`. Import package remains `proxmox_mcp`. Release via `.github/workflows/publish.yml` + PyPI Trusted Publishing (environment `pypi`). Do **not** use the PyPI name `proxmox-mcp-server` — that name is already owned by an unrelated project (see D20).

## D13 — Shared guest helpers, parallel VM/LXC classes

Keep `VMTools` and `ContainerTools` as separate classes for clear agent-facing tool names. Extract shared internals (`pick_storage`, `assert_id_absent`, constants for `vmbr0` / default features). Do not merge into one GuestTools class in v1.0.

## D14 — Response strings frozen for v1.0

Existing emoji / prose `Content` payloads stay byte-stable where possible. New internal helpers may use plain structured text. Bulk formatter rewrite is post-1.0.

## D15 — JSON config + env interpolation is canonical auth

`PROXMOX_MCP_CONFIG` JSON is the only startup path. Secrets may use `${ENV_VAR}` interpolation in JSON values. Remove unused `utils/auth.py` env-only loader to avoid dual silent paths.

## D16 — Single logging module

Only `core.logging.setup_logging` is used. Delete `utils/logging.py`. Attach a redacting filter for token/password patterns.

## D17 — Guest routing via guest.py

Cross-cutting qemu|lxc tools (snapshot, migrate, firewall) must use `guest_resource` / `normalize_guest_type`. Enforced by design-invariant tests.

## D18 — Lab default constants

Hardcoded defaults (`vmbr0`, `nesting=1`) live as named constants for testability. New optional create params remain Phase D (see D11) when they would change the public schema.

## D19 — Declarative tool metadata + register module

Each tools domain exports `TOOL_SPECS` (name + description ref). Registration wrappers live in `tools/register.py`; `server._setup_tools` calls `register_all`. Public tool names/params unchanged; `expected_tools.py` remains the golden inventory.

## D20 — Avoid colliding PyPI names

`proxmox-mcp-server` on PyPI belongs to [GethosTheWalrus/proxmox-mcp](https://github.com/GethosTheWalrus/proxmox-mcp). Publishing under that name would fail or, worse, confuse installers. Canonical distribution name is `cursor-proxmox-mcp` (matches the GitHub repo). Document the collision in README / SECURITY / PUBLISHING.

## D22 — UPID response footer standard

Tools that return a Proxmox task UPID must append `upid_response_footer` (Task ID + `wait_for_task` hint). Never claim the work is finished when only a UPID was returned. Prefer “initiated” / “task started” language over “successfully completed.”

## D23 — Destructive response echo

Destructive tools already warn in descriptions (D2). Responses must also echo `⚠️ IRREVERSIBLE` so agents that skip descriptions still see the warning.

## D24 — Docker-in-LXC

Nested Docker on unprivileged LXC fails at `docker run` (not install) when host AppArmor + runc CVE-2025-52881 interact (`ip_unprivileged_port_start` reopen denied).

**Stance (implemented by `prepare_lxc_for_docker`):**

1. Prefer host **`lxc-pve ≥ 6.0.5-2`** (generated nested AppArmor fix). Strip stale `unconfined` workarounds after upgrade.
2. Unpatched host: allowlisted dual raw lines via host conf — `lxc.apparmor.profile: unconfined` **and** `lxc.mount.entry: /dev/null sys/module/apparmor/parameters/enabled none bind 0 0` — then full stop/start. Never bare `unconfined` alone (overrides nesting / breaks Docker AppArmor checks).
3. Do **not** treat Docker `--privileged` / `--sysctl` / containerd downgrade as the supported path.
4. Keep unprivileged default; privileged CT is last-resort docs only.
5. Success criterion: `docker run --rm nginx:alpine`, not merely `docker --version`.

## D25 — Create auto-wait (Phase F.1 / shipped)

D10 keeps create tools UPID-first. `create_vm` / `create_lxc` accept optional `wait: bool = False` that polls the create UPID when true. **Default remains false** — default-on is high product risk (MCP latency, agent expectations).

## D26 — Community announce tooling before Phase C

Ship operator tooling for `docs/community/` drafts (`scripts/post-community.*`) and keep Phase C (SDN/ACME/Ceph/cluster join/VNC proxy/PBS/node power) **deferred** until a concrete lab demand appears. F/F.1 already cover the day-2 path that unblocked Cursor↔Proxmox agents.
