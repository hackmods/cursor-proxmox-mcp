"""
Proxmox API setup and management.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict

from proxmoxer import ProxmoxAPI

from ..config.models import AuthConfig, ProxmoxConfig


class ProxmoxManager:
    """Manager class for Proxmox API operations."""

    def __init__(self, proxmox_config: ProxmoxConfig, auth_config: AuthConfig):
        self.logger = logging.getLogger("proxmox-mcp.proxmox")
        self.config = self._create_config(proxmox_config, auth_config)
        self.api = self._setup_api()

    def _create_config(
        self, proxmox_config: ProxmoxConfig, auth_config: AuthConfig
    ) -> Dict[str, Any]:
        cfg: Dict[str, Any] = {
            "host": proxmox_config.host,
            "port": proxmox_config.port,
            "user": auth_config.user,
            "token_name": auth_config.token_name,
            "token_value": auth_config.token_value,
            "verify_ssl": proxmox_config.verify_ssl,
            "service": proxmox_config.service,
        }
        if proxmox_config.ca_cert_path:
            # requests/proxmoxer accept a CA path via REQUESTS_CA_BUNDLE or verify path
            os.environ.setdefault("REQUESTS_CA_BUNDLE", proxmox_config.ca_cert_path)
            cfg["verify_ssl"] = proxmox_config.ca_cert_path
        return cfg

    def _setup_api(self) -> ProxmoxAPI:
        try:
            if self.config.get("verify_ssl") is False:
                self.logger.warning(
                    "TLS certificate verification is DISABLED (verify_ssl=false). "
                    "Use only in trusted lab networks; prefer verify_ssl=true with ca_cert_path."
                )
            self.logger.info("Connecting to Proxmox host: %s", self.config["host"])
            api = ProxmoxAPI(**self.config)
            api.version.get()
            self.logger.info("Successfully connected to Proxmox API")
            return api
        except Exception as e:
            self.logger.error("Failed to connect to Proxmox: %s", e)
            raise RuntimeError(f"Failed to connect to Proxmox: {e}") from e

    def get_api(self) -> ProxmoxAPI:
        return self.api
