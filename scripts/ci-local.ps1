# Local CI gate for Windows PowerShell — mirrors .github/workflows/ci.yml
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$env:PYTHONPATH = Join-Path $Root "src"

Write-Host "==> Installing package + dev deps"
python -m pip install -e ".[dev]" -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Entrypoint smoke"
python -c "from proxmox_mcp.server import main; print('entrypoint ok')"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Ruff"
python -m ruff check src tests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Pytest"
python -m pytest tests/ -q --tb=short
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Tool inventory sanity"
python -c "from tests.expected_tools import EXPECTED_TOOLS; print(f'Expected tools: {len(EXPECTED_TOOLS)}'); assert len(EXPECTED_TOOLS) >= 100"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Optional OpenAPI (mcpo) smoke"
python -m pip install -e ".[openapi]" -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -c "import mcpo; print('mcpo import ok')"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Local CI passed"
