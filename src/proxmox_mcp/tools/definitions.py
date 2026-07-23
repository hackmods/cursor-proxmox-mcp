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
GET_VMS_DESC = """List all QEMU virtual machines across the cluster (not LXC — use get_containers, or get_cluster_resources(type=vm) for both). Status and resource usage included."""

CREATE_VM_DESC = """Create a QEMU VM (async UPID — always wait_for_task before start unless wait=true). Guest DNS via cloud-init ipconfig0 / guest resolvers (not LXC nameserver). Parameters: node*, vmid*, name*, cpus*, memory* (MB), disk_size* (GB); storage?, ostype?, bridge?, net0?, iso?, boot?, ciuser?, cipassword?, sshkeys?, ipconfig0?, wait?=false, onboot?, description?, tags?"""

GET_VM_CONFIG_DESC = """Get full QEMU VM configuration.

Parameters: node*, vmid*"""

UPDATE_VM_CONFIG_DESC = """Update QEMU VM config. On 403 returns structured vm_acl_denied (try qm_set_vm). Parameters: node*, vmid*; cores?, memory?, name?, net0?, onboot?, agent?, iso?, boot?, ciuser?, cipassword?, sshkeys?, ipconfig0?, ide2?, description?, tags?"""

EXECUTE_VM_COMMAND_DESC = """Execute commands in a VM via QEMU guest agent.

Parameters: node*, vmid*, command*"""

GET_VM_NETWORK_DESC = """Get VM network: configured netN from config plus optional runtime interfaces via QEMU guest agent (network-get-interfaces). Agent must be running. Parameters: node*, vmid*, resolve_runtime?=true"""

GET_VM_GUEST_INFO_DESC = """QEMU guest-agent introspection (info/os/fs/host/timezone/users). Per-section soft-fail; VM must be running with agent. Parameters: node*, vmid*, sections?=os,fs,host,info (comma list)"""

FSFREEZE_VM_DESC = """Freeze guest filesystems via QEMU guest-agent (fsfreeze-freeze). Always thaw after backup/snapshot. VM must be running. Parameters: node*, vmid*"""

FSTHAW_VM_DESC = """Thaw guest filesystems via QEMU guest-agent (fsfreeze-thaw). Call after fsfreeze_vm. Parameters: node*, vmid*"""

BOOTSTRAP_CLOUDINIT_VM_DESC = """One-shot cloud-init VM from a template: clone→ci config→start→runtime IP (requires qemu-guest-agent). Prefer sshkeys over cipassword. Not a blank-disk create — clone_from* must be a cloud image template. If tool missing → get_mcp_capabilities + reload MCP. Parameters: node*, name*, clone_from*; vmid?, full?=true, ciuser?, cipassword?, sshkeys?, ipconfig0?, storage?, target?, cores?, memory?, timeout?"""

PUSH_TO_VM_DESC = """Push a file into a running VM via QEMU guest agent file-write. Provide local_path or content_base64. Max 32 MiB. Parameters: node*, vmid*, remote_path*; local_path?, content_base64?"""

PULL_FROM_VM_DESC = """Pull a file from a running VM via QEMU guest agent file-read. Writes local_path when set; otherwise returns base64. Parameters: node*, vmid*, remote_path*; local_path?"""

QM_SET_VM_DESC = """Allowlisted host qm set when REST token lacks ACL (requires ssh). Keys: onboot, description, tags. Not free-form shell. Prefer update_vm_config first. Parameters: node*, vmid*; onboot?, description?, tags?"""

START_VM_DESC = """Start a QEMU VM (not LXC — use start_lxc / start_guest). Parameters: node*, vmid*"""
STOP_VM_DESC = """Force-stop a QEMU VM. Parameters: node*, vmid*"""
SHUTDOWN_VM_DESC = """Gracefully shut down a QEMU VM. Parameters: node*, vmid*"""
RESET_VM_DESC = """Hard-reset a QEMU VM. Parameters: node*, vmid*"""
REBOOT_VM_DESC = """Graceful ACPI reboot (distinct from reset). Parameters: node*, vmid*"""
SUSPEND_VM_DESC = """Suspend a VM. Parameters: node*, vmid*"""
RESUME_VM_DESC = """Resume a suspended VM. Parameters: node*, vmid*"""
DELETE_VM_DESC = """IRREVERSIBLE: permanently delete a QEMU VM and its disks (not LXC). Parameters: node*, vmid*, force?=false"""
CLONE_VM_DESC = """Clone a VM to a new ID (async UPID — wait_for_task). Parameters: node*, vmid*, newid*, name?, full?=true, target?, storage?"""

RESIZE_VM_DISK_DESC = """Grow a VM disk. Parameters: node*, vmid*, disk* (e.g. scsi0), size* (e.g. +10G)"""
CONVERT_VM_TEMPLATE_DESC = """Convert VM to template. Parameters: node*, vmid*"""

# LXC
GET_CONTAINERS_DESC = """List all LXC containers across the cluster (includes configured IP from netN when set). Optional probes=true runs cheap pct checks for docker binary and :80 listeners (requires host SSH; slow on large fleets). Parameters: probes?=false. For QEMU use get_vms."""
CREATE_LXC_DESC = """Create an LXC (async UPID — always wait_for_task before start unless wait=true). OS template only — not Docker/app deploy. Prefer ssh_public_keys for guest SSH (many templates block root password SSH; create password ≠ SSH login). Guest password optional when host SSH + pct exec works. For one-shot create→start→IP→SSH bootstrap use provision_lxc. docker_ready=true tries nesting=1,keyctl=1 (retries nesting-only + needs_crun warning on ACL deny) and tips prepare_lxc_for_docker (does not install Docker). Day-2: push_to_lxc (prefer for private sources — not guest git clone), deploy_static_nginx, deploy_node_app. If any named tool is missing from your MCP list → get_mcp_capabilities then reload MCP; do not invent base64/scp/public-repo workarounds. Parameters: node*, vmid*, hostname*; ostemplate?, cpus?, memory?, disk_size?, storage?, features?, password?, ssh_public_keys?, unprivileged?, bridge?, ip?, gw?, net0?, ostemplate_filter?, docker_ready?=false, wait?=false, nameserver?, searchdomain?, onboot?, description?, tags?"""
GET_LXC_CONFIG_DESC = """Get full LXC configuration. Parameters: node*, vmid*"""
UPDATE_LXC_CONFIG_DESC = """Update LXC config (cores/memory/hostname/net0/features/nameserver/searchdomain/onboot/description/tags). Does NOT set password or SSH keys — use set_lxc_password / set_lxc_ssh_keys (need host SSH/pct) or recreate with password/ssh_public_keys."""
START_LXC_DESC = """Start an LXC container. Parameters: node*, vmid*"""
STOP_LXC_DESC = """Force-stop an LXC container. Parameters: node*, vmid*"""
SHUTDOWN_LXC_DESC = """Gracefully shut down an LXC. Parameters: node*, vmid*"""
REBOOT_LXC_DESC = """Reboot an LXC (applies pending config). Parameters: node*, vmid*"""
DELETE_LXC_DESC = """IRREVERSIBLE: permanently delete an LXC and its rootfs. Parameters: node*, vmid*, force?=false"""
UPDATE_LXC_FEATURES_DESC = """Update LXC features (nesting/keyctl/fuse). Does not strip flags. On keyctl/fuse 403 returns structured feature_acl_denied (recommended_fallback=crun). Prefer prepare_lxc_for_docker(docker_mode=auto) or pct_set_lxc when token lacks ACL. After change: get_guest_pending + stop/start. Parameters: node*, vmid*, features*"""
CLONE_LXC_DESC = """Clone an LXC (async UPID — wait_for_task). Parameters: node*, vmid*, newid*, hostname?, full?=true, target?, storage?"""

RESIZE_LXC_DISK_DESC = """Grow an LXC volume. Parameters: node*, vmid*, disk* (e.g. rootfs), size* (e.g. +5G)"""
CONVERT_LXC_TEMPLATE_DESC = """Convert LXC to template. Parameters: node*, vmid*"""
EXECUTE_LXC_COMMAND_DESC = """Execute a command inside a running LXC via host SSH + pct exec (no Proxmox REST /exec — HTTP 501 means stale MCP build). Requires opt-in ssh config. Response includes stdout/stderr and output/error aliases. Stock Debian templates often lack curl — prefer wget -qO- URL or python3 for HTTP checks. Parameters: node*, vmid*, command*; timeout? (seconds, else ssh.timeout / PROXMOX_MCP_EXEC_TIMEOUT)"""
SET_LXC_PASSWORD_DESC = """Set/reset LXC root password via pct exec (no REST after-create password API). Optionally enables root password SSH in sshd. Requires config ssh. Parameters: node*, vmid*, password*, enable_password_ssh?=true"""
SET_LXC_SSH_KEYS_DESC = """Install root authorized_keys via pct exec (prefer ssh_public_keys on create_lxc). Parameters: node*, vmid*, ssh_public_keys*, mode?=replace|append"""
PREPARE_LXC_FOR_DOCKER_DESC = """Idempotent Docker-in-LXC prep (D24): features + AppArmor; docker_mode=auto|keyctl|crun (auto falls back to nesting+crun when keyctl ACL denied); optional install_docker/smoke_test. Requires ssh. Success = docker run (hello-world) — not docker --version. Do not claim ready with nesting-only + stock runc. Parameters: node*, vmid*; fuse?=false, allow_apparmor_workaround?=true, install_docker?=false, smoke_test?=false, timeout?, docker_mode?=auto"""
CONFIGURE_LXC_DNS_DESC = """Set CT nameserver/searchdomain via REST (falls back to pct set). Optionally prefer IPv4 in guest gai.conf when running. Prefer CT nameserver over editing resolv.conf (PVE rewrites on start). Parameters: node*, vmid*; nameserver?=8.8.8.8 9.9.9.9, searchdomain?, prefer_ipv4?=true"""
PCT_SET_LXC_DESC = """Allowlisted host pct set for when REST token lacks ACL (requires ssh). Keys: features, nameserver, searchdomain, onboot, description, tags. Not free-form shell. Parameters: node*, vmid*; features?, nameserver?, searchdomain?, onboot?, description?, tags?"""
CONFIGURE_LXC_SSH_DESC = """Ensure openssh-server enabled; optionally install ssh_public_keys and/or set password; return sshd_listening. Requires ssh. Parameters: node*, vmid*; ssh_public_keys?, password?, enable_password_ssh?=true, install_openssh?=true"""
GET_DOCKER_LXC_STATUS_DESC = """Read-only Docker-in-LXC probe: features, DefaultRuntime, docker/compose versions, disk, IP. Does not install or smoke-test. Requires ssh for runtime fields. Parameters: node*, vmid*"""
BOOTSTRAP_DOCKER_LXC_DESC = """Orchestrate Docker LXC: create(docker_ready)+wait → start → DNS → SSH → prepare_lxc_for_docker(docker_mode=auto, install+smoke) → restart if needed → status. Prefer when user asks for Docker LXC. For a plain small CT use provision_lxc. Requires ssh. Parameters: node*, hostname*; vmid?, cpus?, memory?, disk_size?, storage?, bridge?, ip?, gw?, nameservers?=8.8.8.8 9.9.9.9, ostemplate_filter?=ubuntu, ssh_public_keys?, password?, docker_mode?=auto, timeout?"""
PROVISION_LXC_DESC = """One-shot small LXC: create(wait)+start(wait) → optional configure_lxc_ssh → resolve runtime IP → return {vmid,hostname,ip,ssh_hint}. OS template only (not Docker — use bootstrap_docker_lxc). Requires host SSH. Prefer ssh_public_keys; password at create still needs enable_password_ssh (default true when password set). Never echoes password. Parameters: node*, hostname*; vmid?, cpus?=1, memory?=2048, disk_size?=8, storage?, bridge?, ip?, gw?, ostemplate?, ostemplate_filter?, nameserver?, password?, ssh_public_keys?, enable_password_ssh?=true, onboot?, description?, tags?, timeout?"""
PUSH_TO_LXC_DESC = """Push a file into a running LXC via host SSH + pct push (SFTP to host temp then pct push). Prefer local_path (Cursor-side) over content_base64 — avoid base64 chunk workarounds. Preferred path for private app sources (not guest HTTPS git clone without creds). Max 32 MiB. Requires ssh. Parameters: node*, vmid*, remote_path*; local_path?, content_base64?, timeout?"""
PULL_FROM_LXC_DESC = """Pull a file from a running LXC via pct pull. Writes local_path when set; otherwise returns base64. Requires ssh. Parameters: node*, vmid*, remote_path*; local_path?, timeout?"""
DEPLOY_STATIC_NGINX_DESC = """Install nginx in a running LXC and deploy static content to /var/www/html (Lumon-style fallback). Requires host SSH/pct. Prefer local_path tarball over content_base64. Optional content_base64 or local_path tarball/html. Health: wget -qO- (curl often missing on Debian). Parameters: node*, vmid*; local_path?, content_base64?, remote_extract_dir?=/var/www/html, timeout?"""
DEPLOY_NODE_APP_DESC = """Install Node.js LTS in a running LXC, deploy an app tarball, build, and run under systemd (Next.js / Node portfolio path). Requires host SSH/pct. Prefer local_path tarball (private sources — not guest git clone). Default: Node 22, npm ci && npm run build, systemd on port 3000. Health: wget -qO-. Parameters: node*, vmid*; local_path?, content_base64?, remote_dir?=/opt/app, node_major?=22, build_command?, start_command?, port?=3000, service_name?=node-app, timeout?"""
SUSPEND_LXC_DESC = """WARNING: LXC suspend uses CRIU checkpoint and is often unreliable/unsupported. Prefer shutdown. Parameters: node*, vmid*"""
RESUME_LXC_DESC = """WARNING: resume after LXC suspend (CRIU) is best-effort. Parameters: node*, vmid*"""
GET_LXC_RRD_DATA_DESC = """Get RRD metrics for an LXC. Parameters: node*, vmid*, timeframe?=hour"""
CREATE_SPICE_TICKET_LXC_DESC = """Mint SPICE ticket for an LXC (connect externally). Parameters: node*, vmid*"""
GET_LXC_NETWORK_DESC = """Get LXC network: configured netN (static/dhcp/MAC/bridge) plus optional runtime IPv4 via pct exec when SSH is configured. Parameters: node*, vmid*, resolve_runtime?=true"""
GET_LXC_STATUS_DESC = """Get current runtime status for one LXC (includes configured_ip/networks from config). Parameters: node*, vmid*"""
# Unified guest power (additive; keeps *_vm / *_lxc)
START_GUEST_DESC = """Start a VM or LXC. Parameters: node*, vmid*, guest_type?=qemu|lxc"""
STOP_GUEST_DESC = """Force-stop a VM or LXC. Parameters: node*, vmid*, guest_type?=qemu|lxc"""
SHUTDOWN_GUEST_DESC = """Gracefully shut down a VM or LXC. Parameters: node*, vmid*, guest_type?=qemu|lxc"""
REBOOT_GUEST_DESC = """Reboot a VM or LXC. Parameters: node*, vmid*, guest_type?=qemu|lxc"""
DELETE_GUEST_DESC = """IRREVERSIBLE: permanently delete a VM or LXC. Parameters: node*, vmid*, guest_type?=qemu|lxc, force?=false"""
GET_GUEST_STATUS_DESC = """Get runtime status for a VM or LXC. Parameters: node*, vmid*, guest_type?=qemu|lxc"""
GET_GUEST_PENDING_DESC = """Get pending (not-yet-applied) config for a VM or LXC. Parameters: node*, vmid*, guest_type?=qemu|lxc"""
MOVE_GUEST_DISK_DESC = """Move a guest disk/volume to another storage. Parameters: node*, vmid*, disk*, storage*, guest_type?=qemu|lxc, delete?=true"""

# Snapshots
LIST_SNAPSHOTS_DESC = """List snapshots for a guest. Parameters: node*, vmid*, guest_type?=qemu|lxc"""
CREATE_SNAPSHOT_DESC = """Create a snapshot. Parameters: node*, vmid*, snapname*, guest_type?, description?, vmstate?=false"""
DELETE_SNAPSHOT_DESC = """IRREVERSIBLE: delete a snapshot. Parameters: node*, vmid*, snapname*, guest_type?"""
ROLLBACK_SNAPSHOT_DESC = """WARNING: rollback discards state after the snapshot. Parameters: node*, vmid*, snapname*, guest_type?"""

# Backup
CREATE_BACKUP_DESC = """Create a vzdump backup (async UPID — wait_for_task). Parameters: node*, vmid*, storage?, mode?=snapshot, compress?=zstd, notes?"""

LIST_BACKUPS_DESC = """List backups on storage. Parameters: node*, storage*, vmid?"""
RESTORE_BACKUP_DESC = """WARNING: restore may overwrite guest disks when force is set (async UPID — wait_for_task). Parameters: node*, archive*, vmid*, storage?, force?=false, guest_type?=qemu"""

DELETE_BACKUP_DESC = """IRREVERSIBLE: delete a backup volume. Parameters: node*, storage*, volume*"""
LIST_BACKUP_JOBS_DESC = """List scheduled cluster backup jobs (/cluster/backup)."""
CREATE_BACKUP_JOB_DESC = """Create a scheduled backup job. Parameters: schedule*, storage*; vmid? (comma-separated), mode?=snapshot, compress?=zstd, enabled?=true, comment?, mailto?, mailnotification?, all?=false"""
DELETE_BACKUP_JOB_DESC = """IRREVERSIBLE: delete a scheduled backup job. Parameters: id*"""

# Tasks / cluster
GET_TASK_STATUS_DESC = """Get status for a task UPID. Parameters: node*, upid*"""
LIST_TASKS_DESC = """List recent tasks on a node. Parameters: node*"""
WAIT_FOR_TASK_DESC = """Poll a task UPID until it stops (or timeout). Required after create_vm/create_lxc before start — create returns UPID immediately; failures (missing template, etc.) appear here. Parameters: node*, upid*, timeout?=300, poll_interval?=2.0"""
GET_NEXT_VMID_DESC = """Get the next free VM/CT ID from the cluster (best-effort — race possible before create)."""

GET_CLUSTER_STATUS_DESC = """Get overall Proxmox cluster health and quorum status."""

# Storage
GET_STORAGE_DESC = """List storage pools across the cluster with usage."""
GET_STORAGE_CONTENT_DESC = """List storage content (iso/vztmpl/backup/images). Parameters: node*, storage*, content?"""
LIST_OS_TEMPLATES_DESC = """List LXC OS templates (vztmpl) across storages. Parameters: node*, storage?, filter? (e.g. ubuntu)"""
LIST_ISOS_DESC = """List ISO images. Parameters: node*, storage?, filter?"""
DELETE_STORAGE_CONTENT_DESC = """IRREVERSIBLE: delete a storage volume. Parameters: node*, storage*, volume*"""
DOWNLOAD_URL_TO_STORAGE_DESC = """Download URL into storage (async UPID — wait_for_task). http/https only; host fetches URL. Parameters: node*, storage*, url*, filename?, content?=iso, verify_certificate?=true, checksum?, checksum_algorithm?"""

CREATE_STORAGE_DESC = """Create cluster storage definition. Parameters: storage*, type*, content?, path?, server?, export?, vgname?, pool?, monhost?, username?, password?, nodes?, disable?"""
UPDATE_STORAGE_DESC = """Update storage definition. Parameters: storage*, content?, nodes?, disable?"""
DELETE_STORAGE_DESC = """IRREVERSIBLE: delete storage definition (not underlying data by default). Parameters: storage*"""

# Migrate
MIGRATE_GUEST_DESC = """Migrate a VM or LXC to another node (async UPID — wait_for_task). Parameters: node*, vmid*, target*, guest_type?=qemu, online?=true, with_local_disks?=false"""


# HA
GET_HA_STATUS_DESC = """Get current HA manager status."""
LIST_HA_GROUPS_DESC = """List HA groups."""
CREATE_HA_GROUP_DESC = """Create HA group (often needs elevated privileges). Parameters: group*, nodes*, comment?"""

DELETE_HA_GROUP_DESC = """IRREVERSIBLE: delete HA group. Parameters: group*"""
LIST_HA_RESOURCES_DESC = """List HA resources."""
CREATE_HA_RESOURCE_DESC = """Create HA resource (often needs elevated privileges). Parameters: sid* (e.g. vm:100), group?, state?=started, comment?"""

UPDATE_HA_RESOURCE_DESC = """Update HA resource. Parameters: sid*, group?, state?, comment?"""
DELETE_HA_RESOURCE_DESC = """IRREVERSIBLE: delete HA resource. Parameters: sid*"""

# Firewall
GET_CLUSTER_FW_OPTIONS_DESC = """Get cluster firewall options."""
SET_CLUSTER_FW_OPTIONS_DESC = """WARNING: changes cluster-wide firewall policy. Parameters: enable?, policy_in?, policy_out?"""
LIST_CLUSTER_FW_RULES_DESC = """List cluster firewall rules."""
CREATE_CLUSTER_FW_RULE_DESC = """Create cluster firewall rule. Parameters: action*, type*, enable?, source?, dest?, proto?, dport?, sport?, comment?, pos?"""
DELETE_CLUSTER_FW_RULE_DESC = """IRREVERSIBLE: delete cluster firewall rule. Parameters: pos*"""
LIST_GUEST_FW_RULES_DESC = """List guest firewall rules. Parameters: node*, vmid*, guest_type?"""
CREATE_GUEST_FW_RULE_DESC = """Create guest firewall rule. Parameters: node*, vmid*, action*, type*, guest_type?, enable?, source?, dest?, proto?, dport?, comment?"""
DELETE_GUEST_FW_RULE_DESC = """IRREVERSIBLE: delete guest firewall rule. Parameters: node*, vmid*, pos*, guest_type?"""
GET_GUEST_FW_OPTIONS_DESC = """Get guest firewall options. Parameters: node*, vmid*, guest_type?"""
SET_GUEST_FW_OPTIONS_DESC = """Set guest firewall options. Parameters: node*, vmid*, guest_type?, enable?, dhcp?, ipfilter?"""

# Access
LIST_USERS_DESC = """List Proxmox users."""
GET_USER_DESC = """Get a user. Parameters: userid*"""
CREATE_USER_DESC = """Create a user. Parameters: userid*, password?, comment?, email?, enable?=true"""
DELETE_USER_DESC = """IRREVERSIBLE: delete a user. Parameters: userid*"""
LIST_GROUPS_DESC = """List groups."""
CREATE_GROUP_DESC = """Create a group. Parameters: groupid*, comment?"""
DELETE_GROUP_DESC = """IRREVERSIBLE: delete a group. Parameters: groupid*"""
LIST_ROLES_DESC = """List roles."""
LIST_ACL_DESC = """List ACL entries."""
UPDATE_ACL_DESC = """WARNING: modifies access control; delete=true removes ACL entries. Parameters: path*, roles*, users?, groups?, propagate?=true, delete?=false"""
LIST_TOKENS_DESC = """List API tokens for a user. Parameters: userid*"""
CREATE_TOKEN_DESC = """Create API token (secret shown once — store immediately). Parameters: userid*, tokenid*, comment?, privsep?=true. privsep=true (default): token needs its own ACL (user@realm!tokenid); effective perms = user ∩ token. privsep=false: token inherits all user permissions (lab shortcut; larger blast radius)."""
DELETE_TOKEN_DESC = """IRREVERSIBLE: delete API token. Parameters: userid*, tokenid*"""
GET_PERMISSIONS_DESC = """Get effective permissions for the current auth identity (useful to verify token ACLs / Privilege Separation)."""
GET_TOKEN_PERMISSIONS_DESC = """Get effective permissions for an API token (privsep). Parameters: userid* (user@realm), tokenid*. Empty result often means Privilege Separation with no ACL on user@realm!tokenid."""

# Replication
LIST_REPLICATION_JOBS_DESC = """List cluster storage replication jobs."""
GET_REPLICATION_STATUS_DESC = """Get replication job status. Parameters: node*, jobid*"""
RUN_REPLICATION_JOB_DESC = """Schedule a replication job to run now. Parameters: node*, jobid*"""
CREATE_REPLICATION_JOB_DESC = """Create replication job. Parameters: id* (e.g. 100-0), target*, schedule?, comment?, enabled?=true"""
UPDATE_REPLICATION_JOB_DESC = """Update replication job. Parameters: id*; schedule?, comment?, enabled?"""
DELETE_REPLICATION_JOB_DESC = """IRREVERSIBLE: delete replication job. Parameters: id*"""

# ACME
LIST_ACME_PLUGINS_DESC = """List ACME challenge plugins."""
LIST_ACME_ACCOUNTS_DESC = """List ACME accounts."""
GET_ACME_DIRECTORIES_DESC = """List known ACME directories (Let's Encrypt etc.)."""

# SDN
LIST_SDN_ZONES_DESC = """List SDN zones."""
LIST_SDN_VNETS_DESC = """List SDN virtual networks."""
LIST_SDN_CONTROLLERS_DESC = """List SDN controllers."""
LIST_SDN_IPAMS_DESC = """List SDN IPAMs."""
LIST_SDN_DNS_DESC = """List SDN DNS entries."""
APPLY_SDN_DESC = """Apply pending SDN configuration cluster-wide (often needs Sys.Modify / elevated privileges)."""


# Pools
LIST_POOLS_DESC = """List resource pools."""
GET_POOL_DESC = """Get a resource pool and its members. Parameters: poolid*"""
CREATE_POOL_DESC = """Create a resource pool. Parameters: poolid*, comment?"""
UPDATE_POOL_DESC = """Update pool membership. Parameters: poolid*; comment?, vms? (comma IDs), storage? (comma names), delete?=false (true=remove members)"""
DELETE_POOL_DESC = """IRREVERSIBLE: delete a resource pool. Parameters: poolid*"""

# Node extras
GET_NODE_SUBSCRIPTION_DESC = """Get node subscription status (read-only). Parameters: node*"""
LIST_NODE_CERTIFICATES_DESC = """List SSL certificates on a node. Parameters: node*"""
GET_NODE_REPORT_DESC = """Get diagnostic report for a node. Parameters: node*"""
LIST_NODE_SERVICES_DESC = """List Proxmox-managed services on a node. Parameters: node*"""
GET_NODE_TIME_DESC = """Get node timezone and time. Parameters: node*"""
WAKE_NODE_DESC = """Send Wake-on-LAN to a node. Parameters: node*"""
REBOOT_NODE_DESC = """IRREVERSIBLE: reboot a Proxmox host (Sys.PowerMgmt). Guests go down; MCP may disconnect if this is the API host. confirm* must equal the exact node name. Parameters: node*, confirm*"""
SHUTDOWN_NODE_DESC = """IRREVERSIBLE: shut down / power off a Proxmox host (Sys.PowerMgmt). Guests go down; MCP may disconnect if this is the API host. confirm* must equal the exact node name. Parameters: node*, confirm*"""

# Console tickets (mint only — no websocket proxy)
CREATE_VNC_TICKET_VM_DESC = """Mint VNC ticket for a VM (connect externally). Parameters: node*, vmid*, websocket?=true"""
CREATE_SPICE_TICKET_VM_DESC = """Mint SPICE ticket for a VM. Parameters: node*, vmid*"""
CREATE_TERMPROXY_TICKET_VM_DESC = """Mint termproxy ticket for a VM. Parameters: node*, vmid*"""
CREATE_VNC_TICKET_LXC_DESC = """Mint VNC ticket for an LXC. Parameters: node*, vmid*, websocket?=true"""
CREATE_TERMPROXY_TICKET_LXC_DESC = """Mint termproxy ticket for an LXC. Parameters: node*, vmid*"""
GET_VM_STATUS_DESC = """Get current runtime status for one VM. Parameters: node*, vmid*"""
GET_VM_RRD_DATA_DESC = """Get RRD metrics for a VM. Parameters: node*, vmid*, timeframe?=hour"""

# Cluster extras
GET_VERSION_DESC = """Get Proxmox VE version/API info."""
GET_MCP_CAPABILITIES_DESC = """Self-check: MCP package version, ssh.enabled, paramiko, day-2 tool presence, logging (level/verbose/tool_calls/file), optional pct version probe. Call after reload/config change. Parameters: probe_node?"""
GET_CLUSTER_RESOURCES_DESC = """List cluster resources. Parameters: type? (vm|storage|node|sdn)"""
GET_CLUSTER_LOG_DESC = """Get recent cluster log. Parameters: max_entries?=50"""
GET_CLUSTER_OPTIONS_DESC = """Get cluster-wide options."""
GET_CLUSTER_JOIN_INFO_DESC = """Read cluster join info (fingerprints/nodelist) from an existing cluster member — copy fingerprint for join_cluster. Parameters: node?"""
JOIN_CLUSTER_DESC = """IRREVERSIBLE: join THIS API host into an existing cluster (POST /cluster/config/join). Point MCP at the standalone node being joined, not an existing member. confirm* must be the literal JOIN. Never echo password. Parameters: hostname* (peer), fingerprint*, password*, confirm*; nodeid?, votes?, force?=false"""

# Firewall extras
LIST_FIREWALL_ALIASES_DESC = """List cluster firewall aliases."""
CREATE_FIREWALL_ALIAS_DESC = """Create firewall alias. Parameters: name*, cidr*, comment?"""
DELETE_FIREWALL_ALIAS_DESC = """IRREVERSIBLE: delete firewall alias. Parameters: name*"""
LIST_FIREWALL_IPSETS_DESC = """List cluster firewall IP sets."""
CREATE_FIREWALL_IPSET_DESC = """Create firewall IP set. Parameters: name*, comment?"""
DELETE_FIREWALL_IPSET_DESC = """IRREVERSIBLE: delete firewall IP set. Parameters: name*"""
LIST_FIREWALL_IPSET_CIDRS_DESC = """List CIDR members of a firewall IP set. Parameters: name*"""
ADD_FIREWALL_IPSET_CIDR_DESC = """Add a CIDR/IP to a firewall IP set. Parameters: name*, cidr*, comment?, nomatch?=false"""
DELETE_FIREWALL_IPSET_CIDR_DESC = """IRREVERSIBLE: remove a CIDR from a firewall IP set. Parameters: name*, cidr*"""
LIST_FIREWALL_MACROS_DESC = """List available firewall macros."""

