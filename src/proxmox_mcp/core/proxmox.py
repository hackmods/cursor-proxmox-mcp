"""
Proxmox API setup and management.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from proxmoxer import ProxmoxAPI

from ..config.models import AuthConfig, ProxmoxConfig


class ProxmoxManager:
    """Manager class for Proxmox API operations.

    Supports optional dual credentials (D31): ``auth`` is the primary/read
    identity; ``auth_write`` elevates mutating tool calls when configured.
    """

    def __init__(
        self,
        proxmox_config: ProxmoxConfig,
        auth_config: AuthConfig,
        auth_write: Optional[AuthConfig] = None,
    ):
        self.logger = logging.getLogger("proxmox-mcp.proxmox")
        self._auth = auth_config
        self._auth_write = auth_write
        self._proxmox_config = proxmox_config
        self.config = self._create_config(proxmox_config, auth_config)
        self.api = self._setup_api(self.config, label="primary")
        self.write_api: ProxmoxAPI
        if auth_write is not None:
            write_cfg = self._create_config(proxmox_config, auth_write)
            self.write_api = self._setup_api(write_cfg, label="write")
            self.logger.info(
                "Dual auth (D31): primary=%s!%s write=%s!%s",
                auth_config.user,
                auth_config.token_name,
                auth_write.user,
                auth_write.token_name,
            )
        else:
            self.write_api = self.api

    @property
    def dual_auth(self) -> bool:
        return self._auth_write is not None

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

    def _setup_api(self, config: Dict[str, Any], *, label: str) -> ProxmoxAPI:
        try:
            if config.get("verify_ssl") is False:
                self.logger.warning(
                    "TLS certificate verification is DISABLED (verify_ssl=false). "
                    "Use only in trusted lab networks; prefer verify_ssl=true with ca_cert_path."
                )
            self.logger.info(
                "Connecting to Proxmox host: %s (%s auth)", config["host"], label
            )
            api = ProxmoxAPI(**config)
            api.version.get()
            self.logger.info("Successfully connected to Proxmox API (%s)", label)
            return api
        except Exception as e:
            self.logger.error("Failed to connect to Proxmox (%s): %s", label, e)
            raise RuntimeError(f"Failed to connect to Proxmox ({label}): {e}") from e

    def get_api(self) -> ProxmoxAPI:
        """Primary / read API (``auth``)."""
        return self.api

    def get_write_api(self) -> ProxmoxAPI:
        """Elevated write API when ``auth_write`` set; otherwise same as primary."""
        return self.write_api

    def auth_summary(self) -> Dict[str, Any]:
        """Masked identity summary for capabilities (never includes secrets)."""
        primary = f"{self._auth.user}!{self._auth.token_name}"
        out: Dict[str, Any] = {
            "dual_auth": self.dual_auth,
            "auth_user": self._auth.user,
            "auth_token_name": self._auth.token_name,
            "auth_identity": primary,
            "mutating_api": "write" if self.dual_auth else "primary",
        }
        if self._auth_write is not None:
            out["auth_write_user"] = self._auth_write.user
            out["auth_write_token_name"] = self._auth_write.token_name
            out["auth_write_identity"] = (
                f"{self._auth_write.user}!{self._auth_write.token_name}"
            )
        return out
