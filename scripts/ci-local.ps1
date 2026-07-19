# Local CI gate for Windows PowerShell — mirrors .github/workflows/ci.yml
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$env:PYTHONPATH = Join-Path $Root "src"

Write-Host "==> Installing package + dev deps"
python -m pip install -e ".[dev]" -q

Write-Host "==> Ruff"
python -m ruff check src tests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Pytest"
python -m pytest tests/ -q --tb=short
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Tool inventory sanity"
python -c "from tests.expected_tools import EXPECTED_TOOLS; print(f'Expected tools: {len(EXPECTED_TOOLS)}'); assert len(EXPECTED_TOOLS) >= 70"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Local CI passed"
