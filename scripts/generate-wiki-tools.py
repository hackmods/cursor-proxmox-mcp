#!/usr/bin/env python3
"""Regenerate the tool catalog section in docs/wiki/Tools.md from inventory.

Run from repo root (package installed or PYTHONPATH=src):

    python scripts/generate-wiki-tools.py

After adding/renaming MCP tools, update DOMAIN_GROUPS if needed, re-run this
script, then sync the GitHub wiki with scripts/sync-wiki.ps1 / sync-wiki.sh.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from proxmox_mcp.tools.inventory import ALL_TOOL_NAMES, all_tool_specs  # noqa: E402

TOOLS_MD = ROOT / "docs" / "wiki" / "Tools.md"
BEGIN = "<!-- BEGIN GENERATED TOOLS -->"
END = "<!-- END GENERATED TOOLS -->"

# Ordered domains — every inventory tool must appear in exactly one group.
DOMAIN_GROUPS: list[tuple[str, frozenset[str]]] = [
    (
        "Nodes",
        frozenset(
            {
                "get_nodes",
                "get_node_status",
                "list_node_networks",
                "get_node_subscription",
                "list_node_certificates",
                "get_node_report",
                "list_node_services",
                "get_node_time",
                "wake_node",
            }
        ),
    ),
    (
        "Cluster / tasks",
        frozenset(
            {
                "get_cluster_status",
                "get_next_vmid",
                "get_task_status",
                "list_tasks",
                "wait_for_task",
                "get_version",
                "get_mcp_capabilities",
                "get_cluster_resources",
                "get_cluster_log",
                "get_cluster_options",
            }
        ),
    ),
    (
        "QEMU",
        frozenset(
            {
                "get_vms",
                "create_vm",
                "get_vm_config",
                "update_vm_config",
                "execute_vm_command",
                "get_vm_network",
                "push_to_vm",
                "pull_from_vm",
                "start_vm",
                "stop_vm",
                "shutdown_vm",
                "reset_vm",
                "reboot_vm",
                "suspend_vm",
                "resume_vm",
                "delete_vm",
                "clone_vm",
                "resize_vm_disk",
                "convert_vm_to_template",
                "get_vm_status",
                "get_vm_rrd_data",
                "create_vnc_ticket_vm",
                "create_spice_ticket_vm",
                "create_termproxy_ticket_vm",
            }
        ),
    ),
    (
        "LXC",
        frozenset(
            {
                "get_containers",
                "create_lxc",
                "get_lxc_config",
                "update_lxc_config",
                "start_lxc",
                "stop_lxc",
                "shutdown_lxc",
                "reboot_lxc",
                "suspend_lxc",
                "resume_lxc",
                "delete_lxc",
                "update_lxc_features",
                "clone_lxc",
                "resize_lxc_disk",
                "convert_lxc_to_template",
                "execute_lxc_command",
                "set_lxc_password",
                "set_lxc_ssh_keys",
                "prepare_lxc_for_docker",
                "configure_lxc_dns",
                "pct_set_lxc",
                "push_to_lxc",
                "pull_from_lxc",
                "deploy_static_nginx",
                "get_lxc_status",
                "get_lxc_network",
                "get_lxc_rrd_data",
                "create_vnc_ticket_lxc",
                "create_spice_ticket_lxc",
                "create_termproxy_ticket_lxc",
            }
        ),
    ),
    (
        "Guest (unified)",
        frozenset(
            {
                "start_guest",
                "stop_guest",
                "shutdown_guest",
                "reboot_guest",
                "delete_guest",
                "get_guest_status",
                "get_guest_pending",
                "move_guest_disk",
            }
        ),
    ),
    (
        "Snapshots / backups",
        frozenset(
            {
                "list_snapshots",
                "create_snapshot",
                "delete_snapshot",
                "rollback_snapshot",
                "create_backup",
                "list_backups",
                "restore_backup",
                "delete_backup",
                "list_backup_jobs",
                "create_backup_job",
                "delete_backup_job",
            }
        ),
    ),
    (
        "Storage",
        frozenset(
            {
                "get_storage",
                "get_storage_content",
                "list_os_templates",
                "list_isos",
                "delete_storage_content",
                "download_url_to_storage",
                "create_storage",
                "update_storage",
                "delete_storage",
            }
        ),
    ),
    (
        "Migrate / HA",
        frozenset(
            {
                "migrate_guest",
                "get_ha_status",
                "list_ha_groups",
                "create_ha_group",
                "delete_ha_group",
                "list_ha_resources",
                "create_ha_resource",
                "update_ha_resource",
                "delete_ha_resource",
            }
        ),
    ),
    (
        "Firewall",
        frozenset(
            {
                "get_cluster_firewall_options",
                "set_cluster_firewall_options",
                "list_cluster_firewall_rules",
                "create_cluster_firewall_rule",
                "delete_cluster_firewall_rule",
                "list_guest_firewall_rules",
                "create_guest_firewall_rule",
                "delete_guest_firewall_rule",
                "get_guest_firewall_options",
                "set_guest_firewall_options",
                "list_firewall_aliases",
                "create_firewall_alias",
                "delete_firewall_alias",
                "list_firewall_ipsets",
                "create_firewall_ipset",
                "delete_firewall_ipset",
                "list_firewall_ipset_cidrs",
                "add_firewall_ipset_cidr",
                "delete_firewall_ipset_cidr",
                "list_firewall_macros",
            }
        ),
    ),
    (
        "Access",
        frozenset(
            {
                "list_users",
                "get_user",
                "create_user",
                "delete_user",
                "list_groups",
                "create_group",
                "delete_group",
                "list_roles",
                "list_acl",
                "update_acl",
                "list_tokens",
                "create_token",
                "delete_token",
                "get_permissions",
                "get_token_permissions",
            }
        ),
    ),
    (
        "Replication",
        frozenset(
            {
                "list_replication_jobs",
                "get_replication_status",
                "run_replication_job",
                "create_replication_job",
                "update_replication_job",
                "delete_replication_job",
            }
        ),
    ),
    (
        "SDN",
        frozenset(
            {
                "list_sdn_zones",
                "list_sdn_vnets",
                "list_sdn_controllers",
                "list_sdn_ipams",
                "list_sdn_dns",
                "apply_sdn",
            }
        ),
    ),
    (
        "ACME",
        frozenset(
            {
                "list_acme_plugins",
                "list_acme_accounts",
                "get_acme_directories",
            }
        ),
    ),
    (
        "Pools",
        frozenset(
            {
                "list_pools",
                "get_pool",
                "create_pool",
                "update_pool",
                "delete_pool",
            }
        ),
    ),
]


def _first_line(desc: str) -> str:
    line = desc.strip().split("\n", 1)[0].strip()
    # Escape pipes for markdown tables
    return line.replace("|", "\\|")


def _validate_groups() -> None:
    mapped: set[str] = set()
    for title, names in DOMAIN_GROUPS:
        overlap = mapped & names
        if overlap:
            raise SystemExit(f"Duplicate tools in domain groups ({title}): {sorted(overlap)}")
        mapped |= names
    missing = ALL_TOOL_NAMES - mapped
    extra = mapped - ALL_TOOL_NAMES
    if missing:
        raise SystemExit(f"DOMAIN_GROUPS missing tools: {sorted(missing)}")
    if extra:
        raise SystemExit(f"DOMAIN_GROUPS has unknown tools: {sorted(extra)}")
    if len(mapped) != len(ALL_TOOL_NAMES):
        raise SystemExit("DOMAIN_GROUPS size mismatch vs ALL_TOOL_NAMES")


def render_generated() -> str:
    _validate_groups()
    by_name = {s.name: s.description for s in all_tool_specs()}
    lines: list[str] = [
        BEGIN,
        "",
        f"_Generated from `tools/inventory.py` — **{len(ALL_TOOL_NAMES)}** tools. "
        "Do not edit by hand; run `python scripts/generate-wiki-tools.py`._",
        "",
    ]
    for title, names in DOMAIN_GROUPS:
        lines.append(f"### {title}")
        lines.append("")
        lines.append("| Tool | Description |")
        lines.append("|------|-------------|")
        for name in sorted(names):
            lines.append(f"| `{name}` | {_first_line(by_name[name])} |")
        lines.append("")
    lines.append(END)
    return "\n".join(lines) + "\n"


def main() -> None:
    if not TOOLS_MD.is_file():
        raise SystemExit(f"Missing {TOOLS_MD}")
    text = TOOLS_MD.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        raise SystemExit(f"{TOOLS_MD} must contain {BEGIN} and {END} markers")
    pattern = re.compile(
        re.escape(BEGIN) + r".*?" + re.escape(END),
        re.DOTALL,
    )
    new_block = render_generated().rstrip("\n")
    updated, n = pattern.subn(new_block, text, count=1)
    if n != 1:
        raise SystemExit("Failed to replace generated tools block")
    if not updated.endswith("\n"):
        updated += "\n"
    TOOLS_MD.write_text(updated, encoding="utf-8")
    print(f"Updated {TOOLS_MD} with {len(ALL_TOOL_NAMES)} tools")


if __name__ == "__main__":
    main()
