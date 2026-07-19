@echo off
echo Starting Proxmox MCP server...

:: Move to your project directory
cd /d C:\Users\Ryan\Projects\cursor-proxmox-mcp

:: Set the required config variable from the bash script
set PROXMOX_MCP_CONFIG=proxmox-config\config.json

:: Check if the configuration file actually exists
if not exist "%PROXMOX_MCP_CONFIG%" (
    echo [ERROR] Configuration file does not exist: %PROXMOX_MCP_CONFIG%
    echo Please ensure the configuration file is properly set up.
    exit /b 1
)

:: Set python path to src so local create_lxc and other tools are loaded
set PYTHONPATH=C:\Users\Ryan\Projects\cursor-proxmox-mcp\src
C:\Python314\python.exe -m proxmox_mcp.server