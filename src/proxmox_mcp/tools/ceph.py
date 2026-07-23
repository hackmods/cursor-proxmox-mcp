"""Ceph cluster status and pool admin (no OSD/MON create/destroy)."""
from __future__ import annotations

from typing import List, Optional

from mcp.types import TextContent as Content

from .base import ProxmoxTool
from .helpers import destructive_warning, privilege_required_note, privsep_empty_hint


class CephTools(ProxmoxTool):
    """Read Ceph health/inventory; light pool create/delete with typed confirm."""

    def get_ceph_status(self) -> List[Content]:
        try:
            status = self.proxmox.cluster.ceph.status.get()
            return self._format_response(status)
        except Exception as e:
            self._handle_error("get Ceph status", e)

    def list_ceph_pools(self) -> List[Content]:
        try:
            pools = self.proxmox.cluster.ceph.pool.get()
            if not pools:
                return [Content(type="text", text=privsep_empty_hint("Ceph pools"))]
            return self._format_response(pools)
        except Exception as e:
            self._handle_error("list Ceph pools", e)

    def list_ceph_osds(self) -> List[Content]:
        try:
            osds = self.proxmox.cluster.ceph.osd.get()
            if not osds:
                return [Content(type="text", text=privsep_empty_hint("Ceph OSDs"))]
            return self._format_response(osds)
        except Exception as e:
            self._handle_error("list Ceph OSDs", e)

    def list_ceph_mons(self) -> List[Content]:
        try:
            mons = self.proxmox.cluster.ceph.mon.get()
            if not mons:
                return [Content(type="text", text=privsep_empty_hint("Ceph MONs"))]
            return self._format_response(mons)
        except Exception as e:
            self._handle_error("list Ceph MONs", e)

    def list_ceph_mgrs(self) -> List[Content]:
        try:
            mgrs = self.proxmox.cluster.ceph.mgr.get()
            if not mgrs:
                return [Content(type="text", text=privsep_empty_hint("Ceph MGRs"))]
            return self._format_response(mgrs)
        except Exception as e:
            self._handle_error("list Ceph MGRs", e)

    def create_ceph_pool(
        self,
        name: str,
        size: Optional[int] = None,
        min_size: Optional[int] = None,
        pg_num: Optional[int] = None,
        application: Optional[str] = None,
    ) -> List[Content]:
        try:
            params: dict = {"name": name}
            if size is not None:
                params["size"] = int(size)
            if min_size is not None:
                params["min_size"] = int(min_size)
            if pg_num is not None:
                params["pg_num"] = int(pg_num)
            if application is not None:
                params["application"] = application
            result = self.proxmox.cluster.ceph.pool.post(**params)
            return [
                Content(
                    type="text",
                    text=(
                        f"Ceph pool '{name}' create initiated\nResult: {result}\n"
                        f"{privilege_required_note('Ceph pool create')}\n"
                        "OSD/MON/MGR create/destroy remain out of MCP scope — use Ceph tooling."
                    ),
                )
            ]
        except Exception as e:
            self._handle_mutation_error(
                f"create Ceph pool {name}",
                e,
                code="ceph_acl_denied",
                path="/cluster/ceph/pool",
            )

    def delete_ceph_pool(self, name: str, confirm: str) -> List[Content]:
        """Delete a Ceph pool. confirm must equal the pool name (D29)."""
        try:
            if confirm != name:
                raise ValueError(
                    f"confirm must equal the exact pool name '{name}' "
                    f"(got {confirm!r}). Refusing delete."
                )
            result = self.proxmox.cluster.ceph.pool(name).delete()
            return [
                Content(
                    type="text",
                    text=(
                        f"{destructive_warning('deleted')}\n"
                        f"⚠️ IRREVERSIBLE: Ceph pool '{name}' deleted\n"
                        f"Result: {result}"
                    ),
                )
            ]
        except ValueError:
            raise
        except Exception as e:
            self._handle_mutation_error(
                f"delete Ceph pool {name}",
                e,
                code="ceph_acl_denied",
                path=f"/cluster/ceph/pool/{name}",
            )
