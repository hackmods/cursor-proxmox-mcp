"""
LXC container tools for Proxmox MCP.

Provides lifecycle management for LXC containers:
- Listing containers across the cluster
- Creating containers (with nesting/features for Docker-in-LXC)
- Power control (start, stop, shutdown, reboot)
- Deletion
- Post-create feature updates (nesting, keyctl, fuse)
"""
from typing import List, Optional
from mcp.types import TextContent as Content
from .base import ProxmoxTool


class ContainerTools(ProxmoxTool):
    """Tools for managing Proxmox LXC containers."""

    def get_containers(self) -> List[Content]:
        """List all LXC containers across the cluster with detailed status.

        Returns:
            List of Content objects containing formatted container information

        Raises:
            RuntimeError: If the cluster-wide container query fails
        """
        try:
            result = []
            for node in self.proxmox.nodes.get():
                node_name = node["node"]
                containers = self.proxmox.nodes(node_name).lxc.get()
                for ct in containers:
                    vmid = ct["vmid"]
                    name = ct.get("name") or ct.get("hostname") or f"CT-{vmid}"
                    try:
                        config = self.proxmox.nodes(node_name).lxc(vmid).config.get()
                        result.append({
                            "vmid": vmid,
                            "name": config.get("hostname", name),
                            "status": ct["status"],
                            "node": node_name,
                            "cpus": config.get("cores", "N/A"),
                            "memory": {
                                "used": ct.get("mem", 0),
                                "total": ct.get("maxmem", 0),
                            },
                        })
                    except Exception:
                        result.append({
                            "vmid": vmid,
                            "name": name,
                            "status": ct["status"],
                            "node": node_name,
                            "cpus": "N/A",
                            "memory": {
                                "used": ct.get("mem", 0),
                                "total": ct.get("maxmem", 0),
                            },
                        })
            return self._format_response(result, "containers")
        except Exception as e:
            self._handle_error("get containers", e)

    def create_lxc(
        self,
        node: str,
        vmid: str,
        hostname: str,
        ostemplate: str,
        cpus: int,
        memory: int,
        disk_size: int,
        storage: Optional[str] = None,
        features: Optional[str] = None,
        password: Optional[str] = None,
        unprivileged: bool = True,
    ) -> List[Content]:
        """Create a new LXC container with specified configuration.

        Args:
            node: Host node name (e.g., 'pve')
            vmid: New container ID number (e.g., '200')
            hostname: Container hostname (e.g., 'my-lxc')
            ostemplate: OS template path (e.g., 'local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst')
            cpus: Number of CPU cores (e.g., 1, 2, 4)
            memory: Memory size in MB (e.g., 2048 for 2GB)
            disk_size: Root filesystem size in GB (e.g., 8, 10, 20)
            storage: Storage name for rootfs (e.g., 'local-lvm'). If None, will auto-detect
            features: Container features string (e.g., 'nesting=1', 'nesting=1,keyctl=1').
                      Default: 'nesting=1'
            password: Root password for the container. Optional.
            unprivileged: Whether to create an unprivileged container. Default: True

        Returns:
            List of Content objects containing creation result

        Raises:
            ValueError: If container ID already exists or invalid parameters
            RuntimeError: If container creation fails
        """
        try:
            try:
                self.proxmox.nodes(node).lxc(vmid).config.get()
                raise ValueError(f"LXC container {vmid} already exists on node {node}")
            except Exception as e:
                if "does not exist" not in str(e).lower():
                    raise e

            try:
                self.proxmox.nodes(node).qemu(vmid).config.get()
                raise ValueError(f"VM ID {vmid} is already used by a QEMU VM on node {node}")
            except Exception as e:
                if "does not exist" not in str(e).lower():
                    raise e

            storage_list = self.proxmox.nodes(node).storage.get()
            storage_info = {}
            for s in storage_list:
                storage_info[s["storage"]] = s

            if storage is None:
                for s in storage_list:
                    if s["storage"] == "local-lvm" and "rootdir" in s.get("content", ""):
                        storage = s["storage"]
                        break
                if storage is None:
                    for s in storage_list:
                        if s["storage"] == "vm-storage" and "rootdir" in s.get("content", ""):
                            storage = s["storage"]
                            break
                if storage is None:
                    for s in storage_list:
                        if "rootdir" in s.get("content", ""):
                            storage = s["storage"]
                            break
                    if storage is None:
                        raise ValueError("No suitable storage found for LXC rootfs (rootdir)")

            if storage not in storage_info:
                raise ValueError(f"Storage '{storage}' not found on node {node}")

            if "rootdir" not in storage_info[storage].get("content", ""):
                raise ValueError(f"Storage '{storage}' does not support LXC rootfs (rootdir)")

            storage_type = storage_info[storage]["type"]

            if features is None:
                features = "nesting=1"

            lxc_config = {
                "vmid": vmid,
                "hostname": hostname,
                "ostemplate": ostemplate,
                "cores": cpus,
                "memory": memory,
                "rootfs": f"{storage}:{disk_size}",
                "net0": "name=eth0,bridge=vmbr0,ip=dhcp",
                "features": features,
                "unprivileged": 1 if unprivileged else 0,
            }

            if password is not None:
                lxc_config["password"] = password

            task_result = self.proxmox.nodes(node).lxc.create(**lxc_config)

            result_text = f"""🎉 LXC container {vmid} created successfully!

📋 Container Configuration:
  • Hostname: {hostname}
  • Node: {node}
  • Container ID: {vmid}
  • CPU Cores: {cpus}
  • Memory: {memory} MB ({memory/1024:.1f} GB)
  • Rootfs: {disk_size} GB ({storage})
  • Storage Type: {storage_type}
  • OS Template: {ostemplate}
  • Features: {features}
  • Unprivileged: {unprivileged}
  • Network: eth0 (bridge=vmbr0, dhcp)

🔧 Task ID: {task_result}

💡 Next steps:
  1. Start the container with start_lxc (or update_lxc_features first if Docker needs keyctl)
  2. Enter the container console to finish setup
  3. Adjust networking or mount points as needed"""

            return [Content(type="text", text=result_text)]

        except ValueError as e:
            raise e
        except Exception as e:
            self._handle_error(f"create LXC {vmid}", e)

    def start_lxc(self, node: str, vmid: str) -> List[Content]:
        """Start an LXC container."""
        try:
            ct_status = self.proxmox.nodes(node).lxc(vmid).status.current.get()
            current_status = ct_status.get("status")

            if current_status == "running":
                result_text = f"🟢 LXC {vmid} is already running"
            else:
                task_result = self.proxmox.nodes(node).lxc(vmid).status.start.post()
                result_text = f"🚀 LXC {vmid} start initiated successfully\nTask ID: {task_result}"

            return [Content(type="text", text=result_text)]

        except Exception as e:
            if "does not exist" in str(e).lower() or "not found" in str(e).lower():
                raise ValueError(f"LXC {vmid} not found on node {node}")
            self._handle_error(f"start LXC {vmid}", e)

    def stop_lxc(self, node: str, vmid: str) -> List[Content]:
        """Force-stop an LXC container."""
        try:
            ct_status = self.proxmox.nodes(node).lxc(vmid).status.current.get()
            current_status = ct_status.get("status")

            if current_status == "stopped":
                result_text = f"🔴 LXC {vmid} is already stopped"
            else:
                task_result = self.proxmox.nodes(node).lxc(vmid).status.stop.post()
                result_text = f"🛑 LXC {vmid} stop initiated successfully\nTask ID: {task_result}"

            return [Content(type="text", text=result_text)]

        except Exception as e:
            if "does not exist" in str(e).lower() or "not found" in str(e).lower():
                raise ValueError(f"LXC {vmid} not found on node {node}")
            self._handle_error(f"stop LXC {vmid}", e)

    def shutdown_lxc(self, node: str, vmid: str) -> List[Content]:
        """Gracefully shut down an LXC container."""
        try:
            ct_status = self.proxmox.nodes(node).lxc(vmid).status.current.get()
            current_status = ct_status.get("status")

            if current_status == "stopped":
                result_text = f"🔴 LXC {vmid} is already stopped"
            else:
                task_result = self.proxmox.nodes(node).lxc(vmid).status.shutdown.post()
                result_text = f"💤 LXC {vmid} graceful shutdown initiated\nTask ID: {task_result}"

            return [Content(type="text", text=result_text)]

        except Exception as e:
            if "does not exist" in str(e).lower() or "not found" in str(e).lower():
                raise ValueError(f"LXC {vmid} not found on node {node}")
            self._handle_error(f"shutdown LXC {vmid}", e)

    def reboot_lxc(self, node: str, vmid: str) -> List[Content]:
        """Reboot an LXC container (LXC counterpart to reset_vm)."""
        try:
            ct_status = self.proxmox.nodes(node).lxc(vmid).status.current.get()
            current_status = ct_status.get("status")

            if current_status == "stopped":
                result_text = (
                    f"⚠️ Cannot reboot LXC {vmid}: container is currently stopped\n"
                    f"Use start_lxc to start it first"
                )
            else:
                task_result = self.proxmox.nodes(node).lxc(vmid).status.reboot.post()
                result_text = f"🔄 LXC {vmid} reboot initiated successfully\nTask ID: {task_result}"

            return [Content(type="text", text=result_text)]

        except Exception as e:
            if "does not exist" in str(e).lower() or "not found" in str(e).lower():
                raise ValueError(f"LXC {vmid} not found on node {node}")
            self._handle_error(f"reboot LXC {vmid}", e)

    def delete_lxc(self, node: str, vmid: str, force: bool = False) -> List[Content]:
        """Delete an LXC container permanently.

        Args:
            node: Host node name
            vmid: Container ID
            force: If True, stop a running container before deleting
        """
        try:
            try:
                ct_status = self.proxmox.nodes(node).lxc(vmid).status.current.get()
                current_status = ct_status.get("status")
                ct_name = ct_status.get("name") or ct_status.get("hostname") or f"CT-{vmid}"
            except Exception as e:
                if "does not exist" in str(e).lower() or "not found" in str(e).lower():
                    raise ValueError(f"LXC {vmid} not found on node {node}")
                raise e

            if current_status == "running":
                if not force:
                    raise ValueError(
                        f"LXC {vmid} ({ct_name}) is currently running. "
                        f"Please stop it first or use force=True to stop and delete."
                    )
                self.proxmox.nodes(node).lxc(vmid).status.stop.post()
                result_text = f"🛑 Stopping LXC {vmid} ({ct_name}) before deletion...\n"
            else:
                result_text = f"🗑️ Deleting LXC {vmid} ({ct_name})...\n"

            task_result = self.proxmox.nodes(node).lxc(vmid).delete()

            result_text += f"""🗑️ LXC {vmid} ({ct_name}) deletion initiated successfully!

⚠️ WARNING: This operation will permanently remove:
  • Container configuration
  • Root filesystem
  • All snapshots
  • Cannot be undone!

🔧 Task ID: {task_result}

✅ LXC {vmid} ({ct_name}) is being deleted from node {node}"""

            return [Content(type="text", text=result_text)]

        except ValueError as e:
            raise e
        except Exception as e:
            self._handle_error(f"delete LXC {vmid}", e)

    def update_lxc_features(self, node: str, vmid: str, features: str) -> List[Content]:
        """Update LXC feature flags (nesting, keyctl, fuse, etc.).

        Used for Docker-in-LXC after create. Note: Proxmox often restricts
        setting keyctl/fuse (anything beyond nesting) to root@pam.

        Args:
            node: Host node name
            vmid: Container ID
            features: Features string, e.g. 'nesting=1,keyctl=1' or 'nesting=1,keyctl=1,fuse=1'
        """
        try:
            try:
                config = self.proxmox.nodes(node).lxc(vmid).config.get()
            except Exception as e:
                if "does not exist" in str(e).lower() or "not found" in str(e).lower():
                    raise ValueError(f"LXC {vmid} not found on node {node}")
                raise e

            previous = config.get("features", "(none)")
            task_result = self.proxmox.nodes(node).lxc(vmid).config.put(features=features)

            result_text = f"""✅ LXC {vmid} features updated

  • Previous: {previous}
  • New: {features}
  • Node: {node}

🔧 Task/result: {task_result}

💡 Note: Setting keyctl/fuse (beyond nesting) typically requires root@pam.
   Restart or reboot_lxc may be needed for some feature changes to take effect."""

            return [Content(type="text", text=result_text)]

        except ValueError as e:
            raise e
        except Exception as e:
            self._handle_error(f"update LXC {vmid} features", e)
