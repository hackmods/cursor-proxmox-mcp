#!/usr/bin/env bash
# Local CI gate — run before commit/push. Mirrors .github/workflows/ci.yml
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="${ROOT}/src${PYTHONPATH:+:$PYTHONPATH}"

echo "==> Installing package + dev deps"
python -m pip install -e ".[dev]" -q

echo "==> Entrypoint smoke"
python -c "from proxmox_mcp.server import main; print('entrypoint ok')"

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
