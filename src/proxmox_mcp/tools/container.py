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
from .helpers import DEFAULT_LXC_FEATURES, assert_id_absent, pick_storage
from .spec import ToolSpec
from . import definitions as D

TOOL_SPECS = [
    ToolSpec("get_containers", D.GET_CONTAINERS_DESC),
    ToolSpec("create_lxc", D.CREATE_LXC_DESC),
    ToolSpec("get_lxc_config", D.GET_LXC_CONFIG_DESC),
    ToolSpec("update_lxc_config", D.UPDATE_LXC_CONFIG_DESC),
    ToolSpec("start_lxc", D.START_LXC_DESC),
    ToolSpec("stop_lxc", D.STOP_LXC_DESC),
    ToolSpec("shutdown_lxc", D.SHUTDOWN_LXC_DESC),
    ToolSpec("reboot_lxc", D.REBOOT_LXC_DESC),
    ToolSpec("delete_lxc", D.DELETE_LXC_DESC),
    ToolSpec("update_lxc_features", D.UPDATE_LXC_FEATURES_DESC),
    ToolSpec("clone_lxc", D.CLONE_LXC_DESC),
    ToolSpec("resize_lxc_disk", D.RESIZE_LXC_DISK_DESC),
    ToolSpec("convert_lxc_to_template", D.CONVERT_LXC_TEMPLATE_DESC),
    ToolSpec("execute_lxc_command", D.EXECUTE_LXC_COMMAND_DESC),
    ToolSpec("suspend_lxc", D.SUSPEND_LXC_DESC),
    ToolSpec("resume_lxc", D.RESUME_LXC_DESC),
    ToolSpec("get_lxc_status", D.GET_LXC_STATUS_DESC),
    ToolSpec("get_lxc_rrd_data", D.GET_LXC_RRD_DATA_DESC),
    ToolSpec("create_vnc_ticket_lxc", D.CREATE_VNC_TICKET_LXC_DESC),
    ToolSpec("create_spice_ticket_lxc", D.CREATE_SPICE_TICKET_LXC_DESC),
    ToolSpec("create_termproxy_ticket_lxc", D.CREATE_TERMPROXY_TICKET_LXC_DESC),
]


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
        ostemplate: Optional[str] = None,
        cpus: int = 1,
        memory: int = 2048,
        disk_size: int = 8,
        storage: Optional[str] = None,
        features: Optional[str] = None,
        password: Optional[str] = None,
        unprivileged: bool = True,
        bridge: Optional[str] = None,
        ip: Optional[str] = None,
        gw: Optional[str] = None,
        net0: Optional[str] = None,
        ostemplate_filter: Optional[str] = None,
    ) -> List[Content]:
        """Create an LXC container. If ostemplate is omitted, auto-picks from storage (optional filter)."""
        try:
            assert_id_absent(self.proxmox, node, vmid, "lxc")
            assert_id_absent(self.proxmox, node, vmid, "qemu")

            storage_list = self.proxmox.nodes(node).storage.get()
            storage_info = {s["storage"]: s for s in storage_list}
            storage = pick_storage(
                storage_list,
                content="rootdir",
                preferred=["local-lvm", "vm-storage"],
                explicit=storage,
            )

            if not ostemplate:
                ostemplate = self._resolve_ostemplate(node, ostemplate_filter)

            if features is None:
                features = DEFAULT_LXC_FEATURES

            from .helpers import DEFAULT_BRIDGE

            bridge = bridge or DEFAULT_BRIDGE
            ip_val = ip or "dhcp"
            if net0:
                net0_value = net0
            else:
                net0_value = f"name=eth0,bridge={bridge},ip={ip_val}"
                if gw and ip_val != "dhcp":
                    net0_value += f",gw={gw}"

            storage_type = storage_info[storage]["type"]
            lxc_config = {
                "vmid": vmid,
                "hostname": hostname,
                "ostemplate": ostemplate,
                "cores": cpus,
                "memory": memory,
                "rootfs": f"{storage}:{disk_size}",
                "net0": net0_value,
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
  • Rootfs: {disk_size} GB ({storage}, {storage_type})
  • OS Template: {ostemplate}
  • Features: {features}
  • Unprivileged: {unprivileged}
  • Network: {net0_value}

🔧 Task ID: {task_result}

💡 Next: wait_for_task → update_lxc_features (if Docker needs keyctl) → start_lxc."""

            return [Content(type="text", text=result_text)]

        except ValueError as e:
            raise e
        except Exception as e:
            self._handle_error(f"create LXC {vmid}", e)

    def _resolve_ostemplate(self, node: str, filter: Optional[str] = None) -> str:
        """Pick first matching vztmpl from node storage."""
        storage_list = self.proxmox.nodes(node).storage.get()
        candidates = []
        for s in storage_list:
            if "vztmpl" not in str(s.get("content", "")):
                continue
            items = self.proxmox.nodes(node).storage(s["storage"]).content.get(content="vztmpl")
            for item in items or []:
                volid = str(item.get("volid", ""))
                if not volid:
                    continue
                if filter and filter.lower() not in volid.lower():
                    continue
                candidates.append(volid)
        if not candidates:
            raise ValueError(
                "No ostemplate found. Pass ostemplate= explicitly, or use list_os_templates / "
                "download_url_to_storage (content=vztmpl). Optional ostemplate_filter e.g. 'ubuntu'."
            )
        return candidates[0]

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

    def suspend_lxc(self, node: str, vmid: str) -> List[Content]:
        """Suspend an LXC (CRIU checkpoint — often unreliable)."""
        try:
            task_result = self.proxmox.nodes(node).lxc(vmid).status.suspend.post()
            return [
                Content(
                    type="text",
                    text=(
                        f"⚠️ LXC {vmid} suspend initiated (CRIU — best-effort)\n"
                        f"Task ID: {task_result}\n"
                        f"Prefer shutdown_lxc for reliable power-off."
                    ),
                )
            ]
        except Exception as e:
            self._handle_error(f"suspend LXC {vmid}", e)

    def resume_lxc(self, node: str, vmid: str) -> List[Content]:
        """Resume a suspended LXC (CRIU — best-effort)."""
        try:
            task_result = self.proxmox.nodes(node).lxc(vmid).status.resume.post()
            return [
                Content(
                    type="text",
                    text=(
                        f"⚠️ LXC {vmid} resume initiated (CRIU — best-effort)\n"
                        f"Task ID: {task_result}"
                    ),
                )
            ]
        except Exception as e:
            self._handle_error(f"resume LXC {vmid}", e)

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

    def get_lxc_config(self, node: str, vmid: str) -> List[Content]:
        """Get full LXC container configuration."""
        try:
            config = self.proxmox.nodes(node).lxc(vmid).config.get()
            return self._format_response(config)
        except Exception as e:
            self._handle_error(f"get LXC {vmid} config", e)

    def update_lxc_config(self, node: str, vmid: str, **kwargs) -> List[Content]:
        """Update LXC configuration (cores, memory, hostname, net0, features, etc.)."""
        try:
            params = {k: v for k, v in kwargs.items() if v is not None}
            if not params:
                raise ValueError("No configuration parameters provided to update")
            result = self.proxmox.nodes(node).lxc(vmid).config.put(**params)
            return [
                Content(
                    type="text",
                    text=f"LXC {vmid} config updated\nParams: {params}\nResult: {result}",
                )
            ]
        except ValueError:
            raise
        except Exception as e:
            self._handle_error(f"update LXC {vmid} config", e)

    def clone_lxc(
        self,
        node: str,
        vmid: str,
        newid: str,
        hostname: Optional[str] = None,
        full: bool = True,
        target: Optional[str] = None,
        storage: Optional[str] = None,
    ) -> List[Content]:
        """Clone an LXC container to a new ID."""
        try:
            params = {"newid": int(newid), "full": 1 if full else 0}
            if hostname:
                params["hostname"] = hostname
            if target:
                params["target"] = target
            if storage:
                params["storage"] = storage
            result = self.proxmox.nodes(node).lxc(vmid).clone.post(**params)
            return [
                Content(
                    type="text",
                    text=f"Clone LXC {vmid} → {newid} initiated\nTask ID: {result}",
                )
            ]
        except Exception as e:
            self._handle_error(f"clone LXC {vmid}", e)

    def resize_lxc_disk(
        self, node: str, vmid: str, disk: str, size: str
    ) -> List[Content]:
        """Grow an LXC disk/volume (e.g. disk='rootfs', size='+5G')."""
        try:
            result = self.proxmox.nodes(node).lxc(vmid).resize.put(disk=disk, size=size)
            return [
                Content(
                    type="text",
                    text=f"Resize {disk} on LXC {vmid} to {size}\nResult: {result}",
                )
            ]
        except Exception as e:
            self._handle_error(f"resize disk on LXC {vmid}", e)

    def convert_lxc_to_template(self, node: str, vmid: str) -> List[Content]:
        """Convert an LXC container into a template."""
        try:
            result = self.proxmox.nodes(node).lxc(vmid).template.post()
            return [
                Content(
                    type="text",
                    text=f"LXC {vmid} convert-to-template initiated\nResult: {result}",
                )
            ]
        except Exception as e:
            self._handle_error(f"convert LXC {vmid} to template", e)

    def execute_lxc_command(self, node: str, vmid: str, command: str) -> List[Content]:
        """Execute a command inside a running LXC via the Proxmox exec API.

        Uses POST /nodes/{node}/lxc/{vmid}/exec when available on the cluster.
        """
        try:
            status = self.proxmox.nodes(node).lxc(vmid).status.current.get()
            if status.get("status") != "running":
                raise ValueError(f"LXC {vmid} is not running on node {node}")

            # Proxmox exposes guest exec as a callable subpath on some versions
            endpoint = self.proxmox.nodes(node).lxc(vmid)
            try:
                result = endpoint("exec").post(command=command)
            except Exception:
                # Fallback: some builds expect command as a list-like string
                result = endpoint.post("exec", command=command)

            return self._format_response(
                {"success": True, "command": command, "result": result}
            )
        except ValueError:
            raise
        except Exception as e:
            self._handle_error(f"execute command on LXC {vmid}", e)

    def create_vnc_ticket(self, node: str, vmid: str, websocket: bool = True) -> List[Content]:
        """Mint a VNC proxy ticket for an LXC (no websocket proxy)."""
        try:
            result = self.proxmox.nodes(node).lxc(vmid).vncproxy.post(
                websocket=1 if websocket else 0
            )
            return self._format_response(result)
        except Exception as e:
            self._handle_error(f"create VNC ticket for LXC {vmid}", e)

    def create_termproxy_ticket(self, node: str, vmid: str) -> List[Content]:
        """Mint a termproxy ticket for an LXC console."""
        try:
            result = self.proxmox.nodes(node).lxc(vmid).termproxy.post()
            return self._format_response(result)
        except Exception as e:
            self._handle_error(f"create termproxy ticket for LXC {vmid}", e)

    def create_spice_ticket(self, node: str, vmid: str) -> List[Content]:
        """Mint a SPICE proxy ticket for an LXC."""
        try:
            result = self.proxmox.nodes(node).lxc(vmid).spiceproxy.post()
            return self._format_response(result)
        except Exception as e:
            self._handle_error(f"create SPICE ticket for LXC {vmid}", e)

    def get_lxc_status(self, node: str, vmid: str) -> List[Content]:
        """Get current runtime status for a single LXC."""
        try:
            status = self.proxmox.nodes(node).lxc(vmid).status.current.get()
            return self._format_response(status)
        except Exception as e:
            self._handle_error(f"get status for LXC {vmid}", e)

    def get_lxc_rrd_data(
        self, node: str, vmid: str, timeframe: str = "hour"
    ) -> List[Content]:
        """Get RRD performance data for an LXC (timeframe: hour|day|week|month|year)."""
        try:
            data = self.proxmox.nodes(node).lxc(vmid).rrddata.get(timeframe=timeframe)
            return self._format_response(data)
        except Exception as e:
            self._handle_error(f"get RRD data for LXC {vmid}", e)
