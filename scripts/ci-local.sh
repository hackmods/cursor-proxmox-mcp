#!/usr/bin/env bash
# Local CI gate — run before commit/push. Mirrors .github/workflows/ci.yml
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="${ROOT}/src${PYTHONPATH:+:$PYTHONPATH}"

echo "==> Installing package + dev deps"
python -m pip install -e ".[dev]" -q

echo "==> Ruff"
python -m ruff check src tests

echo "==> Pytest"
python -m pytest tests/ -q --tb=short

echo "==> Tool inventory sanity"
python -c "
from tests.expected_tools import EXPECTED_TOOLS
print(f'Expected tools: {len(EXPECTED_TOOLS)}')
assert len(EXPECTED_TOOLS) >= 70, 'inventory too small'
print('OK')
"

echo "==> Local CI passed"
