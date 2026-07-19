# Contributing

Thanks for contributing to **cursor-proxmox-mcp**.

## Development setup

```bash
uv venv && uv pip install -e ".[dev]"
# or: pip install -e ".[dev]"
```

## Local CI

```powershell
.\scripts\ci-local.ps1
```

```bash
./scripts/ci-local.sh
```

Runs ruff, pytest (with coverage ≥80% on package logic; registration/UI chrome omitted), and inventory checks.

## Adding or changing a tool

1. Implement in the appropriate `src/proxmox_mcp/tools/*.py` module.
2. Add description in `definitions.py`.
3. Register in `tools/register.py`.
4. Add the name to `tools/inventory.py` (`ALL_TOOL_NAMES`).
5. Update README Available Tools table.
6. Add/extend unit tests (every public method should be reachable from tests).
7. Update `.cursor/research/proxmox-api-coverage.md` if API coverage changes.

Design invariants in `tests/test_design_invariants.py` must stay green.

## Security

See [SECURITY.md](SECURITY.md). Do not commit `proxmox-config/config.json` or real tokens.

## Pull requests

- Keep the public MCP tool surface stable unless the PR is an intentional breaking change with a major version bump.
- Prefer small, focused PRs.
- Ensure CI is green before merge.
