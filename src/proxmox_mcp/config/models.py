"""
Configuration models for the Proxmox MCP server.

This module defines Pydantic models for configuration validation:
- Proxmox connection settings
- Authentication credentials
- Logging configuration
- Tool-specific parameter models

The models provide:
- Type validation
- Default values
- Field descriptions
- Required vs optional field handling
"""
import logging
from typing import Dict, Optional, Annotated
from pydantic import BaseModel, Field, model_validator

_ssh_logger = logging.getLogger("proxmox-mcp.config")

class NodeStatus(BaseModel):
    """Model for node status query parameters.
    
    Validates and documents the required parameters for
    querying a specific node's status in the cluster.
    """
    node: Annotated[str, Field(description="Name/ID of node to query (e.g. 'pve1', 'proxmox-node2')")]

class VMCommand(BaseModel):
    """Model for VM command execution parameters.
    
    Validates and documents the required parameters for
    executing commands within a VM via QEMU guest agent.
    """
    node: Annotated[str, Field(description="Host node name (e.g. 'pve1', 'proxmox-node2')")]
    vmid: Annotated[str, Field(description="VM ID number (e.g. '100', '101')")]
    command: Annotated[str, Field(description="Shell command to run (e.g. 'uname -a', 'systemctl status nginx')")]

class ProxmoxConfig(BaseModel):
    """Model for Proxmox connection configuration.
    
    Defines the required and optional parameters for
    establishing a connection to the Proxmox API server.
    Provides sensible defaults for optional parameters.
    """
    host: str  # Required: Proxmox host address
    port: int = 8006  # Optional: API port (default: 8006)
    verify_ssl: bool = True  # Optional: SSL verification (default: True)
    ca_cert_path: Optional[str] = None  # Optional: path to CA bundle when verify_ssl is True
    service: str = "PVE"  # Optional: Service type (default: PVE)

class AuthConfig(BaseModel):
    """Model for Proxmox authentication configuration.
    
    Defines the required parameters for API authentication
    using token-based authentication. All fields are required
    to ensure secure API access.
    """
    user: str  # Required: Username (e.g., 'root@pam')
    token_name: str  # Required: API token name
    token_value: str  # Required: API token secret

class LoggingConfig(BaseModel):
    """Model for logging configuration.

    Supports file + console handlers, structured tool-call audit lines,
    and a ``verbose`` mode for richer (still redacted) diagnostics.

    Env overrides (applied in ``setup_logging``): ``PROXMOX_MCP_LOG_LEVEL``,
    ``PROXMOX_MCP_VERBOSE``, ``PROXMOX_MCP_TOOL_CALLS``, ``PROXMOX_MCP_CONSOLE_LEVEL``.
    """
    level: str = "INFO"  # DEBUG | INFO | WARNING | ERROR
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None  # Relative paths resolve from process cwd
    # QOL / observability
    verbose: bool = False  # Richer tool_call detail; bumps level INFO→DEBUG
    tool_calls: bool = True  # One-line audit per MCP tool invocation
    console_level: str = "ERROR"  # Keep Cursor stderr quiet unless raised
    quiet_libraries: bool = True  # Suppress urllib3/asyncio/mcp handshake spam
    http_debug: bool = False  # When true, allow urllib3 DEBUG (noisy)

    @model_validator(mode="after")
    def _normalize_levels(self) -> "LoggingConfig":
        self.level = self.level.upper()
        self.console_level = self.console_level.upper()
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.level not in allowed:
            raise ValueError(f"logging.level must be one of {sorted(allowed)}")
        if self.console_level not in allowed:
            raise ValueError(f"logging.console_level must be one of {sorted(allowed)}")
        return self


class SSHConfig(BaseModel):
    """Opt-in SSH access to Proxmox nodes for host-side ``pct`` (exec/push/set).

    Required for ``execute_lxc_command``, push/pull, prepare_lxc_for_docker, and
    runtime IP discovery via pct. There is no Proxmox REST API for LXC shell (D4).
    Paramiko is a core dependency; opt-in remains ``enabled`` + host key trust.
    """
    enabled: bool = False
    user: str = "root"
    port: int = 22
    private_key_path: Optional[str] = None
    # Map Proxmox node name → SSH hostname/IP when API host differs from nodes
    host_overrides: Dict[str, str] = Field(default_factory=dict)
    pct_path: str = "/usr/sbin/pct"
    timeout: int = 120  # Day-2 apt/npm/Docker; or PROXMOX_MCP_EXEC_TIMEOUT

    @model_validator(mode="after")
    def _warn_missing_key(self) -> "SSHConfig":
        if self.enabled and not self.private_key_path:
            _ssh_logger.warning(
                "ssh.enabled=true but private_key_path is unset — "
                "will try SSH agent / default keys; prefer an explicit key path. "
                "Reload MCP after fixing config."
            )
        return self


class Config(BaseModel):
    """Root configuration model.
    
    Combines all configuration models into a single validated
    configuration object. All sections are required to ensure
    proper server operation.
    """
    proxmox: ProxmoxConfig  # Required: Proxmox connection settings
    auth: AuthConfig  # Required: Authentication credentials
    logging: LoggingConfig  # Required: Logging configuration
    ssh: Optional[SSHConfig] = None  # Optional: host SSH for pct exec
