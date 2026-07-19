# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Post-r11 (rev r12):** structured ACL denials (HA/firewall/access/SDN/VM); `configure_lxc_ssh`, `get_docker_lxc_status`, `bootstrap_docker_lxc`; `qm_set_vm`; VM `onboot`/`description`/`tags` on create/update (**169 tools**).
- **Docker LXC Path B (rev r11):** `prepare_lxc_for_docker(docker_mode=auto|keyctl|crun)` with modern crun fallback; `configure_lxc_dns`; `pct_set_lxc`; create `nameserver`/`searchdomain`.

### Notes

- Community announce tooling: `scripts/post-community.ps1` / `.sh` + `docs/community/` draft format.
- Phase C remains deferred (D26).

## [1.4.0] - 2026-07-19

### Added

- **Phase F.1:** `get_vm_network`, `push_to_vm`, `pull_from_vm`, `deploy_static_nginx` (**163 tools**).
- Optional `wait=true` on `create_vm` / `create_lxc` (default **false**, D25) — polls create UPID when set.
- Optional `get_containers(probes=true)` — cheap docker / `:80` pct probes (SSH required; off by default).

### Notes

- Create tools remain UPID-first unless `wait=true`. Inventory probes stay opt-in.

## [1.3.0] - 2026-07-19

### Added

- **Phase F — LXC day-2:** `get_mcp_capabilities`, `prepare_lxc_for_docker`, `push_to_lxc`, `pull_from_lxc` (**159 tools**).
- `create_lxc(docker_ready=true)` sets `nesting=1,keyctl=1` and tips prepare (does not claim Docker runtime ready).
- Docker-in-LXC prep probes host `lxc-pve ≥ 6.0.5-2`; unpatched hosts get dual AppArmor workaround via host conf (never bare `unconfined`).

### Changed

- **paramiko** is a **core** dependency (`[ssh]` extra kept as empty back-compat alias).
- Shared `require_host_ssh` tips (reload MCP; no `pip install …[ssh]`).
- `execute_lxc_command` optional `timeout`; honors `PROXMOX_MCP_EXEC_TIMEOUT`; response includes `output`/`error` aliases.
- Startup warning when LXC pct tools are registered but `ssh` is off.
- `update_lxc_features` hints `get_guest_pending` + stop/start.

## [1.2.0] - 2026-07-19

### Added

- Unit test for `wait_for_task` non-OK `exitstatus` (returns ❌ content; does not raise).

### Notes

- First **tagged** release since `v1.1.0`. Includes the previously untagged 1.1.1–1.1.3 line: LXC SSH/`pct` exec, guest auth helpers, host SSH setup docs, and the post-1.1 QOL sweep (honest UPID messaging, force-delete wait, VM↔LXC hints, guest-agent exit-code truthfulness). Still **155 tools**.

## [1.1.3] - 2026-07-19

### Fixed

- **`execute_vm_command`**: `success` now reflects guest-agent exit code (was always `true`).
- **Force delete** (`delete_vm` / `delete_lxc` / `delete_guest`): wait for stop UPID before delete to avoid race.
- Symmetric VM↔LXC not-found hints on `*_lxc` tools and cross-cutting guest tools.
- `create_vm` headline no longer claims “created successfully” for an async UPID.
- `restore_backup` uses `normalize_guest_type` and echoes force/overwrite warnings.

### Changed

- Async tools append a standard `wait_for_task` footer (clone, migrate, backup, restore, download-url, resize/template, replication run, deletes, power ops).
- Destructive responses echo ⚠️ IRREVERSIBLE (D23).
- Empty inventory / ACL lists hint at privsep / `get_token_permissions`.
- Console ticket responses note external viewer required (D6).
- HA / SDN apply / ACME empty lists note elevated privilege requirements.
- `download_url_to_storage`: optional `verify_certificate`, `checksum`, `checksum_algorithm`; reject non-http(s) URLs.
- `get_next_vmid` notes best-effort race before create.

## [1.1.2] - 2026-07-19

### Fixed

- Document why create-time `password` often fails guest SSH: many templates use `PermitRootLogin prohibit-password`. Prefer `ssh_public_keys` at create, or `set_lxc_password(enable_password_ssh=true)` after start (needs host SSH/pct).
- Honest `create_lxc` messaging: OS create ≠ Docker/app deploy; warns on duplicate hostnames; surfaces whether host SSH/pct is configured (HTTP 501 on `/lxc/.../exec` = stale MCP pre-1.1.1).

### Added

- `ssh_public_keys` on `create_lxc` → Proxmox API `ssh-public-keys`
- `set_lxc_password` / `set_lxc_ssh_keys` via pct exec (**155 tools**)
- SETUP Docker-host bootstrap recipe

## [1.1.1] - 2026-07-19

### Fixed

- **`execute_lxc_command`**: Proxmox has no REST `/lxc/{vmid}/exec` (agents hit 501). Now uses opt-in SSH + host `pct exec` (requires `ssh` config + `paramiko` / `[ssh]` extra). Clear error when SSH is not configured.
- QEMU-only tools (`start_vm`, `delete_vm`, etc.) append a hint to use `get_containers` / `*_lxc` / `start_guest(guest_type=lxc)` when the VM ID is missing.

### Added

- `get_lxc_network` — configured netN + optional runtime IPv4 via pct when SSH enabled (**153 tools**)
- Optional `ssh` config section; `pip install 'cursor-proxmox-mcp[ssh]'`
- Configured IP on `get_containers` / `get_lxc_status`

### Changed

- Louder `wait_for_task` guidance on create VM/LXC success and tool descriptions
- Decision D4 revised: LXC exec is SSH/`pct` only (not version-dependent REST)

## [1.1.0] - 2026-07-19

### Added

- LXC parity: `suspend_lxc` / `resume_lxc` (CRIU warnings), `get_lxc_rrd_data`, `create_spice_ticket_lxc`
- Unified guest tools: `start_guest`, `stop_guest`, `shutdown_guest`, `reboot_guest`, `delete_guest`, `get_guest_status`, `get_guest_pending`, `move_guest_disk`
- Ops completeness: `update_pool`, firewall IPSet CIDR CRUD, `update_replication_job`, `list_backup_jobs` / `create_backup_job` / `delete_backup_job`
- Inventory baseline now **152 tools**
- GitHub wiki source under `docs/wiki/` + `scripts/sync-wiki.{ps1,sh}`

### Changed

- SETUP reload checklist documents stale ~14-tool Cursor catalog + wrong `uvx proxmox-mcp-server` package pitfall
- Decision D1: additive `*_guest` aliases alongside parallel `*_vm` / `*_lxc`
- `update_vm_config` / `update_lxc_config` hint agents to call `get_guest_pending` + reboot when needed
- Community drafts, Cursor MCP example, repo description aligned to 152 tools

## [1.0.1] - 2026-07-19

### Fixed

- PyPI package renamed to **`cursor-proxmox-mcp`** — `proxmox-mcp-server` on PyPI is an unrelated project; bare `uvx proxmox-mcp-server` would install the wrong package
- Release workflow no longer double-publishes to PyPI without the `pypi` environment (OIDC trusted publisher claims)

### Added

- `PUBLISHING.md`, `server.json`, `glama.json`, community announcement drafts
- MCP registry ownership marker (`mcp-name`) in README; OCI label on Docker image
- Console script `cursor-proxmox-mcp` (aliases `proxmox-mcp` / `proxmox-mcp-server` retained)

## [1.0.0] - 2026-07-19

### Security

- Env-var interpolation for secrets in JSON config (`${PROXMOX_TOKEN_VALUE}`)
- Example config defaults: `verify_ssl: true`, log level `INFO`
- Startup warning when TLS verification is disabled
- Log redaction filter for tokens/passwords
- Typed, sanitized API errors (reduce secret leakage in messages)
- Optional `PROXMOX_MCP_EXEC_ALLOWLIST` for guest command execution
- Guest exec polls `exec-status` with `PROXMOX_MCP_EXEC_TIMEOUT` (default 30s)
- Destructive tool descriptions marked IRREVERSIBLE/WARNING
- `SECURITY.md` + security review notes

### Changed

- Declarative tool inventory (`tools/inventory.py`) + registration module (`tools/register.py`)
- Shared helpers for storage selection and guest ID checks
- Removed unused `utils/auth.py` / `utils/logging.py`
- Package version **1.0.0** (Production/Stable)
- Docker image slimmed for `cursor-proxmox-mcp` / `proxmox-mcp-server` entrypoint
- CI: coverage gate, CodeQL, Dependabot, release workflow (PyPI OIDC + GHCR)

### Added

- Full unit/behavior test suite with fake Proxmox API and design-invariant locks
- Code design audit documentation

### Removed

- Legacy `test_scripts/`, `setup.py`, redundant start scripts

## [0.3.0] - 2026-07-18

Phase B tools, uvx entrypoint, setup QOL (pre-1.0 history).
