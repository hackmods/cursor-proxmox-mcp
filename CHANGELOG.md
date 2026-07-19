# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
