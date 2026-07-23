# Tools reference

Complete inventory of MCP tools registered by **cursor-proxmox-mcp** (`tools/inventory.py` / `tools/register.py`). CI fails if this page drifts from the golden set.

**Count:** see generated section below (CI-locked inventory).

## Naming and agent tips

- **QEMU vs LXC:** `get_vms` is QEMU-only; use `get_containers` for LXC, or `get_cluster_resources(type=vm)` for both.
- **Unified guests:** Prefer `*_guest` + `guest_type=qemu|lxc` when the agent does not know the type. Parallel `*_vm` / `*_lxc` names remain for existing prompts.
- **Async UPIDs:** `create_*`, clone, migrate, backup, download, and many power/delete ops return a Proxmox task UPID immediately. Always call `wait_for_task` before assuming success — create ≠ ready.
- **LXC exec / runtime IP:** `execute_lxc_command` and runtime addresses on `get_lxc_network` need opt-in **host** SSH + `pct` (see [Setup](Setup)). Guest `ssh_public_keys` is separate.
- **Console tickets:** VNC/SPICE/termproxy tools mint tickets only — an external viewer is required.
- **Destructive tools:** Descriptions mark IRREVERSIBLE/WARNING; responses echo the same.

Coverage matrix (API roadmap): [`docs/api-coverage.md`](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/docs/api-coverage.md) · [`.cursor/research/proxmox-api-coverage.md`](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/.cursor/research/proxmox-api-coverage.md).

Playbooks: [Recipes](Recipes).

## Full inventory

Regenerate after tool changes:

```bash
python scripts/generate-wiki-tools.py
```

<!-- BEGIN GENERATED TOOLS -->

_Generated from `tools/inventory.py` — **207** tools. Do not edit by hand; run `python scripts/generate-wiki-tools.py`._

### Nodes

| Tool | Description |
|------|-------------|
| `create_node_network` | Create a node network iface (staged until reload). Parameters: node*, iface*, type* (bridge\|bond\|eth\|vlan\|…); bridge_ports?, bridge_stp?, bridge_fd?, address?, netmask?, gateway?, cidr?, autostart?=true, comments?, mtu?, slaves?, bond_mode?, vlan_id?, vlan_raw_device? |
| `delete_node_network` | IRREVERSIBLE: delete a node network iface definition (staged until reload). Parameters: node*, iface* |
| `get_node_report` | Get diagnostic report for a node. Parameters: node* |
| `get_node_status` | Get detailed status information for a specific Proxmox node. |
| `get_node_subscription` | Get node subscription status (read-only). Parameters: node* |
| `get_node_time` | Get node timezone and time. Parameters: node* |
| `get_nodes` | List all nodes in the Proxmox cluster with their status, CPU, memory, and role information. |
| `list_node_certificates` | List SSL certificates on a node. Parameters: node* |
| `list_node_networks` | List network interfaces/bridges on a node (vmbr0, bonds, etc.). Parameters: node* |
| `list_node_services` | List Proxmox-managed services on a node. Parameters: node* |
| `reboot_node` | IRREVERSIBLE: reboot a Proxmox host (Sys.PowerMgmt). Guests go down; MCP may disconnect if this is the API host. confirm* must equal the exact node name. Parameters: node*, confirm* |
| `reload_node_network` | WARNING: apply pending network config on a node (ifupdown2 reload). Bad config can disconnect the host. Parameters: node* |
| `shutdown_node` | IRREVERSIBLE: shut down / power off a Proxmox host (Sys.PowerMgmt). Guests go down; MCP may disconnect if this is the API host. confirm* must equal the exact node name. Parameters: node*, confirm* |
| `update_node_network` | Update a node network iface (staged until reload). Parameters: node*, iface*; bridge_ports?, address?, netmask?, gateway?, cidr?, autostart?, comments?, mtu?, slaves?, bond_mode?, delete? (comma props to clear) |
| `wake_node` | Send Wake-on-LAN to a node. Parameters: node* |

### Cluster / tasks

| Tool | Description |
|------|-------------|
| `get_cluster_join_info` | Read cluster join info (fingerprints/nodelist) from an existing cluster member — copy fingerprint for join_cluster. Parameters: node? |
| `get_cluster_log` | Get recent cluster log. Parameters: max_entries?=50 |
| `get_cluster_options` | Get cluster-wide options. |
| `get_cluster_resources` | List cluster resources. Parameters: type? (vm\|storage\|node\|sdn) |
| `get_cluster_status` | Get overall Proxmox cluster health and quorum status. |
| `get_mcp_capabilities` | Self-check: MCP package version, ssh.enabled, paramiko, day-2 tool presence, logging (level/verbose/tool_calls/file), optional pct version probe. Call after reload/config change. Parameters: probe_node? |
| `get_next_vmid` | Get the next free VM/CT ID from the cluster (best-effort — race possible before create). |
| `get_task_status` | Get status for a task UPID. Parameters: node*, upid* |
| `get_version` | Get Proxmox VE version/API info. |
| `join_cluster` | IRREVERSIBLE: join THIS API host into an existing cluster (POST /cluster/config/join). Point MCP at the standalone node being joined, not an existing member. confirm* must be the literal JOIN. Never echo password. Parameters: hostname* (peer), fingerprint*, password*, confirm*; nodeid?, votes?, force?=false |
| `list_tasks` | List recent tasks on a node. Parameters: node* |
| `wait_for_task` | Poll a task UPID until it stops (or timeout). Required after create_vm/create_lxc before start — create returns UPID immediately; failures (missing template, etc.) appear here. Parameters: node*, upid*, timeout?=300, poll_interval?=2.0 |

### QEMU

| Tool | Description |
|------|-------------|
| `bootstrap_cloudinit_vm` | One-shot cloud-init VM from a template: clone→ci config→start→runtime IP (requires qemu-guest-agent). Prefer sshkeys over cipassword. Not a blank-disk create — clone_from* must be a cloud image template. If tool missing → get_mcp_capabilities + reload MCP. Parameters: node*, name*, clone_from*; vmid?, full?=true, ciuser?, cipassword?, sshkeys?, ipconfig0?, storage?, target?, cores?, memory?, timeout? |
| `clone_vm` | Clone a VM to a new ID (async UPID — wait_for_task). Parameters: node*, vmid*, newid*, name?, full?=true, target?, storage? |
| `convert_vm_to_template` | Convert VM to template. Parameters: node*, vmid* |
| `create_spice_ticket_vm` | Mint SPICE ticket for a VM. Parameters: node*, vmid* |
| `create_termproxy_ticket_vm` | Mint termproxy ticket for a VM. Parameters: node*, vmid* |
| `create_vm` | Create a QEMU VM (async UPID — always wait_for_task before start unless wait=true). Guest DNS via cloud-init ipconfig0 / guest resolvers (not LXC nameserver). Parameters: node*, vmid*, name*, cpus*, memory* (MB), disk_size* (GB); storage?, ostype?, bridge?, net0?, iso?, boot?, ciuser?, cipassword?, sshkeys?, ipconfig0?, wait?=false, onboot?, description?, tags? |
| `create_vnc_ticket_vm` | Mint VNC ticket for a VM (connect externally). Parameters: node*, vmid*, websocket?=true |
| `delete_vm` | IRREVERSIBLE: permanently delete a QEMU VM and its disks (not LXC). Parameters: node*, vmid*, force?=false |
| `execute_vm_command` | Execute commands in a VM via QEMU guest agent. |
| `fsfreeze_vm` | Freeze guest filesystems via QEMU guest-agent (fsfreeze-freeze). Always thaw after backup/snapshot. VM must be running. Parameters: node*, vmid* |
| `fsthaw_vm` | Thaw guest filesystems via QEMU guest-agent (fsfreeze-thaw). Call after fsfreeze_vm. Parameters: node*, vmid* |
| `get_vm_config` | Get full QEMU VM configuration. |
| `get_vm_guest_info` | QEMU guest-agent introspection (info/os/fs/host/timezone/users). Per-section soft-fail; VM must be running with agent. Parameters: node*, vmid*, sections?=os,fs,host,info (comma list) |
| `get_vm_network` | Get VM network: configured netN from config plus optional runtime interfaces via QEMU guest agent (network-get-interfaces). Agent must be running. Parameters: node*, vmid*, resolve_runtime?=true |
| `get_vm_rrd_data` | Get RRD metrics for a VM. Parameters: node*, vmid*, timeframe?=hour |
| `get_vm_status` | Get current runtime status for one VM. Parameters: node*, vmid* |
| `get_vms` | List all QEMU virtual machines across the cluster (not LXC — use get_containers, or get_cluster_resources(type=vm) for both). Status and resource usage included. |
| `pull_from_vm` | Pull a file from a running VM via QEMU guest agent file-read. Writes local_path when set; otherwise returns base64. Parameters: node*, vmid*, remote_path*; local_path? |
| `push_to_vm` | Push a file into a running VM via QEMU guest agent file-write. Provide local_path or content_base64. Max 32 MiB. Parameters: node*, vmid*, remote_path*; local_path?, content_base64? |
| `qm_set_vm` | Allowlisted host qm set when REST token lacks ACL (requires ssh). Keys: onboot, description, tags. Not free-form shell. Prefer update_vm_config first. Parameters: node*, vmid*; onboot?, description?, tags? |
| `reboot_vm` | Graceful ACPI reboot (distinct from reset). Parameters: node*, vmid* |
| `reset_vm` | Hard-reset a QEMU VM. Parameters: node*, vmid* |
| `resize_vm_disk` | Grow a VM disk. Parameters: node*, vmid*, disk* (e.g. scsi0), size* (e.g. +10G) |
| `resume_vm` | Resume a suspended VM. Parameters: node*, vmid* |
| `shutdown_vm` | Gracefully shut down a QEMU VM. Parameters: node*, vmid* |
| `start_vm` | Start a QEMU VM (not LXC — use start_lxc / start_guest). Parameters: node*, vmid* |
| `stop_vm` | Force-stop a QEMU VM. Parameters: node*, vmid* |
| `suspend_vm` | Suspend a VM. Parameters: node*, vmid* |
| `update_vm_config` | Update QEMU VM config. On 403 returns structured vm_acl_denied (try qm_set_vm). Parameters: node*, vmid*; cores?, memory?, name?, net0?, onboot?, agent?, iso?, boot?, ciuser?, cipassword?, sshkeys?, ipconfig0?, ide2?, description?, tags? |

### LXC

| Tool | Description |
|------|-------------|
| `bootstrap_docker_lxc` | Orchestrate Docker LXC: create(docker_ready)+wait → start → DNS → SSH → prepare_lxc_for_docker(docker_mode=auto, install+smoke) → restart if needed → status. Prefer when user asks for Docker LXC. For a plain small CT use provision_lxc. Requires ssh. Parameters: node*, hostname*; vmid?, cpus?, memory?, disk_size?, storage?, bridge?, ip?, gw?, nameservers?=8.8.8.8 9.9.9.9, ostemplate_filter?=ubuntu, ssh_public_keys?, password?, docker_mode?=auto, timeout? |
| `clone_lxc` | Clone an LXC (async UPID — wait_for_task). Parameters: node*, vmid*, newid*, hostname?, full?=true, target?, storage? |
| `configure_lxc_dns` | Set CT nameserver/searchdomain via REST (falls back to pct set). Optionally prefer IPv4 in guest gai.conf when running. Prefer CT nameserver over editing resolv.conf (PVE rewrites on start). Parameters: node*, vmid*; nameserver?=8.8.8.8 9.9.9.9, searchdomain?, prefer_ipv4?=true |
| `configure_lxc_ssh` | Ensure openssh-server enabled; optionally install ssh_public_keys and/or set password; return sshd_listening. Requires ssh. Parameters: node*, vmid*; ssh_public_keys?, password?, enable_password_ssh?=true, install_openssh?=true |
| `convert_lxc_to_template` | Convert LXC to template. Parameters: node*, vmid* |
| `create_lxc` | Create an LXC (async UPID — always wait_for_task before start unless wait=true). OS template only — not Docker/app deploy. Prefer ssh_public_keys for guest SSH (many templates block root password SSH; create password ≠ SSH login). Guest password optional when host SSH + pct exec works. For one-shot create→start→IP→SSH bootstrap use provision_lxc. docker_ready=true tries nesting=1,keyctl=1 (retries nesting-only + needs_crun warning on ACL deny) and tips prepare_lxc_for_docker (does not install Docker). Day-2: push_to_lxc (prefer for private sources — not guest git clone), deploy_static_nginx, deploy_node_app. If any named tool is missing from your MCP list → get_mcp_capabilities then reload MCP; do not invent base64/scp/public-repo workarounds. Parameters: node*, vmid*, hostname*; ostemplate?, cpus?, memory?, disk_size?, storage?, features?, password?, ssh_public_keys?, unprivileged?, bridge?, ip?, gw?, net0?, ostemplate_filter?, docker_ready?=false, wait?=false, nameserver?, searchdomain?, onboot?, description?, tags? |
| `create_spice_ticket_lxc` | Mint SPICE ticket for an LXC (connect externally). Parameters: node*, vmid* |
| `create_termproxy_ticket_lxc` | Mint termproxy ticket for an LXC. Parameters: node*, vmid* |
| `create_vnc_ticket_lxc` | Mint VNC ticket for an LXC. Parameters: node*, vmid*, websocket?=true |
| `delete_lxc` | IRREVERSIBLE: permanently delete an LXC and its rootfs. Parameters: node*, vmid*, force?=false |
| `deploy_node_app` | Install Node.js LTS in a running LXC, deploy an app tarball, build, and run under systemd (Next.js / Node portfolio path). Requires host SSH/pct. Prefer local_path tarball (private sources — not guest git clone). Default: Node 22, npm ci && npm run build, systemd on port 3000. Health: wget -qO-. Parameters: node*, vmid*; local_path?, content_base64?, remote_dir?=/opt/app, node_major?=22, build_command?, start_command?, port?=3000, service_name?=node-app, timeout? |
| `deploy_static_nginx` | Install nginx in a running LXC and deploy static content to /var/www/html (Lumon-style fallback). Requires host SSH/pct. Prefer local_path tarball over content_base64. Optional content_base64 or local_path tarball/html. Health: wget -qO- (curl often missing on Debian). Parameters: node*, vmid*; local_path?, content_base64?, remote_extract_dir?=/var/www/html, timeout? |
| `execute_lxc_command` | Execute a command inside a running LXC via host SSH + pct exec (no Proxmox REST /exec — HTTP 501 means stale MCP build). Requires opt-in ssh config. Response includes stdout/stderr and output/error aliases. Stock Debian templates often lack curl — prefer wget -qO- URL or python3 for HTTP checks. Parameters: node*, vmid*, command*; timeout? (seconds, else ssh.timeout / PROXMOX_MCP_EXEC_TIMEOUT) |
| `get_containers` | List all LXC containers across the cluster (includes configured IP from netN when set). Optional probes=true runs cheap pct checks for docker binary and :80 listeners (requires host SSH; slow on large fleets). Parameters: probes?=false. For QEMU use get_vms. |
| `get_docker_lxc_status` | Read-only Docker-in-LXC probe: features, DefaultRuntime, docker/compose versions, disk, IP. Does not install or smoke-test. Requires ssh for runtime fields. Parameters: node*, vmid* |
| `get_lxc_config` | Get full LXC configuration. Parameters: node*, vmid* |
| `get_lxc_network` | Get LXC network: configured netN (static/dhcp/MAC/bridge) plus optional runtime IPv4 via pct exec when SSH is configured. Parameters: node*, vmid*, resolve_runtime?=true |
| `get_lxc_rrd_data` | Get RRD metrics for an LXC. Parameters: node*, vmid*, timeframe?=hour |
| `get_lxc_status` | Get current runtime status for one LXC (includes configured_ip/networks from config). Parameters: node*, vmid* |
| `pct_set_lxc` | Allowlisted host pct set for when REST token lacks ACL (requires ssh). Keys: features, nameserver, searchdomain, onboot, description, tags. Not free-form shell. Parameters: node*, vmid*; features?, nameserver?, searchdomain?, onboot?, description?, tags? |
| `prepare_lxc_for_docker` | Idempotent Docker-in-LXC prep (D24): features + AppArmor; docker_mode=auto\|keyctl\|crun (auto falls back to nesting+crun when keyctl ACL denied); optional install_docker/smoke_test. Requires ssh. Success = docker run (hello-world) — not docker --version. Do not claim ready with nesting-only + stock runc. Parameters: node*, vmid*; fuse?=false, allow_apparmor_workaround?=true, install_docker?=false, smoke_test?=false, timeout?, docker_mode?=auto |
| `provision_lxc` | One-shot small LXC: create(wait)+start(wait) → optional configure_lxc_ssh → resolve runtime IP → return {vmid,hostname,ip,ssh_hint}. OS template only (not Docker — use bootstrap_docker_lxc). Requires host SSH. Prefer ssh_public_keys; password at create still needs enable_password_ssh (default true when password set). Never echoes password. Parameters: node*, hostname*; vmid?, cpus?=1, memory?=2048, disk_size?=8, storage?, bridge?, ip?, gw?, ostemplate?, ostemplate_filter?, nameserver?, password?, ssh_public_keys?, enable_password_ssh?=true, onboot?, description?, tags?, timeout? |
| `pull_from_lxc` | Pull a file from a running LXC via pct pull. Writes local_path when set; otherwise returns base64. Requires ssh. Parameters: node*, vmid*, remote_path*; local_path?, timeout? |
| `push_to_lxc` | Push a file into a running LXC via host SSH + pct push (SFTP to host temp then pct push). Prefer local_path (Cursor-side) over content_base64 — avoid base64 chunk workarounds. Preferred path for private app sources (not guest HTTPS git clone without creds). Max 32 MiB. Requires ssh. Parameters: node*, vmid*, remote_path*; local_path?, content_base64?, timeout? |
| `reboot_lxc` | Reboot an LXC (applies pending config). Parameters: node*, vmid* |
| `resize_lxc_disk` | Grow an LXC volume. Parameters: node*, vmid*, disk* (e.g. rootfs), size* (e.g. +5G) |
| `resume_lxc` | WARNING: resume after LXC suspend (CRIU) is best-effort. Parameters: node*, vmid* |
| `set_lxc_password` | Set/reset LXC root password via pct exec (no REST after-create password API). Optionally enables root password SSH in sshd. Requires config ssh. Parameters: node*, vmid*, password*, enable_password_ssh?=true |
| `set_lxc_ssh_keys` | Install root authorized_keys via pct exec (prefer ssh_public_keys on create_lxc). Parameters: node*, vmid*, ssh_public_keys*, mode?=replace\|append |
| `shutdown_lxc` | Gracefully shut down an LXC. Parameters: node*, vmid* |
| `start_lxc` | Start an LXC container. Parameters: node*, vmid* |
| `stop_lxc` | Force-stop an LXC container. Parameters: node*, vmid* |
| `suspend_lxc` | WARNING: LXC suspend uses CRIU checkpoint and is often unreliable/unsupported. Prefer shutdown. Parameters: node*, vmid* |
| `update_lxc_config` | Update LXC config (cores/memory/hostname/net0/features/nameserver/searchdomain/onboot/description/tags). Does NOT set password or SSH keys — use set_lxc_password / set_lxc_ssh_keys (need host SSH/pct) or recreate with password/ssh_public_keys. |
| `update_lxc_features` | Update LXC features (nesting/keyctl/fuse). Does not strip flags. On keyctl/fuse 403 returns structured feature_acl_denied (recommended_fallback=crun). Prefer prepare_lxc_for_docker(docker_mode=auto) or pct_set_lxc when token lacks ACL. After change: get_guest_pending + stop/start. Parameters: node*, vmid*, features* |

### Guest (unified)

| Tool | Description |
|------|-------------|
| `delete_guest` | IRREVERSIBLE: permanently delete a VM or LXC. Parameters: node*, vmid*, guest_type?=qemu\|lxc, force?=false |
| `get_console_connection` | Mint console ticket + structured viewer hints (no MCP websocket proxy — D6). Parameters: node*, vmid*; guest_type?=qemu\|lxc, console?=vnc\|spice\|termproxy, websocket?=true, host? |
| `get_guest_pending` | Get pending (not-yet-applied) config for a VM or LXC. Parameters: node*, vmid*, guest_type?=qemu\|lxc |
| `get_guest_status` | Get runtime status for a VM or LXC. Parameters: node*, vmid*, guest_type?=qemu\|lxc |
| `move_guest_disk` | Move a guest disk/volume to another storage. Parameters: node*, vmid*, disk*, storage*, guest_type?=qemu\|lxc, delete?=true |
| `reboot_guest` | Reboot a VM or LXC. Parameters: node*, vmid*, guest_type?=qemu\|lxc |
| `shutdown_guest` | Gracefully shut down a VM or LXC. Parameters: node*, vmid*, guest_type?=qemu\|lxc |
| `start_guest` | Start a VM or LXC. Parameters: node*, vmid*, guest_type?=qemu\|lxc |
| `stop_guest` | Force-stop a VM or LXC. Parameters: node*, vmid*, guest_type?=qemu\|lxc |

### Snapshots / backups

| Tool | Description |
|------|-------------|
| `create_backup` | Create a vzdump backup (async UPID — wait_for_task). Parameters: node*, vmid*, storage?, mode?=snapshot, compress?=zstd, notes? |
| `create_backup_job` | Create a scheduled backup job. Parameters: schedule*, storage*; vmid? (comma-separated), mode?=snapshot, compress?=zstd, enabled?=true, comment?, mailto?, mailnotification?, all?=false |
| `create_snapshot` | Create a snapshot. Parameters: node*, vmid*, snapname*, guest_type?, description?, vmstate?=false |
| `delete_backup` | IRREVERSIBLE: delete a backup volume. Parameters: node*, storage*, volume* |
| `delete_backup_job` | IRREVERSIBLE: delete a scheduled backup job. Parameters: id* |
| `delete_snapshot` | IRREVERSIBLE: delete a snapshot. Parameters: node*, vmid*, snapname*, guest_type? |
| `list_backup_jobs` | List scheduled cluster backup jobs (/cluster/backup). |
| `list_backups` | List backups on storage. Parameters: node*, storage*, vmid? |
| `list_snapshots` | List snapshots for a guest. Parameters: node*, vmid*, guest_type?=qemu\|lxc |
| `restore_backup` | WARNING: restore may overwrite guest disks when force is set (async UPID — wait_for_task). Parameters: node*, archive*, vmid*, storage?, force?=false, guest_type?=qemu |
| `rollback_snapshot` | WARNING: rollback discards state after the snapshot. Parameters: node*, vmid*, snapname*, guest_type? |

### Storage

| Tool | Description |
|------|-------------|
| `create_storage` | Create cluster storage definition. For type=pbs pass datastore/fingerprint/server/username/password. Parameters: storage*, type*, content?, path?, server?, export?, vgname?, pool?, monhost?, username?, password?, nodes?, disable?, datastore?, fingerprint?, port? |
| `delete_storage` | IRREVERSIBLE: delete storage definition (not underlying data by default). Parameters: storage* |
| `delete_storage_content` | IRREVERSIBLE: delete a storage volume. Parameters: node*, storage*, volume* |
| `download_url_to_storage` | Download URL into storage (async UPID — wait_for_task). http/https only; host fetches URL. Parameters: node*, storage*, url*, filename?, content?=iso, verify_certificate?=true, checksum?, checksum_algorithm? |
| `get_pbs_storage_status` | Status for a PVE storage of type=pbs. Parameters: node*, storage* |
| `get_storage` | List storage pools across the cluster with usage. |
| `get_storage_content` | List storage content (iso/vztmpl/backup/images). Parameters: node*, storage*, content? |
| `list_isos` | List ISO images. Parameters: node*, storage?, filter? |
| `list_os_templates` | List LXC OS templates (vztmpl) across storages. Parameters: node*, storage?, filter? (e.g. ubuntu) |
| `update_storage` | Update storage definition. Parameters: storage*, content?, nodes?, disable? |

### Migrate / HA

| Tool | Description |
|------|-------------|
| `create_ha_group` | Create HA group (often needs elevated privileges). Parameters: group*, nodes*, comment? |
| `create_ha_resource` | Create HA resource (often needs elevated privileges). Parameters: sid* (e.g. vm:100), group?, state?=started, comment? |
| `delete_ha_group` | IRREVERSIBLE: delete HA group. Parameters: group* |
| `delete_ha_resource` | IRREVERSIBLE: delete HA resource. Parameters: sid* |
| `get_ha_status` | Get current HA manager status. |
| `list_ha_groups` | List HA groups. |
| `list_ha_resources` | List HA resources. |
| `migrate_guest` | Migrate a VM or LXC to another node (async UPID — wait_for_task). Parameters: node*, vmid*, target*, guest_type?=qemu, online?=true, with_local_disks?=false |
| `update_ha_resource` | Update HA resource. Parameters: sid*, group?, state?, comment? |

### Firewall

| Tool | Description |
|------|-------------|
| `add_firewall_ipset_cidr` | Add a CIDR/IP to a firewall IP set. Parameters: name*, cidr*, comment?, nomatch?=false |
| `create_cluster_firewall_rule` | Create cluster firewall rule. Parameters: action*, type*, enable?, source?, dest?, proto?, dport?, sport?, comment?, pos? |
| `create_firewall_alias` | Create firewall alias. Parameters: name*, cidr*, comment? |
| `create_firewall_ipset` | Create firewall IP set. Parameters: name*, comment? |
| `create_guest_firewall_rule` | Create guest firewall rule. Parameters: node*, vmid*, action*, type*, guest_type?, enable?, source?, dest?, proto?, dport?, comment? |
| `delete_cluster_firewall_rule` | IRREVERSIBLE: delete cluster firewall rule. Parameters: pos* |
| `delete_firewall_alias` | IRREVERSIBLE: delete firewall alias. Parameters: name* |
| `delete_firewall_ipset` | IRREVERSIBLE: delete firewall IP set. Parameters: name* |
| `delete_firewall_ipset_cidr` | IRREVERSIBLE: remove a CIDR from a firewall IP set. Parameters: name*, cidr* |
| `delete_guest_firewall_rule` | IRREVERSIBLE: delete guest firewall rule. Parameters: node*, vmid*, pos*, guest_type? |
| `get_cluster_firewall_options` | Get cluster firewall options. |
| `get_guest_firewall_options` | Get guest firewall options. Parameters: node*, vmid*, guest_type? |
| `list_cluster_firewall_rules` | List cluster firewall rules. |
| `list_firewall_aliases` | List cluster firewall aliases. |
| `list_firewall_ipset_cidrs` | List CIDR members of a firewall IP set. Parameters: name* |
| `list_firewall_ipsets` | List cluster firewall IP sets. |
| `list_firewall_macros` | List available firewall macros. |
| `list_guest_firewall_rules` | List guest firewall rules. Parameters: node*, vmid*, guest_type? |
| `set_cluster_firewall_options` | WARNING: changes cluster-wide firewall policy. Parameters: enable?, policy_in?, policy_out? |
| `set_guest_firewall_options` | Set guest firewall options. Parameters: node*, vmid*, guest_type?, enable?, dhcp?, ipfilter? |

### Access

| Tool | Description |
|------|-------------|
| `create_group` | Create a group. Parameters: groupid*, comment? |
| `create_token` | Create API token (secret shown once — store immediately). Parameters: userid*, tokenid*, comment?, privsep?=true. privsep=true (default): token needs its own ACL (user@realm!tokenid); effective perms = user ∩ token. privsep=false: token inherits all user permissions (lab shortcut; larger blast radius). |
| `create_user` | Create a user. Parameters: userid*, password?, comment?, email?, enable?=true |
| `delete_group` | IRREVERSIBLE: delete a group. Parameters: groupid* |
| `delete_token` | IRREVERSIBLE: delete API token. Parameters: userid*, tokenid* |
| `delete_user` | IRREVERSIBLE: delete a user. Parameters: userid* |
| `get_permissions` | Get effective permissions for the current auth identity (useful to verify token ACLs / Privilege Separation). |
| `get_token_permissions` | Get effective permissions for an API token (privsep). Parameters: userid* (user@realm), tokenid*. Empty result often means Privilege Separation with no ACL on user@realm!tokenid. |
| `get_user` | Get a user. Parameters: userid* |
| `list_acl` | List ACL entries. |
| `list_groups` | List groups. |
| `list_roles` | List roles. |
| `list_tokens` | List API tokens for a user. Parameters: userid* |
| `list_users` | List Proxmox users. |
| `update_acl` | WARNING: modifies access control; delete=true removes ACL entries. Parameters: path*, roles*, users?, groups?, propagate?=true, delete?=false |

### Replication

| Tool | Description |
|------|-------------|
| `create_replication_job` | Create replication job. Parameters: id* (e.g. 100-0), target*, schedule?, comment?, enabled?=true |
| `delete_replication_job` | IRREVERSIBLE: delete replication job. Parameters: id* |
| `get_replication_status` | Get replication job status. Parameters: node*, jobid* |
| `list_replication_jobs` | List cluster storage replication jobs. |
| `run_replication_job` | Schedule a replication job to run now. Parameters: node*, jobid* |
| `update_replication_job` | Update replication job. Parameters: id*; schedule?, comment?, enabled? |

### SDN

| Tool | Description |
|------|-------------|
| `apply_sdn` | Apply pending SDN configuration cluster-wide (often needs Sys.Modify / elevated privileges). |
| `create_sdn_subnet` | Create SDN subnet (staged until apply_sdn). Parameters: vnet*, subnet* (CIDR); gateway?, snat?, type?=subnet, dnszoneprefix? |
| `create_sdn_vnet` | Create SDN vnet (staged until apply_sdn). Parameters: vnet*, zone*; alias?, tag?, vlanaware?, comment? |
| `create_sdn_zone` | Create SDN zone (staged until apply_sdn). Parameters: zone*, type* (simple\|vlan\|qinq\|vxlan\|evpn); bridge?, nodes?, mtu?, ipam?, dns?, reversedns?, dnszone?, comment? |
| `delete_sdn_subnet` | IRREVERSIBLE: delete SDN subnet (staged until apply_sdn). Parameters: vnet*, subnet* |
| `delete_sdn_vnet` | IRREVERSIBLE: delete SDN vnet (staged until apply_sdn). Parameters: vnet* |
| `delete_sdn_zone` | IRREVERSIBLE: delete SDN zone (staged until apply_sdn). Parameters: zone* |
| `list_sdn_controllers` | List SDN controllers. |
| `list_sdn_dns` | List SDN DNS entries. |
| `list_sdn_ipams` | List SDN IPAMs. |
| `list_sdn_subnets` | List SDN subnets on a vnet. Parameters: vnet* |
| `list_sdn_vnets` | List SDN virtual networks. |
| `list_sdn_zones` | List SDN zones. |
| `update_sdn_subnet` | Update SDN subnet (staged until apply_sdn). Parameters: vnet*, subnet*; gateway?, snat?, dnszoneprefix? |
| `update_sdn_vnet` | Update SDN vnet (staged until apply_sdn). Parameters: vnet*; alias?, tag?, vlanaware?, comment?, zone? |
| `update_sdn_zone` | Update SDN zone (staged until apply_sdn). Parameters: zone*; bridge?, nodes?, mtu?, ipam?, dns?, reversedns?, dnszone?, comment? |

### ACME

| Tool | Description |
|------|-------------|
| `create_acme_account` | Create/register an ACME account. Parameters: name*, contact*; directory?, tos_url? |
| `create_acme_plugin` | Create ACME challenge plugin (dns/standalone). Credential data is never echoed. Parameters: id*, type*; api?, data?, validation_delay?, disable?=false |
| `delete_acme_plugin` | IRREVERSIBLE: delete an ACME plugin. Parameters: id* |
| `get_acme_directories` | List known ACME directories (Let's Encrypt etc.). |
| `list_acme_accounts` | List ACME accounts. |
| `list_acme_plugins` | List ACME challenge plugins. |
| `order_acme_certificate` | Order ACME certificate for a node (async UPID — wait_for_task). Parameters: node*, force?=false |
| `renew_acme_certificate` | Renew ACME certificate for a node (async UPID — wait_for_task). Parameters: node*, force?=false |

### Ceph

| Tool | Description |
|------|-------------|
| `create_ceph_pool` | Create a Ceph pool (light write). Parameters: name*; size?, min_size?, pg_num?, application? |
| `delete_ceph_pool` | IRREVERSIBLE: delete a Ceph pool. confirm* must equal the pool name. Parameters: name*, confirm* |
| `get_ceph_status` | Get Ceph cluster health/status (requires Ceph). |
| `list_ceph_mgrs` | List Ceph managers (read-only). |
| `list_ceph_mons` | List Ceph monitors (read-only). |
| `list_ceph_osds` | List Ceph OSDs (read-only — create/destroy out of scope). |
| `list_ceph_pools` | List Ceph pools. |

### Pools

| Tool | Description |
|------|-------------|
| `create_pool` | Create a resource pool. Parameters: poolid*, comment? |
| `delete_pool` | IRREVERSIBLE: delete a resource pool. Parameters: poolid* |
| `get_pool` | Get a resource pool and its members. Parameters: poolid* |
| `list_pools` | List resource pools. |
| `update_pool` | Update pool membership. Parameters: poolid*; comment?, vms? (comma IDs), storage? (comma names), delete?=false (true=remove members) |

<!-- END GENERATED TOOLS -->
