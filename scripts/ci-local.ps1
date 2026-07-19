# Local CI gate for Windows PowerShell — mirrors .github/workflows/ci.yml
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$env:PYTHONPATH = Join-Path $Root "src"

Write-Host "==> Installing package + dev deps (cursor-proxmox-mcp)"
python -m pip install -e ".[dev]" -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Entrypoint smoke"
python -c "from proxmox_mcp.server import main; print('entrypoint ok')"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Console script smoke"
python -c @"
from importlib.metadata import entry_points
eps = entry_points()
scripts = {e.name for e in (eps.select(group='console_scripts') if hasattr(eps, 'select') else eps.get('console_scripts', []))}
assert 'cursor-proxmox-mcp' in scripts, scripts
assert 'proxmox-mcp' in scripts and 'proxmox-mcp-server' in scripts
print('console scripts ok: cursor-proxmox-mcp + aliases')
"@
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Ruff"
python -m ruff check src tests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Pytest"
python -m pytest tests/ -q --tb=short
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Tool inventory sanity"
python -c "from proxmox_mcp.tools.inventory import ALL_TOOL_NAMES; print(f'Tools: {len(ALL_TOOL_NAMES)}'); assert len(ALL_TOOL_NAMES) >= 100"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Optional OpenAPI (mcpo) smoke"
python -m pip install -e ".[openapi]" -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -c "import mcpo; print('mcpo import ok')"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Local CI passed"
