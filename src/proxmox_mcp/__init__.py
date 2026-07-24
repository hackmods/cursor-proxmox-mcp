"""
Proxmox MCP Server - A Model Context Protocol server for interacting with Proxmox hypervisors.
"""

__version__ = "1.8.0"
__all__ = ["ProxmoxMCPServer"]


def __getattr__(name: str):
    # Lazy import so `python -m proxmox_mcp.server` does not double-load the module.
    if name == "ProxmoxMCPServer":
        from .server import ProxmoxMCPServer
        return ProxmoxMCPServer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
