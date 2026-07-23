"""Shared helpers for guest/storage operations."""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

# Lab defaults (public create params for bridge/IP remain Phase D — D11/D18)
DEFAULT_BRIDGE = "vmbr0"
DEFAULT_LXC_FEATURES = "nesting=1"
DEFAULT_NET0 = f"virtio,bridge={DEFAULT_BRIDGE}"
DEFAULT_DOCKER_NAMESERVERS = "8.8.8.8 9.9.9.9"

# Host ``pct set`` keys exposed by ``pct_set_lxc`` (no free-form shell).
PCT_SET_ALLOWED_KEYS = frozenset(
    {"features", "nameserver", "searchdomain", "onboot", "description", "tags"}
)

# Host ``qm set`` keys for ``qm_set_vm`` (no free-form shell).
QM_SET_ALLOWED_KEYS = frozenset({"onboot", "description", "tags"})


# Pinned crun release for Docker-in-LXC Path B (Ubuntu jammy apt crun 0.17 is too old).
CRUN_VERSION = "1.21"
CRUN_BIN_PATH = "/usr/local/bin/crun"
CRUN_DOWNLOAD_URL = (
    f"https://github.com/containers/crun/releases/download/{CRUN_VERSION}/"
    f"crun-{CRUN_VERSION}-linux-amd64"
)

# Appended when *_vm tools miss a guest that may be an LXC
QEMU_NOT_FOUND_HINT = (
    "💡 Next: if this ID is an LXC, use get_containers / start_lxc / "
    "start_guest(guest_type=lxc) — get_vms is QEMU-only."
)

# Appended when *_lxc tools miss a guest that may be a QEMU VM
LXC_NOT_FOUND_HINT = (
    "💡 Next: if this ID is a QEMU VM, use get_vms / start_vm / "
    "start_guest(guest_type=qemu) — get_containers is LXC-only."
)

# Appended when guest_type-routed tools miss a guest
GUEST_NOT_FOUND_HINT = (
    "💡 Next: confirm guest_type (qemu|lxc) and node; "
    "use get_cluster_resources(type=vm) if unsure."
)

WAIT_FOR_TASK_HINT = (
    "💡 Next: wait_for_task(node, upid) until stopped — "
    "this call returned a task UPID, not a finished result."
)

PRIVSEP_EMPTY_HINT = (
    "💡 If this looks wrong: with Privilege Separation=Yes, empty lists often mean "
    "missing token ACL — check get_token_permissions / get_permissions."
)


def is_missing_resource_error(error: BaseException) -> bool:
    """True if proxmoxer/API error indicates the resource does not exist."""
    text = str(error).lower()
    return "does not exist" in text or "not found" in text


def qemu_not_found_message(vmid: str, node: str) -> str:
    """Clear error when a QEMU-only tool is used against a missing/wrong guest."""
    return f"VM {vmid} not found on node {node}\n{QEMU_NOT_FOUND_HINT}"


def lxc_not_found_message(vmid: str, node: str) -> str:
    """Clear error when an LXC-only tool is used against a missing/wrong guest."""
    return f"LXC {vmid} not found on node {node}\n{LXC_NOT_FOUND_HINT}"


def guest_not_found_message(vmid: str, node: str, guest_type: str) -> str:
    """Clear error when a guest_type-routed tool misses a guest."""
    label = "VM" if guest_type == "qemu" else "LXC"
    return f"{label} {vmid} not found on node {node} (guest_type={guest_type})\n{GUEST_NOT_FOUND_HINT}"


def upid_response_footer(upid: Any, *, node: Optional[str] = None) -> str:
    """Standard footer for tools that return a Proxmox task UPID (D22)."""
    lines = [f"Task ID: {upid}"]
    if node:
        lines.append(f"Node: {node}")
    lines.append(WAIT_FOR_TASK_HINT)
    return "\n".join(lines)


def destructive_warning(action: str = "deleted") -> str:
    """⚠️ IRREVERSIBLE line for destructive tool responses (D23 / D2)."""
    return f"⚠️ IRREVERSIBLE: resource {action}"


def privsep_empty_hint(resource: str = "results") -> str:
    """Hint when a list tool returns empty (may be ACL/privsep)."""
    return f"No {resource} found.\n{PRIVSEP_EMPTY_HINT}"


def console_ticket_footer(kind: str = "VNC") -> str:
    """Note that console tools only mint tickets (D6) — no MCP websocket proxy."""
    return (
        f"💡 Ticket only — connect externally with a {kind} client "
        "(noVNC / virt-viewer / termproxy). This MCP does not proxy the console "
        "(D6). Use get_console_connection for structured ticket + viewer hints."
    )


def format_console_connection(
    *,
    kind: str,
    node: str,
    vmid: str,
    guest_type: str,
    ticket_payload: Any,
    host: Optional[str] = None,
) -> str:
    """Structured console connection helper text (still no websocket proxy)."""
    import json

    payload = ticket_payload if isinstance(ticket_payload, dict) else {"raw": ticket_payload}
    port = payload.get("port") or payload.get("spiceport")
    ticket = payload.get("ticket") or payload.get("spice")
    lines = [
        f"Console connection ({kind}) for {guest_type} {vmid}@{node}",
        json.dumps(payload, indent=2, default=str),
        "",
        "Viewer hints (external — MCP does not open a websocket):",
    ]
    if kind.upper() == "VNC" and port:
        lines.append(
            f"  • noVNC / VNC client → host={host or '<proxmox-host>'} port={port} "
            f"(ticket in JSON above)"
        )
    elif kind.upper() == "SPICE":
        lines.append("  • virt-viewer / remote-viewer with SPICE ticket from JSON")
    else:
        lines.append("  • termproxy / serial console client with ticket from JSON")
    if ticket:
        lines.append(f"  • ticket present: yes (len={len(str(ticket))})")
    lines.append(console_ticket_footer(kind))
    return "\n".join(lines)


def privilege_required_note(context: str = "this operation") -> str:
    """Note that elevated Proxmox privileges are typically required."""
    return (
        f"💡 Note: {context} often requires elevated privileges "
        "(e.g. Sys.Modify / root@pam). A 403 usually means token ACL, not a missing tool."
    )


def parse_feature_flags(features: str) -> set[str]:
    """Parse ``nesting=1,keyctl=1`` into ``{'nesting', 'keyctl'}``."""
    flags: set[str] = set()
    for part in str(features or "").split(","):
        part = part.strip()
        if not part:
            continue
        key = part.split("=", 1)[0].strip().lower()
        if key:
            flags.add(key)
    return flags


def is_permission_denied_error(error: BaseException) -> bool:
    """True when an exception looks like HTTP 403 / permission denied."""
    lower = str(error).lower()
    return (
        "permission denied" in lower
        or "403" in lower
        or "changing feature flags" in lower
        or "only allowed for root@pam" in lower
    )


def acl_denied_message(
    code: str,
    *,
    operation: str,
    path: Optional[str] = None,
    denied: Optional[List[str]] = None,
    recommended_next: Optional[str] = None,
    mcp_fallback: Optional[str] = None,
    cause: str = "",
    **extra: Any,
) -> str:
    """Structured agent-facing error for privilege / token ACL denials."""
    import json

    payload: Dict[str, Any] = {
        "error": code,
        "operation": operation,
        "recommended_next": recommended_next
        or (
            "Call get_token_permissions(userid, tokenid) and grant ACL on "
            "user@realm!tokenid (SETUP.md Privilege Separation). "
            "A 403 usually means token ACL, not a missing MCP tool."
        ),
    }
    if path is not None:
        payload["path"] = path
    if denied is not None:
        payload["denied"] = denied
    if mcp_fallback is not None:
        payload["mcp_fallback"] = mcp_fallback
    if cause:
        payload["cause"] = sanitize_error_snippet(cause)
    payload.update(extra)
    return f"{code} - permission denied for {operation}.\n" + json.dumps(
        payload, indent=2
    )


def feature_acl_denied_message(
    vmid: str,
    requested: str,
    *,
    cause: str = "",
) -> str:
    """Structured agent-facing error when keyctl/fuse cannot be set (D24 Path B)."""
    flags = parse_feature_flags(requested)
    gated = sorted(flags & {"keyctl", "fuse"})
    allowed = sorted(flags - {"keyctl", "fuse"}) or ["nesting"]
    return acl_denied_message(
        "feature_acl_denied",
        operation=f"set LXC {vmid} features",
        path=f"/nodes/*/lxc/{vmid}",
        denied=gated or sorted(flags),
        recommended_next=(
            "Prefer prepare_lxc_for_docker(docker_mode=auto|crun) for nesting+crun; "
            "or grant elevated ACL / root@pam for keyctl. "
            "Also check get_token_permissions (SETUP.md privsep)."
        ),
        mcp_fallback=(
            "pct_set_lxc(features='nesting=1,keyctl=1') if host SSH is root-capable; "
            "else prepare_lxc_for_docker(docker_mode='auto'|'crun')"
        ),
        cause=cause,
        vmid=str(vmid),
        requested=requested,
        allowed=allowed,
        docker_implication="stock_runc_will_fail",
        recommended_fallback="crun",
        host_fix=f"pct set {vmid} -features nesting=1,keyctl=1",
    )


def sanitize_error_snippet(text: str, limit: int = 400) -> str:
    """Truncate a cause string for structured errors (no secret scrub beyond length)."""
    cleaned = " ".join(str(text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


def normalize_docker_mode(mode: Optional[str]) -> str:
    """Validate ``docker_mode`` for prepare_lxc_for_docker."""
    value = (mode or "auto").strip().lower()
    if value not in ("auto", "keyctl", "crun"):
        raise ValueError(
            f"docker_mode must be auto|keyctl|crun (got {mode!r})"
        )
    return value


def crun_daemon_json(
    *,
    nameservers: Optional[List[str]] = None,
    crun_path: str = CRUN_BIN_PATH,
) -> str:
    """``/etc/docker/daemon.json`` body for Path B (crun default-runtime)."""
    import json

    dns = nameservers or DEFAULT_DOCKER_NAMESERVERS.split()
    return json.dumps(
        {
            "runtimes": {"crun": {"path": crun_path}},
            "default-runtime": "crun",
            "dns": dns,
        },
        indent=2,
    )


def build_crun_install_script(
    *,
    nameservers: Optional[List[str]] = None,
) -> str:
    """Guest shell script: install modern crun + set Docker default-runtime (idempotent)."""
    daemon = crun_daemon_json(nameservers=nameservers)
    # Avoid nested quotes issues in pct exec by using a heredoc.
    return f"""set -e
export DEBIAN_FRONTEND=noninteractive
if command -v docker >/dev/null 2>&1; then
  rt=$(docker info -f '{{{{.DefaultRuntime}}}}' 2>/dev/null || true)
  if [ "$rt" = "crun" ] && [ -x {CRUN_BIN_PATH} ]; then
    echo "crun already default-runtime"
    exit 0
  fi
fi
curl -fsSL -o {CRUN_BIN_PATH} {CRUN_DOWNLOAD_URL}
chmod +x {CRUN_BIN_PATH}
mkdir -p /etc/docker
cat >/etc/docker/daemon.json <<'EOF'
{daemon}
EOF
systemctl restart docker 2>/dev/null || service docker restart 2>/dev/null || true
docker info -f '{{{{.DefaultRuntime}}}}'
"""


def validate_download_url(url: str) -> str:
    """Allow only http/https URLs for download_url_to_storage (SSRF soft guard)."""
    cleaned = (url or "").strip()
    if not cleaned:
        raise ValueError("url is required")
    lower = cleaned.lower()
    if not (lower.startswith("http://") or lower.startswith("https://")):
        raise ValueError(
            "url must start with http:// or https:// "
            "(file:// and other schemes are rejected)"
        )
    return cleaned


def wait_for_upid(
    proxmox: Any,
    node: str,
    upid: Any,
    *,
    timeout: float = 120.0,
    poll_interval: float = 1.0,
) -> dict:
    """Block until a task UPID stops (used by force-delete stop-then-delete).

    Returns the final status dict. Raises TimeoutError or RuntimeError on failure.
    """
    import time

    deadline = time.time() + timeout
    last: Optional[dict] = None
    while time.time() < deadline:
        last = proxmox.nodes(node).tasks(upid).status.get()
        if (last or {}).get("status") == "stopped":
            exitstatus = str((last or {}).get("exitstatus", "unknown"))
            if exitstatus.upper() not in ("OK", "WARNING"):
                raise RuntimeError(
                    f"Task {upid} failed with exitstatus={exitstatus}: {last}"
                )
            return last or {}
        time.sleep(poll_interval)
    raise TimeoutError(
        f"Task {upid} still running after {timeout}s. Last status: {last}"
    )


def check_exec_allowlist(command: str) -> None:
    """Enforce optional PROXMOX_MCP_EXEC_ALLOWLIST regex (shared by VM + LXC exec)."""
    pattern = os.environ.get("PROXMOX_MCP_EXEC_ALLOWLIST", "").strip()
    if not pattern:
        return
    if not re.search(pattern, command):
        raise ValueError(
            f"Command blocked by PROXMOX_MCP_EXEC_ALLOWLIST (pattern={pattern!r})"
        )


def parse_net_kv(net_value: str) -> Dict[str, str]:
    """Parse a Proxmox netN config string into a dict of key=value pairs."""
    result: Dict[str, str] = {}
    if not net_value:
        return result
    for part in str(net_value).split(","):
        part = part.strip()
        if not part:
            continue
        if "=" in part:
            key, val = part.split("=", 1)
            result[key.strip()] = val.strip()
        else:
            # e.g. virtio / e1000 bare model token on QEMU nets
            result.setdefault("model", part)
    return result


def parse_lxc_networks(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract structured network interfaces from an LXC config dict."""
    networks: List[Dict[str, Any]] = []
    if not isinstance(config, dict):
        return networks
    for key, raw in sorted(config.items()):
        if not re.fullmatch(r"net\d+", str(key)):
            continue
        parsed = parse_net_kv(str(raw))
        ip_val = parsed.get("ip") or parsed.get("ip6")
        mode = "unknown"
        if ip_val:
            mode = "dhcp" if str(ip_val).lower() == "dhcp" else "static"
        networks.append(
            {
                "iface": key,
                "name": parsed.get("name"),
                "bridge": parsed.get("bridge"),
                "hwaddr": parsed.get("hwaddr") or parsed.get("mac"),
                "ip": ip_val,
                "gw": parsed.get("gw") or parsed.get("gw6"),
                "mode": mode,
                "raw": raw,
            }
        )
    return networks


def parse_qemu_networks(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract structured network interfaces from a QEMU VM config dict."""
    model_keys = ("virtio", "e1000", "e1000e", "rtl8139", "vmxnet3", "vhost")
    networks: List[Dict[str, Any]] = []
    if not isinstance(config, dict):
        return networks
    for key, raw in sorted(config.items()):
        if not re.fullmatch(r"net\d+", str(key)):
            continue
        parsed = parse_net_kv(str(raw))
        model = parsed.get("model")
        hwaddr = parsed.get("macaddr") or parsed.get("hwaddr")
        for mk in model_keys:
            if mk in parsed:
                model = model or mk
                hwaddr = hwaddr or parsed.get(mk)
                break
        networks.append(
            {
                "iface": key,
                "model": model,
                "bridge": parsed.get("bridge"),
                "hwaddr": hwaddr,
                "firewall": parsed.get("firewall"),
                "tag": parsed.get("tag"),
                "raw": raw,
            }
        )
    return networks


def parse_agent_network_interfaces(agent_result: Any) -> List[Dict[str, Any]]:
    """Normalize QEMU guest-agent network-get-interfaces result to a simple list."""
    interfaces: List[Dict[str, Any]] = []
    data = agent_result
    if isinstance(agent_result, dict):
        data = agent_result.get("result") or agent_result.get("data") or agent_result
    if not isinstance(data, list):
        return interfaces
    for item in data:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("ifname")
        mac = item.get("hardware-address") or item.get("hardware_address")
        addrs: List[str] = []
        for ipinfo in item.get("ip-addresses") or item.get("ip_addresses") or []:
            if not isinstance(ipinfo, dict):
                continue
            addr = ipinfo.get("ip-address") or ipinfo.get("ip_address")
            if addr:
                addrs.append(str(addr))
        interfaces.append(
            {
                "name": name,
                "hwaddr": mac,
                "addresses": addrs,
            }
        )
    return interfaces


def agent_runtime_ipv4_summary(interfaces: List[Dict[str, Any]]) -> List[str]:
    """Collect global-looking IPv4 addresses from agent interface list."""
    ips: List[str] = []
    for iface in interfaces:
        name = str(iface.get("name") or "")
        if name in ("lo", "lo0"):
            continue
        for addr in iface.get("addresses") or []:
            s = str(addr)
            if "." in s and ":" not in s and not s.startswith("127."):
                ips.append(s)
    return ips


def configured_ipv4_summary(networks: List[Dict[str, Any]]) -> Optional[str]:
    """Best-effort configured IPv4 string for list views (static CIDR or 'dhcp')."""
    for net in networks:
        ip = net.get("ip")
        if not ip:
            continue
        # Prefer IPv4-looking values
        if ":" in str(ip) and "." not in str(ip):
            continue
        return str(ip)
    return None


def assert_id_absent(proxmox: Any, node: str, vmid: str, kind: str) -> None:
    """Raise ValueError if a guest already occupies ``vmid``.

    Args:
        kind: ``qemu`` (QEMU only), ``lxc`` (LXC only), or ``any`` (both;
            used by create_lxc to refuse IDs already taken by a VM).
    """
    if kind in ("qemu", "any"):
        try:
            proxmox.nodes(node).qemu(vmid).config.get()
            if kind == "any":
                raise ValueError(
                    f"VM ID {vmid} is already used by a QEMU VM on node {node}"
                )
            raise ValueError(f"VM {vmid} already exists on node {node}")
        except ValueError:
            raise
        except Exception as e:
            if not is_missing_resource_error(e):
                raise

    if kind in ("lxc", "any"):
        try:
            proxmox.nodes(node).lxc(vmid).config.get()
            if kind == "any":
                raise ValueError(
                    f"VM ID {vmid} is already used by an LXC container on node {node}"
                )
            raise ValueError(f"LXC container {vmid} already exists on node {node}")
        except ValueError:
            raise
        except Exception as e:
            if not is_missing_resource_error(e):
                raise


def pick_storage(
    storage_list: List[dict],
    *,
    content: str,
    preferred: Optional[List[str]] = None,
    explicit: Optional[str] = None,
) -> str:
    """Pick a storage id that supports ``content`` (e.g. images, rootdir)."""
    storage_info = {s["storage"]: s for s in storage_list}

    if explicit is not None:
        if explicit not in storage_info:
            raise ValueError(f"Storage '{explicit}' not found")
        if content not in storage_info[explicit].get("content", ""):
            raise ValueError(f"Storage '{explicit}' does not support {content}")
        return explicit

    for name in preferred or []:
        s = storage_info.get(name)
        if s and content in s.get("content", ""):
            return name

    for s in storage_list:
        if content in s.get("content", ""):
            return s["storage"]

    raise ValueError(f"No suitable storage found for {content}")
