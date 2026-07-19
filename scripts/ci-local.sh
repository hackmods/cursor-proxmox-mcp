#!/usr/bin/env bash
# Local CI gate — run before commit/push. Mirrors .github/workflows/ci.yml
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="${ROOT}/src${PYTHONPATH:+:$PYTHONPATH}"

echo "==> Installing package + dev deps (cursor-proxmox-mcp)"
python -m pip install -e ".[dev]" -q

echo "==> Entrypoint smoke"
python -c "from proxmox_mcp.server import main; print('entrypoint ok')"

echo "==> Console script smoke"
python -c "
from importlib.metadata import entry_points
eps = entry_points()
scripts = {e.name for e in (eps.select(group='console_scripts') if hasattr(eps, 'select') else eps.get('console_scripts', []))}
assert 'cursor-proxmox-mcp' in scripts, scripts
assert 'proxmox-mcp' in scripts and 'proxmox-mcp-server' in scripts
print('console scripts ok:', 'cursor-proxmox-mcp', '+ aliases')
"

echo "==> Ruff"
python -m ruff check src tests

echo "==> Pytest"
python -m pytest tests/ -q --tb=short

echo "==> Tool inventory sanity"
python -c "
from proxmox_mcp.tools.inventory import ALL_TOOL_NAMES
print(f'Tools: {len(ALL_TOOL_NAMES)}')
assert len(ALL_TOOL_NAMES) >= 100, 'inventory too small'
print('OK')
"

echo "==> Optional OpenAPI (mcpo) smoke"
python -m pip install -e ".[openapi]" -q
python -c "import mcpo; print('mcpo import ok')"

echo "==> Local CI passed"
