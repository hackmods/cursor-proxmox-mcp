"""
LXC container tools for Proxmox MCP.

Provides lifecycle management for LXC containers:
- Listing containers across the cluster
- Creating containers (with nesting/features for Docker-in-LXC)
- Power control (start, stop, shutdown, reboot)
- Deletion
- Post-create feature updates (nesting, keyctl, fuse)
"""
from typing import Any, List, Optional
import base64
import shlex
from mcp.types import TextContent as Content
from .base import ProxmoxTool
from .helpers import (
    DEFAULT_LXC_FEATURES,
    assert_id_absent,
    check_exec_allowlist,
    console_ticket_footer,
    configured_ipv4_summary,
    is_missing_resource_error,
    lxc_not_found_message,
    parse_lxc_networks,
    pick_storage,
    upid_response_footer,
    wait_for_upid,
)
from .spec import ToolSpec
from . import definitions as D
from ..ssh import PctExecError, PctExecutor, require_host_ssh_message, ssh_configured

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
    ToolSpec("set_lxc_password", D.SET_LXC_PASSWORD_DESC),
    ToolSpec("set_lxc_ssh_keys", D.SET_LXC_SSH_KEYS_DESC),
    ToolSpec("prepare_lxc_for_docker", D.PREPARE_LXC_FOR_DOCKER_DESC),
    ToolSpec("push_to_lxc", D.PUSH_TO_LXC_DESC),
    ToolSpec("pull_from_lxc", D.PULL_FROM_LXC_DESC),
    ToolSpec("deploy_static_nginx", D.DEPLOY_STATIC_NGINX_DESC),
    ToolSpec("suspend_lxc", D.SUSPEND_LXC_DESC),
    ToolSpec("resume_lxc", D.RESUME_LXC_DESC),
    ToolSpec("get_lxc_status", D.GET_LXC_STATUS_DESC),
    ToolSpec("get_lxc_network", D.GET_LXC_NETWORK_DESC),
    ToolSpec("get_lxc_rrd_data", D.GET_LXC_RRD_DATA_DESC),
    ToolSpec("create_vnc_ticket_lxc", D.CREATE_VNC_TICKET_LXC_DESC),
    ToolSpec("create_spice_ticket_lxc", D.CREATE_SPICE_TICKET_LXC_DESC),
    ToolSpec("create_termproxy_ticket_lxc", D.CREATE_TERMPROXY_TICKET_LXC_DESC),
]


class ContainerTools(ProxmoxTool):
    """Tools for managing Proxmox LXC containers."""

    def __init__(
        self,
        proxmox_api: Any,
        ssh_config: Optional[Any] = None,
        proxmox_host: Optional[str] = None,
    ):
        super().__init__(proxmox_api)
        self.ssh_config = ssh_config
        self.proxmox_host = proxmox_host or ""
        self._pct: Optional[PctExecutor] = None
        if ssh_configured(ssh_config) and self.proxmox_host:
            self._pct = PctExecutor(ssh_config, self.proxmox_host)

    def get_containers(self, probes: bool = False) -> List[Content]:
        """List all LXC containers across the cluster with detailed status.

        When ``probes=True`` and host SSH is configured, run cheap pct checks for
        docker binary and :80 listeners on *running* CTs only (opt-in; D25-adjacent).
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
                        networks = parse_lxc_networks(config)
                        entry = {
                            "vmid": vmid,
                            "name": config.get("hostname", name),
                            "status": ct["status"],
                            "node": node_name,
                            "cpus": config.get("cores", "N/A"),
                            "memory": {
                                "used": ct.get("mem", 0),
                                "total": ct.get("maxmem", 0),
                            },
                            "ip": configured_ipv4_summary(networks),
                            "networks": networks,
                        }
                    except Exception:
                        entry = {
                            "vmid": vmid,
                            "name": name,
                            "status": ct["status"],
                            "node": node_name,
                            "cpus": "N/A",
                            "memory": {
                                "used": ct.get("mem", 0),
                                "total": ct.get("maxmem", 0),
                            },
                            "ip": None,
                            "networks": [],
                        }
                    if probes:
                        entry.update(
                            self._probe_container(node_name, str(vmid), ct.get("status"))
                        )
                    result.append(entry)
            return self._format_response(result, "containers")
        except Exception as e:
            self._handle_error("get containers", e)

    def _probe_container(
        self, node: str, vmid: str, status: Optional[str]
    ) -> dict:
        """Cheap docker / :80 probes; never raises."""
        out: dict = {
            "probe_docker": None,
            "probe_port_80": None,
            "probe_note": None,
        }
        if status != "running":
            out["probe_note"] = "skipped (not running)"
            return out
        if not self._pct:
            out["probe_note"] = "skipped (host SSH not configured)"
            return out
        try:
            docker = self._pct.execute(
                node,
                vmid,
                "command -v docker >/dev/null 2>&1 && echo yes || echo no",
                timeout=15,
            )
            out["probe_docker"] = (
                "yes" if "yes" in (docker.stdout or "").strip().lower() else "no"
            )
        except Exception as e:
            out["probe_docker"] = None
            out["probe_note"] = f"docker probe failed: {e}"
        try:
            port80 = self._pct.execute(
                node,
                vmid,
                "ss -ltn 2>/dev/null | grep -q ':80 ' && echo yes || "
                "(netstat -ltn 2>/dev/null | grep -q ':80 ' && echo yes || echo no)",
                timeout=15,
            )
            out["probe_port_80"] = (
                "yes" if "yes" in (port80.stdout or "").strip().lower() else "no"
            )
        except Exception as e:
            out["probe_port_80"] = None
            note = out.get("probe_note")
            fail = f"port80 probe failed: {e}"
            out["probe_note"] = f"{note}; {fail}" if note else fail
        return out

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
        ssh_public_keys: Optional[str] = None,
        unprivileged: bool = True,
        bridge: Optional[str] = None,
        ip: Optional[str] = None,
        gw: Optional[str] = None,
        net0: Optional[str] = None,
        ostemplate_filter: Optional[str] = None,
        docker_ready: bool = False,
        wait: bool = False,
    ) -> List[Content]:
        """Create an LXC container. If ostemplate is omitted, auto-picks from storage (optional filter).

        ``password`` and ``ssh_public_keys`` are applied only at create time by Proxmox
        (rootfs provisioning). Many templates still block root password SSH
        (PermitRootLogin prohibit-password) — prefer ``ssh_public_keys`` for guest SSH.
        ``docker_ready`` sets nesting+keyctl features and tips ``prepare_lxc_for_docker``;
        it does not install Docker or claim runtime readiness (D21).
        When ``wait=True``, poll the create UPID until stopped (D25; default remains false).
        """
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

            if docker_ready and features is None:
                features = "nesting=1,keyctl=1"
            elif features is None:
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
            if ssh_public_keys is not None and str(ssh_public_keys).strip():
                # Proxmox API key is hyphenated (create-time only)
                lxc_config["ssh-public-keys"] = str(ssh_public_keys).strip()

            hostname_warn = self._hostname_collision_warning(hostname, exclude_vmid=None)

            task_result = self.proxmox.nodes(node).lxc.create(**lxc_config)

            auth_lines = []
            if password is not None:
                auth_lines.append(
                    "  • Root password: set at create (API password=) — NOT echoed here"
                )
                auth_lines.append(
                    "  • Note: many templates block root *password* SSH "
                    "(PermitRootLogin prohibit-password). Prefer ssh_public_keys, "
                    "or after start use set_lxc_password(enable_password_ssh=true) "
                    "when host SSH/pct is configured."
                )
            else:
                auth_lines.append("  • Root password: not set")
            if ssh_public_keys is not None and str(ssh_public_keys).strip():
                key_count = len(
                    [ln for ln in str(ssh_public_keys).splitlines() if ln.strip()]
                )
                auth_lines.append(f"  • SSH public keys: {key_count} key(s) injected at create")
            else:
                auth_lines.append("  • SSH public keys: none (pass ssh_public_keys for guest SSH)")

            ssh_pct = (
                "configured — execute_lxc_command / set_lxc_password / prepare_lxc_for_docker / push_to_lxc available after start"
                if self._pct
                else "NOT configured — enable config ssh + reload MCP for pct "
                "(Proxmox has no REST LXC shell; 501 /exec means stale MCP build)"
            )

            warn_block = f"\n⚠️ {hostname_warn}\n" if hostname_warn else "\n"
            docker_line = (
                "  • docker_ready: true (features nesting+keyctl; call prepare_lxc_for_docker after start)\n"
                if docker_ready
                else ""
            )

            if wait:
                final = wait_for_upid(self.proxmox, node, task_result, timeout=600)
                status = final.get("status") if isinstance(final, dict) else final
                exitstatus = (
                    final.get("exitstatus") if isinstance(final, dict) else None
                )
                task_block = (
                    f"⏳ wait=true — task finished: status={status} "
                    f"exitstatus={exitstatus}\n🔧 Task ID: {task_result}"
                )
                next_step_1 = (
                    "1. Create finished (wait=true) — proceed to start_lxc "
                    "(re-check get_task_status if exitstatus != OK)"
                )
            else:
                task_block = (
                    f"🔧 Task ID: {task_result}\n"
                    f"{upid_response_footer(task_result, node=node)}"
                )
                next_step_1 = (
                    "1. wait_for_task(node, upid) until stopped — create ≠ ready; "
                    "task errors (missing template) surface here"
                )

            result_text = f"""🎉 LXC container {vmid} create task started (OS template only — not a deployed app).

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
{docker_line}{chr(10).join(auth_lines)}
  • Host SSH/pct for MCP: {ssh_pct}
{warn_block}{task_block}

💡 Next (bootstrap):
  {next_step_1}
  2. start_lxc → get_lxc_network (configured/runtime IP)
  3. Guest access: prefer ssh_public_keys at create; or set_lxc_password / set_lxc_ssh_keys / execute_lxc_command (all need config ssh)
  4. For Docker: prepare_lxc_for_docker → stop_lxc + start_lxc → smoke with docker run --rm nginx:alpine (nesting alone ≠ Docker)
  5. Static site without Docker: deploy_static_nginx
  6. keyctl for Docker-in-LXC often needs elevated role / root@pam (update_lxc_features / prepare)"""

            return [Content(type="text", text=result_text)]

        except ValueError as e:
            raise e
        except Exception as e:
            self._handle_error(f"create LXC {vmid}", e)

    def _hostname_collision_warning(
        self, hostname: str, exclude_vmid: Optional[str] = None
    ) -> Optional[str]:
        """Warn if another LXC already uses this hostname (Proxmox allows duplicates)."""
        try:
            hits = []
            nodes = self.proxmox.nodes.get()
            if not isinstance(nodes, list):
                return None
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                node_name = node.get("node")
                if not node_name:
                    continue
                containers = self.proxmox.nodes(node_name).lxc.get()
                if not isinstance(containers, list):
                    continue
                for ct in containers:
                    if not isinstance(ct, dict):
                        continue
                    vmid = str(ct.get("vmid", ""))
                    if exclude_vmid is not None and vmid == str(exclude_vmid):
                        continue
                    name = ct.get("name") or ct.get("hostname") or ""
                    try:
                        cfg = self.proxmox.nodes(node_name).lxc(vmid).config.get()
                        if isinstance(cfg, dict):
                            name = cfg.get("hostname") or name
                    except Exception:
                        pass
                    if str(name).lower() == str(hostname).lower():
                        hits.append(f"{vmid}@{node_name}")
            if hits:
                return (
                    f"Hostname '{hostname}' already used by LXC {', '.join(hits)}. "
                    "Proxmox allows this; prefer unique names for agent listings."
                )
        except Exception:
            return None
        return None

    def _require_pct(self) -> PctExecutor:
        if not self._pct:
            raise ValueError(require_host_ssh_message(context="This operation"))
        return self._pct

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
                result_text = (
                    f"🚀 LXC {vmid} start initiated\n"
                    f"{upid_response_footer(task_result, node=node)}"
                )

            return [Content(type="text", text=result_text)]

        except Exception as e:
            if is_missing_resource_error(e):
                raise ValueError(lxc_not_found_message(vmid, node))
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
                result_text = (
                    f"🛑 LXC {vmid} stop initiated\n"
                    f"{upid_response_footer(task_result, node=node)}"
                )

            return [Content(type="text", text=result_text)]

        except Exception as e:
            if is_missing_resource_error(e):
                raise ValueError(lxc_not_found_message(vmid, node))
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
                result_text = (
                    f"💤 LXC {vmid} graceful shutdown initiated\n"
                    f"{upid_response_footer(task_result, node=node)}"
                )

            return [Content(type="text", text=result_text)]

        except Exception as e:
            if is_missing_resource_error(e):
                raise ValueError(lxc_not_found_message(vmid, node))
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
                result_text = (
                    f"🔄 LXC {vmid} reboot initiated\n"
                    f"{upid_response_footer(task_result, node=node)}"
                )

            return [Content(type="text", text=result_text)]

        except Exception as e:
            if is_missing_resource_error(e):
                raise ValueError(lxc_not_found_message(vmid, node))
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
                        f"{upid_response_footer(task_result, node=node)}\n"
                        f"Prefer shutdown_lxc for reliable power-off."
                    ),
                )
            ]
        except Exception as e:
            if is_missing_resource_error(e):
                raise ValueError(lxc_not_found_message(vmid, node))
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
                        f"{upid_response_footer(task_result, node=node)}"
                    ),
                )
            ]
        except Exception as e:
            if is_missing_resource_error(e):
                raise ValueError(lxc_not_found_message(vmid, node))
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
                if is_missing_resource_error(e):
                    raise ValueError(lxc_not_found_message(vmid, node))
                raise e

            if current_status == "running":
                if not force:
                    raise ValueError(
                        f"LXC {vmid} ({ct_name}) is currently running. "
                        f"Please stop it first or use force=True to stop and delete."
                    )
                stop_upid = self.proxmox.nodes(node).lxc(vmid).status.stop.post()
                wait_for_upid(self.proxmox, node, stop_upid, timeout=120)
                result_text = (
                    f"🛑 Stopped LXC {vmid} ({ct_name}) before deletion "
                    f"(stop UPID: {stop_upid})\n"
                )
            else:
                result_text = f"🗑️ Deleting LXC {vmid} ({ct_name})...\n"

            task_result = self.proxmox.nodes(node).lxc(vmid).delete()

            result_text += f"""🗑️ LXC {vmid} ({ct_name}) deletion initiated!

⚠️ IRREVERSIBLE: This operation will permanently remove:
  • Container configuration
  • Root filesystem
  • All snapshots
  • Cannot be undone!

{upid_response_footer(task_result, node=node)}"""

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
                if is_missing_resource_error(e):
                    raise ValueError(lxc_not_found_message(vmid, node))
                raise e

            previous = config.get("features", "(none)")
            task_result = self.proxmox.nodes(node).lxc(vmid).config.put(features=features)

            result_text = f"""✅ LXC {vmid} features updated

  • Previous: {previous}
  • New: {features}
  • Node: {node}

🔧 Task/result: {task_result}

💡 Note: Setting keyctl/fuse (beyond nesting) typically requires root@pam.
💡 Next: get_guest_pending (guest_type=lxc) — prefer stop_lxc + start_lxc (or reboot_lxc)
   so feature / raw config changes apply. For Docker-in-LXC use prepare_lxc_for_docker."""

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
            if is_missing_resource_error(e):
                raise ValueError(lxc_not_found_message(vmid, node))
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
                    text=(
                        f"LXC {vmid} config updated\nParams: {params}\nResult: {result}\n"
                        f"💡 Next: get_guest_pending (guest_type=lxc) — reboot_lxc / reboot_guest "
                        f"if keys are pending and not hot-pluggable."
                    ),
                )
            ]
        except ValueError:
            raise
        except Exception as e:
            if is_missing_resource_error(e):
                raise ValueError(lxc_not_found_message(vmid, node))
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
                    text=(
                        f"Clone LXC {vmid} → {newid} initiated\n"
                        f"{upid_response_footer(result, node=node)}"
                    ),
                )
            ]
        except Exception as e:
            if is_missing_resource_error(e):
                raise ValueError(lxc_not_found_message(vmid, node))
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
                    text=(
                        f"Resize {disk} on LXC {vmid} to {size} initiated\n"
                        f"{upid_response_footer(result, node=node)}"
                    ),
                )
            ]
        except Exception as e:
            if is_missing_resource_error(e):
                raise ValueError(lxc_not_found_message(vmid, node))
            self._handle_error(f"resize disk on LXC {vmid}", e)

    def convert_lxc_to_template(self, node: str, vmid: str) -> List[Content]:
        """Convert an LXC container into a template."""
        try:
            result = self.proxmox.nodes(node).lxc(vmid).template.post()
            return [
                Content(
                    type="text",
                    text=(
                        f"LXC {vmid} convert-to-template initiated\n"
                        f"{upid_response_footer(result, node=node)}"
                    ),
                )
            ]
        except Exception as e:
            if is_missing_resource_error(e):
                raise ValueError(lxc_not_found_message(vmid, node))
            self._handle_error(f"convert LXC {vmid} to template", e)

    def execute_lxc_command(
        self,
        node: str,
        vmid: str,
        command: str,
        timeout: Optional[int] = None,
    ) -> List[Content]:
        """Execute a command inside a running LXC via host-side ``pct exec`` over SSH.

        Proxmox has no REST ``/lxc/{vmid}/exec`` endpoint. Requires opt-in
        ``ssh`` config. See SETUP.md / D4. Response includes VM-parity output/error aliases.
        """
        try:
            check_exec_allowlist(command)
            pct = self._require_pct()

            status = self.proxmox.nodes(node).lxc(vmid).status.current.get()
            if status.get("status") != "running":
                raise ValueError(f"LXC {vmid} is not running on node {node}")

            result = pct.execute(node, vmid, command, timeout=timeout)
            return self._format_response(
                {
                    "success": result.success,
                    "command": result.command,
                    "exit_code": result.exit_code,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "output": result.stdout,
                    "error": result.stderr,
                }
            )
        except ValueError:
            raise
        except PctExecError as e:
            raise RuntimeError(str(e)) from e
        except Exception as e:
            if is_missing_resource_error(e):
                raise ValueError(lxc_not_found_message(vmid, node))
            self._handle_error(f"execute command on LXC {vmid}", e)

    def set_lxc_password(
        self,
        node: str,
        vmid: str,
        password: str,
        enable_password_ssh: bool = True,
    ) -> List[Content]:
        """Set/reset root password inside a running LXC via ``pct exec``.

        Proxmox has no REST API to change LXC password after create. Optionally
        enables PermitRootLogin + PasswordAuthentication (many templates block
        root password SSH even when the password is correct).
        """
        try:
            if not password:
                raise ValueError("password must be non-empty")
            check_exec_allowlist("chpasswd")
            pct = self._require_pct()

            status = self.proxmox.nodes(node).lxc(vmid).status.current.get()
            if status.get("status") != "running":
                raise ValueError(
                    f"LXC {vmid} is not running on node {node} — start_lxc first"
                )

            # Avoid putting the raw password in logs; chpasswd via printf.
            pw_q = shlex.quote(f"root:{password}")
            steps = [f"printf '%s\\n' {pw_q} | chpasswd"]
            if enable_password_ssh:
                steps.extend(
                    [
                        "mkdir -p /etc/ssh/sshd_config.d",
                        "printf '%s\\n' 'PermitRootLogin yes' "
                        "'PasswordAuthentication yes' > /etc/ssh/sshd_config.d/99-proxmox-mcp.conf",
                        "(command -v systemctl >/dev/null && systemctl restart ssh) "
                        "|| (command -v systemctl >/dev/null && systemctl restart sshd) "
                        "|| service ssh restart || service sshd restart || true",
                    ]
                )
            cmd = " && ".join(steps)
            result = pct.execute(node, vmid, cmd)
            if not result.success:
                raise RuntimeError(
                    f"set_lxc_password failed (exit {result.exit_code}): "
                    f"{result.stderr or result.stdout}"
                )
            return [
                Content(
                    type="text",
                    text=(
                        f"Root password updated on LXC {vmid} via pct exec "
                        f"(password not logged).\n"
                        f"enable_password_ssh={enable_password_ssh}\n"
                        f"💡 Next: get_lxc_network → SSH as root@<ip> "
                        f"or continue with execute_lxc_command."
                    ),
                )
            ]
        except ValueError:
            raise
        except PctExecError as e:
            raise RuntimeError(str(e)) from e
        except Exception as e:
            self._handle_error(f"set password on LXC {vmid}", e)

    def set_lxc_ssh_keys(
        self,
        node: str,
        vmid: str,
        ssh_public_keys: str,
        mode: str = "replace",
    ) -> List[Content]:
        """Install root authorized_keys inside a running LXC via ``pct exec``.

        Prefer passing ``ssh_public_keys`` on create_lxc when possible (native API).
        Post-create injection requires host SSH/pct (no REST equivalent for update).
        """
        try:
            keys = str(ssh_public_keys or "").strip()
            if not keys:
                raise ValueError("ssh_public_keys must be non-empty OpenSSH public key(s)")
            mode_norm = (mode or "replace").lower().strip()
            if mode_norm not in ("replace", "append"):
                raise ValueError("mode must be 'replace' or 'append'")

            check_exec_allowlist("authorized_keys")
            pct = self._require_pct()

            status = self.proxmox.nodes(node).lxc(vmid).status.current.get()
            if status.get("status") != "running":
                raise ValueError(
                    f"LXC {vmid} is not running on node {node} — start_lxc first"
                )

            # Transport keys as base64 to avoid shell-metacharacter issues
            b64 = base64.b64encode((keys + "\n").encode("utf-8")).decode("ascii")
            b64_q = shlex.quote(b64)
            if mode_norm == "replace":
                write = (
                    f"echo {b64_q} | base64 -d > /root/.ssh/authorized_keys"
                )
            else:
                write = (
                    f"echo {b64_q} | base64 -d >> /root/.ssh/authorized_keys"
                )
            cmd = (
                "mkdir -p /root/.ssh && chmod 700 /root/.ssh && "
                f"{write} && chmod 600 /root/.ssh/authorized_keys && "
                "chown -R root:root /root/.ssh"
            )
            result = pct.execute(node, vmid, cmd)
            if not result.success:
                raise RuntimeError(
                    f"set_lxc_ssh_keys failed (exit {result.exit_code}): "
                    f"{result.stderr or result.stdout}"
                )
            key_count = len([ln for ln in keys.splitlines() if ln.strip()])
            return [
                Content(
                    type="text",
                    text=(
                        f"Installed {key_count} SSH public key(s) for root on LXC {vmid} "
                        f"(mode={mode_norm}) via pct exec.\n"
                        f"💡 Next: get_lxc_network → ssh -i <key> root@<ip>"
                    ),
                )
            ]
        except ValueError:
            raise
        except PctExecError as e:
            raise RuntimeError(str(e)) from e
        except Exception as e:
            self._handle_error(f"set SSH keys on LXC {vmid}", e)

    def prepare_lxc_for_docker(
        self,
        node: str,
        vmid: str,
        fuse: bool = False,
        allow_apparmor_workaround: bool = True,
        install_docker: bool = False,
        smoke_test: bool = False,
        timeout: Optional[int] = None,
    ) -> List[Content]:
        """Idempotent Proxmox-side prep for Docker-in-LXC (D24)."""
        try:
            pct = self._require_pct()
            try:
                config = self.proxmox.nodes(node).lxc(vmid).config.get()
            except Exception as e:
                if is_missing_resource_error(e):
                    raise ValueError(lxc_not_found_message(vmid, node))
                raise e

            applied: List[str] = []
            features = "nesting=1,keyctl=1" + (",fuse=1" if fuse else "")
            prev_features = str(config.get("features", "") or "")
            if features not in prev_features.replace(" ", "") and prev_features != features:
                try:
                    self.proxmox.nodes(node).lxc(vmid).config.put(features=features)
                    applied.append(f"features → {features} (was {prev_features or '(none)'})")
                except Exception as feat_err:
                    # Fall back to pct set (may need root on host)
                    fr = pct.ensure_features(node, vmid, features)
                    if not fr.success:
                        raise RuntimeError(
                            f"Failed to set features={features}: {feat_err}; "
                            f"pct set also failed: {fr.stderr or fr.stdout}. "
                            "keyctl often needs elevated role / root@pam."
                        ) from feat_err
                    applied.append(f"features → {features} via pct set")

            raw_ver, _parsed, patched = pct.probe_lxc_pve_version(node)
            host_patch = (
                f"ok (lxc-pve {raw_ver})"
                if patched
                else f"unpatched or unknown (lxc-pve={raw_ver or 'n/a'}; need ≥6.0.5-2)"
            )

            restart_required = False
            if patched:
                stripped = pct.strip_docker_apparmor_workaround(node, vmid)
                if stripped:
                    applied.extend(stripped)
                    restart_required = True
                applied.append("host patch OK — left generated AppArmor/nesting (no unconfined)")
            elif allow_apparmor_workaround:
                changes = pct.apply_docker_apparmor_workaround(node, vmid)
                if changes:
                    applied.extend(changes)
                    restart_required = True
                else:
                    applied.append("AppArmor workaround lines already present")
                restart_required = True
            else:
                applied.append(
                    "host unpatched and allow_apparmor_workaround=false — "
                    "upgrade lxc-pve on the node, or re-run with workaround enabled"
                )

            docker_note = ""
            if install_docker:
                status = self.proxmox.nodes(node).lxc(vmid).status.current.get()
                if status.get("status") != "running":
                    raise ValueError(
                        f"LXC {vmid} must be running for install_docker — start_lxc first "
                        "(after stop/start if restart_required)"
                    )
                install_cmd = (
                    "export DEBIAN_FRONTEND=noninteractive; "
                    "(command -v docker >/dev/null && docker --version) || "
                    "(apt-get update -qq && apt-get install -y -qq ca-certificates curl && "
                    "curl -fsSL https://get.docker.com | sh)"
                )
                ir = pct.execute(node, vmid, install_cmd, timeout=timeout or 300)
                if not ir.success:
                    raise RuntimeError(
                        f"install_docker failed (exit {ir.exit_code}): "
                        f"{ir.stderr or ir.stdout}"
                    )
                applied.append("docker install attempted via get.docker.com / existing docker")
                docker_note = f"\nDocker install stdout (tail):\n{(ir.stdout or '')[-500:]}"

            smoke_note = ""
            if smoke_test:
                if restart_required:
                    smoke_note = (
                        "\nsmoke_test skipped: restart_required — "
                        "stop_lxc + start_lxc first, then re-run with smoke_test=true "
                        "or execute_lxc_command('docker run --rm nginx:alpine')"
                    )
                else:
                    status = self.proxmox.nodes(node).lxc(vmid).status.current.get()
                    if status.get("status") != "running":
                        raise ValueError(f"LXC {vmid} must be running for smoke_test")
                    sr = pct.execute(
                        node,
                        vmid,
                        "docker run --rm nginx:alpine true",
                        timeout=timeout or 180,
                    )
                    if not sr.success:
                        smoke_note = (
                            f"\n⚠️ smoke_test FAILED (exit {sr.exit_code}): "
                            f"{sr.stderr or sr.stdout}\n"
                            "If ip_unprivileged_port_start: upgrade host lxc-pve or ensure "
                            "dual AppArmor workaround + full stop/start."
                        )
                    else:
                        smoke_note = "\n✅ smoke_test: docker run --rm nginx:alpine OK"
                        applied.append("smoke_test passed")

            applied_txt = "\n".join(f"  • {a}" for a in applied) or "  • (no changes)"
            result = f"""prepare_lxc_for_docker CT {vmid}@{node}

host_patch_status: {host_patch}
restart_required: {restart_required}
applied:
{applied_txt}
{docker_note}{smoke_note}

Known limitations (D24):
  • Docker --privileged / --sysctl / --security-opt do NOT fix nested AppArmor CVE issues
  • Do not downgrade containerd to "fix" run (re-opens CVE-2025-52881)
  • Bare lxc.apparmor.profile: unconfined without the /dev/null bind breaks nesting/Docker
  • Success criterion: docker run --rm nginx:alpine — not merely docker --version

💡 Next: {"stop_lxc → start_lxc (full stop/start, not reboot alone) → " if restart_required else ""}"""
            result += (
                "execute_lxc_command('docker run --rm -p 8080:80 nginx:alpine') then curl; "
                "use push_to_lxc for app files."
            )
            return [Content(type="text", text=result)]
        except ValueError:
            raise
        except PctExecError as e:
            raise RuntimeError(str(e)) from e
        except Exception as e:
            if is_missing_resource_error(e):
                raise ValueError(lxc_not_found_message(vmid, node))
            self._handle_error(f"prepare LXC {vmid} for docker", e)

    def push_to_lxc(
        self,
        node: str,
        vmid: str,
        remote_path: str,
        local_path: Optional[str] = None,
        content_base64: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> List[Content]:
        """Push file bytes into a CT via SFTP + pct push."""
        try:
            pct = self._require_pct()
            if not remote_path or not str(remote_path).strip():
                raise ValueError("remote_path is required")
            if bool(local_path) == bool(content_base64):
                raise ValueError("Provide exactly one of local_path or content_base64")

            if local_path:
                with open(local_path, "rb") as fh:
                    data = fh.read()
                src = local_path
            else:
                data = base64.b64decode(content_base64 or "")
                src = "content_base64"

            try:
                self.proxmox.nodes(node).lxc(vmid).status.current.get()
            except Exception as e:
                if is_missing_resource_error(e):
                    raise ValueError(lxc_not_found_message(vmid, node))
                raise e

            pct.push_to_guest(node, vmid, data, remote_path, timeout=timeout)
            return [
                Content(
                    type="text",
                    text=(
                        f"Pushed {len(data)} bytes → CT {vmid}:{remote_path} "
                        f"(from {src}) via pct push.\n"
                        f"💡 Next: execute_lxc_command to extract/chmod as needed."
                    ),
                )
            ]
        except ValueError:
            raise
        except PctExecError as e:
            raise RuntimeError(str(e)) from e
        except Exception as e:
            if is_missing_resource_error(e):
                raise ValueError(lxc_not_found_message(vmid, node))
            self._handle_error(f"push to LXC {vmid}", e)

    def pull_from_lxc(
        self,
        node: str,
        vmid: str,
        remote_path: str,
        local_path: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> List[Content]:
        """Pull a file from a CT via pct pull."""
        try:
            pct = self._require_pct()
            if not remote_path or not str(remote_path).strip():
                raise ValueError("remote_path is required")

            try:
                self.proxmox.nodes(node).lxc(vmid).status.current.get()
            except Exception as e:
                if is_missing_resource_error(e):
                    raise ValueError(lxc_not_found_message(vmid, node))
                raise e

            data = pct.pull_from_guest(node, vmid, remote_path, timeout=timeout)
            if local_path:
                with open(local_path, "wb") as fh:
                    fh.write(data)
                return [
                    Content(
                        type="text",
                        text=(
                            f"Pulled CT {vmid}:{remote_path} → {local_path} "
                            f"({len(data)} bytes) via pct pull."
                        ),
                    )
                ]
            b64 = base64.b64encode(data).decode("ascii")
            return self._format_response(
                {
                    "vmid": vmid,
                    "remote_path": remote_path,
                    "size": len(data),
                    "content_base64": b64,
                }
            )
        except ValueError:
            raise
        except PctExecError as e:
            raise RuntimeError(str(e)) from e
        except Exception as e:
            if is_missing_resource_error(e):
                raise ValueError(lxc_not_found_message(vmid, node))
            self._handle_error(f"pull from LXC {vmid}", e)

    def deploy_static_nginx(
        self,
        node: str,
        vmid: str,
        local_path: Optional[str] = None,
        content_base64: Optional[str] = None,
        remote_extract_dir: str = "/var/www/html",
        timeout: Optional[int] = None,
    ) -> List[Content]:
        """Install nginx and deploy static content into a running LXC (Lumon-style)."""
        try:
            pct = self._require_pct()
            status = self.proxmox.nodes(node).lxc(vmid).status.current.get()
            if status.get("status") != "running":
                raise ValueError(f"LXC {vmid} is not running on node {node}")

            dest = (remote_extract_dir or "/var/www/html").rstrip("/") or "/var/www/html"
            t = timeout

            install = pct.execute(
                node,
                vmid,
                "export DEBIAN_FRONTEND=noninteractive; "
                "(command -v nginx >/dev/null 2>&1 || "
                "(apt-get update -qq && apt-get install -y -qq nginx)) && "
                "systemctl enable --now nginx 2>/dev/null || "
                "service nginx start 2>/dev/null || true",
                timeout=t or 300,
            )
            if install.exit_code != 0:
                # Some guests omit systemctl; tolerate if nginx binary exists
                check = pct.execute(node, vmid, "command -v nginx", timeout=15)
                if check.exit_code != 0:
                    raise RuntimeError(
                        f"nginx install failed: exit={install.exit_code} "
                        f"stderr={install.stderr}"
                    )

            content_note = "default nginx index left in place"
            if local_path or content_base64:
                if bool(local_path) == bool(content_base64):
                    raise ValueError(
                        "Provide at most one of local_path or content_base64 "
                        "(omit both to only install nginx)"
                    )
                if local_path:
                    with open(local_path, "rb") as fh:
                        data = fh.read()
                    src_name = local_path.rsplit("/" if "/" in local_path else "\\", 1)[-1]
                else:
                    data = base64.b64decode(content_base64 or "")
                    src_name = "payload.bin"

                lower = src_name.lower()
                if lower.endswith((".tar.gz", ".tgz")):
                    remote_archive = "/root/mcp-nginx-site.tgz"
                    pct.push_to_guest(node, vmid, data, remote_archive, timeout=t)
                    extract = pct.execute(
                        node,
                        vmid,
                        f"mkdir -p {shlex.quote(dest)} && "
                        f"tar -xzf {shlex.quote(remote_archive)} -C {shlex.quote(dest)} && "
                        f"rm -f {shlex.quote(remote_archive)}",
                        timeout=t or 120,
                    )
                    if extract.exit_code != 0:
                        raise RuntimeError(
                            f"extract failed: {extract.stderr or extract.stdout}"
                        )
                    content_note = f"extracted {src_name} → {dest}"
                elif lower.endswith(".tar"):
                    remote_archive = "/root/mcp-nginx-site.tar"
                    pct.push_to_guest(node, vmid, data, remote_archive, timeout=t)
                    extract = pct.execute(
                        node,
                        vmid,
                        f"mkdir -p {shlex.quote(dest)} && "
                        f"tar -xf {shlex.quote(remote_archive)} -C {shlex.quote(dest)} && "
                        f"rm -f {shlex.quote(remote_archive)}",
                        timeout=t or 120,
                    )
                    if extract.exit_code != 0:
                        raise RuntimeError(
                            f"extract failed: {extract.stderr or extract.stdout}"
                        )
                    content_note = f"extracted {src_name} → {dest}"
                else:
                    # Treat as a single HTML/file → index.html
                    remote_file = f"{dest}/index.html"
                    pct.execute(
                        node,
                        vmid,
                        f"mkdir -p {shlex.quote(dest)}",
                        timeout=30,
                    )
                    pct.push_to_guest(node, vmid, data, remote_file, timeout=t)
                    content_note = f"wrote {len(data)} bytes → {remote_file}"

            reload = pct.execute(
                node,
                vmid,
                "nginx -t 2>/dev/null && "
                "(systemctl reload nginx 2>/dev/null || nginx -s reload 2>/dev/null || true)",
                timeout=30,
            )
            ip_hint = ""
            try:
                net = self.get_lxc_network(node, vmid, resolve_runtime=True)
                if net and getattr(net[0], "text", None):
                    ip_hint = "\n💡 Use get_lxc_network for guest IP, then curl http://<ip>/"
            except Exception:
                ip_hint = "\n💡 Use get_lxc_network for guest IP, then curl http://<ip>/"

            return [
                Content(
                    type="text",
                    text=(
                        f"deploy_static_nginx CT {vmid}@{node}\n"
                        f"  • nginx: installed/enabled (best-effort)\n"
                        f"  • content: {content_note}\n"
                        f"  • reload: exit={reload.exit_code}"
                        f"{ip_hint}"
                    ),
                )
            ]
        except ValueError:
            raise
        except PctExecError as e:
            raise RuntimeError(str(e)) from e
        except Exception as e:
            if is_missing_resource_error(e):
                raise ValueError(lxc_not_found_message(vmid, node))
            self._handle_error(f"deploy static nginx on LXC {vmid}", e)

    def create_vnc_ticket(self, node: str, vmid: str, websocket: bool = True) -> List[Content]:
        """Mint a VNC proxy ticket for an LXC (no websocket proxy)."""
        try:
            import json

            result = self.proxmox.nodes(node).lxc(vmid).vncproxy.post(
                websocket=1 if websocket else 0
            )
            body = json.dumps(result, indent=2)
            return [
                Content(
                    type="text",
                    text=f"{body}\n\n{console_ticket_footer('VNC')}",
                )
            ]
        except Exception as e:
            if is_missing_resource_error(e):
                raise ValueError(lxc_not_found_message(vmid, node))
            self._handle_error(f"create VNC ticket for LXC {vmid}", e)

    def create_termproxy_ticket(self, node: str, vmid: str) -> List[Content]:
        """Mint a termproxy ticket for an LXC console."""
        try:
            import json

            result = self.proxmox.nodes(node).lxc(vmid).termproxy.post()
            body = json.dumps(result, indent=2)
            return [
                Content(
                    type="text",
                    text=f"{body}\n\n{console_ticket_footer('termproxy')}",
                )
            ]
        except Exception as e:
            if is_missing_resource_error(e):
                raise ValueError(lxc_not_found_message(vmid, node))
            self._handle_error(f"create termproxy ticket for LXC {vmid}", e)

    def create_spice_ticket(self, node: str, vmid: str) -> List[Content]:
        """Mint a SPICE proxy ticket for an LXC."""
        try:
            import json

            result = self.proxmox.nodes(node).lxc(vmid).spiceproxy.post()
            body = json.dumps(result, indent=2)
            return [
                Content(
                    type="text",
                    text=f"{body}\n\n{console_ticket_footer('SPICE')}",
                )
            ]
        except Exception as e:
            if is_missing_resource_error(e):
                raise ValueError(lxc_not_found_message(vmid, node))
            self._handle_error(f"create SPICE ticket for LXC {vmid}", e)

    def get_lxc_status(self, node: str, vmid: str) -> List[Content]:
        """Get current runtime status for a single LXC (includes configured net)."""
        try:
            status = self.proxmox.nodes(node).lxc(vmid).status.current.get()
            config = self.proxmox.nodes(node).lxc(vmid).config.get()
            networks = parse_lxc_networks(config)
            payload = dict(status) if isinstance(status, dict) else {"status": status}
            payload["configured_ip"] = configured_ipv4_summary(networks)
            payload["networks"] = networks
            return self._format_response(payload)
        except Exception as e:
            if is_missing_resource_error(e):
                raise ValueError(lxc_not_found_message(vmid, node))
            self._handle_error(f"get status for LXC {vmid}", e)

    def get_lxc_network(
        self, node: str, vmid: str, resolve_runtime: bool = True
    ) -> List[Content]:
        """Return configured (and optionally runtime) network info for an LXC.

        Configured addressing comes from netN in CT config. Runtime IPv4 requires
        SSH ``pct exec`` when resolve_runtime=True and ssh is configured.
        """
        try:
            config = self.proxmox.nodes(node).lxc(vmid).config.get()
            status = self.proxmox.nodes(node).lxc(vmid).status.current.get()
            networks = parse_lxc_networks(config)
            payload: dict = {
                "vmid": vmid,
                "node": node,
                "status": status.get("status") if isinstance(status, dict) else status,
                "configured_ip": configured_ipv4_summary(networks),
                "networks": networks,
                "runtime_ips": [],
                "runtime_note": None,
            }

            if resolve_runtime and status.get("status") == "running":
                if self._pct:
                    try:
                        result = self._pct.execute(
                            node,
                            vmid,
                            "hostname -I 2>/dev/null || ip -4 -o addr show scope global "
                            "| awk '{print $4}' | cut -d/ -f1",
                        )
                        ips = [
                            p
                            for p in result.stdout.replace("\n", " ").split()
                            if p and "." in p and ":" not in p
                        ]
                        payload["runtime_ips"] = ips
                        if result.stderr and not ips:
                            payload["runtime_note"] = result.stderr.strip()
                    except PctExecError as e:
                        payload["runtime_note"] = str(e)
                else:
                    payload["runtime_note"] = (
                        "Runtime IP requires opt-in ssh config + pct exec. "
                        "Configured net only (static CIDR or dhcp). "
                        "For DHCP, set a static ip= on create/update or enable SSH."
                    )
            elif resolve_runtime and status.get("status") != "running":
                payload["runtime_note"] = "Container not running; runtime IP unavailable."

            return self._format_response(payload)
        except Exception as e:
            if is_missing_resource_error(e):
                raise ValueError(lxc_not_found_message(vmid, node))
            self._handle_error(f"get network for LXC {vmid}", e)

    def get_lxc_rrd_data(
        self, node: str, vmid: str, timeframe: str = "hour"
    ) -> List[Content]:
        """Get RRD performance data for an LXC (timeframe: hour|day|week|month|year)."""
        try:
            data = self.proxmox.nodes(node).lxc(vmid).rrddata.get(timeframe=timeframe)
            return self._format_response(data)
        except Exception as e:
            if is_missing_resource_error(e):
                raise ValueError(lxc_not_found_message(vmid, node))
            self._handle_error(f"get RRD data for LXC {vmid}", e)
