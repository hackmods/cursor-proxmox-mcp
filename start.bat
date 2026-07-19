@echo off
REM Manual launcher for cursor-proxmox-mcp (prefer Cursor mcp.json + uvx).
REM Do not echo to stdout — MCP uses stdio for JSON-RPC.

cd /d "%~dp0"

set "PROXMOX_MCP_CONFIG=%~dp0proxmox-config\config.json"
if not exist "%PROXMOX_MCP_CONFIG%" (
    echo [ERROR] Configuration file does not exist: %PROXMOX_MCP_CONFIG% 1>&2
    exit /b 1
)

REM Prefer installed console script from editable/PyPI install
where cursor-proxmox-mcp >nul 2>&1
if %ERRORLEVEL%==0 (
    cursor-proxmox-mcp
    exit /b %ERRORLEVEL%
)

REM Fallback: run module from this checkout
set "PYTHONPATH=%~dp0src"
where py >nul 2>&1
if %ERRORLEVEL%==0 (
    py -3 -m proxmox_mcp.server
    exit /b %ERRORLEVEL%
)

where python >nul 2>&1
if %ERRORLEVEL%==0 (
    python -m proxmox_mcp.server
    exit /b %ERRORLEVEL%
)

echo [ERROR] Neither cursor-proxmox-mcp nor python found on PATH. 1>&2
echo Install with: uv pip install -e ".[dev]"   OR   uvx --from . cursor-proxmox-mcp 1>&2
exit /b 1
