"""
Configuration loading utilities for the Proxmox MCP server.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Optional

from .models import Config

_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def expand_env_vars(value: Any) -> Any:
    """Recursively expand ``${VAR}`` placeholders from the process environment."""
    if isinstance(value, str):
        def repl(match: re.Match[str]) -> str:
            key = match.group(1)
            env_val = os.environ.get(key)
            if env_val is None:
                raise ValueError(f"Environment variable '{key}' is not set (needed for config)")
            return env_val

        return _ENV_PATTERN.sub(repl, value)
    if isinstance(value, dict):
        return {k: expand_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [expand_env_vars(v) for v in value]
    return value


def load_config(config_path: Optional[str] = None) -> Config:
    """Load and validate configuration from JSON file (with optional env interpolation)."""
    if not config_path:
        raise ValueError("PROXMOX_MCP_CONFIG environment variable must be set")

    try:
        with open(config_path, encoding="utf-8") as f:
            config_data = json.load(f)
        config_data = expand_env_vars(config_data)
        if not config_data.get("proxmox", {}).get("host"):
            raise ValueError("Proxmox host cannot be empty")
        return Config(**config_data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {e}") from e
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Failed to load config: {e}") from e
