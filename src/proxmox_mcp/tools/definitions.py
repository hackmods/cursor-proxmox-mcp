"""Tool descriptions for Proxmox MCP tools."""

# Node
GET_NODES_DESC = """List all nodes in the Proxmox cluster with their status, CPU, memory, and role information."""

GET_NODE_STATUS_DESC = """Get detailed status information for a specific Proxmox node.

Parameters:
node* - Name/ID of node to query (e.g. 'pve1')"""

LIST_NODE_NETWORKS_DESC = """List network interfaces/bridges on a node (vmbr0, bonds, etc.).

Parameters:
node* - Host node name"""

# VM
GET_VMS_DESC = """List all virtual machines across the cluster with their status and resource usage."""

CREATE_VM_DESC = """Create a new virtual machine with specified configuration.

Parameters:
node*, vmid*, name*, cpus*, memory* (MB), disk_size* (GB)
storage - optional, auto-detect
ostype - optional, default l26"""

GET_VM_CONFIG_DESC = """Get full QEMU VM configuration.

Parameters: node*, vmid*"""

UPDATE_VM_CONFIG_DESC = """Update QEMU VM config. Pass only fields to change.

Parameters:
node*, vmid*
cores, memory, name, net0, onboot, agent — optional strings/ints"""

EXECUTE_VM_COMMAND_DESC = """Execute commands in a VM via QEMU guest agent.

Parameters: node*, vmid*, command*"""

START_VM_DESC = """Start a virtual machine. Parameters: node*, vmid*"""
STOP_VM_DESC = """Force-stop a virtual machine. Parameters: node*, vmid*"""
SHUTDOWN_VM_DESC = """Gracefully shut down a VM. Parameters: node*, vmid*"""
RESET_VM_DESC = """Hard-reset a VM. Parameters: node*, vmid*"""
REBOOT_VM_DESC = """Graceful ACPI reboot (distinct from reset). Parameters: node*, vmid*"""
SUSPEND_VM_DESC = """Suspend a VM. Parameters: node*, vmid*"""
RESUME_VM_DESC = """Resume a suspended VM. Parameters: node*, vmid*"""
DELETE_VM_DESC = """Permanently delete a VM. Parameters: node*, vmid*, force?=false"""
CLONE_VM_DESC = """Clone a VM to a new ID. Parameters: node*, vmid*, newid*, name?, full?=true, target?, storage?"""
RESIZE_VM_DISK_DESC = """Grow a VM disk. Parameters: node*, vmid*, disk* (e.g. scsi0), size* (e.g. +10G)"""
CONVERT_VM_TEMPLATE_DESC = """Convert VM to template. Parameters: node*, vmid*"""

# LXC
GET_CONTAINERS_DESC = """List all LXC containers across the cluster."""
CREATE_LXC_DESC = """Create an LXC container. Parameters: node*, vmid*, hostname*, ostemplate*, cpus*, memory*, disk_size*, storage?, features?, password?, unprivileged?=true"""
GET_LXC_CONFIG_DESC = """Get full LXC configuration. Parameters: node*, vmid*"""
UPDATE_LXC_CONFIG_DESC = """Update LXC config. Parameters: node*, vmid* plus cores/memory/hostname/net0/features etc."""
START_LXC_DESC = """Start an LXC container. Parameters: node*, vmid*"""
STOP_LXC_DESC = """Force-stop an LXC container. Parameters: node*, vmid*"""
SHUTDOWN_LXC_DESC = """Gracefully shut down an LXC. Parameters: node*, vmid*"""
REBOOT_LXC_DESC = """Reboot an LXC (applies pending config). Parameters: node*, vmid*"""
DELETE_LXC_DESC = """Permanently delete an LXC. Parameters: node*, vmid*, force?=false"""
UPDATE_LXC_FEATURES_DESC = """Update LXC features (nesting/keyctl/fuse). Parameters: node*, vmid*, features*"""
CLONE_LXC_DESC = """Clone an LXC. Parameters: node*, vmid*, newid*, hostname?, full?=true, target?, storage?"""
RESIZE_LXC_DISK_DESC = """Grow an LXC volume. Parameters: node*, vmid*, disk* (e.g. rootfs), size* (e.g. +5G)"""
CONVERT_LXC_TEMPLATE_DESC = """Convert LXC to template. Parameters: node*, vmid*"""
EXECUTE_LXC_COMMAND_DESC = """Execute a command inside a running LXC. Parameters: node*, vmid*, command*"""

# Snapshots
LIST_SNAPSHOTS_DESC = """List snapshots for a guest. Parameters: node*, vmid*, guest_type?=qemu|lxc"""
CREATE_SNAPSHOT_DESC = """Create a snapshot. Parameters: node*, vmid*, snapname*, guest_type?, description?, vmstate?=false"""
DELETE_SNAPSHOT_DESC = """Delete a snapshot. Parameters: node*, vmid*, snapname*, guest_type?"""
ROLLBACK_SNAPSHOT_DESC = """Rollback to a snapshot. Parameters: node*, vmid*, snapname*, guest_type?"""

# Backup
CREATE_BACKUP_DESC = """Create a vzdump backup. Parameters: node*, vmid*, storage?, mode?=snapshot, compress?=zstd, notes?"""
LIST_BACKUPS_DESC = """List backups on storage. Parameters: node*, storage*, vmid?"""
RESTORE_BACKUP_DESC = """Restore a backup archive. Parameters: node*, archive*, vmid*, storage?, force?=false, guest_type?=qemu"""
DELETE_BACKUP_DESC = """Delete a backup volume. Parameters: node*, storage*, volume*"""

# Tasks / cluster
GET_TASK_STATUS_DESC = """Get status for a task UPID. Parameters: node*, upid*"""
LIST_TASKS_DESC = """List recent tasks on a node. Parameters: node*"""
GET_NEXT_VMID_DESC = """Get the next free VM/CT ID from the cluster."""
GET_CLUSTER_STATUS_DESC = """Get overall Proxmox cluster health and quorum status."""

# Storage
GET_STORAGE_DESC = """List storage pools across the cluster with usage."""
GET_STORAGE_CONTENT_DESC = """List storage content (iso/vztmpl/backup/images). Parameters: node*, storage*, content?"""
DELETE_STORAGE_CONTENT_DESC = """Delete a storage volume. Parameters: node*, storage*, volume*"""
DOWNLOAD_URL_TO_STORAGE_DESC = """Download URL into storage. Parameters: node*, storage*, url*, filename?, content?=iso"""
CREATE_STORAGE_DESC = """Create cluster storage definition. Parameters: storage*, type*, content?, path?, server?, export?, vgname?, pool?, monhost?, username?, password?, nodes?, disable?"""
UPDATE_STORAGE_DESC = """Update storage definition. Parameters: storage*, content?, nodes?, disable?"""
DELETE_STORAGE_DESC = """Delete storage definition. Parameters: storage*"""

# Migrate
MIGRATE_GUEST_DESC = """Migrate a VM or LXC to another node. Parameters: node*, vmid*, target*, guest_type?=qemu, online?=true, with_local_disks?=false"""

# HA
GET_HA_STATUS_DESC = """Get current HA manager status."""
LIST_HA_GROUPS_DESC = """List HA groups."""
CREATE_HA_GROUP_DESC = """Create HA group. Parameters: group*, nodes*, comment?"""
DELETE_HA_GROUP_DESC = """Delete HA group. Parameters: group*"""
LIST_HA_RESOURCES_DESC = """List HA resources."""
CREATE_HA_RESOURCE_DESC = """Create HA resource. Parameters: sid* (e.g. vm:100), group?, state?=started, comment?"""
UPDATE_HA_RESOURCE_DESC = """Update HA resource. Parameters: sid*, group?, state?, comment?"""
DELETE_HA_RESOURCE_DESC = """Delete HA resource. Parameters: sid*"""

# Firewall
GET_CLUSTER_FW_OPTIONS_DESC = """Get cluster firewall options."""
SET_CLUSTER_FW_OPTIONS_DESC = """Set cluster firewall options. Parameters: enable?, policy_in?, policy_out?"""
LIST_CLUSTER_FW_RULES_DESC = """List cluster firewall rules."""
CREATE_CLUSTER_FW_RULE_DESC = """Create cluster firewall rule. Parameters: action*, type*, enable?, source?, dest?, proto?, dport?, sport?, comment?, pos?"""
DELETE_CLUSTER_FW_RULE_DESC = """Delete cluster firewall rule. Parameters: pos*"""
LIST_GUEST_FW_RULES_DESC = """List guest firewall rules. Parameters: node*, vmid*, guest_type?"""
CREATE_GUEST_FW_RULE_DESC = """Create guest firewall rule. Parameters: node*, vmid*, action*, type*, guest_type?, enable?, source?, dest?, proto?, dport?, comment?"""
DELETE_GUEST_FW_RULE_DESC = """Delete guest firewall rule. Parameters: node*, vmid*, pos*, guest_type?"""
GET_GUEST_FW_OPTIONS_DESC = """Get guest firewall options. Parameters: node*, vmid*, guest_type?"""
SET_GUEST_FW_OPTIONS_DESC = """Set guest firewall options. Parameters: node*, vmid*, guest_type?, enable?, dhcp?, ipfilter?"""

# Access
LIST_USERS_DESC = """List Proxmox users."""
GET_USER_DESC = """Get a user. Parameters: userid*"""
CREATE_USER_DESC = """Create a user. Parameters: userid*, password?, comment?, email?, enable?=true"""
DELETE_USER_DESC = """Delete a user. Parameters: userid*"""
LIST_GROUPS_DESC = """List groups."""
CREATE_GROUP_DESC = """Create a group. Parameters: groupid*, comment?"""
DELETE_GROUP_DESC = """Delete a group. Parameters: groupid*"""
LIST_ROLES_DESC = """List roles."""
LIST_ACL_DESC = """List ACL entries."""
UPDATE_ACL_DESC = """Update ACL. Parameters: path*, roles*, users?, groups?, propagate?=true, delete?=false"""
LIST_TOKENS_DESC = """List API tokens for a user. Parameters: userid*"""
CREATE_TOKEN_DESC = """Create API token (secret shown once). Parameters: userid*, tokenid*, comment?, privsep?=true"""
DELETE_TOKEN_DESC = """Delete API token. Parameters: userid*, tokenid*"""
GET_PERMISSIONS_DESC = """Get effective permissions for the current auth identity."""
