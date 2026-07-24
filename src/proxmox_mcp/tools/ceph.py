"""Ceph cluster status, pools, and carefully gated OSD disk ops."""
from __future__ import annotations

import json
from typing import Any, List, Optional

from mcp.types import TextContent as Content

from .base import ProxmoxTool
from .helpers import (
    destructive_warning,
    privilege_required_note,
    privsep_empty_hint,
    upid_response_footer,
)


def _normalize_dev(dev: str) -> str:
    d = (dev or "").strip()
    if not d:
        raise ValueError("dev must be a non-empty block device path (e.g. /dev/sdb)")
    if not d.startswith("/"):
        d = f"/dev/{d.lstrip('/')}"
    return d


def _disk_is_free(disk: dict) -> bool:
    """Heuristic: unused and not already an OSD."""
    osdid = disk.get("osdid")
    osdid_list = disk.get("osdid-list") or []
    used = (disk.get("used") or "").strip().lower()
    if osdid is not None and int(osdid) >= 0:
        return False
    if any(int(x) >= 0 for x in osdid_list if x is not None):
        return False
    if used in ("", "unused", "none", "no"):
        return True
    # PVE often uses used="" or used="partitions" — treat unknown used as not free
    return used in ("unused",)


class CephTools(ProxmoxTool):
    """Read Ceph health/inventory; pool CRUD; gated OSD create/destroy (D30)."""

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

    def list_node_disks(
        self,
        node: str,
        type: Optional[str] = None,
        include_partitions: bool = False,
        skipsmart: bool = False,
    ) -> List[Content]:
        """List local disks (use type=unused before OSD create)."""
        try:
            params: dict = {}
            if type is not None:
                params["type"] = type
            if include_partitions:
                params["include-partitions"] = 1
            if skipsmart:
                params["skipsmart"] = 1
            disks = self.proxmox.nodes(node).disks.list.get(**params) or []
            if not disks:
                return [Content(type="text", text=privsep_empty_hint(f"disks on {node}"))]
            free = [d for d in disks if isinstance(d, dict) and _disk_is_free(d)]
            payload = {
                "node": node,
                "disks": disks,
                "free_candidate_count": len(free),
                "free_candidates": [
                    {
                        "devpath": d.get("devpath"),
                        "size": d.get("size"),
                        "model": d.get("model"),
                        "serial": d.get("serial"),
                        "health": d.get("health"),
                        "used": d.get("used"),
                    }
                    for d in free
                ],
                "next": (
                    "Call propose_ceph_osd(node, dev=/dev/…) then "
                    "create_ceph_osd(..., confirm=<exact-dev>, dry_run=false) "
                    "only after reviewing the proposal."
                ),
            }
            return self._format_response(payload)
        except Exception as e:
            self._handle_error(f"list disks on {node}", e)

    def propose_ceph_osd(
        self,
        node: str,
        dev: str,
        db_dev: Optional[str] = None,
        wal_dev: Optional[str] = None,
        encrypted: bool = False,
        crush_device_class: Optional[str] = None,
        osds_per_device: Optional[int] = None,
    ) -> List[Content]:
        """Dry proposal for OSD create — never mutates; validates disk when possible."""
        try:
            proposal = self._build_osd_proposal(
                node,
                dev,
                db_dev=db_dev,
                wal_dev=wal_dev,
                encrypted=encrypted,
                crush_device_class=crush_device_class,
                osds_per_device=osds_per_device,
            )
            text = (
                "Ceph OSD create proposal (dry — no changes made)\n"
                f"{json.dumps(proposal, indent=2, default=str)}\n\n"
                "⚠️ Creating an OSD will wipe/claim the data device. "
                "To execute: create_ceph_osd with the same params, "
                f"confirm={proposal['confirm']!r}, dry_run=false."
            )
            return [Content(type="text", text=text)]
        except ValueError:
            raise
        except Exception as e:
            self._handle_error(f"propose Ceph OSD on {node}", e)

    def create_ceph_osd(
        self,
        node: str,
        dev: str,
        confirm: str,
        dry_run: bool = True,
        db_dev: Optional[str] = None,
        wal_dev: Optional[str] = None,
        encrypted: bool = False,
        crush_device_class: Optional[str] = None,
        osds_per_device: Optional[int] = None,
    ) -> List[Content]:
        """Create OSD. Defaults to dry_run=true; confirm must equal exact normalized dev."""
        try:
            proposal = self._build_osd_proposal(
                node,
                dev,
                db_dev=db_dev,
                wal_dev=wal_dev,
                encrypted=encrypted,
                crush_device_class=crush_device_class,
                osds_per_device=osds_per_device,
            )
            expected = proposal["confirm"]
            if confirm != expected:
                raise ValueError(
                    f"confirm must equal the exact device path {expected!r} "
                    f"(got {confirm!r}). Refusing OSD create."
                )
            if dry_run:
                text = (
                    "Ceph OSD create DRY-RUN (no API mutation)\n"
                    f"{json.dumps(proposal, indent=2, default=str)}\n\n"
                    "Re-call with dry_run=false to execute after review."
                )
                return [Content(type="text", text=text)]

            params: dict[str, Any] = {"dev": expected}
            if proposal.get("db_dev"):
                params["db_dev"] = proposal["db_dev"]
            if proposal.get("wal_dev"):
                params["wal_dev"] = proposal["wal_dev"]
            if encrypted:
                params["encrypted"] = 1
            if crush_device_class is not None:
                params["crush-device-class"] = crush_device_class
            if osds_per_device is not None:
                params["osds-per-device"] = int(osds_per_device)

            result = self.proxmox.nodes(node).ceph.osd.post(**params)
            return [
                Content(
                    type="text",
                    text=(
                        f"⚠️ Ceph OSD create initiated on {node} for {expected}\n"
                        f"{upid_response_footer(result, node=node)}\n"
                        f"{privilege_required_note('Ceph OSD create')}\n"
                        "MON/MGR create/destroy remain out of MCP scope."
                    ),
                )
            ]
        except ValueError:
            raise
        except Exception as e:
            self._handle_mutation_error(
                f"create Ceph OSD on {node}",
                e,
                code="ceph_acl_denied",
                path=f"/nodes/{node}/ceph/osd",
            )

    def destroy_ceph_osd(
        self,
        node: str,
        osdid: int,
        confirm: str,
        cleanup: bool = False,
    ) -> List[Content]:
        """Destroy OSD. confirm must equal str(osdid). OSD must be out+down on PVE side."""
        try:
            expected = str(int(osdid))
            if confirm != expected:
                raise ValueError(
                    f"confirm must equal the exact OSD id string {expected!r} "
                    f"(got {confirm!r}). Refusing OSD destroy."
                )
            params: dict[str, Any] = {}
            if cleanup:
                params["cleanup"] = 1
            result = self.proxmox.nodes(node).ceph.osd(int(osdid)).delete(**params)
            return [
                Content(
                    type="text",
                    text=(
                        f"{destructive_warning('destroyed')}\n"
                        f"⚠️ IRREVERSIBLE: Ceph OSD {expected} destroy initiated on {node}\n"
                        f"cleanup={bool(cleanup)}\n"
                        f"{upid_response_footer(result, node=node)}"
                    ),
                )
            ]
        except ValueError:
            raise
        except Exception as e:
            self._handle_mutation_error(
                f"destroy Ceph OSD {osdid} on {node}",
                e,
                code="ceph_acl_denied",
                path=f"/nodes/{node}/ceph/osd/{osdid}",
            )

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
                        "💡 OSD disks: list_node_disks → propose_ceph_osd → "
                        "create_ceph_osd(confirm=<dev>, dry_run=false). "
                        "MON/MGR create/destroy stay out of scope."
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

    def _build_osd_proposal(
        self,
        node: str,
        dev: str,
        *,
        db_dev: Optional[str] = None,
        wal_dev: Optional[str] = None,
        encrypted: bool = False,
        crush_device_class: Optional[str] = None,
        osds_per_device: Optional[int] = None,
    ) -> dict:
        norm = _normalize_dev(dev)
        db_n = _normalize_dev(db_dev) if db_dev else None
        wal_n = _normalize_dev(wal_dev) if wal_dev else None
        warnings: list[str] = []
        match: Optional[dict] = None
        try:
            disks = self.proxmox.nodes(node).disks.list.get() or []
            for d in disks:
                if not isinstance(d, dict):
                    continue
                if d.get("devpath") == norm:
                    match = d
                    break
            if match is None:
                warnings.append(
                    f"Device {norm} not found in disks/list — verify path before dry_run=false."
                )
            elif not _disk_is_free(match):
                warnings.append(
                    f"Device {norm} looks in-use (used={match.get('used')!r}, "
                    f"osdid={match.get('osdid')!r}). Creating an OSD may destroy data."
                )
            else:
                warnings.append(f"Device {norm} appears free/unused on {node}.")
        except Exception as e:
            warnings.append(f"Could not verify disks/list ({e}); proceed with caution.")

        return {
            "node": node,
            "dev": norm,
            "confirm": norm,
            "db_dev": db_n,
            "wal_dev": wal_n,
            "encrypted": bool(encrypted),
            "crush_device_class": crush_device_class,
            "osds_per_device": osds_per_device,
            "disk": match,
            "warnings": warnings,
            "api": f"POST /nodes/{node}/ceph/osd",
        }
