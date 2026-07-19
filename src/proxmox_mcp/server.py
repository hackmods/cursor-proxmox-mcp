"""
Main server implementation for Proxmox MCP.

Formal Cursor ↔ Proxmox VE integration: VMs, LXC, storage, cluster, HA,
firewall, access control, backups, snapshots, migration, and tasks.
"""
from __future__ import annotations

import os
import sys
import signal
from typing import Optional, Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from .config.loader import load_config
from .core.logging import setup_logging
from .core.proxmox import ProxmoxManager
from .tools.node import NodeTools
from .tools.vm import VMTools
from .tools.container import ContainerTools
from .tools.storage import StorageTools
from .tools.cluster import ClusterTools
from .tools.tasks import TaskTools
from .tools.snapshot import SnapshotTools
from .tools.backup import BackupTools
from .tools.migrate import MigrateTools
from .tools.ha import HATools
from .tools.firewall import FirewallTools
from .tools.access import AccessTools
from .tools.network import NetworkTools
from .tools import definitions as D


class ProxmoxMCPServer:
    """Main server class for Proxmox MCP."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = load_config(config_path)
        self.logger = setup_logging(self.config.logging)

        self.proxmox_manager = ProxmoxManager(self.config.proxmox, self.config.auth)
        self.proxmox = self.proxmox_manager.get_api()

        self.node_tools = NodeTools(self.proxmox)
        self.vm_tools = VMTools(self.proxmox)
        self.container_tools = ContainerTools(self.proxmox)
        self.storage_tools = StorageTools(self.proxmox)
        self.cluster_tools = ClusterTools(self.proxmox)
        self.task_tools = TaskTools(self.proxmox)
        self.snapshot_tools = SnapshotTools(self.proxmox)
        self.backup_tools = BackupTools(self.proxmox)
        self.migrate_tools = MigrateTools(self.proxmox)
        self.ha_tools = HATools(self.proxmox)
        self.firewall_tools = FirewallTools(self.proxmox)
        self.access_tools = AccessTools(self.proxmox)
        self.network_tools = NetworkTools(self.proxmox)

        self.mcp = FastMCP("ProxmoxMCP")
        self._setup_tools()

    def _setup_tools(self) -> None:
        """Register all MCP tools. Source of truth for Available Tools docs."""

        # --- Nodes ---
        @self.mcp.tool(description=D.GET_NODES_DESC)
        def get_nodes():
            return self.node_tools.get_nodes()

        @self.mcp.tool(description=D.GET_NODE_STATUS_DESC)
        def get_node_status(
            node: Annotated[str, Field(description="Node name")],
        ):
            return self.node_tools.get_node_status(node)

        @self.mcp.tool(description=D.LIST_NODE_NETWORKS_DESC)
        def list_node_networks(
            node: Annotated[str, Field(description="Node name")],
        ):
            return self.network_tools.list_node_networks(node)

        # --- Cluster / tasks ---
        @self.mcp.tool(description=D.GET_CLUSTER_STATUS_DESC)
        def get_cluster_status():
            return self.cluster_tools.get_cluster_status()

        @self.mcp.tool(description=D.GET_NEXT_VMID_DESC)
        def get_next_vmid():
            return self.cluster_tools.get_next_vmid()

        @self.mcp.tool(description=D.GET_TASK_STATUS_DESC)
        def get_task_status(
            node: Annotated[str, Field(description="Node name")],
            upid: Annotated[str, Field(description="Task UPID")],
        ):
            return self.task_tools.get_task_status(node, upid)

        @self.mcp.tool(description=D.LIST_TASKS_DESC)
        def list_tasks(
            node: Annotated[str, Field(description="Node name")],
        ):
            return self.task_tools.list_tasks(node)

        # --- QEMU VMs ---
        @self.mcp.tool(description=D.GET_VMS_DESC)
        def get_vms():
            return self.vm_tools.get_vms()

        @self.mcp.tool(description=D.CREATE_VM_DESC)
        def create_vm(
            node: Annotated[str, Field(description="Node name")],
            vmid: Annotated[str, Field(description="New VM ID")],
            name: Annotated[str, Field(description="VM name")],
            cpus: Annotated[int, Field(description="CPU cores", ge=1, le=32)],
            memory: Annotated[int, Field(description="Memory MB", ge=512, le=131072)],
            disk_size: Annotated[int, Field(description="Disk GB", ge=5, le=1000)],
            storage: Annotated[Optional[str], Field(description="Storage", default=None)] = None,
            ostype: Annotated[Optional[str], Field(description="OS type", default=None)] = None,
        ):
            return self.vm_tools.create_vm(node, vmid, name, cpus, memory, disk_size, storage, ostype)

        @self.mcp.tool(description=D.GET_VM_CONFIG_DESC)
        def get_vm_config(
            node: Annotated[str, Field(description="Node name")],
            vmid: Annotated[str, Field(description="VM ID")],
        ):
            return self.vm_tools.get_vm_config(node, vmid)

        @self.mcp.tool(description=D.UPDATE_VM_CONFIG_DESC)
        def update_vm_config(
            node: Annotated[str, Field(description="Node name")],
            vmid: Annotated[str, Field(description="VM ID")],
            cores: Annotated[Optional[int], Field(description="CPU cores", default=None)] = None,
            memory: Annotated[Optional[int], Field(description="Memory MB", default=None)] = None,
            name: Annotated[Optional[str], Field(description="VM name", default=None)] = None,
            net0: Annotated[Optional[str], Field(description="net0 config", default=None)] = None,
            onboot: Annotated[Optional[bool], Field(description="Start on boot", default=None)] = None,
            agent: Annotated[Optional[str], Field(description="QEMU agent", default=None)] = None,
        ):
            kwargs = {}
            if cores is not None:
                kwargs["cores"] = cores
            if memory is not None:
                kwargs["memory"] = memory
            if name is not None:
                kwargs["name"] = name
            if net0 is not None:
                kwargs["net0"] = net0
            if onboot is not None:
                kwargs["onboot"] = 1 if onboot else 0
            if agent is not None:
                kwargs["agent"] = agent
            return self.vm_tools.update_vm_config(node, vmid, **kwargs)

        @self.mcp.tool(description=D.EXECUTE_VM_COMMAND_DESC)
        async def execute_vm_command(
            node: Annotated[str, Field(description="Node name")],
            vmid: Annotated[str, Field(description="VM ID")],
            command: Annotated[str, Field(description="Shell command")],
        ):
            return await self.vm_tools.execute_command(node, vmid, command)

        @self.mcp.tool(description=D.START_VM_DESC)
        def start_vm(node: Annotated[str, Field(description="Node")], vmid: Annotated[str, Field(description="VM ID")]):
            return self.vm_tools.start_vm(node, vmid)

        @self.mcp.tool(description=D.STOP_VM_DESC)
        def stop_vm(node: Annotated[str, Field(description="Node")], vmid: Annotated[str, Field(description="VM ID")]):
            return self.vm_tools.stop_vm(node, vmid)

        @self.mcp.tool(description=D.SHUTDOWN_VM_DESC)
        def shutdown_vm(node: Annotated[str, Field(description="Node")], vmid: Annotated[str, Field(description="VM ID")]):
            return self.vm_tools.shutdown_vm(node, vmid)

        @self.mcp.tool(description=D.RESET_VM_DESC)
        def reset_vm(node: Annotated[str, Field(description="Node")], vmid: Annotated[str, Field(description="VM ID")]):
            return self.vm_tools.reset_vm(node, vmid)

        @self.mcp.tool(description=D.REBOOT_VM_DESC)
        def reboot_vm(node: Annotated[str, Field(description="Node")], vmid: Annotated[str, Field(description="VM ID")]):
            return self.vm_tools.reboot_vm(node, vmid)

        @self.mcp.tool(description=D.SUSPEND_VM_DESC)
        def suspend_vm(node: Annotated[str, Field(description="Node")], vmid: Annotated[str, Field(description="VM ID")]):
            return self.vm_tools.suspend_vm(node, vmid)

        @self.mcp.tool(description=D.RESUME_VM_DESC)
        def resume_vm(node: Annotated[str, Field(description="Node")], vmid: Annotated[str, Field(description="VM ID")]):
            return self.vm_tools.resume_vm(node, vmid)

        @self.mcp.tool(description=D.DELETE_VM_DESC)
        def delete_vm(
            node: Annotated[str, Field(description="Node")],
            vmid: Annotated[str, Field(description="VM ID")],
            force: Annotated[bool, Field(description="Force if running", default=False)] = False,
        ):
            return self.vm_tools.delete_vm(node, vmid, force)

        @self.mcp.tool(description=D.CLONE_VM_DESC)
        def clone_vm(
            node: Annotated[str, Field(description="Node")],
            vmid: Annotated[str, Field(description="Source VM ID")],
            newid: Annotated[str, Field(description="New VM ID")],
            name: Annotated[Optional[str], Field(description="New name", default=None)] = None,
            full: Annotated[bool, Field(description="Full clone", default=True)] = True,
            target: Annotated[Optional[str], Field(description="Target node", default=None)] = None,
            storage: Annotated[Optional[str], Field(description="Target storage", default=None)] = None,
        ):
            return self.vm_tools.clone_vm(node, vmid, newid, name, full, target, storage)

        @self.mcp.tool(description=D.RESIZE_VM_DISK_DESC)
        def resize_vm_disk(
            node: Annotated[str, Field(description="Node")],
            vmid: Annotated[str, Field(description="VM ID")],
            disk: Annotated[str, Field(description="Disk id e.g. scsi0")],
            size: Annotated[str, Field(description="Size e.g. +10G")],
        ):
            return self.vm_tools.resize_vm_disk(node, vmid, disk, size)

        @self.mcp.tool(description=D.CONVERT_VM_TEMPLATE_DESC)
        def convert_vm_to_template(
            node: Annotated[str, Field(description="Node")],
            vmid: Annotated[str, Field(description="VM ID")],
        ):
            return self.vm_tools.convert_vm_to_template(node, vmid)

        # --- LXC ---
        @self.mcp.tool(description=D.GET_CONTAINERS_DESC)
        def get_containers():
            return self.container_tools.get_containers()

        @self.mcp.tool(description=D.CREATE_LXC_DESC)
        def create_lxc(
            node: Annotated[str, Field(description="Node")],
            vmid: Annotated[str, Field(description="New CT ID")],
            hostname: Annotated[str, Field(description="Hostname")],
            ostemplate: Annotated[str, Field(description="OS template path")],
            cpus: Annotated[int, Field(description="Cores", ge=1, le=32)],
            memory: Annotated[int, Field(description="Memory MB", ge=512, le=131072)],
            disk_size: Annotated[int, Field(description="Disk GB", ge=4, le=1000)],
            storage: Annotated[Optional[str], Field(description="Storage", default=None)] = None,
            features: Annotated[Optional[str], Field(description="Features", default=None)] = None,
            password: Annotated[Optional[str], Field(description="Root password", default=None)] = None,
            unprivileged: Annotated[bool, Field(description="Unprivileged", default=True)] = True,
        ):
            return self.container_tools.create_lxc(
                node, vmid, hostname, ostemplate, cpus, memory, disk_size,
                storage, features, password, unprivileged,
            )

        @self.mcp.tool(description=D.GET_LXC_CONFIG_DESC)
        def get_lxc_config(
            node: Annotated[str, Field(description="Node")],
            vmid: Annotated[str, Field(description="CT ID")],
        ):
            return self.container_tools.get_lxc_config(node, vmid)

        @self.mcp.tool(description=D.UPDATE_LXC_CONFIG_DESC)
        def update_lxc_config(
            node: Annotated[str, Field(description="Node")],
            vmid: Annotated[str, Field(description="CT ID")],
            cores: Annotated[Optional[int], Field(description="Cores", default=None)] = None,
            memory: Annotated[Optional[int], Field(description="Memory MB", default=None)] = None,
            hostname: Annotated[Optional[str], Field(description="Hostname", default=None)] = None,
            net0: Annotated[Optional[str], Field(description="net0", default=None)] = None,
            features: Annotated[Optional[str], Field(description="Features", default=None)] = None,
        ):
            kwargs = {}
            if cores is not None:
                kwargs["cores"] = cores
            if memory is not None:
                kwargs["memory"] = memory
            if hostname is not None:
                kwargs["hostname"] = hostname
            if net0 is not None:
                kwargs["net0"] = net0
            if features is not None:
                kwargs["features"] = features
            return self.container_tools.update_lxc_config(node, vmid, **kwargs)

        @self.mcp.tool(description=D.START_LXC_DESC)
        def start_lxc(node: Annotated[str, Field(description="Node")], vmid: Annotated[str, Field(description="CT ID")]):
            return self.container_tools.start_lxc(node, vmid)

        @self.mcp.tool(description=D.STOP_LXC_DESC)
        def stop_lxc(node: Annotated[str, Field(description="Node")], vmid: Annotated[str, Field(description="CT ID")]):
            return self.container_tools.stop_lxc(node, vmid)

        @self.mcp.tool(description=D.SHUTDOWN_LXC_DESC)
        def shutdown_lxc(node: Annotated[str, Field(description="Node")], vmid: Annotated[str, Field(description="CT ID")]):
            return self.container_tools.shutdown_lxc(node, vmid)

        @self.mcp.tool(description=D.REBOOT_LXC_DESC)
        def reboot_lxc(node: Annotated[str, Field(description="Node")], vmid: Annotated[str, Field(description="CT ID")]):
            return self.container_tools.reboot_lxc(node, vmid)

        @self.mcp.tool(description=D.DELETE_LXC_DESC)
        def delete_lxc(
            node: Annotated[str, Field(description="Node")],
            vmid: Annotated[str, Field(description="CT ID")],
            force: Annotated[bool, Field(description="Force if running", default=False)] = False,
        ):
            return self.container_tools.delete_lxc(node, vmid, force)

        @self.mcp.tool(description=D.UPDATE_LXC_FEATURES_DESC)
        def update_lxc_features(
            node: Annotated[str, Field(description="Node")],
            vmid: Annotated[str, Field(description="CT ID")],
            features: Annotated[str, Field(description="Features string")],
        ):
            return self.container_tools.update_lxc_features(node, vmid, features)

        @self.mcp.tool(description=D.CLONE_LXC_DESC)
        def clone_lxc(
            node: Annotated[str, Field(description="Node")],
            vmid: Annotated[str, Field(description="Source CT ID")],
            newid: Annotated[str, Field(description="New CT ID")],
            hostname: Annotated[Optional[str], Field(description="Hostname", default=None)] = None,
            full: Annotated[bool, Field(description="Full clone", default=True)] = True,
            target: Annotated[Optional[str], Field(description="Target node", default=None)] = None,
            storage: Annotated[Optional[str], Field(description="Storage", default=None)] = None,
        ):
            return self.container_tools.clone_lxc(node, vmid, newid, hostname, full, target, storage)

        @self.mcp.tool(description=D.RESIZE_LXC_DISK_DESC)
        def resize_lxc_disk(
            node: Annotated[str, Field(description="Node")],
            vmid: Annotated[str, Field(description="CT ID")],
            disk: Annotated[str, Field(description="Volume e.g. rootfs")],
            size: Annotated[str, Field(description="Size e.g. +5G")],
        ):
            return self.container_tools.resize_lxc_disk(node, vmid, disk, size)

        @self.mcp.tool(description=D.CONVERT_LXC_TEMPLATE_DESC)
        def convert_lxc_to_template(
            node: Annotated[str, Field(description="Node")],
            vmid: Annotated[str, Field(description="CT ID")],
        ):
            return self.container_tools.convert_lxc_to_template(node, vmid)

        @self.mcp.tool(description=D.EXECUTE_LXC_COMMAND_DESC)
        def execute_lxc_command(
            node: Annotated[str, Field(description="Node")],
            vmid: Annotated[str, Field(description="CT ID")],
            command: Annotated[str, Field(description="Command")],
        ):
            return self.container_tools.execute_lxc_command(node, vmid, command)

        # --- Snapshots ---
        @self.mcp.tool(description=D.LIST_SNAPSHOTS_DESC)
        def list_snapshots(
            node: Annotated[str, Field(description="Node")],
            vmid: Annotated[str, Field(description="Guest ID")],
            guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
        ):
            return self.snapshot_tools.list_snapshots(node, vmid, guest_type)

        @self.mcp.tool(description=D.CREATE_SNAPSHOT_DESC)
        def create_snapshot(
            node: Annotated[str, Field(description="Node")],
            vmid: Annotated[str, Field(description="Guest ID")],
            snapname: Annotated[str, Field(description="Snapshot name")],
            guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
            description: Annotated[Optional[str], Field(description="Description", default=None)] = None,
            vmstate: Annotated[bool, Field(description="Include RAM (qemu)", default=False)] = False,
        ):
            return self.snapshot_tools.create_snapshot(
                node, vmid, snapname, guest_type, description, vmstate
            )

        @self.mcp.tool(description=D.DELETE_SNAPSHOT_DESC)
        def delete_snapshot(
            node: Annotated[str, Field(description="Node")],
            vmid: Annotated[str, Field(description="Guest ID")],
            snapname: Annotated[str, Field(description="Snapshot name")],
            guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
        ):
            return self.snapshot_tools.delete_snapshot(node, vmid, snapname, guest_type)

        @self.mcp.tool(description=D.ROLLBACK_SNAPSHOT_DESC)
        def rollback_snapshot(
            node: Annotated[str, Field(description="Node")],
            vmid: Annotated[str, Field(description="Guest ID")],
            snapname: Annotated[str, Field(description="Snapshot name")],
            guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
        ):
            return self.snapshot_tools.rollback_snapshot(node, vmid, snapname, guest_type)

        # --- Backups ---
        @self.mcp.tool(description=D.CREATE_BACKUP_DESC)
        def create_backup(
            node: Annotated[str, Field(description="Node")],
            vmid: Annotated[str, Field(description="Guest ID")],
            storage: Annotated[Optional[str], Field(description="Backup storage", default=None)] = None,
            mode: Annotated[str, Field(description="snapshot|suspend|stop", default="snapshot")] = "snapshot",
            compress: Annotated[str, Field(description="zstd|gzip|lzo|0", default="zstd")] = "zstd",
            notes: Annotated[Optional[str], Field(description="Notes", default=None)] = None,
        ):
            return self.backup_tools.create_backup(node, vmid, storage, mode, compress, notes)

        @self.mcp.tool(description=D.LIST_BACKUPS_DESC)
        def list_backups(
            node: Annotated[str, Field(description="Node")],
            storage: Annotated[str, Field(description="Storage")],
            vmid: Annotated[Optional[str], Field(description="Filter VMID", default=None)] = None,
        ):
            return self.backup_tools.list_backups(node, storage, vmid)

        @self.mcp.tool(description=D.RESTORE_BACKUP_DESC)
        def restore_backup(
            node: Annotated[str, Field(description="Node")],
            archive: Annotated[str, Field(description="Archive volid")],
            vmid: Annotated[str, Field(description="Target VMID")],
            storage: Annotated[Optional[str], Field(description="Storage", default=None)] = None,
            force: Annotated[bool, Field(description="Overwrite", default=False)] = False,
            guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
        ):
            return self.backup_tools.restore_backup(node, archive, vmid, storage, force, guest_type)

        @self.mcp.tool(description=D.DELETE_BACKUP_DESC)
        def delete_backup(
            node: Annotated[str, Field(description="Node")],
            storage: Annotated[str, Field(description="Storage")],
            volume: Annotated[str, Field(description="Volume id")],
        ):
            return self.backup_tools.delete_backup(node, storage, volume)

        # --- Storage ---
        @self.mcp.tool(description=D.GET_STORAGE_DESC)
        def get_storage():
            return self.storage_tools.get_storage()

        @self.mcp.tool(description=D.GET_STORAGE_CONTENT_DESC)
        def get_storage_content(
            node: Annotated[str, Field(description="Node")],
            storage: Annotated[str, Field(description="Storage")],
            content: Annotated[Optional[str], Field(description="iso|vztmpl|backup|images", default=None)] = None,
        ):
            return self.storage_tools.get_storage_content(node, storage, content)

        @self.mcp.tool(description=D.DELETE_STORAGE_CONTENT_DESC)
        def delete_storage_content(
            node: Annotated[str, Field(description="Node")],
            storage: Annotated[str, Field(description="Storage")],
            volume: Annotated[str, Field(description="Volume id")],
        ):
            return self.storage_tools.delete_storage_content(node, storage, volume)

        @self.mcp.tool(description=D.DOWNLOAD_URL_TO_STORAGE_DESC)
        def download_url_to_storage(
            node: Annotated[str, Field(description="Node")],
            storage: Annotated[str, Field(description="Storage")],
            url: Annotated[str, Field(description="Download URL")],
            filename: Annotated[Optional[str], Field(description="Filename", default=None)] = None,
            content: Annotated[str, Field(description="iso or vztmpl", default="iso")] = "iso",
        ):
            return self.storage_tools.download_url_to_storage(node, storage, url, filename, content)

        @self.mcp.tool(description=D.CREATE_STORAGE_DESC)
        def create_storage(
            storage: Annotated[str, Field(description="Storage id")],
            type: Annotated[str, Field(description="dir|nfs|cifs|lvm|rbd|...")],
            content: Annotated[Optional[str], Field(description="Content types", default=None)] = None,
            path: Annotated[Optional[str], Field(description="Path (dir)", default=None)] = None,
            server: Annotated[Optional[str], Field(description="Server", default=None)] = None,
            export: Annotated[Optional[str], Field(description="NFS export", default=None)] = None,
            vgname: Annotated[Optional[str], Field(description="LVM VG", default=None)] = None,
            pool: Annotated[Optional[str], Field(description="RBD pool", default=None)] = None,
            monhost: Annotated[Optional[str], Field(description="Ceph mons", default=None)] = None,
            username: Annotated[Optional[str], Field(description="Username", default=None)] = None,
            password: Annotated[Optional[str], Field(description="Password", default=None)] = None,
            nodes: Annotated[Optional[str], Field(description="Node list", default=None)] = None,
            disable: Annotated[bool, Field(description="Disable", default=False)] = False,
        ):
            return self.storage_tools.create_storage(
                storage, type, content, path, server, export, vgname, pool,
                monhost, username, password, nodes, disable,
            )

        @self.mcp.tool(description=D.UPDATE_STORAGE_DESC)
        def update_storage(
            storage: Annotated[str, Field(description="Storage id")],
            content: Annotated[Optional[str], Field(description="Content", default=None)] = None,
            nodes: Annotated[Optional[str], Field(description="Nodes", default=None)] = None,
            disable: Annotated[Optional[bool], Field(description="Disable", default=None)] = None,
        ):
            return self.storage_tools.update_storage(storage, content, nodes, disable)

        @self.mcp.tool(description=D.DELETE_STORAGE_DESC)
        def delete_storage(storage: Annotated[str, Field(description="Storage id")]):
            return self.storage_tools.delete_storage(storage)

        # --- Migrate ---
        @self.mcp.tool(description=D.MIGRATE_GUEST_DESC)
        def migrate_guest(
            node: Annotated[str, Field(description="Source node")],
            vmid: Annotated[str, Field(description="Guest ID")],
            target: Annotated[str, Field(description="Target node")],
            guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
            online: Annotated[bool, Field(description="Online migrate", default=True)] = True,
            with_local_disks: Annotated[bool, Field(description="Migrate local disks", default=False)] = False,
        ):
            return self.migrate_tools.migrate_guest(
                node, vmid, target, guest_type, online, with_local_disks
            )

        # --- HA ---
        @self.mcp.tool(description=D.GET_HA_STATUS_DESC)
        def get_ha_status():
            return self.ha_tools.get_ha_status()

        @self.mcp.tool(description=D.LIST_HA_GROUPS_DESC)
        def list_ha_groups():
            return self.ha_tools.list_ha_groups()

        @self.mcp.tool(description=D.CREATE_HA_GROUP_DESC)
        def create_ha_group(
            group: Annotated[str, Field(description="Group id")],
            nodes: Annotated[str, Field(description="Nodes e.g. pve1:100,pve2")],
            comment: Annotated[Optional[str], Field(description="Comment", default=None)] = None,
        ):
            return self.ha_tools.create_ha_group(group, nodes, comment)

        @self.mcp.tool(description=D.DELETE_HA_GROUP_DESC)
        def delete_ha_group(group: Annotated[str, Field(description="Group id")]):
            return self.ha_tools.delete_ha_group(group)

        @self.mcp.tool(description=D.LIST_HA_RESOURCES_DESC)
        def list_ha_resources():
            return self.ha_tools.list_ha_resources()

        @self.mcp.tool(description=D.CREATE_HA_RESOURCE_DESC)
        def create_ha_resource(
            sid: Annotated[str, Field(description="e.g. vm:100")],
            group: Annotated[Optional[str], Field(description="HA group", default=None)] = None,
            state: Annotated[str, Field(description="started|stopped|ignored", default="started")] = "started",
            comment: Annotated[Optional[str], Field(description="Comment", default=None)] = None,
        ):
            return self.ha_tools.create_ha_resource(sid, group, state, comment)

        @self.mcp.tool(description=D.UPDATE_HA_RESOURCE_DESC)
        def update_ha_resource(
            sid: Annotated[str, Field(description="Resource id")],
            group: Annotated[Optional[str], Field(description="Group", default=None)] = None,
            state: Annotated[Optional[str], Field(description="State", default=None)] = None,
            comment: Annotated[Optional[str], Field(description="Comment", default=None)] = None,
        ):
            return self.ha_tools.update_ha_resource(sid, group, state, comment)

        @self.mcp.tool(description=D.DELETE_HA_RESOURCE_DESC)
        def delete_ha_resource(sid: Annotated[str, Field(description="Resource id")]):
            return self.ha_tools.delete_ha_resource(sid)

        # --- Firewall ---
        @self.mcp.tool(description=D.GET_CLUSTER_FW_OPTIONS_DESC)
        def get_cluster_firewall_options():
            return self.firewall_tools.get_cluster_firewall_options()

        @self.mcp.tool(description=D.SET_CLUSTER_FW_OPTIONS_DESC)
        def set_cluster_firewall_options(
            enable: Annotated[Optional[bool], Field(description="Enable", default=None)] = None,
            policy_in: Annotated[Optional[str], Field(description="ACCEPT|REJECT|DROP", default=None)] = None,
            policy_out: Annotated[Optional[str], Field(description="ACCEPT|REJECT|DROP", default=None)] = None,
        ):
            return self.firewall_tools.set_cluster_firewall_options(enable, policy_in, policy_out)

        @self.mcp.tool(description=D.LIST_CLUSTER_FW_RULES_DESC)
        def list_cluster_firewall_rules():
            return self.firewall_tools.list_cluster_firewall_rules()

        @self.mcp.tool(description=D.CREATE_CLUSTER_FW_RULE_DESC)
        def create_cluster_firewall_rule(
            action: Annotated[str, Field(description="ACCEPT|DROP|REJECT")],
            type: Annotated[str, Field(description="in|out|group")],
            enable: Annotated[bool, Field(description="Enable", default=True)] = True,
            source: Annotated[Optional[str], Field(description="Source", default=None)] = None,
            dest: Annotated[Optional[str], Field(description="Dest", default=None)] = None,
            proto: Annotated[Optional[str], Field(description="Protocol", default=None)] = None,
            dport: Annotated[Optional[str], Field(description="Dest port", default=None)] = None,
            sport: Annotated[Optional[str], Field(description="Source port", default=None)] = None,
            comment: Annotated[Optional[str], Field(description="Comment", default=None)] = None,
            pos: Annotated[Optional[int], Field(description="Position", default=None)] = None,
        ):
            return self.firewall_tools.create_cluster_firewall_rule(
                action, type, enable, source, dest, proto, dport, sport, comment, pos
            )

        @self.mcp.tool(description=D.DELETE_CLUSTER_FW_RULE_DESC)
        def delete_cluster_firewall_rule(pos: Annotated[int, Field(description="Rule position")]):
            return self.firewall_tools.delete_cluster_firewall_rule(pos)

        @self.mcp.tool(description=D.LIST_GUEST_FW_RULES_DESC)
        def list_guest_firewall_rules(
            node: Annotated[str, Field(description="Node")],
            vmid: Annotated[str, Field(description="Guest ID")],
            guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
        ):
            return self.firewall_tools.list_guest_firewall_rules(node, vmid, guest_type)

        @self.mcp.tool(description=D.CREATE_GUEST_FW_RULE_DESC)
        def create_guest_firewall_rule(
            node: Annotated[str, Field(description="Node")],
            vmid: Annotated[str, Field(description="Guest ID")],
            action: Annotated[str, Field(description="ACCEPT|DROP|REJECT")],
            type: Annotated[str, Field(description="in|out")],
            guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
            enable: Annotated[bool, Field(description="Enable", default=True)] = True,
            source: Annotated[Optional[str], Field(description="Source", default=None)] = None,
            dest: Annotated[Optional[str], Field(description="Dest", default=None)] = None,
            proto: Annotated[Optional[str], Field(description="Protocol", default=None)] = None,
            dport: Annotated[Optional[str], Field(description="Dest port", default=None)] = None,
            comment: Annotated[Optional[str], Field(description="Comment", default=None)] = None,
        ):
            return self.firewall_tools.create_guest_firewall_rule(
                node, vmid, action, type, guest_type, enable, source, dest, proto, dport, comment
            )

        @self.mcp.tool(description=D.DELETE_GUEST_FW_RULE_DESC)
        def delete_guest_firewall_rule(
            node: Annotated[str, Field(description="Node")],
            vmid: Annotated[str, Field(description="Guest ID")],
            pos: Annotated[int, Field(description="Rule position")],
            guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
        ):
            return self.firewall_tools.delete_guest_firewall_rule(node, vmid, pos, guest_type)

        @self.mcp.tool(description=D.GET_GUEST_FW_OPTIONS_DESC)
        def get_guest_firewall_options(
            node: Annotated[str, Field(description="Node")],
            vmid: Annotated[str, Field(description="Guest ID")],
            guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
        ):
            return self.firewall_tools.get_guest_firewall_options(node, vmid, guest_type)

        @self.mcp.tool(description=D.SET_GUEST_FW_OPTIONS_DESC)
        def set_guest_firewall_options(
            node: Annotated[str, Field(description="Node")],
            vmid: Annotated[str, Field(description="Guest ID")],
            guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
            enable: Annotated[Optional[bool], Field(description="Enable", default=None)] = None,
            dhcp: Annotated[Optional[bool], Field(description="DHCP", default=None)] = None,
            ipfilter: Annotated[Optional[bool], Field(description="IP filter", default=None)] = None,
        ):
            return self.firewall_tools.set_guest_firewall_options(
                node, vmid, guest_type, enable, dhcp, ipfilter
            )

        # --- Access ---
        @self.mcp.tool(description=D.LIST_USERS_DESC)
        def list_users():
            return self.access_tools.list_users()

        @self.mcp.tool(description=D.GET_USER_DESC)
        def get_user(userid: Annotated[str, Field(description="e.g. user@pve")]):
            return self.access_tools.get_user(userid)

        @self.mcp.tool(description=D.CREATE_USER_DESC)
        def create_user(
            userid: Annotated[str, Field(description="e.g. user@pve")],
            password: Annotated[Optional[str], Field(description="Password", default=None)] = None,
            comment: Annotated[Optional[str], Field(description="Comment", default=None)] = None,
            email: Annotated[Optional[str], Field(description="Email", default=None)] = None,
            enable: Annotated[bool, Field(description="Enabled", default=True)] = True,
        ):
            return self.access_tools.create_user(userid, password, comment, email, enable)

        @self.mcp.tool(description=D.DELETE_USER_DESC)
        def delete_user(userid: Annotated[str, Field(description="User id")]):
            return self.access_tools.delete_user(userid)

        @self.mcp.tool(description=D.LIST_GROUPS_DESC)
        def list_groups():
            return self.access_tools.list_groups()

        @self.mcp.tool(description=D.CREATE_GROUP_DESC)
        def create_group(
            groupid: Annotated[str, Field(description="Group id")],
            comment: Annotated[Optional[str], Field(description="Comment", default=None)] = None,
        ):
            return self.access_tools.create_group(groupid, comment)

        @self.mcp.tool(description=D.DELETE_GROUP_DESC)
        def delete_group(groupid: Annotated[str, Field(description="Group id")]):
            return self.access_tools.delete_group(groupid)

        @self.mcp.tool(description=D.LIST_ROLES_DESC)
        def list_roles():
            return self.access_tools.list_roles()

        @self.mcp.tool(description=D.LIST_ACL_DESC)
        def list_acl():
            return self.access_tools.list_acl()

        @self.mcp.tool(description=D.UPDATE_ACL_DESC)
        def update_acl(
            path: Annotated[str, Field(description="ACL path e.g. /vms/100")],
            roles: Annotated[str, Field(description="Role list")],
            users: Annotated[Optional[str], Field(description="Users", default=None)] = None,
            groups: Annotated[Optional[str], Field(description="Groups", default=None)] = None,
            propagate: Annotated[bool, Field(description="Propagate", default=True)] = True,
            delete: Annotated[bool, Field(description="Remove ACL", default=False)] = False,
        ):
            return self.access_tools.update_acl(path, roles, users, groups, propagate, delete)

        @self.mcp.tool(description=D.LIST_TOKENS_DESC)
        def list_tokens(userid: Annotated[str, Field(description="User id")]):
            return self.access_tools.list_tokens(userid)

        @self.mcp.tool(description=D.CREATE_TOKEN_DESC)
        def create_token(
            userid: Annotated[str, Field(description="User id")],
            tokenid: Annotated[str, Field(description="Token id")],
            comment: Annotated[Optional[str], Field(description="Comment", default=None)] = None,
            privsep: Annotated[bool, Field(description="Privilege separation", default=True)] = True,
        ):
            return self.access_tools.create_token(userid, tokenid, comment, privsep)

        @self.mcp.tool(description=D.DELETE_TOKEN_DESC)
        def delete_token(
            userid: Annotated[str, Field(description="User id")],
            tokenid: Annotated[str, Field(description="Token id")],
        ):
            return self.access_tools.delete_token(userid, tokenid)

        @self.mcp.tool(description=D.GET_PERMISSIONS_DESC)
        def get_permissions():
            return self.access_tools.get_permissions()

    def start(self) -> None:
        import anyio

        def signal_handler(signum, frame):
            self.logger.info("Received signal to shutdown...")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            self.logger.info("Starting MCP server...")
            anyio.run(self.mcp.run_stdio_async)
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            sys.exit(1)


def main() -> None:
    config_path = os.getenv("PROXMOX_MCP_CONFIG")
    if not config_path:
        print("PROXMOX_MCP_CONFIG environment variable must be set")
        sys.exit(1)
    try:
        server = ProxmoxMCPServer(config_path)
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
