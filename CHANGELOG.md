# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
