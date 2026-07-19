@echo off
REM Manual launcher for Proxmox MCP (prefer Cursor mcp.json direct python spawn).
REM Do not echo to stdout — MCP uses stdio for JSON-RPC.

cd /d C:\Users\Ryan\Projects\cursor-proxmox-mcp

set PROXMOX_MCP_CONFIG=proxmox-config\config.json
if not exist "%PROXMOX_MCP_CONFIG%" (
    echo [ERROR] Configuration file does not exist: %PROXMOX_MCP_CONFIG% 1>&2
    exit /b 1
)

set PYTHONPATH=C:\Users\Ryan\Projects\cursor-proxmox-mcp\src
C:\Python314\python.exe -m proxmox_mcp.server
