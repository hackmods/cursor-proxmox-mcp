"""
VM-related tools for Proxmox MCP.

This module provides tools for managing and interacting with Proxmox VMs:
- Listing all VMs across the cluster with their status
- Retrieving detailed VM information including:
  * Resource allocation (CPU, memory)
  * Runtime status
  * Node placement
- Executing commands within VMs via QEMU guest agent
- Handling VM console operations
- VM power management (start, stop, shutdown, reset)
- VM creation with customizable specifications

LXC container lifecycle lives in container.ContainerTools.

The tools implement fallback mechanisms for scenarios where
detailed VM information might be temporarily unavailable.
"""
from typing import List, Optional
from mcp.types import TextContent as Content
from .base import ProxmoxTool
from .console.manager import VMConsoleManager
from .helpers import assert_id_absent, pick_storage, qemu_not_found_message
from .spec import ToolSpec
from . import definitions as D

TOOL_SPECS = [
    ToolSpec("get_vms", D.GET_VMS_DESC),
    ToolSpec("create_vm", D.CREATE_VM_DESC),
    ToolSpec("get_vm_config", D.GET_VM_CONFIG_DESC),
    ToolSpec("update_vm_config", D.UPDATE_VM_CONFIG_DESC),
    ToolSpec("execute_vm_command", D.EXECUTE_VM_COMMAND_DESC),
    ToolSpec("start_vm", D.START_VM_DESC),
    ToolSpec("stop_vm", D.STOP_VM_DESC),
    ToolSpec("shutdown_vm", D.SHUTDOWN_VM_DESC),
    ToolSpec("reset_vm", D.RESET_VM_DESC),
    ToolSpec("reboot_vm", D.REBOOT_VM_DESC),
    ToolSpec("suspend_vm", D.SUSPEND_VM_DESC),
    ToolSpec("resume_vm", D.RESUME_VM_DESC),
    ToolSpec("delete_vm", D.DELETE_VM_DESC),
    ToolSpec("clone_vm", D.CLONE_VM_DESC),
    ToolSpec("resize_vm_disk", D.RESIZE_VM_DISK_DESC),
    ToolSpec("convert_vm_to_template", D.CONVERT_VM_TEMPLATE_DESC),
    ToolSpec("get_vm_status", D.GET_VM_STATUS_DESC),
    ToolSpec("get_vm_rrd_data", D.GET_VM_RRD_DATA_DESC),
    ToolSpec("create_vnc_ticket_vm", D.CREATE_VNC_TICKET_VM_DESC),
    ToolSpec("create_spice_ticket_vm", D.CREATE_SPICE_TICKET_VM_DESC),
    ToolSpec("create_termproxy_ticket_vm", D.CREATE_TERMPROXY_TICKET_VM_DESC),
]

class VMTools(ProxmoxTool):
    """Tools for managing Proxmox QEMU VMs.
    
    Provides functionality for:
    - Retrieving cluster-wide VM information
    - Getting detailed VM status and configuration
    - Executing commands within VMs
    - Managing VM console operations
    - VM power management (start, stop, shutdown, reset)
    - VM creation with customizable specifications
    
    Implements fallback mechanisms for scenarios where detailed
    VM information might be temporarily unavailable. Integrates
    with QEMU guest agent for VM command execution.
    """

    def __init__(self, proxmox_api):
        """Initialize VM tools.

        Args:
            proxmox_api: Initialized ProxmoxAPI instance
        """
        super().__init__(proxmox_api)
        self.console_manager = VMConsoleManager(proxmox_api)

    def get_vms(self) -> List[Content]:
        """List all virtual machines across the cluster with detailed status.

        Retrieves comprehensive information for each VM including:
        - Basic identification (ID, name)
        - Runtime status (running, stopped)
        - Resource allocation and usage:
          * CPU cores
          * Memory allocation and usage
        - Node placement
        
        Implements a fallback mechanism that returns basic information
        if detailed configuration retrieval fails for any VM.

        Returns:
            List of Content objects containing formatted VM information:
            {
                "vmid": "100",
                "name": "vm-name",
                "status": "running/stopped",
                "node": "node-name",
                "cpus": core_count,
                "memory": {
                    "used": bytes,
                    "total": bytes
                }
            }

        Raises:
            RuntimeError: If the cluster-wide VM query fails
        """
        try:
            result = []
            for node in self.proxmox.nodes.get():
                node_name = node["node"]
                vms = self.proxmox.nodes(node_name).qemu.get()
                for vm in vms:
                    vmid = vm["vmid"]
                    # Get VM config for CPU cores
                    try:
                        config = self.proxmox.nodes(node_name).qemu(vmid).config.get()
                        result.append({
                            "vmid": vmid,
                            "name": vm["name"],
                            "status": vm["status"],
                            "node": node_name,
                            "cpus": config.get("cores", "N/A"),
                            "memory": {
                                "used": vm.get("mem", 0),
                                "total": vm.get("maxmem", 0)
                            }
                        })
                    except Exception:
                        # Fallback if can't get config
                        result.append({
                            "vmid": vmid,
                            "name": vm["name"],
                            "status": vm["status"],
                            "node": node_name,
                            "cpus": "N/A",
                            "memory": {
                                "used": vm.get("mem", 0),
                                "total": vm.get("maxmem", 0)
                            }
                        })
            return self._format_response(result, "vms")
        except Exception as e:
            self._handle_error("get VMs", e)

    def create_vm(
        self,
        node: str,
        vmid: str,
        name: str,
        cpus: int,
        memory: int,
        disk_size: int,
        storage: Optional[str] = None,
        ostype: Optional[str] = None,
        bridge: Optional[str] = None,
        net0: Optional[str] = None,
        iso: Optional[str] = None,
        boot: Optional[str] = None,
        ciuser: Optional[str] = None,
        cipassword: Optional[str] = None,
        sshkeys: Optional[str] = None,
        ipconfig0: Optional[str] = None,
    ) -> List[Content]:
        """Create a new virtual machine with optional ISO, cloud-init, and network overrides."""
        try:
            assert_id_absent(self.proxmox, node, vmid, "qemu")

            storage_list = self.proxmox.nodes(node).storage.get()
            storage_info = {s["storage"]: s for s in storage_list}
            storage = pick_storage(
                storage_list,
                content="images",
                preferred=["local-lvm", "vm-storage"],
                explicit=storage,
            )

            storage_type = storage_info[storage]["type"]
            disk_format = "raw" if storage_type in ["lvm", "lvmthin"] else "qcow2"
            if ostype is None:
                ostype = "l26"

            from .helpers import DEFAULT_BRIDGE

            bridge = bridge or DEFAULT_BRIDGE
            net0_value = net0 or f"virtio,bridge={bridge}"

            want_cloudinit = any([ciuser, cipassword, sshkeys, ipconfig0])
            if storage_type in ["lvm", "lvmthin"] and want_cloudinit and not iso:
                # cloud-init drive often unsupported on pure LVM; still pass ci* keys for API
                pass

            vm_config = {
                "vmid": vmid,
                "name": name,
                "cores": cpus,
                "memory": memory,
                "ostype": ostype,
                "scsihw": "virtio-scsi-pci",
                "scsi0": f"{storage}:{disk_size},format={disk_format}",
                "agent": "1",
                "vga": "std",
                "net0": net0_value,
            }

            if iso:
                vm_config["ide2"] = f"{iso},media=cdrom"
                vm_config["boot"] = boot or "order=ide2;scsi0"
                if want_cloudinit:
                    vm_config["ide3"] = f"{storage}:cloudinit"
            elif want_cloudinit or storage_type in ["dir", "nfs", "cifs"]:
                if storage_type in ["dir", "nfs", "cifs"] or want_cloudinit:
                    vm_config["ide2"] = f"{storage}:cloudinit"
                vm_config["boot"] = boot or "order=scsi0"
            else:
                vm_config["boot"] = boot or "order=scsi0"

            if ciuser is not None:
                vm_config["ciuser"] = ciuser
            if cipassword is not None:
                vm_config["cipassword"] = cipassword
            if sshkeys is not None:
                vm_config["sshkeys"] = sshkeys
            if ipconfig0 is not None:
                vm_config["ipconfig0"] = ipconfig0

            task_result = self.proxmox.nodes(node).qemu.create(**vm_config)

            result_text = f"""🎉 VM {vmid} created successfully!

📋 VM Configuration:
  • Name: {name}
  • Node: {node}
  • VM ID: {vmid}
  • CPU Cores: {cpus}
  • Memory: {memory} MB ({memory/1024:.1f} GB)
  • Disk: {disk_size} GB ({storage}, {disk_format})
  • OS Type: {ostype}
  • Network: {net0_value}
  • ISO: {iso or '(none)'}
  • Cloud-init: {'yes' if want_cloudinit else 'drive/defaults only'}
  • Boot: {vm_config.get('boot')}

🔧 Task ID: {task_result}

💡 Next: wait_for_task(node, upid) until stopped (create is async — VM not usable yet). Then start_vm (or install from ISO console)."""

            return [Content(type="text", text=result_text)]

        except ValueError as e:
            raise e
        except Exception as e:
            self._handle_error(f"create VM {vmid}", e)

    def start_vm(self, node: str, vmid: str) -> List[Content]:
        """Start a virtual machine.
        
        Args:
            node: Host node name (e.g., 'pve1', 'proxmox-node2')
            vmid: VM ID number (e.g., '100', '101')
            
        Returns:
            List of Content objects containing operation result
            
        Raises:
            ValueError: If VM is not found
            RuntimeError: If start operation fails
        """
        try:
            # Check if VM exists and get current status
            vm_status = self.proxmox.nodes(node).qemu(vmid).status.current.get()
            current_status = vm_status.get("status")

            if current_status == "running":
                result_text = f"🟢 VM {vmid} is already running"
            else:
                # Start the VM
                task_result = self.proxmox.nodes(node).qemu(vmid).status.start.post()
                result_text = f"🚀 VM {vmid} start initiated successfully\nTask ID: {task_result}"

            return [Content(type="text", text=result_text)]

        except Exception as e:
            if "does not exist" in str(e).lower() or "not found" in str(e).lower():
                raise ValueError(qemu_not_found_message(vmid, node))
            self._handle_error(f"start VM {vmid}", e)

    def stop_vm(self, node: str, vmid: str) -> List[Content]:
        """Stop a virtual machine (force stop).
        
        Args:
            node: Host node name (e.g., 'pve1', 'proxmox-node2') 
            vmid: VM ID number (e.g., '100', '101')
            
        Returns:
            List of Content objects containing operation result
            
        Raises:
            ValueError: If VM is not found
            RuntimeError: If stop operation fails
        """
        try:
            # Check if VM exists and get current status
            vm_status = self.proxmox.nodes(node).qemu(vmid).status.current.get()
            current_status = vm_status.get("status")

            if current_status == "stopped":
                result_text = f"🔴 VM {vmid} is already stopped"
            else:
                # Stop the VM
                task_result = self.proxmox.nodes(node).qemu(vmid).status.stop.post()
                result_text = f"🛑 VM {vmid} stop initiated successfully\nTask ID: {task_result}"

            return [Content(type="text", text=result_text)]

        except Exception as e:
            if "does not exist" in str(e).lower() or "not found" in str(e).lower():
                raise ValueError(qemu_not_found_message(vmid, node))
            self._handle_error(f"stop VM {vmid}", e)

    def shutdown_vm(self, node: str, vmid: str) -> List[Content]:
        """Shutdown a virtual machine gracefully.
        
        Args:
            node: Host node name (e.g., 'pve1', 'proxmox-node2')
            vmid: VM ID number (e.g., '100', '101')
            
        Returns:
            List of Content objects containing operation result
            
        Raises:
            ValueError: If VM is not found
            RuntimeError: If shutdown operation fails
        """
        try:
            # Check if VM exists and get current status
            vm_status = self.proxmox.nodes(node).qemu(vmid).status.current.get()
            current_status = vm_status.get("status")

            if current_status == "stopped":
                result_text = f"🔴 VM {vmid} is already stopped"
            else:
                # Shutdown the VM gracefully
                task_result = self.proxmox.nodes(node).qemu(vmid).status.shutdown.post()
                result_text = f"💤 VM {vmid} graceful shutdown initiated\nTask ID: {task_result}"

            return [Content(type="text", text=result_text)]

        except Exception as e:
            if "does not exist" in str(e).lower() or "not found" in str(e).lower():
                raise ValueError(qemu_not_found_message(vmid, node))
            self._handle_error(f"shutdown VM {vmid}", e)

    def reset_vm(self, node: str, vmid: str) -> List[Content]:
        """Reset (restart) a virtual machine.
        
        Args:
            node: Host node name (e.g., 'pve1', 'proxmox-node2')
            vmid: VM ID number (e.g., '100', '101')
            
        Returns:
            List of Content objects containing operation result
            
        Raises:
            ValueError: If VM is not found
            RuntimeError: If reset operation fails
        """
        try:
            # Check if VM exists and get current status
            vm_status = self.proxmox.nodes(node).qemu(vmid).status.current.get()
            current_status = vm_status.get("status")

            if current_status == "stopped":
                result_text = f"⚠️ Cannot reset VM {vmid}: VM is currently stopped\nUse start_vm to start it first"
            else:
                # Reset the VM
                task_result = self.proxmox.nodes(node).qemu(vmid).status.reset.post()
                result_text = f"🔄 VM {vmid} reset initiated successfully\nTask ID: {task_result}"

            return [Content(type="text", text=result_text)]

        except Exception as e:
            if "does not exist" in str(e).lower() or "not found" in str(e).lower():
                raise ValueError(qemu_not_found_message(vmid, node))
            self._handle_error(f"reset VM {vmid}", e)

    async def execute_command(self, node: str, vmid: str, command: str) -> List[Content]:
        """Execute a command in a VM via QEMU guest agent.

        Uses the QEMU guest agent to execute commands within a running VM.
        Requires:
        - VM must be running
        - QEMU guest agent must be installed and running in the VM
        - Command execution permissions must be enabled

        Args:
            node: Host node name (e.g., 'pve1', 'proxmox-node2')
            vmid: VM ID number (e.g., '100', '101')
            command: Shell command to run (e.g., 'uname -a', 'systemctl status nginx')

        Returns:
            List of Content objects containing formatted command output:
            {
                "success": true/false,
                "output": "command output",
                "error": "error message if any"
            }

        Raises:
            ValueError: If VM is not found, not running, or guest agent is not available
            RuntimeError: If command execution fails due to permissions or other issues
        """
        try:
            result = await self.console_manager.execute_command(node, vmid, command)
            # Use the command output formatter from ProxmoxFormatters
            from ..formatting import ProxmoxFormatters
            formatted = ProxmoxFormatters.format_command_output(
                success=result["success"],
                command=command,
                output=result["output"],
                error=result.get("error")
            )
            return [Content(type="text", text=formatted)]
        except Exception as e:
            self._handle_error(f"execute command on VM {vmid}", e)

    def delete_vm(self, node: str, vmid: str, force: bool = False) -> List[Content]:
        """Delete/remove a virtual machine completely.
        
        This will permanently delete the VM and all its associated data including:
        - VM configuration
        - Virtual disks
        - Snapshots
        
        WARNING: This operation cannot be undone!
        
        Args:
            node: Host node name (e.g., 'pve1', 'proxmox-node2')
            vmid: VM ID number (e.g., '100', '101')
            force: Force deletion even if VM is running (will stop first)
            
        Returns:
            List of Content objects containing deletion result
            
        Raises:
            ValueError: If VM is not found or is running and force=False
            RuntimeError: If deletion fails
        """
        try:
            # Check if VM exists and get current status
            try:
                vm_status = self.proxmox.nodes(node).qemu(vmid).status.current.get()
                current_status = vm_status.get("status")
                vm_name = vm_status.get("name", f"VM-{vmid}")
            except Exception as e:
                if "does not exist" in str(e).lower() or "not found" in str(e).lower():
                    raise ValueError(qemu_not_found_message(vmid, node))
                raise e

            # Check if VM is running
            if current_status == "running":
                if not force:
                    raise ValueError(f"VM {vmid} ({vm_name}) is currently running. "
                                   f"Please stop it first or use force=True to stop and delete.")
                else:
                    # Force stop the VM first
                    self.proxmox.nodes(node).qemu(vmid).status.stop.post()
                    result_text = f"🛑 Stopping VM {vmid} ({vm_name}) before deletion...\n"
            else:
                result_text = f"🗑️ Deleting VM {vmid} ({vm_name})...\n"

            # Delete the VM
            task_result = self.proxmox.nodes(node).qemu(vmid).delete()

            result_text += f"""🗑️ VM {vmid} ({vm_name}) deletion initiated successfully!

⚠️ WARNING: This operation will permanently remove:
  • VM configuration
  • All virtual disks
  • All snapshots
  • Cannot be undone!

🔧 Task ID: {task_result}

✅ VM {vmid} ({vm_name}) is being deleted from node {node}"""

            return [Content(type="text", text=result_text)]

        except ValueError as e:
            raise e
        except Exception as e:
            self._handle_error(f"delete VM {vmid}", e)

    def get_vm_config(self, node: str, vmid: str) -> List[Content]:
        """Get full QEMU VM configuration."""
        try:
            config = self.proxmox.nodes(node).qemu(vmid).config.get()
            return self._format_response(config)
        except Exception as e:
            self._handle_error(f"get VM {vmid} config", e)

    def update_vm_config(self, node: str, vmid: str, **kwargs) -> List[Content]:
        """Update QEMU VM configuration (cores, memory, net0, name, etc.)."""
        try:
            params = {k: v for k, v in kwargs.items() if v is not None}
            if not params:
                raise ValueError("No configuration parameters provided to update")
            result = self.proxmox.nodes(node).qemu(vmid).config.put(**params)
            return [
                Content(
                    type="text",
                    text=(
                        f"VM {vmid} config updated\nParams: {params}\nResult: {result}\n"
                        f"💡 Next: get_guest_pending (guest_type=qemu) — reboot_vm / reboot_guest "
                        f"if keys are pending and not hot-pluggable."
                    ),
                )
            ]
        except ValueError:
            raise
        except Exception as e:
            self._handle_error(f"update VM {vmid} config", e)

    def reboot_vm(self, node: str, vmid: str) -> List[Content]:
        """Gracefully reboot a VM (ACPI), distinct from hard reset."""
        try:
            vm_status = self.proxmox.nodes(node).qemu(vmid).status.current.get()
            if vm_status.get("status") == "stopped":
                return [
                    Content(
                        type="text",
                        text=f"⚠️ Cannot reboot VM {vmid}: VM is stopped\nUse start_vm first",
                    )
                ]
            task_result = self.proxmox.nodes(node).qemu(vmid).status.reboot.post()
            return [
                Content(
                    type="text",
                    text=f"🔄 VM {vmid} reboot initiated\nTask ID: {task_result}",
                )
            ]
        except Exception as e:
            if "does not exist" in str(e).lower() or "not found" in str(e).lower():
                raise ValueError(qemu_not_found_message(vmid, node))
            self._handle_error(f"reboot VM {vmid}", e)

    def suspend_vm(self, node: str, vmid: str) -> List[Content]:
        """Suspend a VM."""
        try:
            task_result = self.proxmox.nodes(node).qemu(vmid).status.suspend.post()
            return [
                Content(
                    type="text",
                    text=f"VM {vmid} suspend initiated\nTask ID: {task_result}",
                )
            ]
        except Exception as e:
            self._handle_error(f"suspend VM {vmid}", e)

    def resume_vm(self, node: str, vmid: str) -> List[Content]:
        """Resume a suspended VM."""
        try:
            task_result = self.proxmox.nodes(node).qemu(vmid).status.resume.post()
            return [
                Content(
                    type="text",
                    text=f"VM {vmid} resume initiated\nTask ID: {task_result}",
                )
            ]
        except Exception as e:
            self._handle_error(f"resume VM {vmid}", e)

    def clone_vm(
        self,
        node: str,
        vmid: str,
        newid: str,
        name: Optional[str] = None,
        full: bool = True,
        target: Optional[str] = None,
        storage: Optional[str] = None,
    ) -> List[Content]:
        """Clone a VM to a new ID."""
        try:
            params = {"newid": int(newid), "full": 1 if full else 0}
            if name:
                params["name"] = name
            if target:
                params["target"] = target
            if storage:
                params["storage"] = storage
            result = self.proxmox.nodes(node).qemu(vmid).clone.post(**params)
            return [
                Content(
                    type="text",
                    text=f"Clone VM {vmid} → {newid} initiated\nTask ID: {result}",
                )
            ]
        except Exception as e:
            self._handle_error(f"clone VM {vmid}", e)

    def resize_vm_disk(
        self, node: str, vmid: str, disk: str, size: str
    ) -> List[Content]:
        """Grow a VM disk (e.g. disk='scsi0', size='+10G')."""
        try:
            result = self.proxmox.nodes(node).qemu(vmid).resize.put(disk=disk, size=size)
            return [
                Content(
                    type="text",
                    text=f"Resize {disk} on VM {vmid} to {size}\nResult: {result}",
                )
            ]
        except Exception as e:
            self._handle_error(f"resize disk on VM {vmid}", e)

    def convert_vm_to_template(self, node: str, vmid: str) -> List[Content]:
        """Convert a VM into a template."""
        try:
            result = self.proxmox.nodes(node).qemu(vmid).template.post()
            return [
                Content(
                    type="text",
                    text=f"VM {vmid} convert-to-template initiated\nResult: {result}",
                )
            ]
        except Exception as e:
            self._handle_error(f"convert VM {vmid} to template", e)

    def create_vnc_ticket(self, node: str, vmid: str, websocket: bool = True) -> List[Content]:
        """Mint a VNC proxy ticket (no websocket proxy — connect externally)."""
        try:
            result = self.proxmox.nodes(node).qemu(vmid).vncproxy.post(
                websocket=1 if websocket else 0
            )
            return self._format_response(result)
        except Exception as e:
            self._handle_error(f"create VNC ticket for VM {vmid}", e)

    def create_spice_ticket(self, node: str, vmid: str) -> List[Content]:
        """Mint a SPICE proxy ticket for a VM."""
        try:
            result = self.proxmox.nodes(node).qemu(vmid).spiceproxy.post()
            return self._format_response(result)
        except Exception as e:
            self._handle_error(f"create SPICE ticket for VM {vmid}", e)

    def create_termproxy_ticket(self, node: str, vmid: str) -> List[Content]:
        """Mint a serial/termproxy ticket for a VM console."""
        try:
            result = self.proxmox.nodes(node).qemu(vmid).termproxy.post()
            return self._format_response(result)
        except Exception as e:
            self._handle_error(f"create termproxy ticket for VM {vmid}", e)

    def get_vm_status(self, node: str, vmid: str) -> List[Content]:
        """Get current runtime status for a single VM."""
        try:
            status = self.proxmox.nodes(node).qemu(vmid).status.current.get()
            return self._format_response(status)
        except Exception as e:
            self._handle_error(f"get status for VM {vmid}", e)

    def get_vm_rrd_data(
        self, node: str, vmid: str, timeframe: str = "hour"
    ) -> List[Content]:
        """Get RRD performance data for a VM (timeframe: hour|day|week|month|year)."""
        try:
            data = self.proxmox.nodes(node).qemu(vmid).rrddata.get(timeframe=timeframe)
            return self._format_response(data)
        except Exception as e:
            self._handle_error(f"get RRD data for VM {vmid}", e)
