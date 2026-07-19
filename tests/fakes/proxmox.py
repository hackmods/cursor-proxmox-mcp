"""Chainable fake for proxmoxer.ProxmoxAPI used in unit tests."""
from __future__ import annotations

from typing import Dict, List, Optional
from unittest.mock import MagicMock


class _Missing(Exception):
    pass


def make_fake_proxmox(
    *,
    nodes: Optional[List[dict]] = None,
    qemu: Optional[Dict[str, dict]] = None,
    lxc: Optional[Dict[str, dict]] = None,
    storage_list: Optional[List[dict]] = None,
) -> MagicMock:
    """Build a MagicMock that supports common proxmoxer chaining."""
    api = MagicMock()
    node_name = (nodes or [{"node": "pve"}])[0]["node"]
    qemu = qemu or {}
    lxc = lxc or {}
    storage_list = storage_list or [
        {
            "storage": "local-lvm",
            "type": "lvmthin",
            "content": "images,rootdir",
            "enabled": True,
            "node": node_name,
        },
        {
            "storage": "local",
            "type": "dir",
            "content": "iso,vztmpl,backup",
            "enabled": True,
            "node": node_name,
        },
    ]

    api.nodes.get.return_value = nodes or [{"node": node_name, "status": "online"}]
    api.version.get.return_value = {"version": "8.0"}
    api.storage.get.return_value = storage_list
    api.cluster.status.get.return_value = [{"type": "cluster", "name": "test"}]
    api.cluster.nextid.get.return_value = 200
    api.cluster.resources.get.return_value = []
    api.cluster.log.get.return_value = []
    api.cluster.options.get.return_value = {}
    api.cluster.ha.status.current.get.return_value = []
    api.cluster.ha.groups.get.return_value = []
    api.cluster.ha.resources.get.return_value = []
    api.cluster.firewall.options.get.return_value = {"enable": 0}
    api.cluster.firewall.rules.get.return_value = []
    api.cluster.firewall.aliases.get.return_value = []
    api.cluster.firewall.ipset.get.return_value = []
    api.cluster.firewall.macros.get.return_value = []
    api.cluster.replication.get.return_value = []
    api.cluster.backup.get.return_value = []
    api.cluster.backup.post.return_value = "ok"
    api.cluster.backup.return_value.delete.return_value = "ok"
    api.access.users.get.return_value = []
    api.access.groups.get.return_value = []
    api.access.roles.get.return_value = []
    api.access.acl.get.return_value = []
    api.access.permissions.get.return_value = {}
    api.cluster.sdn.zones.get.return_value = []
    api.cluster.sdn.vnets.get.return_value = []
    api.cluster.sdn.controllers.get.return_value = []
    api.cluster.sdn.ipams.get.return_value = []
    api.cluster.sdn.dns.get.return_value = []
    api.cluster.acme.plugins.get.return_value = []
    api.cluster.acme.account.get.return_value = []
    api.cluster.acme.directories.get.return_value = []
    api.pools.get.return_value = []

    def nodes_call(name: str = node_name) -> MagicMock:
        node = MagicMock()
        node.status.get.return_value = {"status": "online", "uptime": 1}
        node.network.get.return_value = [{"iface": "vmbr0", "type": "bridge"}]
        node.subscription.get.return_value = {"status": "notfound"}
        node.certificates.get.return_value = []
        node.report.get.return_value = "ok"
        node.services.get.return_value = []
        node.time.get.return_value = {"time": "now"}
        node.wakeonlan.post.return_value = "ok"
        node.storage.get.return_value = storage_list

        def storage_call(store: str) -> MagicMock:
            st = MagicMock()
            st.status.get.return_value = {"used": 1, "total": 10, "avail": 9}
            st.content.get.return_value = [
                {"volid": f"{store}:vztmpl/ubuntu.tar.zst", "content": "vztmpl"},
                {"volid": f"{store}:iso/debian.iso", "content": "iso"},
            ]
            st.content.return_value.delete.return_value = "ok"
            st.__call__ = MagicMock(
                return_value=MagicMock(post=MagicMock(return_value="UPID:dl"))
            )
            # download-url path: storage(store)("download-url").post
            dl = MagicMock()
            dl.post.return_value = "UPID:dl"
            st.side_effect = None

            def storage_subpath(path: str) -> MagicMock:
                m = MagicMock()
                m.post.return_value = "UPID:dl"
                return m

            st.__call__ = storage_subpath  # type: ignore
            return st

        node.storage.side_effect = storage_call
        node.storage.get.return_value = storage_list

        def qemu_list() -> List[dict]:
            return [
                {
                    "vmid": vid,
                    "name": meta.get("name", f"vm-{vid}"),
                    "status": meta.get("status", "stopped"),
                    "mem": 0,
                    "maxmem": 1024,
                }
                for vid, meta in qemu.items()
            ]

        node.qemu.get.side_effect = qemu_list

        def qemu_call(vmid: str) -> MagicMock:
            q = MagicMock()
            meta = qemu.get(str(vmid))
            if meta is None and str(vmid) not in qemu:

                def missing(*_a, **_k) -> None:
                    raise Exception(
                        f"Configuration file 'nodes/{name}/qemu-server/{vmid}.conf' does not exist"
                    )

                q.config.get.side_effect = missing
                q.status.current.get.side_effect = missing
                q.status.start.post.side_effect = missing
                q.status.stop.post.side_effect = missing
                q.status.shutdown.post.side_effect = missing
                q.status.reset.post.side_effect = missing
                q.status.reboot.post.side_effect = missing
                q.status.suspend.post.side_effect = missing
                q.status.resume.post.side_effect = missing
                q.clone.post.side_effect = missing
                q.resize.put.side_effect = missing
                q.template.post.side_effect = missing
                q.vncproxy.post.side_effect = missing
                q.spiceproxy.post.side_effect = missing
                q.termproxy.post.side_effect = missing
                q.rrddata.get.side_effect = missing
                q.delete.side_effect = missing
                return q

            q.config.get.return_value = {
                "cores": 2,
                "name": (meta or {}).get("name", f"vm-{vmid}"),
                **(meta or {}),
            }
            status = (meta or {}).get("status", "stopped")
            q.status.current.get.return_value = {
                "status": status,
                "name": (meta or {}).get("name", f"vm-{vmid}"),
            }
            q.status.start.post.return_value = "UPID:start"
            q.status.stop.post.return_value = "UPID:stop"
            q.status.shutdown.post.return_value = "UPID:shutdown"
            q.status.reset.post.return_value = "UPID:reset"
            q.status.reboot.post.return_value = "UPID:reboot"
            q.status.suspend.post.return_value = "UPID:suspend"
            q.status.resume.post.return_value = "UPID:resume"
            q.delete.return_value = "UPID:delete"
            q.clone.post.return_value = "UPID:clone"
            q.resize.put.return_value = "ok"
            q.template.post.return_value = "ok"
            q.config.put.return_value = "ok"
            q.vncproxy.post.return_value = {"ticket": "t", "port": 1}
            q.spiceproxy.post.return_value = {"ticket": "t"}
            q.termproxy.post.return_value = {"ticket": "t"}
            q.rrddata.get.return_value = []
            q.pending.get.return_value = []
            q.move_disk.post.return_value = "UPID:movedisk"
            q.snapshot.get.return_value = []
            q.snapshot.post.return_value = "UPID:snap"
            q.snapshot.return_value.delete.return_value = "UPID:delsnap"
            q.snapshot.return_value.rollback.post.return_value = "UPID:rb"
            q.firewall.rules.get.return_value = []
            q.firewall.rules.post.return_value = "ok"
            q.firewall.rules.return_value.delete.return_value = "ok"
            q.firewall.options.get.return_value = {}
            q.firewall.options.put.return_value = "ok"
            q.migrate.post.return_value = "UPID:mig"

            agent = MagicMock()

            def agent_path(path: str) -> MagicMock:
                m = MagicMock()
                if path == "exec":
                    m.post.return_value = {"pid": 42}
                elif path == "exec-status":
                    m.get.return_value = {
                        "exited": 1,
                        "exitcode": 0,
                        "out-data": "hello",
                        "err-data": "",
                    }
                return m

            agent.side_effect = agent_path
            q.agent = agent
            return q

        node.qemu.side_effect = qemu_call
        node.qemu.create = MagicMock(return_value="UPID:createvm")

        def lxc_list() -> List[dict]:
            return [
                {
                    "vmid": vid,
                    "name": meta.get("hostname", f"ct-{vid}"),
                    "status": meta.get("status", "stopped"),
                    "mem": 0,
                    "maxmem": 1024,
                }
                for vid, meta in lxc.items()
            ]

        node.lxc.get.side_effect = lxc_list

        def lxc_call(vmid: str) -> MagicMock:
            c = MagicMock()
            meta = lxc.get(str(vmid))
            if meta is None and str(vmid) not in lxc:

                def missing(*_a, **_k) -> None:
                    raise Exception("Configuration file does not exist")

                c.config.get.side_effect = missing
                c.status.current.get.side_effect = missing
                c.status.start.post.side_effect = missing
                c.status.stop.post.side_effect = missing
                c.status.shutdown.post.side_effect = missing
                c.status.reboot.post.side_effect = missing
                c.status.suspend.post.side_effect = missing
                c.status.resume.post.side_effect = missing
                c.clone.post.side_effect = missing
                c.resize.put.side_effect = missing
                c.template.post.side_effect = missing
                c.vncproxy.post.side_effect = missing
                c.spiceproxy.post.side_effect = missing
                c.termproxy.post.side_effect = missing
                c.rrddata.get.side_effect = missing
                c.delete.side_effect = missing
                return c

            c.config.get.return_value = {
                "hostname": (meta or {}).get("hostname", f"ct-{vmid}"),
                "cores": 1,
                **(meta or {}),
            }
            status = (meta or {}).get("status", "stopped")
            c.status.current.get.return_value = {
                "status": status,
                "name": (meta or {}).get("hostname", f"ct-{vmid}"),
            }
            c.status.start.post.return_value = "UPID:start"
            c.status.stop.post.return_value = "UPID:stop"
            c.status.shutdown.post.return_value = "UPID:shutdown"
            c.status.reboot.post.return_value = "UPID:reboot"
            c.status.suspend.post.return_value = "UPID:suspend"
            c.status.resume.post.return_value = "UPID:resume"
            c.delete.return_value = "UPID:delete"
            c.clone.post.return_value = "UPID:clone"
            c.resize.put.return_value = "ok"
            c.template.post.return_value = "ok"
            c.config.put.return_value = "ok"
            c.vncproxy.post.return_value = {"ticket": "t"}
            c.spiceproxy.post.return_value = {"ticket": "t"}
            c.termproxy.post.return_value = {"ticket": "t"}
            c.rrddata.get.return_value = []
            c.pending.get.return_value = []
            c.move_volume.post.return_value = "UPID:movevol"
            c.snapshot.get.return_value = []
            c.snapshot.post.return_value = "UPID:snap"
            c.exec.post.return_value = {"exitcode": 0, "stdout": "ok"}
            c.firewall.rules.get.return_value = []
            c.firewall.options.get.return_value = {}
            c.migrate.post.return_value = "UPID:mig"
            return c

        node.lxc.side_effect = lxc_call
        node.lxc.create = MagicMock(return_value="UPID:createct")
        node.tasks.get.return_value = []
        node.tasks.return_value.status.get.return_value = {"status": "stopped", "exitstatus": "OK"}
        node.vzdump.post.return_value = "UPID:backup"
        return node

    api.nodes.side_effect = nodes_call
    api.storage.post.return_value = "ok"
    api.storage.return_value.put.return_value = "ok"
    api.storage.return_value.delete.return_value = "ok"
    api.pools.post.return_value = "ok"
    api.pools.return_value.get.return_value = {"poolid": "p"}
    api.pools.return_value.put.return_value = "ok"
    api.pools.return_value.delete.return_value = "ok"
    api.access.users.post.return_value = "ok"
    api.access.users.return_value.get.return_value = {"userid": "u@pve"}
    api.access.users.return_value.delete.return_value = "ok"
    api.access.users.return_value.token.get.return_value = []
    api.access.users.return_value.token.return_value.post.return_value = {
        "value": "secret-once",
        "full-tokenid": "u@pve!t",
    }
    api.access.users.return_value.token.return_value.delete.return_value = "ok"
    api.access.groups.post.return_value = "ok"
    api.access.groups.return_value.delete.return_value = "ok"
    api.access.acl.put.return_value = "ok"
    api.cluster.ha.groups.post.return_value = "ok"
    api.cluster.ha.groups.return_value.delete.return_value = "ok"
    api.cluster.ha.resources.post.return_value = "ok"
    api.cluster.ha.resources.return_value.put.return_value = "ok"
    api.cluster.ha.resources.return_value.delete.return_value = "ok"
    api.cluster.firewall.rules.post.return_value = "ok"
    api.cluster.firewall.rules.return_value.delete.return_value = "ok"
    api.cluster.firewall.options.put.return_value = "ok"
    api.cluster.firewall.aliases.post.return_value = "ok"
    api.cluster.firewall.aliases.return_value.delete.return_value = "ok"
    api.cluster.firewall.ipset.post.return_value = "ok"
    api.cluster.firewall.ipset.return_value.get.return_value = []
    api.cluster.firewall.ipset.return_value.post.return_value = "ok"
    api.cluster.firewall.ipset.return_value.delete.return_value = "ok"
    api.cluster.firewall.ipset.return_value.return_value.delete.return_value = "ok"
    api.cluster.replication.post.return_value = "ok"
    api.cluster.replication.return_value.put.return_value = "ok"
    api.cluster.replication.return_value.delete.return_value = "ok"
    api.cluster.sdn.apply.put.return_value = "ok"
    return api
