#!/usr/bin/env bash
# Manual launcher for cursor-proxmox-mcp (prefer Cursor mcp.json + uvx).
# Do not echo to stdout — MCP uses stdio for JSON-RPC.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

export PROXMOX_MCP_CONFIG="${PROXMOX_MCP_CONFIG:-$ROOT/proxmox-config/config.json}"
if [[ ! -f "$PROXMOX_MCP_CONFIG" ]]; then
  echo "[ERROR] Configuration file does not exist: $PROXMOX_MCP_CONFIG" >&2
  exit 1
fi

# Prefer installed console script from editable/PyPI install
if command -v cursor-proxmox-mcp >/dev/null 2>&1; then
  exec cursor-proxmox-mcp
fi

# Fallback: run module from this checkout
export PYTHONPATH="${ROOT}/src${PYTHONPATH:+:$PYTHONPATH}"
exec python -m proxmox_mcp.server
