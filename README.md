# cursor-proxmox-mcp

Cursor-focused Python MCP server for [Proxmox](https://www.proxmox.com/) — manage QEMU VMs and LXC containers from Cursor (optional OpenAPI/Open WebUI).

**Repo:** [hackmods/cursor-proxmox-mcp](https://github.com/hackmods/cursor-proxmox-mcp)

## MCP tools

| Tool | Purpose |
|------|---------|
| `get_nodes` | List cluster nodes |
| `get_node_status` | Detailed status for one node |
| `get_vms` | List QEMU VMs across the cluster |
| `create_vm` | Create a QEMU VM |
| `get_containers` | List LXC containers across the cluster |
| `create_lxc` | Create an LXC container (`features` defaults to `nesting=1`) |
| `start_lxc` / `stop_lxc` / `shutdown_lxc` / `reboot_lxc` | LXC power control |
| `delete_lxc` | Delete an LXC container (optional force) |
| `update_lxc_features` | Set LXC features (nesting/keyctl/fuse) after create |
| `execute_vm_command` | Run a command via QEMU guest agent |
| `start_vm` / `stop_vm` / `shutdown_vm` / `reset_vm` | VM power control |
| `delete_vm` | Delete a VM (optional force) |
| `get_storage` | List storage pools |
| `get_cluster_status` | Cluster health / status |

## What's in this fork

- VM lifecycle: `create_vm`, power controls, `delete_vm`, storage auto-detect
- LXC lifecycle: `create_lxc`, `get_containers`, power controls, `delete_lxc`, `update_lxc_features`
- Windows-friendly launch: prefer Cursor `mcp.json` → Python directly; `start.bat` is a manual fallback (no stdout noise)
- OpenAPI/Open WebUI via `mcpo` (optional)
- Tests fixed so they complete

Maintained for personal Proxmox + Cursor use; updates land here as needed.

## Built With

- [Cursor](https://cursor.com)
- [Proxmoxer](https://github.com/proxmoxer/proxmoxer) — Proxmox API wrapper
- [MCP SDK](https://github.com/modelcontextprotocol/sdk)
- [Pydantic](https://docs.pydantic.dev/)

## Features

- Token auth to Proxmox
- QEMU VM create / power / delete / guest-agent commands
- LXC create / list / power / delete / feature updates (Docker-in-LXC friendly)
- Storage type detection (LVM vs file-based)
- Typed config, logging, formatted tool output
- Optional OpenAPI REST proxy for Open WebUI


## Installation

### Prerequisites
- UV package manager (recommended)
- Python 3.10 or higher
- Git
- Access to a Proxmox server with API token credentials

Before starting, ensure you have:
- [ ] Proxmox server hostname or IP
- [ ] Proxmox API token (see [API Token Setup](#proxmox-api-token-setup))
- [ ] UV installed (`pip install uv`)

### Option 1: Quick Install (Recommended)

1. Clone and set up environment:
   ```bash
   # Clone repository (this fork)
   git clone https://github.com/hackmods/cursor-proxmox-mcp.git
   cd cursor-proxmox-mcp

   # Create and activate virtual environment
   uv venv

   # or force 3.11 (for mcpo dependency)
   python3.11 -m venv .venv

   # then activate it 
   source .venv/bin/activate  # Linux/macOS
   # OR
   .\.venv\Scripts\Activate.ps1  # Windows
   ```

2. Install dependencies:
   ```bash
   # Install with development dependencies
   uv pip install -e ".[dev]"

   #or via pip
   pip install -e .
   pip install pytest pytest-asyncio black mypy ruff types-requests
   pip install mcpo #need python 3.11
   ```

3. Create configuration:
   ```bash
   # Create config directory and copy template
   mkdir -p proxmox-config
   cp proxmox-config/config.example.json proxmox-config/config.json
   ```

4. Edit `proxmox-config/config.json`:
   ```json
   {
       "proxmox": {
           "host": "PROXMOX_HOST",        # Required: Your Proxmox server address
           "port": 8006,                  # Optional: Default is 8006
           "verify_ssl": false,           # Optional: Set false for self-signed certs
           "service": "PVE"               # Optional: Default is PVE
       },
       "auth": {
           "user": "USER@pve",            # Required: Your Proxmox username
           "token_name": "TOKEN_NAME",    # Required: API token ID
           "token_value": "TOKEN_VALUE"   # Required: API token value
       },
       "logging": {
           "level": "INFO",               # Optional: DEBUG for more detail
           "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
           "file": "proxmox_mcp.log"      # Optional: Log to file
       }
   }
   ```

### Verifying Installation

1. Check Python environment:
   ```bash
   python -c "import proxmox_mcp; print('Installation OK')"
   ```

2. Run the tests:
   ```bash
   pytest
   ```

3. Verify configuration:
   ```bash
   # Linux/macOS
   PROXMOX_MCP_CONFIG="proxmox-config/config.json" python -m proxmox_mcp.server

   # Windows (PowerShell)
   $env:PROXMOX_MCP_CONFIG="proxmox-config\config.json"; python -m proxmox_mcp.server
   ```

## Configuration

### Proxmox API Token Setup
1. Log into your Proxmox web interface
2. Navigate to Datacenter -> Permissions -> API Tokens
3. Create a new API token:
   - Select a user (e.g., root@pam)
   - Enter a token ID (e.g., "mcp-token")
   - Uncheck "Privilege Separation" if you want full access
   - Save and copy both the token ID and secret

## Running the Server

### Development Mode
For testing and development:
```bash
# Activate virtual environment first
source .venv/bin/activate  # Linux/macOS
# OR
.\.venv\Scripts\Activate.ps1  # Windows

# Run the server (set config first)
export PROXMOX_MCP_CONFIG=proxmox-config/config.json   # Linux/macOS
# OR
$env:PROXMOX_MCP_CONFIG="proxmox-config\config.json"   # Windows PowerShell
python -m proxmox_mcp.server
```

### Windows / Cursor (`start.bat`)
For Cursor on Windows, use the included launcher (also referenced from `~/.cursor/mcp.json`):

```bat
start.bat
```

It sets `PROXMOX_MCP_CONFIG=proxmox-config\config.json`, `PYTHONPATH=...\src`, and runs `python -m proxmox_mcp.server`. After adding tools like `create_lxc`, restart the **proxmox** MCP server in Cursor Settings → MCP so the new tools appear.

### OpenAPI Deployment (Production Ready)

Deploy ProxmoxMCP Plus as standard OpenAPI REST endpoints for integration with Open WebUI and other applications.

#### Quick OpenAPI Start
```bash
# Install mcpo (MCP-to-OpenAPI proxy)
pip install mcpo

# Start OpenAPI service on port 8811
./start_openapi.sh
```

#### Docker Deployment
```bash
# Build and run with Docker
docker build -t proxmox-mcp-api .
docker run -d --name proxmox-mcp-api -p 8811:8811 \
  -v $(pwd)/proxmox-config:/app/proxmox-config proxmox-mcp-api

# Or use Docker Compose
docker-compose up -d
```

#### Access OpenAPI Service
Once deployed, access your service at:
- **📖 API Documentation**: http://your-server:8811/docs
- **🔧 OpenAPI Specification**: http://your-server:8811/openapi.json
- **❤️ Health Check**: http://your-server:8811/health

### Cline Desktop Integration

For Cline users, add this configuration to your MCP settings file (typically at `~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`):

```json
{
    "mcpServers": {
        "ProxmoxMCP-Plus": {
            "command": "/absolute/path/to/ProxmoxMCP-Plus/.venv/bin/python",
            "args": ["-m", "proxmox_mcp.server"],
            "cwd": "/absolute/path/to/ProxmoxMCP-Plus",
            "env": {
                "PYTHONPATH": "/absolute/path/to/ProxmoxMCP-Plus/src",
                "PROXMOX_MCP_CONFIG": "/absolute/path/to/ProxmoxMCP-Plus/proxmox-config/config.json",
                "PROXMOX_HOST": "your-proxmox-host",
                "PROXMOX_USER": "username@pve",
                "PROXMOX_TOKEN_NAME": "token-name",
                "PROXMOX_TOKEN_VALUE": "token-value",
                "PROXMOX_PORT": "8006",
                "PROXMOX_VERIFY_SSL": "false",
                "PROXMOX_SERVICE": "PVE",
                "LOG_LEVEL": "DEBUG"
            },
            "disabled": false,
            "autoApprove": []
        }
    }
}
```

## Available Tools & API Endpoints

The server provides comprehensive MCP tools for VM and LXC management:

### VM Management Tools

#### create_vm 
Create a new virtual machine with specified resources.

**Parameters:**
- `node` (string, required): Name of the node
- `vmid` (string, required): ID for the new VM
- `name` (string, required): Name for the VM
- `cpus` (integer, required): Number of CPU cores (1-32)
- `memory` (integer, required): Memory in MB (512-131072)
- `disk_size` (integer, required): Disk size in GB (5-1000)
- `storage` (string, optional): Storage pool name
- `ostype` (string, optional): OS type (default: l26)

**API Endpoint:**
```http
POST /create_vm
Content-Type: application/json

{
    "node": "pve",
    "vmid": "200",
    "name": "my-vm",
    "cpus": 1,
    "memory": 2048,
    "disk_size": 10
}
```

**Example Response:**
```
🎉 VM 200 created successfully!

📋 VM Configuration:
  • Name: my-vm
  • Node: pve
  • VM ID: 200
  • CPU Cores: 1
  • Memory: 2048 MB (2.0 GB)
  • Disk: 10 GB (local-lvm, raw format)
  • Storage Type: lvmthin
  • Network: virtio (bridge=vmbr0)
  • QEMU Agent: Enabled

🔧 Task ID: UPID:pve:001AB729:0442E853:682FF380:qmcreate:200:root@pam!mcp
```

#### create_lxc
Create a new LXC container via the Proxmox LXC API (`POST /nodes/{node}/lxc`).

**Parameters:**
- `node` (string, required): Name of the node
- `vmid` (string, required): ID for the new container
- `hostname` (string, required): Hostname for the container
- `ostemplate` (string, required): OS template path (e.g. `local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst`)
- `cpus` (integer, required): Number of CPU cores (1-32)
- `memory` (integer, required): Memory in MB (512-131072)
- `disk_size` (integer, required): Root filesystem size in GB (4-1000)
- `storage` (string, optional): Storage pool for rootfs (auto-detects `rootdir` storage)
- `features` (string, optional): LXC features string — **defaults to `nesting=1`**; e.g. `nesting=1,keyctl=1,fuse=1`
- `password` (string, optional): Root password
- `unprivileged` (boolean, optional): Create unprivileged container (default: `true`)

**Example (MCP tool call):**
```json
{
    "node": "pve",
    "vmid": "210",
    "hostname": "dev-lxc",
    "ostemplate": "local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst",
    "cpus": 2,
    "memory": 2048,
    "disk_size": 8,
    "features": "nesting=1"
}
```

**Example Response:**
```
🎉 LXC container 210 created successfully!

📋 Container Configuration:
  • Hostname: dev-lxc
  • Node: pve
  • Container ID: 210
  • CPU Cores: 2
  • Memory: 2048 MB (2.0 GB)
  • Rootfs: 8 GB (local-lvm)
  • Features: nesting=1
  • Unprivileged: True
  • Network: eth0 (bridge=vmbr0, dhcp)
```

#### VM Power Management 🆕

**start_vm**: Start a virtual machine
```http
POST /start_vm
{"node": "pve", "vmid": "200"}
```

**stop_vm**: Force stop a virtual machine
```http
POST /stop_vm
{"node": "pve", "vmid": "200"}
```

**shutdown_vm**: Gracefully shutdown a virtual machine
```http
POST /shutdown_vm
{"node": "pve", "vmid": "200"}
```

**reset_vm**: Reset (restart) a virtual machine
```http
POST /reset_vm
{"node": "pve", "vmid": "200"}
```

**delete_vm** 🆕: Completely delete a virtual machine
```http
POST /delete_vm
{"node": "pve", "vmid": "200", "force": false}
```

### Container Management Tools

#### get_containers
List all LXC containers across the cluster (status, node, CPU, memory).

**API Endpoint:** `POST /get_containers`

#### create_lxc
See full parameter docs above. Creates via Proxmox `POST /nodes/{node}/lxc` (proxmoxer).

#### LXC Power Management

Use these for containers — `start_vm` / etc. only target QEMU VMs.

**start_lxc**: Start an LXC container
```http
POST /start_lxc
{"node": "pve", "vmid": "121"}
```

**stop_lxc**: Force stop an LXC container
```http
POST /stop_lxc
{"node": "pve", "vmid": "121"}
```

**shutdown_lxc**: Gracefully shut down an LXC container
```http
POST /shutdown_lxc
{"node": "pve", "vmid": "121"}
```

**reboot_lxc**: Reboot an LXC container (counterpart to `reset_vm`; uses Proxmox `status/reboot`)
```http
POST /reboot_lxc
{"node": "pve", "vmid": "121"}
```

**delete_lxc**: Permanently delete an LXC container
```http
POST /delete_lxc
{"node": "pve", "vmid": "120", "force": false}
```

#### update_lxc_features
Update LXC feature flags after create (e.g. add `keyctl` for Docker-in-LXC).

**Parameters:**
- `node` (string, required)
- `vmid` (string, required)
- `features` (string, required): e.g. `nesting=1,keyctl=1` or `nesting=1,keyctl=1,fuse=1`

**Docker-in-LXC notes:**
- Typical features: `nesting=1,keyctl=1` (optional `fuse=1`)
- Proxmox often allows only `root@pam` to set features beyond `nesting` — API tokens may get 403 on `keyctl`
- Suggested flow: `create_lxc` → `update_lxc_features` (if needed) → `start_lxc` → `get_containers`

### Monitoring Tools

#### get_nodes
Lists all nodes in the Proxmox cluster.

**API Endpoint:** `POST /get_nodes`

**Example Response:**
```
🖥️ Proxmox Nodes

🖥️ pve-compute-01
  • Status: ONLINE
  • Uptime: ⏳ 156d 12h
  • CPU Cores: 64
  • Memory: 186.5 GB / 512.0 GB (36.4%)
```

#### get_node_status
Get detailed status of a specific node.

**Parameters:**
- `node` (string, required): Name of the node

**API Endpoint:** `POST /get_node_status`

#### get_vms
List all VMs across the cluster.

**API Endpoint:** `POST /get_vms`

#### get_storage
List available storage pools.

**API Endpoint:** `POST /get_storage`

#### get_cluster_status
Get overall cluster status and health.

**API Endpoint:** `POST /get_cluster_status`

#### execute_vm_command
Execute a command in a VM's console using QEMU Guest Agent.

**Parameters:**
- `node` (string, required): Name of the node where VM is running
- `vmid` (string, required): ID of the VM
- `command` (string, required): Command to execute

**API Endpoint:** `POST /execute_vm_command`

**Requirements:**
- VM must be running
- QEMU Guest Agent must be installed and running in the VM

## Open WebUI Integration

### Configure Open WebUI

1. Access your Open WebUI instance
2. Navigate to **Settings** → **Connections** → **OpenAPI**
3. Add new API configuration:

```json
{
  "name": "Proxmox MCP API Plus",
  "base_url": "http://your-server:8811",
  "api_key": "",
  "description": "Enhanced Proxmox Virtualization Management API"
}
```

### Natural Language VM Creation

Users can now request VMs using natural language:

- **"Can you create a VM with 1 cpu core and 2 GB ram with 10GB of storage disk"**
- **"Create a new VM for testing with minimal resources"**
- **"I need a development server with 4 cores and 8GB RAM"**

The AI assistant will automatically call the appropriate APIs and provide detailed feedback.

## Storage Type Support

### Intelligent Storage Detection

ProxmoxMCP Plus automatically detects storage types and selects appropriate disk formats:

#### LVM Storage (local-lvm, vm-storage)
- ✅ Format: `raw`
- ✅ High performance
- ⚠️ No cloud-init image support

#### File-based Storage (local, NFS, CIFS)
- ✅ Format: `qcow2`
- ✅ Cloud-init support
- ✅ Flexible snapshot capabilities

## Project Structure

```
ProxmoxMCP-Plus/
├── 📁 src/                          # Source code
│   └── proxmox_mcp/
│       ├── server.py                # Main MCP server implementation
│       ├── config/                  # Configuration handling
│       ├── core/                    # Core functionality
│       ├── formatting/              # Output formatting and themes
│       ├── tools/                   # Tool implementations
│       │   ├── vm.py               # VM management (create/power) 🆕
│       │   ├── container.py        # Container management 🆕
│       │   └── console/            # VM console operations
│       └── utils/                   # Utilities (auth, logging)
│
├── 📁 tests/                       # Unit test suite
├── 📁 test_scripts/                # Integration tests & demos
│   ├── README.md                   # Test documentation
│   ├── test_vm_power.py           # VM power management tests 🆕
│   ├── test_vm_start.py           # VM startup tests
│   ├── test_create_vm.py          # VM creation tests 🆕
│   └── test_openapi.py            # OpenAPI service tests
│
├── 📁 proxmox-config/              # Configuration files
│   └── config.json                # Server configuration
│
├── 📄 Configuration Files
│   ├── pyproject.toml             # Project metadata
│   ├── docker-compose.yml         # Docker orchestration
│   ├── Dockerfile                 # Docker image definition
│   └── requirements.in            # Dependencies
│
├── 📄 Scripts
│   ├── start_server.sh            # MCP server launcher
│   └── start_openapi.sh           # OpenAPI service launcher
│
└── 📄 Documentation
    ├── README.md                  # This file
    ├── VM_CREATION_GUIDE.md       # VM creation guide
    ├── OPENAPI_DEPLOYMENT.md      # OpenAPI deployment
    └── LICENSE                    # MIT License
```

## Testing

### Run Unit Tests
```bash
pytest
```

### Run Integration Tests
```bash
cd test_scripts

# Test VM power management
python test_vm_power.py

# Test VM creation
python test_create_vm.py

# Test OpenAPI service
python test_openapi.py
```

### API Testing with curl
```bash
# Test node listing
curl -X POST "http://your-server:8811/get_nodes" \
  -H "Content-Type: application/json" \
  -d "{}"

# Test VM creation
curl -X POST "http://your-server:8811/create_vm" \
  -H "Content-Type: application/json" \
  -d '{
    "node": "pve",
    "vmid": "300",
    "name": "test-vm",
    "cpus": 1,
    "memory": 2048,
    "disk_size": 10
  }'
```

## Production Security

### API Key Authentication
Set up secure API access:

```bash
export PROXMOX_API_KEY="your-secure-api-key"
export PROXMOX_MCP_CONFIG="/app/proxmox-config/config.json"
```

### Nginx Reverse Proxy
Example nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8811;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   netstat -tlnp | grep 8811
   # Change port if needed
   mcpo --port 8812 -- ./start_server.sh
   ```

2. **Configuration errors**
   ```bash
   # Verify config file
   cat proxmox-config/config.json
   ```

3. **Connection issues**
   ```bash
   # Test Proxmox connectivity
   curl -k https://your-proxmox:8006/api2/json/version
   ```

### View Logs
```bash
# View service logs
tail -f proxmox_mcp.log

# Docker logs
docker logs proxmox-mcp-api -f
```

## Status

- [x] `create_vm` / power tools / `delete_vm`
- [x] `create_lxc` with nesting/features
- [x] `get_containers` + LXC power / `delete_lxc` / `update_lxc_features`
- [x] LVM / file storage handling
- [x] Optional OpenAPI (`mcpo`, port 8811)

## Development

After activating your virtual environment:

- Run tests: `pytest`
- Format code: `black .`
- Type checking: `mypy .`
- Lint: `ruff .`

## License

MIT License

## Acknowledgments

Based on [ProxmoxMCP](https://github.com/RekklesNA/ProxmoxMCP-Plus) / [canvrno/ProxmoxMCP](https://github.com/canvrno/ProxmoxMCP). Continued for Cursor IDE + personal Proxmox use.
