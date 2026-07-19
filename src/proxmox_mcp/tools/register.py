"""MCP tool registration (extracted from server for maintainability)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Optional

from pydantic import Field

from . import definitions as D

if TYPE_CHECKING:
    from ..server import ProxmoxMCPServer


def register_all(server: ProxmoxMCPServer) -> None:
    """Register all MCP tools on ``server.mcp``."""
    @server.mcp.tool(description=D.GET_NODES_DESC)
    def get_nodes():
        return server.node_tools.get_nodes()

    @server.mcp.tool(description=D.GET_NODE_STATUS_DESC)
    def get_node_status(
        node: Annotated[str, Field(description="Node name")],
    ):
        return server.node_tools.get_node_status(node)

    @server.mcp.tool(description=D.LIST_NODE_NETWORKS_DESC)
    def list_node_networks(
        node: Annotated[str, Field(description="Node name")],
    ):
        return server.network_tools.list_node_networks(node)

    # --- Cluster / tasks ---
    @server.mcp.tool(description=D.GET_CLUSTER_STATUS_DESC)
    def get_cluster_status():
        return server.cluster_tools.get_cluster_status()

    @server.mcp.tool(description=D.GET_NEXT_VMID_DESC)
    def get_next_vmid():
        return server.cluster_tools.get_next_vmid()

    @server.mcp.tool(description=D.GET_TASK_STATUS_DESC)
    def get_task_status(
        node: Annotated[str, Field(description="Node name")],
        upid: Annotated[str, Field(description="Task UPID")],
    ):
        return server.task_tools.get_task_status(node, upid)

    @server.mcp.tool(description=D.LIST_TASKS_DESC)
    def list_tasks(
        node: Annotated[str, Field(description="Node name")],
    ):
        return server.task_tools.list_tasks(node)

    @server.mcp.tool(description=D.WAIT_FOR_TASK_DESC)
    def wait_for_task(
        node: Annotated[str, Field(description="Node name")],
        upid: Annotated[str, Field(description="Task UPID")],
        timeout: Annotated[int, Field(description="Timeout seconds", default=300)] = 300,
        poll_interval: Annotated[float, Field(description="Poll interval seconds", default=2.0)] = 2.0,
    ):
        return server.task_tools.wait_for_task(node, upid, timeout, poll_interval)

    # --- QEMU VMs ---
    @server.mcp.tool(description=D.GET_VMS_DESC)
    def get_vms():
        return server.vm_tools.get_vms()

    @server.mcp.tool(description=D.CREATE_VM_DESC)
    def create_vm(
        node: Annotated[str, Field(description="Node name")],
        vmid: Annotated[str, Field(description="New VM ID")],
        name: Annotated[str, Field(description="VM name")],
        cpus: Annotated[int, Field(description="CPU cores", ge=1, le=32)],
        memory: Annotated[int, Field(description="Memory MB", ge=512, le=131072)],
        disk_size: Annotated[int, Field(description="Disk GB", ge=5, le=1000)],
        storage: Annotated[Optional[str], Field(description="Storage", default=None)] = None,
        ostype: Annotated[Optional[str], Field(description="OS type", default=None)] = None,
        bridge: Annotated[Optional[str], Field(description="Bridge e.g. vmbr0", default=None)] = None,
        net0: Annotated[Optional[str], Field(description="Full net0 string override", default=None)] = None,
        iso: Annotated[Optional[str], Field(description="ISO volid e.g. local:iso/ubuntu.iso", default=None)] = None,
        boot: Annotated[Optional[str], Field(description="Boot order e.g. order=ide2;scsi0", default=None)] = None,
        ciuser: Annotated[Optional[str], Field(description="Cloud-init user", default=None)] = None,
        cipassword: Annotated[Optional[str], Field(description="Cloud-init password", default=None)] = None,
        sshkeys: Annotated[Optional[str], Field(description="Cloud-init SSH public keys", default=None)] = None,
        ipconfig0: Annotated[Optional[str], Field(description="Cloud-init ipconfig0", default=None)] = None,
    ):
        return server.vm_tools.create_vm(
            node, vmid, name, cpus, memory, disk_size, storage, ostype,
            bridge, net0, iso, boot, ciuser, cipassword, sshkeys, ipconfig0,
        )

    @server.mcp.tool(description=D.GET_VM_CONFIG_DESC)
    def get_vm_config(
        node: Annotated[str, Field(description="Node name")],
        vmid: Annotated[str, Field(description="VM ID")],
    ):
        return server.vm_tools.get_vm_config(node, vmid)

    @server.mcp.tool(description=D.UPDATE_VM_CONFIG_DESC)
    def update_vm_config(
        node: Annotated[str, Field(description="Node name")],
        vmid: Annotated[str, Field(description="VM ID")],
        cores: Annotated[Optional[int], Field(description="CPU cores", default=None)] = None,
        memory: Annotated[Optional[int], Field(description="Memory MB", default=None)] = None,
        name: Annotated[Optional[str], Field(description="VM name", default=None)] = None,
        net0: Annotated[Optional[str], Field(description="net0 config", default=None)] = None,
        onboot: Annotated[Optional[bool], Field(description="Start on boot", default=None)] = None,
        agent: Annotated[Optional[str], Field(description="QEMU agent", default=None)] = None,
        iso: Annotated[Optional[str], Field(description="ISO volid → ide2 cdrom", default=None)] = None,
        boot: Annotated[Optional[str], Field(description="Boot order", default=None)] = None,
        ciuser: Annotated[Optional[str], Field(description="Cloud-init user", default=None)] = None,
        cipassword: Annotated[Optional[str], Field(description="Cloud-init password", default=None)] = None,
        sshkeys: Annotated[Optional[str], Field(description="SSH keys", default=None)] = None,
        ipconfig0: Annotated[Optional[str], Field(description="ipconfig0", default=None)] = None,
        ide2: Annotated[Optional[str], Field(description="Raw ide2 string", default=None)] = None,
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
        if boot is not None:
            kwargs["boot"] = boot
        if ciuser is not None:
            kwargs["ciuser"] = ciuser
        if cipassword is not None:
            kwargs["cipassword"] = cipassword
        if sshkeys is not None:
            kwargs["sshkeys"] = sshkeys
        if ipconfig0 is not None:
            kwargs["ipconfig0"] = ipconfig0
        if ide2 is not None:
            kwargs["ide2"] = ide2
        elif iso is not None:
            kwargs["ide2"] = f"{iso},media=cdrom"
            if boot is None:
                kwargs["boot"] = "order=ide2;scsi0"
        return server.vm_tools.update_vm_config(node, vmid, **kwargs)

    @server.mcp.tool(description=D.EXECUTE_VM_COMMAND_DESC)
    async def execute_vm_command(
        node: Annotated[str, Field(description="Node name")],
        vmid: Annotated[str, Field(description="VM ID")],
        command: Annotated[str, Field(description="Shell command")],
    ):
        return await server.vm_tools.execute_command(node, vmid, command)

    @server.mcp.tool(description=D.START_VM_DESC)
    def start_vm(node: Annotated[str, Field(description="Node")], vmid: Annotated[str, Field(description="VM ID")]):
        return server.vm_tools.start_vm(node, vmid)

    @server.mcp.tool(description=D.STOP_VM_DESC)
    def stop_vm(node: Annotated[str, Field(description="Node")], vmid: Annotated[str, Field(description="VM ID")]):
        return server.vm_tools.stop_vm(node, vmid)

    @server.mcp.tool(description=D.SHUTDOWN_VM_DESC)
    def shutdown_vm(node: Annotated[str, Field(description="Node")], vmid: Annotated[str, Field(description="VM ID")]):
        return server.vm_tools.shutdown_vm(node, vmid)

    @server.mcp.tool(description=D.RESET_VM_DESC)
    def reset_vm(node: Annotated[str, Field(description="Node")], vmid: Annotated[str, Field(description="VM ID")]):
        return server.vm_tools.reset_vm(node, vmid)

    @server.mcp.tool(description=D.REBOOT_VM_DESC)
    def reboot_vm(node: Annotated[str, Field(description="Node")], vmid: Annotated[str, Field(description="VM ID")]):
        return server.vm_tools.reboot_vm(node, vmid)

    @server.mcp.tool(description=D.SUSPEND_VM_DESC)
    def suspend_vm(node: Annotated[str, Field(description="Node")], vmid: Annotated[str, Field(description="VM ID")]):
        return server.vm_tools.suspend_vm(node, vmid)

    @server.mcp.tool(description=D.RESUME_VM_DESC)
    def resume_vm(node: Annotated[str, Field(description="Node")], vmid: Annotated[str, Field(description="VM ID")]):
        return server.vm_tools.resume_vm(node, vmid)

    @server.mcp.tool(description=D.DELETE_VM_DESC)
    def delete_vm(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="VM ID")],
        force: Annotated[bool, Field(description="Force if running", default=False)] = False,
    ):
        return server.vm_tools.delete_vm(node, vmid, force)

    @server.mcp.tool(description=D.CLONE_VM_DESC)
    def clone_vm(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="Source VM ID")],
        newid: Annotated[str, Field(description="New VM ID")],
        name: Annotated[Optional[str], Field(description="New name", default=None)] = None,
        full: Annotated[bool, Field(description="Full clone", default=True)] = True,
        target: Annotated[Optional[str], Field(description="Target node", default=None)] = None,
        storage: Annotated[Optional[str], Field(description="Target storage", default=None)] = None,
    ):
        return server.vm_tools.clone_vm(node, vmid, newid, name, full, target, storage)

    @server.mcp.tool(description=D.RESIZE_VM_DISK_DESC)
    def resize_vm_disk(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="VM ID")],
        disk: Annotated[str, Field(description="Disk id e.g. scsi0")],
        size: Annotated[str, Field(description="Size e.g. +10G")],
    ):
        return server.vm_tools.resize_vm_disk(node, vmid, disk, size)

    @server.mcp.tool(description=D.CONVERT_VM_TEMPLATE_DESC)
    def convert_vm_to_template(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="VM ID")],
    ):
        return server.vm_tools.convert_vm_to_template(node, vmid)

    # --- LXC ---
    @server.mcp.tool(description=D.GET_CONTAINERS_DESC)
    def get_containers():
        return server.container_tools.get_containers()

    @server.mcp.tool(description=D.CREATE_LXC_DESC)
    def create_lxc(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="New CT ID")],
        hostname: Annotated[str, Field(description="Hostname")],
        ostemplate: Annotated[Optional[str], Field(description="OS template volid; auto-pick if omitted", default=None)] = None,
        cpus: Annotated[int, Field(description="Cores", ge=1, le=32, default=1)] = 1,
        memory: Annotated[int, Field(description="Memory MB", ge=512, le=131072, default=2048)] = 2048,
        disk_size: Annotated[int, Field(description="Disk GB", ge=4, le=1000, default=8)] = 8,
        storage: Annotated[Optional[str], Field(description="Storage", default=None)] = None,
        features: Annotated[Optional[str], Field(description="Features", default=None)] = None,
        password: Annotated[Optional[str], Field(description="Root password (create-time only; templates may still block password SSH)", default=None)] = None,
        ssh_public_keys: Annotated[Optional[str], Field(description="OpenSSH public keys (one per line) → API ssh-public-keys", default=None)] = None,
        unprivileged: Annotated[bool, Field(description="Unprivileged", default=True)] = True,
        bridge: Annotated[Optional[str], Field(description="Bridge e.g. vmbr0", default=None)] = None,
        ip: Annotated[Optional[str], Field(description="dhcp or CIDR", default=None)] = None,
        gw: Annotated[Optional[str], Field(description="Gateway", default=None)] = None,
        net0: Annotated[Optional[str], Field(description="Full net0 override", default=None)] = None,
        ostemplate_filter: Annotated[Optional[str], Field(description="Auto-pick filter e.g. ubuntu", default=None)] = None,
        docker_ready: Annotated[bool, Field(description="Set nesting+keyctl and tip prepare_lxc_for_docker", default=False)] = False,
    ):
        return server.container_tools.create_lxc(
            node=node,
            vmid=vmid,
            hostname=hostname,
            ostemplate=ostemplate,
            cpus=cpus,
            memory=memory,
            disk_size=disk_size,
            storage=storage,
            features=features,
            password=password,
            ssh_public_keys=ssh_public_keys,
            unprivileged=unprivileged,
            bridge=bridge,
            ip=ip,
            gw=gw,
            net0=net0,
            ostemplate_filter=ostemplate_filter,
            docker_ready=docker_ready,
        )

    @server.mcp.tool(description=D.GET_LXC_CONFIG_DESC)
    def get_lxc_config(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="CT ID")],
    ):
        return server.container_tools.get_lxc_config(node, vmid)

    @server.mcp.tool(description=D.UPDATE_LXC_CONFIG_DESC)
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
        return server.container_tools.update_lxc_config(node, vmid, **kwargs)

    @server.mcp.tool(description=D.START_LXC_DESC)
    def start_lxc(node: Annotated[str, Field(description="Node")], vmid: Annotated[str, Field(description="CT ID")]):
        return server.container_tools.start_lxc(node, vmid)

    @server.mcp.tool(description=D.STOP_LXC_DESC)
    def stop_lxc(node: Annotated[str, Field(description="Node")], vmid: Annotated[str, Field(description="CT ID")]):
        return server.container_tools.stop_lxc(node, vmid)

    @server.mcp.tool(description=D.SHUTDOWN_LXC_DESC)
    def shutdown_lxc(node: Annotated[str, Field(description="Node")], vmid: Annotated[str, Field(description="CT ID")]):
        return server.container_tools.shutdown_lxc(node, vmid)

    @server.mcp.tool(description=D.REBOOT_LXC_DESC)
    def reboot_lxc(node: Annotated[str, Field(description="Node")], vmid: Annotated[str, Field(description="CT ID")]):
        return server.container_tools.reboot_lxc(node, vmid)

    @server.mcp.tool(description=D.SUSPEND_LXC_DESC)
    def suspend_lxc(node: Annotated[str, Field(description="Node")], vmid: Annotated[str, Field(description="CT ID")]):
        return server.container_tools.suspend_lxc(node, vmid)

    @server.mcp.tool(description=D.RESUME_LXC_DESC)
    def resume_lxc(node: Annotated[str, Field(description="Node")], vmid: Annotated[str, Field(description="CT ID")]):
        return server.container_tools.resume_lxc(node, vmid)

    @server.mcp.tool(description=D.DELETE_LXC_DESC)
    def delete_lxc(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="CT ID")],
        force: Annotated[bool, Field(description="Force if running", default=False)] = False,
    ):
        return server.container_tools.delete_lxc(node, vmid, force)

    @server.mcp.tool(description=D.UPDATE_LXC_FEATURES_DESC)
    def update_lxc_features(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="CT ID")],
        features: Annotated[str, Field(description="Features string")],
    ):
        return server.container_tools.update_lxc_features(node, vmid, features)

    @server.mcp.tool(description=D.CLONE_LXC_DESC)
    def clone_lxc(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="Source CT ID")],
        newid: Annotated[str, Field(description="New CT ID")],
        hostname: Annotated[Optional[str], Field(description="Hostname", default=None)] = None,
        full: Annotated[bool, Field(description="Full clone", default=True)] = True,
        target: Annotated[Optional[str], Field(description="Target node", default=None)] = None,
        storage: Annotated[Optional[str], Field(description="Storage", default=None)] = None,
    ):
        return server.container_tools.clone_lxc(node, vmid, newid, hostname, full, target, storage)

    @server.mcp.tool(description=D.RESIZE_LXC_DISK_DESC)
    def resize_lxc_disk(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="CT ID")],
        disk: Annotated[str, Field(description="Volume e.g. rootfs")],
        size: Annotated[str, Field(description="Size e.g. +5G")],
    ):
        return server.container_tools.resize_lxc_disk(node, vmid, disk, size)

    @server.mcp.tool(description=D.CONVERT_LXC_TEMPLATE_DESC)
    def convert_lxc_to_template(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="CT ID")],
    ):
        return server.container_tools.convert_lxc_to_template(node, vmid)

    @server.mcp.tool(description=D.EXECUTE_LXC_COMMAND_DESC)
    def execute_lxc_command(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="CT ID")],
        command: Annotated[str, Field(description="Command")],
        timeout: Annotated[Optional[int], Field(description="Seconds (else ssh.timeout / PROXMOX_MCP_EXEC_TIMEOUT)", default=None)] = None,
    ):
        return server.container_tools.execute_lxc_command(node, vmid, command, timeout)

    @server.mcp.tool(description=D.SET_LXC_PASSWORD_DESC)
    def set_lxc_password(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="CT ID")],
        password: Annotated[str, Field(description="New root password")],
        enable_password_ssh: Annotated[
            bool, Field(description="Enable PermitRootLogin + PasswordAuthentication", default=True)
        ] = True,
    ):
        return server.container_tools.set_lxc_password(
            node, vmid, password, enable_password_ssh
        )

    @server.mcp.tool(description=D.SET_LXC_SSH_KEYS_DESC)
    def set_lxc_ssh_keys(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="CT ID")],
        ssh_public_keys: Annotated[str, Field(description="OpenSSH public key(s), one per line")],
        mode: Annotated[str, Field(description="replace or append", default="replace")] = "replace",
    ):
        return server.container_tools.set_lxc_ssh_keys(node, vmid, ssh_public_keys, mode)

    @server.mcp.tool(description=D.PREPARE_LXC_FOR_DOCKER_DESC)
    def prepare_lxc_for_docker(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="CT ID")],
        fuse: Annotated[bool, Field(description="Also set fuse=1", default=False)] = False,
        allow_apparmor_workaround: Annotated[
            bool, Field(description="Apply dual AppArmor lines if host unpatched", default=True)
        ] = True,
        install_docker: Annotated[bool, Field(description="Install Docker CE via pct exec", default=False)] = False,
        smoke_test: Annotated[bool, Field(description="Run docker run --rm nginx:alpine", default=False)] = False,
        timeout: Annotated[Optional[int], Field(description="Seconds for long installs", default=None)] = None,
    ):
        return server.container_tools.prepare_lxc_for_docker(
            node,
            vmid,
            fuse=fuse,
            allow_apparmor_workaround=allow_apparmor_workaround,
            install_docker=install_docker,
            smoke_test=smoke_test,
            timeout=timeout,
        )

    @server.mcp.tool(description=D.PUSH_TO_LXC_DESC)
    def push_to_lxc(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="CT ID")],
        remote_path: Annotated[str, Field(description="Path inside CT")],
        local_path: Annotated[Optional[str], Field(description="Local file path", default=None)] = None,
        content_base64: Annotated[Optional[str], Field(description="Base64 file content", default=None)] = None,
        timeout: Annotated[Optional[int], Field(description="Seconds", default=None)] = None,
    ):
        return server.container_tools.push_to_lxc(
            node, vmid, remote_path, local_path, content_base64, timeout
        )

    @server.mcp.tool(description=D.PULL_FROM_LXC_DESC)
    def pull_from_lxc(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="CT ID")],
        remote_path: Annotated[str, Field(description="Path inside CT")],
        local_path: Annotated[Optional[str], Field(description="Write to local path", default=None)] = None,
        timeout: Annotated[Optional[int], Field(description="Seconds", default=None)] = None,
    ):
        return server.container_tools.pull_from_lxc(node, vmid, remote_path, local_path, timeout)

    # --- Unified guest power (additive) ---
    @server.mcp.tool(description=D.START_GUEST_DESC)
    def start_guest(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="Guest ID")],
        guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
    ):
        return server.guest_power_tools.start_guest(node, vmid, guest_type)

    @server.mcp.tool(description=D.STOP_GUEST_DESC)
    def stop_guest(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="Guest ID")],
        guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
    ):
        return server.guest_power_tools.stop_guest(node, vmid, guest_type)

    @server.mcp.tool(description=D.SHUTDOWN_GUEST_DESC)
    def shutdown_guest(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="Guest ID")],
        guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
    ):
        return server.guest_power_tools.shutdown_guest(node, vmid, guest_type)

    @server.mcp.tool(description=D.REBOOT_GUEST_DESC)
    def reboot_guest(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="Guest ID")],
        guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
    ):
        return server.guest_power_tools.reboot_guest(node, vmid, guest_type)

    @server.mcp.tool(description=D.DELETE_GUEST_DESC)
    def delete_guest(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="Guest ID")],
        guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
        force: Annotated[bool, Field(description="Force if running", default=False)] = False,
    ):
        return server.guest_power_tools.delete_guest(node, vmid, guest_type, force)

    @server.mcp.tool(description=D.GET_GUEST_STATUS_DESC)
    def get_guest_status(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="Guest ID")],
        guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
    ):
        return server.guest_power_tools.get_guest_status(node, vmid, guest_type)

    @server.mcp.tool(description=D.GET_GUEST_PENDING_DESC)
    def get_guest_pending(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="Guest ID")],
        guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
    ):
        return server.guest_power_tools.get_guest_pending(node, vmid, guest_type)

    @server.mcp.tool(description=D.MOVE_GUEST_DISK_DESC)
    def move_guest_disk(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="Guest ID")],
        disk: Annotated[str, Field(description="Disk/volume e.g. scsi0 or rootfs")],
        storage: Annotated[str, Field(description="Target storage")],
        guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
        delete: Annotated[bool, Field(description="Delete source after move", default=True)] = True,
    ):
        return server.guest_power_tools.move_guest_disk(
            node, vmid, disk, storage, guest_type, delete
        )

    # --- Snapshots ---
    @server.mcp.tool(description=D.LIST_SNAPSHOTS_DESC)
    def list_snapshots(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="Guest ID")],
        guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
    ):
        return server.snapshot_tools.list_snapshots(node, vmid, guest_type)

    @server.mcp.tool(description=D.CREATE_SNAPSHOT_DESC)
    def create_snapshot(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="Guest ID")],
        snapname: Annotated[str, Field(description="Snapshot name")],
        guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
        description: Annotated[Optional[str], Field(description="Description", default=None)] = None,
        vmstate: Annotated[bool, Field(description="Include RAM (qemu)", default=False)] = False,
    ):
        return server.snapshot_tools.create_snapshot(
            node, vmid, snapname, guest_type, description, vmstate
        )

    @server.mcp.tool(description=D.DELETE_SNAPSHOT_DESC)
    def delete_snapshot(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="Guest ID")],
        snapname: Annotated[str, Field(description="Snapshot name")],
        guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
    ):
        return server.snapshot_tools.delete_snapshot(node, vmid, snapname, guest_type)

    @server.mcp.tool(description=D.ROLLBACK_SNAPSHOT_DESC)
    def rollback_snapshot(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="Guest ID")],
        snapname: Annotated[str, Field(description="Snapshot name")],
        guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
    ):
        return server.snapshot_tools.rollback_snapshot(node, vmid, snapname, guest_type)

    # --- Backups ---
    @server.mcp.tool(description=D.CREATE_BACKUP_DESC)
    def create_backup(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="Guest ID")],
        storage: Annotated[Optional[str], Field(description="Backup storage", default=None)] = None,
        mode: Annotated[str, Field(description="snapshot|suspend|stop", default="snapshot")] = "snapshot",
        compress: Annotated[str, Field(description="zstd|gzip|lzo|0", default="zstd")] = "zstd",
        notes: Annotated[Optional[str], Field(description="Notes", default=None)] = None,
    ):
        return server.backup_tools.create_backup(node, vmid, storage, mode, compress, notes)

    @server.mcp.tool(description=D.LIST_BACKUPS_DESC)
    def list_backups(
        node: Annotated[str, Field(description="Node")],
        storage: Annotated[str, Field(description="Storage")],
        vmid: Annotated[Optional[str], Field(description="Filter VMID", default=None)] = None,
    ):
        return server.backup_tools.list_backups(node, storage, vmid)

    @server.mcp.tool(description=D.RESTORE_BACKUP_DESC)
    def restore_backup(
        node: Annotated[str, Field(description="Node")],
        archive: Annotated[str, Field(description="Archive volid")],
        vmid: Annotated[str, Field(description="Target VMID")],
        storage: Annotated[Optional[str], Field(description="Storage", default=None)] = None,
        force: Annotated[bool, Field(description="Overwrite", default=False)] = False,
        guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
    ):
        return server.backup_tools.restore_backup(node, archive, vmid, storage, force, guest_type)

    @server.mcp.tool(description=D.DELETE_BACKUP_DESC)
    def delete_backup(
        node: Annotated[str, Field(description="Node")],
        storage: Annotated[str, Field(description="Storage")],
        volume: Annotated[str, Field(description="Volume id")],
    ):
        return server.backup_tools.delete_backup(node, storage, volume)

    @server.mcp.tool(description=D.LIST_BACKUP_JOBS_DESC)
    def list_backup_jobs():
        return server.backup_tools.list_backup_jobs()

    @server.mcp.tool(description=D.CREATE_BACKUP_JOB_DESC)
    def create_backup_job(
        schedule: Annotated[str, Field(description="Cron-like schedule e.g. sun 01:00")],
        storage: Annotated[str, Field(description="Backup storage")],
        vmid: Annotated[Optional[str], Field(description="Comma-separated VMIDs", default=None)] = None,
        mode: Annotated[str, Field(description="snapshot|suspend|stop", default="snapshot")] = "snapshot",
        compress: Annotated[str, Field(description="zstd|gzip|lzo|0", default="zstd")] = "zstd",
        enabled: Annotated[bool, Field(description="Enabled", default=True)] = True,
        comment: Annotated[Optional[str], Field(description="Comment", default=None)] = None,
        mailto: Annotated[Optional[str], Field(description="Mail to", default=None)] = None,
        mailnotification: Annotated[Optional[str], Field(description="always|failure", default=None)] = None,
        all: Annotated[bool, Field(description="Backup all guests", default=False)] = False,
    ):
        return server.backup_tools.create_backup_job(
            schedule,
            storage,
            vmid,
            mode,
            compress,
            enabled,
            comment,
            mailto,
            mailnotification,
            all,
        )

    @server.mcp.tool(description=D.DELETE_BACKUP_JOB_DESC)
    def delete_backup_job(id: Annotated[str, Field(description="Backup job id")]):
        return server.backup_tools.delete_backup_job(id)

    # --- Storage ---
    @server.mcp.tool(description=D.GET_STORAGE_DESC)
    def get_storage():
        return server.storage_tools.get_storage()

    @server.mcp.tool(description=D.GET_STORAGE_CONTENT_DESC)
    def get_storage_content(
        node: Annotated[str, Field(description="Node")],
        storage: Annotated[str, Field(description="Storage")],
        content: Annotated[Optional[str], Field(description="iso|vztmpl|backup|images", default=None)] = None,
    ):
        return server.storage_tools.get_storage_content(node, storage, content)

    @server.mcp.tool(description=D.LIST_OS_TEMPLATES_DESC)
    def list_os_templates(
        node: Annotated[str, Field(description="Node")],
        storage: Annotated[Optional[str], Field(description="Limit to storage", default=None)] = None,
        filter: Annotated[Optional[str], Field(description="Substring filter e.g. ubuntu", default=None)] = None,
    ):
        return server.storage_tools.list_os_templates(node, storage, filter)

    @server.mcp.tool(description=D.LIST_ISOS_DESC)
    def list_isos(
        node: Annotated[str, Field(description="Node")],
        storage: Annotated[Optional[str], Field(description="Limit to storage", default=None)] = None,
        filter: Annotated[Optional[str], Field(description="Substring filter", default=None)] = None,
    ):
        return server.storage_tools.list_isos(node, storage, filter)

    @server.mcp.tool(description=D.DELETE_STORAGE_CONTENT_DESC)
    def delete_storage_content(
        node: Annotated[str, Field(description="Node")],
        storage: Annotated[str, Field(description="Storage")],
        volume: Annotated[str, Field(description="Volume id")],
    ):
        return server.storage_tools.delete_storage_content(node, storage, volume)

    @server.mcp.tool(description=D.DOWNLOAD_URL_TO_STORAGE_DESC)
    def download_url_to_storage(
        node: Annotated[str, Field(description="Node")],
        storage: Annotated[str, Field(description="Storage")],
        url: Annotated[str, Field(description="Download URL (http/https)")],
        filename: Annotated[Optional[str], Field(description="Filename", default=None)] = None,
        content: Annotated[str, Field(description="iso or vztmpl", default="iso")] = "iso",
        verify_certificate: Annotated[
            bool, Field(description="Verify TLS certificates on download", default=True)
        ] = True,
        checksum: Annotated[
            Optional[str], Field(description="Expected checksum", default=None)
        ] = None,
        checksum_algorithm: Annotated[
            Optional[str],
            Field(description="Checksum algorithm (md5|sha1|sha224|sha256|sha384|sha512)", default=None),
        ] = None,
    ):
        return server.storage_tools.download_url_to_storage(
            node,
            storage,
            url,
            filename,
            content,
            verify_certificate,
            checksum,
            checksum_algorithm,
        )

    @server.mcp.tool(description=D.CREATE_STORAGE_DESC)
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
        return server.storage_tools.create_storage(
            storage, type, content, path, server, export, vgname, pool,
            monhost, username, password, nodes, disable,
        )

    @server.mcp.tool(description=D.UPDATE_STORAGE_DESC)
    def update_storage(
        storage: Annotated[str, Field(description="Storage id")],
        content: Annotated[Optional[str], Field(description="Content", default=None)] = None,
        nodes: Annotated[Optional[str], Field(description="Nodes", default=None)] = None,
        disable: Annotated[Optional[bool], Field(description="Disable", default=None)] = None,
    ):
        return server.storage_tools.update_storage(storage, content, nodes, disable)

    @server.mcp.tool(description=D.DELETE_STORAGE_DESC)
    def delete_storage(storage: Annotated[str, Field(description="Storage id")]):
        return server.storage_tools.delete_storage(storage)

    # --- Migrate ---
    @server.mcp.tool(description=D.MIGRATE_GUEST_DESC)
    def migrate_guest(
        node: Annotated[str, Field(description="Source node")],
        vmid: Annotated[str, Field(description="Guest ID")],
        target: Annotated[str, Field(description="Target node")],
        guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
        online: Annotated[bool, Field(description="Online migrate", default=True)] = True,
        with_local_disks: Annotated[bool, Field(description="Migrate local disks", default=False)] = False,
    ):
        return server.migrate_tools.migrate_guest(
            node, vmid, target, guest_type, online, with_local_disks
        )

    # --- HA ---
    @server.mcp.tool(description=D.GET_HA_STATUS_DESC)
    def get_ha_status():
        return server.ha_tools.get_ha_status()

    @server.mcp.tool(description=D.LIST_HA_GROUPS_DESC)
    def list_ha_groups():
        return server.ha_tools.list_ha_groups()

    @server.mcp.tool(description=D.CREATE_HA_GROUP_DESC)
    def create_ha_group(
        group: Annotated[str, Field(description="Group id")],
        nodes: Annotated[str, Field(description="Nodes e.g. pve1:100,pve2")],
        comment: Annotated[Optional[str], Field(description="Comment", default=None)] = None,
    ):
        return server.ha_tools.create_ha_group(group, nodes, comment)

    @server.mcp.tool(description=D.DELETE_HA_GROUP_DESC)
    def delete_ha_group(group: Annotated[str, Field(description="Group id")]):
        return server.ha_tools.delete_ha_group(group)

    @server.mcp.tool(description=D.LIST_HA_RESOURCES_DESC)
    def list_ha_resources():
        return server.ha_tools.list_ha_resources()

    @server.mcp.tool(description=D.CREATE_HA_RESOURCE_DESC)
    def create_ha_resource(
        sid: Annotated[str, Field(description="e.g. vm:100")],
        group: Annotated[Optional[str], Field(description="HA group", default=None)] = None,
        state: Annotated[str, Field(description="started|stopped|ignored", default="started")] = "started",
        comment: Annotated[Optional[str], Field(description="Comment", default=None)] = None,
    ):
        return server.ha_tools.create_ha_resource(sid, group, state, comment)

    @server.mcp.tool(description=D.UPDATE_HA_RESOURCE_DESC)
    def update_ha_resource(
        sid: Annotated[str, Field(description="Resource id")],
        group: Annotated[Optional[str], Field(description="Group", default=None)] = None,
        state: Annotated[Optional[str], Field(description="State", default=None)] = None,
        comment: Annotated[Optional[str], Field(description="Comment", default=None)] = None,
    ):
        return server.ha_tools.update_ha_resource(sid, group, state, comment)

    @server.mcp.tool(description=D.DELETE_HA_RESOURCE_DESC)
    def delete_ha_resource(sid: Annotated[str, Field(description="Resource id")]):
        return server.ha_tools.delete_ha_resource(sid)

    # --- Firewall ---
    @server.mcp.tool(description=D.GET_CLUSTER_FW_OPTIONS_DESC)
    def get_cluster_firewall_options():
        return server.firewall_tools.get_cluster_firewall_options()

    @server.mcp.tool(description=D.SET_CLUSTER_FW_OPTIONS_DESC)
    def set_cluster_firewall_options(
        enable: Annotated[Optional[bool], Field(description="Enable", default=None)] = None,
        policy_in: Annotated[Optional[str], Field(description="ACCEPT|REJECT|DROP", default=None)] = None,
        policy_out: Annotated[Optional[str], Field(description="ACCEPT|REJECT|DROP", default=None)] = None,
    ):
        return server.firewall_tools.set_cluster_firewall_options(enable, policy_in, policy_out)

    @server.mcp.tool(description=D.LIST_CLUSTER_FW_RULES_DESC)
    def list_cluster_firewall_rules():
        return server.firewall_tools.list_cluster_firewall_rules()

    @server.mcp.tool(description=D.CREATE_CLUSTER_FW_RULE_DESC)
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
        return server.firewall_tools.create_cluster_firewall_rule(
            action, type, enable, source, dest, proto, dport, sport, comment, pos
        )

    @server.mcp.tool(description=D.DELETE_CLUSTER_FW_RULE_DESC)
    def delete_cluster_firewall_rule(pos: Annotated[int, Field(description="Rule position")]):
        return server.firewall_tools.delete_cluster_firewall_rule(pos)

    @server.mcp.tool(description=D.LIST_GUEST_FW_RULES_DESC)
    def list_guest_firewall_rules(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="Guest ID")],
        guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
    ):
        return server.firewall_tools.list_guest_firewall_rules(node, vmid, guest_type)

    @server.mcp.tool(description=D.CREATE_GUEST_FW_RULE_DESC)
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
        return server.firewall_tools.create_guest_firewall_rule(
            node, vmid, action, type, guest_type, enable, source, dest, proto, dport, comment
        )

    @server.mcp.tool(description=D.DELETE_GUEST_FW_RULE_DESC)
    def delete_guest_firewall_rule(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="Guest ID")],
        pos: Annotated[int, Field(description="Rule position")],
        guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
    ):
        return server.firewall_tools.delete_guest_firewall_rule(node, vmid, pos, guest_type)

    @server.mcp.tool(description=D.GET_GUEST_FW_OPTIONS_DESC)
    def get_guest_firewall_options(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="Guest ID")],
        guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
    ):
        return server.firewall_tools.get_guest_firewall_options(node, vmid, guest_type)

    @server.mcp.tool(description=D.SET_GUEST_FW_OPTIONS_DESC)
    def set_guest_firewall_options(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="Guest ID")],
        guest_type: Annotated[str, Field(description="qemu or lxc", default="qemu")] = "qemu",
        enable: Annotated[Optional[bool], Field(description="Enable", default=None)] = None,
        dhcp: Annotated[Optional[bool], Field(description="DHCP", default=None)] = None,
        ipfilter: Annotated[Optional[bool], Field(description="IP filter", default=None)] = None,
    ):
        return server.firewall_tools.set_guest_firewall_options(
            node, vmid, guest_type, enable, dhcp, ipfilter
        )

    # --- Access ---
    @server.mcp.tool(description=D.LIST_USERS_DESC)
    def list_users():
        return server.access_tools.list_users()

    @server.mcp.tool(description=D.GET_USER_DESC)
    def get_user(userid: Annotated[str, Field(description="e.g. user@pve")]):
        return server.access_tools.get_user(userid)

    @server.mcp.tool(description=D.CREATE_USER_DESC)
    def create_user(
        userid: Annotated[str, Field(description="e.g. user@pve")],
        password: Annotated[Optional[str], Field(description="Password", default=None)] = None,
        comment: Annotated[Optional[str], Field(description="Comment", default=None)] = None,
        email: Annotated[Optional[str], Field(description="Email", default=None)] = None,
        enable: Annotated[bool, Field(description="Enabled", default=True)] = True,
    ):
        return server.access_tools.create_user(userid, password, comment, email, enable)

    @server.mcp.tool(description=D.DELETE_USER_DESC)
    def delete_user(userid: Annotated[str, Field(description="User id")]):
        return server.access_tools.delete_user(userid)

    @server.mcp.tool(description=D.LIST_GROUPS_DESC)
    def list_groups():
        return server.access_tools.list_groups()

    @server.mcp.tool(description=D.CREATE_GROUP_DESC)
    def create_group(
        groupid: Annotated[str, Field(description="Group id")],
        comment: Annotated[Optional[str], Field(description="Comment", default=None)] = None,
    ):
        return server.access_tools.create_group(groupid, comment)

    @server.mcp.tool(description=D.DELETE_GROUP_DESC)
    def delete_group(groupid: Annotated[str, Field(description="Group id")]):
        return server.access_tools.delete_group(groupid)

    @server.mcp.tool(description=D.LIST_ROLES_DESC)
    def list_roles():
        return server.access_tools.list_roles()

    @server.mcp.tool(description=D.LIST_ACL_DESC)
    def list_acl():
        return server.access_tools.list_acl()

    @server.mcp.tool(description=D.UPDATE_ACL_DESC)
    def update_acl(
        path: Annotated[str, Field(description="ACL path e.g. /vms/100")],
        roles: Annotated[str, Field(description="Role list")],
        users: Annotated[Optional[str], Field(description="Users", default=None)] = None,
        groups: Annotated[Optional[str], Field(description="Groups", default=None)] = None,
        propagate: Annotated[bool, Field(description="Propagate", default=True)] = True,
        delete: Annotated[bool, Field(description="Remove ACL", default=False)] = False,
    ):
        return server.access_tools.update_acl(path, roles, users, groups, propagate, delete)

    @server.mcp.tool(description=D.LIST_TOKENS_DESC)
    def list_tokens(userid: Annotated[str, Field(description="User id")]):
        return server.access_tools.list_tokens(userid)

    @server.mcp.tool(description=D.CREATE_TOKEN_DESC)
    def create_token(
        userid: Annotated[str, Field(description="User id")],
        tokenid: Annotated[str, Field(description="Token id")],
        comment: Annotated[Optional[str], Field(description="Comment", default=None)] = None,
        privsep: Annotated[bool, Field(description="Privilege separation", default=True)] = True,
    ):
        return server.access_tools.create_token(userid, tokenid, comment, privsep)

    @server.mcp.tool(description=D.DELETE_TOKEN_DESC)
    def delete_token(
        userid: Annotated[str, Field(description="User id")],
        tokenid: Annotated[str, Field(description="Token id")],
    ):
        return server.access_tools.delete_token(userid, tokenid)

    @server.mcp.tool(description=D.GET_PERMISSIONS_DESC)
    def get_permissions():
        return server.access_tools.get_permissions()

    @server.mcp.tool(description=D.GET_TOKEN_PERMISSIONS_DESC)
    def get_token_permissions(
        userid: Annotated[str, Field(description="user@realm e.g. mcp@pve")],
        tokenid: Annotated[str, Field(description="Token name")],
    ):
        return server.access_tools.get_token_permissions(userid, tokenid)

    # --- Cluster extras ---
    @server.mcp.tool(description=D.GET_VERSION_DESC)
    def get_version():
        return server.cluster_tools.get_version()

    @server.mcp.tool(description=D.GET_MCP_CAPABILITIES_DESC)
    def get_mcp_capabilities(
        probe_node: Annotated[
            Optional[str], Field(description="Optional node name for live pct version probe", default=None)
        ] = None,
    ):
        return server.capabilities_tools.get_mcp_capabilities(probe_node)

    @server.mcp.tool(description=D.GET_CLUSTER_RESOURCES_DESC)
    def get_cluster_resources(
        type: Annotated[Optional[str], Field(description="vm|storage|node|sdn", default=None)] = None,
    ):
        return server.cluster_tools.get_cluster_resources(type)

    @server.mcp.tool(description=D.GET_CLUSTER_LOG_DESC)
    def get_cluster_log(
        max_entries: Annotated[int, Field(description="Max log lines", default=50)] = 50,
    ):
        return server.cluster_tools.get_cluster_log(max_entries)

    @server.mcp.tool(description=D.GET_CLUSTER_OPTIONS_DESC)
    def get_cluster_options():
        return server.cluster_tools.get_cluster_options()

    # --- Node extras ---
    @server.mcp.tool(description=D.GET_NODE_SUBSCRIPTION_DESC)
    def get_node_subscription(node: Annotated[str, Field(description="Node")]):
        return server.node_tools.get_node_subscription(node)

    @server.mcp.tool(description=D.LIST_NODE_CERTIFICATES_DESC)
    def list_node_certificates(node: Annotated[str, Field(description="Node")]):
        return server.node_tools.list_node_certificates(node)

    @server.mcp.tool(description=D.GET_NODE_REPORT_DESC)
    def get_node_report(node: Annotated[str, Field(description="Node")]):
        return server.node_tools.get_node_report(node)

    @server.mcp.tool(description=D.LIST_NODE_SERVICES_DESC)
    def list_node_services(node: Annotated[str, Field(description="Node")]):
        return server.node_tools.list_node_services(node)

    @server.mcp.tool(description=D.GET_NODE_TIME_DESC)
    def get_node_time(node: Annotated[str, Field(description="Node")]):
        return server.node_tools.get_node_time(node)

    @server.mcp.tool(description=D.WAKE_NODE_DESC)
    def wake_node(node: Annotated[str, Field(description="Node")]):
        return server.node_tools.wake_node(node)

    # --- Guest status / RRD / console tickets ---
    @server.mcp.tool(description=D.GET_VM_STATUS_DESC)
    def get_vm_status(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="VM ID")],
    ):
        return server.vm_tools.get_vm_status(node, vmid)

    @server.mcp.tool(description=D.GET_VM_RRD_DATA_DESC)
    def get_vm_rrd_data(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="VM ID")],
        timeframe: Annotated[str, Field(description="hour|day|week|month|year", default="hour")] = "hour",
    ):
        return server.vm_tools.get_vm_rrd_data(node, vmid, timeframe)

    @server.mcp.tool(description=D.CREATE_VNC_TICKET_VM_DESC)
    def create_vnc_ticket_vm(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="VM ID")],
        websocket: Annotated[bool, Field(description="Websocket", default=True)] = True,
    ):
        return server.vm_tools.create_vnc_ticket(node, vmid, websocket)

    @server.mcp.tool(description=D.CREATE_SPICE_TICKET_VM_DESC)
    def create_spice_ticket_vm(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="VM ID")],
    ):
        return server.vm_tools.create_spice_ticket(node, vmid)

    @server.mcp.tool(description=D.CREATE_TERMPROXY_TICKET_VM_DESC)
    def create_termproxy_ticket_vm(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="VM ID")],
    ):
        return server.vm_tools.create_termproxy_ticket(node, vmid)

    @server.mcp.tool(description=D.GET_LXC_STATUS_DESC)
    def get_lxc_status(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="CT ID")],
    ):
        return server.container_tools.get_lxc_status(node, vmid)

    @server.mcp.tool(description=D.GET_LXC_NETWORK_DESC)
    def get_lxc_network(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="CT ID")],
        resolve_runtime: Annotated[
            bool, Field(description="Try pct exec for runtime IPs when SSH configured", default=True)
        ] = True,
    ):
        return server.container_tools.get_lxc_network(node, vmid, resolve_runtime)

    @server.mcp.tool(description=D.GET_LXC_RRD_DATA_DESC)
    def get_lxc_rrd_data(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="CT ID")],
        timeframe: Annotated[str, Field(description="hour|day|week|month|year", default="hour")] = "hour",
    ):
        return server.container_tools.get_lxc_rrd_data(node, vmid, timeframe)

    @server.mcp.tool(description=D.CREATE_VNC_TICKET_LXC_DESC)
    def create_vnc_ticket_lxc(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="CT ID")],
        websocket: Annotated[bool, Field(description="Websocket", default=True)] = True,
    ):
        return server.container_tools.create_vnc_ticket(node, vmid, websocket)

    @server.mcp.tool(description=D.CREATE_SPICE_TICKET_LXC_DESC)
    def create_spice_ticket_lxc(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="CT ID")],
    ):
        return server.container_tools.create_spice_ticket(node, vmid)

    @server.mcp.tool(description=D.CREATE_TERMPROXY_TICKET_LXC_DESC)
    def create_termproxy_ticket_lxc(
        node: Annotated[str, Field(description="Node")],
        vmid: Annotated[str, Field(description="CT ID")],
    ):
        return server.container_tools.create_termproxy_ticket(node, vmid)

    # --- Replication ---
    @server.mcp.tool(description=D.LIST_REPLICATION_JOBS_DESC)
    def list_replication_jobs():
        return server.replication_tools.list_replication_jobs()

    @server.mcp.tool(description=D.GET_REPLICATION_STATUS_DESC)
    def get_replication_status(
        node: Annotated[str, Field(description="Node")],
        jobid: Annotated[str, Field(description="Job id")],
    ):
        return server.replication_tools.get_replication_status(node, jobid)

    @server.mcp.tool(description=D.RUN_REPLICATION_JOB_DESC)
    def run_replication_job(
        node: Annotated[str, Field(description="Node")],
        jobid: Annotated[str, Field(description="Job id")],
    ):
        return server.replication_tools.run_replication_job(node, jobid)

    @server.mcp.tool(description=D.CREATE_REPLICATION_JOB_DESC)
    def create_replication_job(
        id: Annotated[str, Field(description="Job id e.g. 100-0")],
        target: Annotated[str, Field(description="Target node")],
        schedule: Annotated[Optional[str], Field(description="Schedule", default=None)] = None,
        comment: Annotated[Optional[str], Field(description="Comment", default=None)] = None,
        enabled: Annotated[bool, Field(description="Enabled", default=True)] = True,
    ):
        return server.replication_tools.create_replication_job(id, target, schedule, comment, enabled)

    @server.mcp.tool(description=D.UPDATE_REPLICATION_JOB_DESC)
    def update_replication_job(
        id: Annotated[str, Field(description="Job id")],
        schedule: Annotated[Optional[str], Field(description="Schedule", default=None)] = None,
        comment: Annotated[Optional[str], Field(description="Comment", default=None)] = None,
        enabled: Annotated[Optional[bool], Field(description="Enabled", default=None)] = None,
    ):
        return server.replication_tools.update_replication_job(id, schedule, comment, enabled)

    @server.mcp.tool(description=D.DELETE_REPLICATION_JOB_DESC)
    def delete_replication_job(id: Annotated[str, Field(description="Job id")]):
        return server.replication_tools.delete_replication_job(id)

    # --- ACME ---
    @server.mcp.tool(description=D.LIST_ACME_PLUGINS_DESC)
    def list_acme_plugins():
        return server.acme_tools.list_acme_plugins()

    @server.mcp.tool(description=D.LIST_ACME_ACCOUNTS_DESC)
    def list_acme_accounts():
        return server.acme_tools.list_acme_accounts()

    @server.mcp.tool(description=D.GET_ACME_DIRECTORIES_DESC)
    def get_acme_directories():
        return server.acme_tools.get_acme_directories()

    # --- SDN ---
    @server.mcp.tool(description=D.LIST_SDN_ZONES_DESC)
    def list_sdn_zones():
        return server.sdn_tools.list_sdn_zones()

    @server.mcp.tool(description=D.LIST_SDN_VNETS_DESC)
    def list_sdn_vnets():
        return server.sdn_tools.list_sdn_vnets()

    @server.mcp.tool(description=D.LIST_SDN_CONTROLLERS_DESC)
    def list_sdn_controllers():
        return server.sdn_tools.list_sdn_controllers()

    @server.mcp.tool(description=D.LIST_SDN_IPAMS_DESC)
    def list_sdn_ipams():
        return server.sdn_tools.list_sdn_ipams()

    @server.mcp.tool(description=D.LIST_SDN_DNS_DESC)
    def list_sdn_dns():
        return server.sdn_tools.list_sdn_dns()

    @server.mcp.tool(description=D.APPLY_SDN_DESC)
    def apply_sdn():
        return server.sdn_tools.apply_sdn()

    # --- Pools ---
    @server.mcp.tool(description=D.LIST_POOLS_DESC)
    def list_pools():
        return server.pool_tools.list_pools()

    @server.mcp.tool(description=D.GET_POOL_DESC)
    def get_pool(poolid: Annotated[str, Field(description="Pool id")]):
        return server.pool_tools.get_pool(poolid)

    @server.mcp.tool(description=D.CREATE_POOL_DESC)
    def create_pool(
        poolid: Annotated[str, Field(description="Pool id")],
        comment: Annotated[Optional[str], Field(description="Comment", default=None)] = None,
    ):
        return server.pool_tools.create_pool(poolid, comment)

    @server.mcp.tool(description=D.UPDATE_POOL_DESC)
    def update_pool(
        poolid: Annotated[str, Field(description="Pool id")],
        comment: Annotated[Optional[str], Field(description="Comment", default=None)] = None,
        vms: Annotated[Optional[str], Field(description="Comma-separated VMIDs", default=None)] = None,
        storage: Annotated[Optional[str], Field(description="Comma-separated storages", default=None)] = None,
        delete: Annotated[bool, Field(description="Remove members instead of add", default=False)] = False,
    ):
        return server.pool_tools.update_pool(poolid, comment, vms, storage, delete)

    @server.mcp.tool(description=D.DELETE_POOL_DESC)
    def delete_pool(poolid: Annotated[str, Field(description="Pool id")]):
        return server.pool_tools.delete_pool(poolid)

    # --- Firewall extras ---
    @server.mcp.tool(description=D.LIST_FIREWALL_ALIASES_DESC)
    def list_firewall_aliases():
        return server.firewall_tools.list_firewall_aliases()

    @server.mcp.tool(description=D.CREATE_FIREWALL_ALIAS_DESC)
    def create_firewall_alias(
        name: Annotated[str, Field(description="Alias name")],
        cidr: Annotated[str, Field(description="CIDR or IP")],
        comment: Annotated[Optional[str], Field(description="Comment", default=None)] = None,
    ):
        return server.firewall_tools.create_firewall_alias(name, cidr, comment)

    @server.mcp.tool(description=D.DELETE_FIREWALL_ALIAS_DESC)
    def delete_firewall_alias(name: Annotated[str, Field(description="Alias name")]):
        return server.firewall_tools.delete_firewall_alias(name)

    @server.mcp.tool(description=D.LIST_FIREWALL_IPSETS_DESC)
    def list_firewall_ipsets():
        return server.firewall_tools.list_firewall_ipsets()

    @server.mcp.tool(description=D.CREATE_FIREWALL_IPSET_DESC)
    def create_firewall_ipset(
        name: Annotated[str, Field(description="IP set name")],
        comment: Annotated[Optional[str], Field(description="Comment", default=None)] = None,
    ):
        return server.firewall_tools.create_firewall_ipset(name, comment)

    @server.mcp.tool(description=D.DELETE_FIREWALL_IPSET_DESC)
    def delete_firewall_ipset(name: Annotated[str, Field(description="IP set name")]):
        return server.firewall_tools.delete_firewall_ipset(name)

    @server.mcp.tool(description=D.LIST_FIREWALL_IPSET_CIDRS_DESC)
    def list_firewall_ipset_cidrs(name: Annotated[str, Field(description="IP set name")]):
        return server.firewall_tools.list_firewall_ipset_cidrs(name)

    @server.mcp.tool(description=D.ADD_FIREWALL_IPSET_CIDR_DESC)
    def add_firewall_ipset_cidr(
        name: Annotated[str, Field(description="IP set name")],
        cidr: Annotated[str, Field(description="CIDR or IP")],
        comment: Annotated[Optional[str], Field(description="Comment", default=None)] = None,
        nomatch: Annotated[bool, Field(description="nomatch flag", default=False)] = False,
    ):
        return server.firewall_tools.add_firewall_ipset_cidr(name, cidr, comment, nomatch)

    @server.mcp.tool(description=D.DELETE_FIREWALL_IPSET_CIDR_DESC)
    def delete_firewall_ipset_cidr(
        name: Annotated[str, Field(description="IP set name")],
        cidr: Annotated[str, Field(description="CIDR or IP")],
    ):
        return server.firewall_tools.delete_firewall_ipset_cidr(name, cidr)

    @server.mcp.tool(description=D.LIST_FIREWALL_MACROS_DESC)
    def list_firewall_macros():
        return server.firewall_tools.list_firewall_macros()
