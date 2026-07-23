"""ACME (Let's Encrypt) tools — list, account/plugin CRUD, order/renew."""
from __future__ import annotations

from typing import List, Optional

from mcp.types import TextContent as Content

from .base import ProxmoxTool
from .helpers import (
    destructive_warning,
    privilege_required_note,
    privsep_empty_hint,
    upid_response_footer,
)


class ACMETools(ProxmoxTool):
    """ACME plugins/accounts + certificate order/renew on a node."""

    def list_acme_plugins(self) -> List[Content]:
        try:
            plugins = self.proxmox.cluster.acme.plugins.get()
            if not plugins:
                return [
                    Content(
                        type="text",
                        text=(
                            f"{privsep_empty_hint('ACME plugins')}\n"
                            f"{privilege_required_note('ACME plugin listing')}"
                        ),
                    )
                ]
            return self._format_response(plugins)
        except Exception as e:
            self._handle_error("list ACME plugins", e)

    def list_acme_accounts(self) -> List[Content]:
        try:
            accounts = self.proxmox.cluster.acme.account.get()
            if not accounts:
                return [
                    Content(
                        type="text",
                        text=(
                            f"{privsep_empty_hint('ACME accounts')}\n"
                            f"{privilege_required_note('ACME account listing')}"
                        ),
                    )
                ]
            return self._format_response(accounts)
        except Exception as e:
            self._handle_error("list ACME accounts", e)

    def get_acme_directories(self) -> List[Content]:
        try:
            dirs = self.proxmox.cluster.acme.directories.get()
            return self._format_response(dirs)
        except Exception as e:
            self._handle_error("get ACME directories", e)

    def create_acme_account(
        self,
        name: str,
        contact: str,
        directory: Optional[str] = None,
        tos_url: Optional[str] = None,
    ) -> List[Content]:
        """Register an ACME account (Let's Encrypt). Never logs secrets."""
        try:
            params: dict = {"name": name, "contact": contact}
            if directory is not None:
                params["directory"] = directory
            if tos_url is not None:
                params["tos_url"] = tos_url
            result = self.proxmox.cluster.acme.account.post(**params)
            return [
                Content(
                    type="text",
                    text=(
                        f"ACME account '{name}' created\nContact: {contact}\n"
                        f"Result: {result}\n"
                        f"💡 Next: create_acme_plugin (dns) if needed, then "
                        f"order_acme_certificate(node=…)."
                    ),
                )
            ]
        except Exception as e:
            self._handle_mutation_error(
                f"create ACME account {name}",
                e,
                code="acme_acl_denied",
                path="/cluster/acme/account",
            )

    def create_acme_plugin(
        self,
        id: str,
        type: str,
        api: Optional[str] = None,
        data: Optional[str] = None,
        validation_delay: Optional[int] = None,
        disable: bool = False,
    ) -> List[Content]:
        """Create ACME challenge plugin. ``data`` (DNS API creds) is never echoed."""
        try:
            params: dict = {"id": id, "type": type}
            if api is not None:
                params["api"] = api
            if data is not None:
                params["data"] = data
            if validation_delay is not None:
                params["validation-delay"] = int(validation_delay)
            if disable:
                params["disable"] = 1
            result = self.proxmox.cluster.acme.plugins.post(**params)
            return [
                Content(
                    type="text",
                    text=(
                        f"ACME plugin '{id}' created (type={type})\n"
                        f"Result: {result}\n"
                        "Plugin credential data was not echoed in this response."
                    ),
                )
            ]
        except Exception as e:
            self._handle_mutation_error(
                f"create ACME plugin {id}",
                e,
                code="acme_acl_denied",
                path="/cluster/acme/plugins",
            )

    def delete_acme_plugin(self, id: str) -> List[Content]:
        try:
            result = self.proxmox.cluster.acme.plugins(id).delete()
            return [
                Content(
                    type="text",
                    text=(
                        f"{destructive_warning('deleted')}\n"
                        f"ACME plugin '{id}' deleted\nResult: {result}"
                    ),
                )
            ]
        except Exception as e:
            self._handle_mutation_error(
                f"delete ACME plugin {id}",
                e,
                code="acme_acl_denied",
                path=f"/cluster/acme/plugins/{id}",
            )

    def order_acme_certificate(self, node: str, force: bool = False) -> List[Content]:
        """Order a new ACME certificate for a node (async UPID)."""
        try:
            params: dict = {}
            if force:
                params["force"] = 1
            result = (
                self.proxmox.nodes(node).certificates.acme.certificate.post(**params)
            )
            return [
                Content(
                    type="text",
                    text=(
                        f"ACME certificate order initiated on node {node}\n"
                        f"{upid_response_footer(result, node=node)}\n"
                        f"{privilege_required_note('ACME order')}"
                    ),
                )
            ]
        except Exception as e:
            self._handle_mutation_error(
                f"order ACME certificate on {node}",
                e,
                code="acme_acl_denied",
                path=f"/nodes/{node}/certificates/acme/certificate",
            )

    def renew_acme_certificate(self, node: str, force: bool = False) -> List[Content]:
        """Renew the node's ACME certificate (async UPID; force skips expiry window)."""
        try:
            params: dict = {}
            if force:
                params["force"] = 1
            # Same endpoint; renew is the natural follow-up / forced re-order
            result = (
                self.proxmox.nodes(node).certificates.acme.certificate.post(**params)
            )
            return [
                Content(
                    type="text",
                    text=(
                        f"ACME certificate renew initiated on node {node}\n"
                        f"{upid_response_footer(result, node=node)}\n"
                        f"{privilege_required_note('ACME renew')}"
                    ),
                )
            ]
        except Exception as e:
            self._handle_mutation_error(
                f"renew ACME certificate on {node}",
                e,
                code="acme_acl_denied",
                path=f"/nodes/{node}/certificates/acme/certificate",
            )
