"""Expected MCP tool inventory — re-exports canonical list from tools.inventory."""
from proxmox_mcp.tools.inventory import ALL_TOOL_NAMES as EXPECTED_TOOLS

__all__ = ["EXPECTED_TOOLS"]
