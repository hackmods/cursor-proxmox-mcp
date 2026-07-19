"""
Tool descriptions for Proxmox MCP tools.
"""

# Node tool descriptions
GET_NODES_DESC = """List all nodes in the Proxmox cluster with their status, CPU, memory, and role information.

Example:
{"node": "pve1", "status": "online", "cpu_usage": 0.15, "memory": {"used": "8GB", "total": "32GB"}}"""

GET_NODE_STATUS_DESC = """Get detailed status information for a specific Proxmox node.

Parameters:
node* - Name/ID of node to query (e.g. 'pve1')

Example:
{"cpu": {"usage": 0.15}, "memory": {"used": "8GB", "total": "32GB"}}"""

# VM tool descriptions
GET_VMS_DESC = """List all virtual machines across the cluster with their status and resource usage.

Example:
{"vmid": "100", "name": "ubuntu", "status": "running", "cpu": 2, "memory": 4096}"""

CREATE_VM_DESC = """Create a new virtual machine with specified configuration.

Parameters:
node* - Host node name (e.g. 'pve')
vmid* - New VM ID number (e.g. '200', '300')
name* - VM name (e.g. 'my-new-vm', 'web-server')
cpus* - Number of CPU cores (e.g. 1, 2, 4)
memory* - Memory size in MB (e.g. 2048 for 2GB, 4096 for 4GB)
disk_size* - Disk size in GB (e.g. 10, 20, 50)
storage - Storage name (optional, will auto-detect if not specified)
ostype - OS type (optional, default: 'l26' for Linux)

Examples:
- Create VM with 1 CPU, 2GB RAM, 10GB disk: node='pve', vmid='200', name='test-vm', cpus=1, memory=2048, disk_size=10
- Create VM with 2 CPUs, 4GB RAM, 20GB disk: node='pve', vmid='201', name='web-server', cpus=2, memory=4096, disk_size=20"""

CREATE_LXC_DESC = """Create a new LXC container with specified configuration.

Parameters:
node* - Host node name (e.g. 'pve')
vmid* - New container ID number (e.g. '200', '300')
hostname* - Container hostname (e.g. 'my-lxc', 'web-container')
ostemplate* - OS template path (e.g. 'local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst')
cpus* - Number of CPU cores (e.g. 1, 2, 4)
memory* - Memory size in MB (e.g. 2048 for 2GB, 4096 for 4GB)
disk_size* - Root filesystem size in GB (e.g. 8, 10, 20)
storage - Storage name for rootfs (optional, will auto-detect if not specified)
features - Container features string (optional, default: 'nesting=1'; e.g. 'nesting=1,keyctl=1,fuse=1')
password - Root password (optional)
unprivileged - Create as unprivileged container (optional, default: true)

Examples:
- Create LXC with nesting: node='pve', vmid='200', hostname='dev-lxc', ostemplate='local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst', cpus=1, memory=2048, disk_size=8, features='nesting=1'
- Create LXC with nesting+keyctl: node='pve', vmid='201', hostname='docker-lxc', ostemplate='local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst', cpus=2, memory=4096, disk_size=16, features='nesting=1,keyctl=1'"""
EXECUTE_VM_COMMAND_DESC = """Execute commands in a VM via QEMU guest agent.

Parameters:
node* - Host node name (e.g. 'pve1')
vmid* - VM ID number (e.g. '100')
command* - Shell command to run (e.g. 'uname -a')

Example:
{"success": true, "output": "Linux vm1 5.4.0", "exit_code": 0}"""

# VM Power Management tool descriptions
START_VM_DESC = """Start a virtual machine.

Parameters:
node* - Host node name (e.g. 'pve')
vmid* - VM ID number (e.g. '101')

Example:
Power on VPN-Server with ID 101 on node pve"""

STOP_VM_DESC = """Stop a virtual machine (force stop).

Parameters:
node* - Host node name (e.g. 'pve')  
vmid* - VM ID number (e.g. '101')

Example:
Force stop VPN-Server with ID 101 on node pve"""

SHUTDOWN_VM_DESC = """Shutdown a virtual machine gracefully.

Parameters:
node* - Host node name (e.g. 'pve')
vmid* - VM ID number (e.g. '101')

Example:
Gracefully shutdown VPN-Server with ID 101 on node pve"""

RESET_VM_DESC = """Reset (restart) a virtual machine.

Parameters:
node* - Host node name (e.g. 'pve')
vmid* - VM ID number (e.g. '101')

Example:
Reset VPN-Server with ID 101 on node pve"""

DELETE_VM_DESC = """Delete/remove a virtual machine completely.

⚠️ WARNING: This operation permanently deletes the VM and all its data!

Parameters:
node* - Host node name (e.g. 'pve')
vmid* - VM ID number (e.g. '998')
force - Force deletion even if VM is running (optional, default: false)

This will permanently remove:
- VM configuration
- All virtual disks
- All snapshots
- Cannot be undone!

Example:
Delete test VM with ID 998 on node pve"""

# Container tool descriptions
GET_CONTAINERS_DESC = """List all LXC containers across the cluster with their status and configuration.

Example:
{"vmid": "200", "name": "nginx", "status": "running", "cpus": 2, "memory": {"used": 268435456, "total": 2147483648}}"""

START_LXC_DESC = """Start an LXC container.

Parameters:
node* - Host node name (e.g. 'pve')
vmid* - Container ID number (e.g. '121')

Example:
Start container 121 on node pve"""

STOP_LXC_DESC = """Stop an LXC container (force stop).

Parameters:
node* - Host node name (e.g. 'pve')
vmid* - Container ID number (e.g. '121')

Example:
Force stop container 121 on node pve"""

SHUTDOWN_LXC_DESC = """Shutdown an LXC container gracefully.

Parameters:
node* - Host node name (e.g. 'pve')
vmid* - Container ID number (e.g. '121')

Example:
Gracefully shutdown container 121 on node pve"""

REBOOT_LXC_DESC = """Reboot an LXC container (LXC counterpart to reset_vm).

Uses POST /nodes/{node}/lxc/{vmid}/status/reboot — applies pending config changes.

Parameters:
node* - Host node name (e.g. 'pve')
vmid* - Container ID number (e.g. '121')

Example:
Reboot container 121 on node pve"""

DELETE_LXC_DESC = """Delete/remove an LXC container completely.

⚠️ WARNING: This operation permanently deletes the container and its rootfs!

Parameters:
node* - Host node name (e.g. 'pve')
vmid* - Container ID number (e.g. '120')
force - Force deletion even if container is running (optional, default: false)

This will permanently remove:
- Container configuration
- Root filesystem
- All snapshots
- Cannot be undone!

Example:
Delete unused container 120 on node pve"""

UPDATE_LXC_FEATURES_DESC = """Update LXC feature flags (nesting, keyctl, fuse, etc.).

Needed for Docker-in-LXC when features were not set at create time, or to add keyctl after create.

Parameters:
node* - Host node name (e.g. 'pve')
vmid* - Container ID number (e.g. '121')
features* - Features string (e.g. 'nesting=1,keyctl=1' or 'nesting=1,keyctl=1,fuse=1')

Note: Proxmox typically allows only root@pam to set features beyond nesting (e.g. keyctl).
API tokens may get 403 when setting keyctl/fuse.

Example:
node='pve', vmid='121', features='nesting=1,keyctl=1'"""

# Storage tool descriptions
GET_STORAGE_DESC = """List storage pools across the cluster with their usage and configuration.

Example:
{"storage": "local-lvm", "type": "lvm", "used": "500GB", "total": "1TB"}"""

# Cluster tool descriptions
GET_CLUSTER_STATUS_DESC = """Get overall Proxmox cluster health and configuration status.

Example:
{"name": "proxmox", "quorum": "ok", "nodes": 3, "ha_status": "active"}"""
