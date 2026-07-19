# Setup Guide — Proxmox MCP in Cursor

Connect Cursor (or another MCP client) to your Proxmox VE cluster so you can query and manage infrastructure in natural language.

This guide walks through a home-lab style setup for **[hackmods/cursor-proxmox-mcp](https://github.com/hackmods/cursor-proxmox-mcp)** — a formal Cursor ↔ Proxmox integration with **120+ tools** (VMs, LXC, storage, HA, firewall, access, replication, SDN, and more).

Inspired by Brandon Lee’s walkthrough on [Virtualization Howto](https://www.virtualizationhowto.com/2026/07/i-connected-ai-to-my-proxmox-cluster-using-mcp-and-it-was-better-than-i-expected/) (July 2026). That article used an earlier PyPI package with env-var config; this repo uses a **JSON config file** and a much broader tool surface. Steps below match **this** project.

---

## What you’re building

[MCP (Model Context Protocol)](https://modelcontextprotocol.io/) is a standard way for AI agents to call external tools and live APIs. An MCP server sits between the agent and Proxmox’s REST API:

- Without MCP: the model can *explain* how to create a VM.
- With MCP: the agent can *call* Proxmox — list nodes, create LXCs, check tasks, apply SDN, and more — within the permissions of your API token.

Proxmox is a strong fit because nearly everything you do in the UI already goes through that API (Terraform, Ansible, scripts, third-party tools). MCP is just another API consumer — driven by chat instead of code.

---

## Prerequisites

| Requirement | Notes |
|-------------|--------|
| Proxmox VE | Single node or cluster; API reachable on port **8006** |
| [uv](https://github.com/astral-sh/uv) | Recommended runner for Cursor (`uvx`) |
| Cursor | Settings → MCP (or `~/.cursor/mcp.json`) |
| API token | Dedicated token; prefer least privilege (see [Security](#security)) |

Optional: Python 3.10+ if you prefer `pip` / editable install instead of `uvx`.

---

## 1. Create a Proxmox API token

1. In the Proxmox UI: **Datacenter → Permissions → API Tokens**.
2. Create a token for a dedicated user (or `root@pam` for full admin — home lab only).
3. Copy the **token ID** (user + token name) and **secret** once — the secret is shown only at creation.
4. Assign roles that match what you want the agent to do, for example:
   - Read / explore: `PVEAuditor` or custom roles with `Sys.Audit`, `VM.Audit`, `Datastore.Audit`
   - Create VMs / LXCs: `VM.Allocate`, `Datastore.AllocateSpace`, `Datastore.AllocateTemplate`
   - HA / firewall / access admin: often needs elevated roles (many ops effectively require `root@pam`)

Least privilege is strongly recommended: a token that can only audit is fine for health checks; create a second token for write operations if you want a safer daily-driver.

---

## 2. Install uv

**Windows (PowerShell):**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Or: `winget install astral-sh.uv` / `pip install uv`.

**Linux / macOS:** see [astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/).

Verify:

```bash
uv --version
```

---

## 3. Get the server and write config

### Clone (recommended while developing / before PyPI publish)

```bash
git clone https://github.com/hackmods/cursor-proxmox-mcp.git
cd cursor-proxmox-mcp
cp proxmox-config/config.example.json proxmox-config/config.json
```

Edit `proxmox-config/config.json`:

```json
{
  "proxmox": {
    "host": "192.168.1.10",
    "port": 8006,
    "verify_ssl": false,
    "service": "PVE"
  },
  "auth": {
    "user": "mcp@pve",
    "token_name": "cursor",
    "token_value": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "proxmox_mcp.log"
  }
}
```

| Field | Meaning |
|-------|---------|
| `host` | Proxmox hostname or IP (no `https://`) |
| `port` | Usually `8006` |
| `verify_ssl` | `false` for lab self-signed certs; `true` in production with a real cert |
| `user` | Proxmox user, e.g. `mcp@pve` or `root@pam` |
| `token_name` | Token name only (not `user!token`) |
| `token_value` | Secret from token creation |

Do **not** commit `config.json` — it holds credentials. Keep using `config.example.json` as the template.

### Smoke-test outside Cursor

From the repo root:

```bash
# Windows paths work with forward slashes in the env value
uvx --from . proxmox-mcp-server
```

Or with an explicit config path:

```powershell
$env:PROXMOX_MCP_CONFIG = "C:\Users\YOU\Projects\cursor-proxmox-mcp\proxmox-config\config.json"
uvx --from . proxmox-mcp-server
```

The first run downloads dependencies into an isolated env. If the process starts without an immediate auth error, you’re ready for Cursor.

---

## 4. Wire it into Cursor

Open Cursor MCP settings, or edit the global MCP file:

- Windows: `C:\Users\<you>\.cursor\mcp.json`
- macOS / Linux: `~/.cursor/mcp.json`

### Recommended — uvx from a local checkout

```json
{
  "mcpServers": {
    "proxmox": {
      "command": "uvx",
      "args": [
        "--from",
        "C:/Users/YOU/Projects/cursor-proxmox-mcp",
        "proxmox-mcp-server"
      ],
      "env": {
        "PROXMOX_MCP_CONFIG": "C:/Users/YOU/Projects/cursor-proxmox-mcp/proxmox-config/config.json"
      }
    }
  }
}
```

Use **absolute paths** and forward slashes. After saving, enable the **proxmox** server in Cursor Settings → MCP. A green status and a long tool list mean it’s connected.

### Alternative — editable Python install

```bash
cd cursor-proxmox-mcp
uv venv
uv pip install -e ".[dev]"
```

```json
{
  "mcpServers": {
    "proxmox": {
      "command": "python",
      "args": ["-m", "proxmox_mcp.server"],
      "cwd": "C:/Users/YOU/Projects/cursor-proxmox-mcp",
      "env": {
        "PROXMOX_MCP_CONFIG": "C:/Users/YOU/Projects/cursor-proxmox-mcp/proxmox-config/config.json",
        "PYTHONPATH": "C:/Users/YOU/Projects/cursor-proxmox-mcp/src"
      }
    }
  }
}
```

Restart the MCP server in Cursor after `git pull` so new tools appear.

> **Note vs older articles:** some guides set `PROXMOX_HOST`, `PROXMOX_TOKEN_VALUE`, etc. directly in `mcp.json`. This project expects **`PROXMOX_MCP_CONFIG`** pointing at the JSON file above.

---

## 5. Try it — example prompts

Once the green MCP indicator is on, ask in chat. Examples that map well to this server’s tools:

### Cluster health / discovery

> Using the Proxmox MCP server, give me interesting information about my cluster and cluster health — nodes, storage, and workload distribution.

Useful tools behind the scenes: `get_cluster_status`, `get_nodes`, `get_node_status`, `get_storage`, `get_cluster_resources`, SDN list tools.

### Capacity and leftovers

> Which node currently has the most available memory?  
> Which VMs have been powered off the longest?  
> Show me snapshots older than two weeks.

### Create an LXC (same idea as the Virtualization Howto demo)

> Download the Ubuntu LXC template if needed, then create a new container on node `pve1` on bridge `vmbr0` with 2GB RAM, set the root password, and start it.

Typical tool flow:

1. `get_next_vmid`
2. `get_storage_content` / download template if missing
3. `list_node_networks`
4. `create_lxc`
5. `get_task_status` → `start_lxc` (or equivalent power tool)

### Ops beyond “list stuff”

> Create a snapshot of VM 105 named `pre-upgrade`.  
> List failed or recent tasks on the cluster.  
> Show SDN zones and apply pending SDN config if safe.

Not everything the model *suggests* is available via the Proxmox API (host package upgrades are a common limitation). Prefer prompts that match [registered tools](README.md#mcp-tools); see [API coverage](docs/api-coverage.md) for gaps.

---

## 6. Suggested agent workflow

For create / change tasks, steer the agent toward this order:

1. `get_next_vmid` → `get_storage_content` (templates / ISOs) → `list_node_networks`
2. `create_lxc` / `create_vm` → `get_task_status`
3. `create_snapshot` before risky config changes → then update / power tools
4. Migrate, HA, firewall, access, and replication only when you explicitly need them

Full inventory: [README — MCP tools](README.md#mcp-tools).

---

## Security

Treat the MCP server like any other admin interface into the cluster.

| Practice | Why |
|----------|-----|
| Dedicated API token | Easy to revoke; audit separately from your UI login |
| Least privilege roles | A read-only token can’t wipe guests by accident |
| Know what leaves the box | Cloud models may see tool outputs (hostnames, VM names, logs). Local LLMs keep more in-lab |
| No secrets in chat | Put tokens in `config.json` / env, not in prompts |
| Lab first | Build trust on non-prod before pointing at production |

Home labs are ideal for learning where AI+MCP helps (health checks, template clones, boring lookups) and where you still want a human (destructive deletes, firewall cuts, cluster join).

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `spawn uvx ENOENT` | Install uv; restart Cursor so `PATH` updates |
| `PROXMOX_MCP_CONFIG ... must be set` | Set `env.PROXMOX_MCP_CONFIG` to the absolute path of `config.json` |
| Auth / 401 | Check `user`, `token_name`, and `token_value`; confirm token isn’t disabled |
| 403 on HA / firewall / privileged ops | Token needs a stronger role |
| Tools missing after pull | Restart the **proxmox** MCP server in Cursor |
| `ModuleNotFoundError: proxmox_mcp` | Prefer `uvx --from <repo>`; or set `PYTHONPATH` to `.../src` |

Local verification:

```powershell
.\scripts\ci-local.ps1
```

```bash
./scripts/ci-local.sh
```

---

## What’s next

- Daily health prompts (cluster status, storage pressure, odd SDN / HA state)
- Template → clone → configure flows for disposable lab VMs
- More MCP servers alongside Proxmox (Docker, GitHub, monitoring) as your home-lab agent surface grows

Project docs:

- [README](README.md) — tool inventory and install paths
- [API coverage](docs/api-coverage.md) — what’s implemented vs planned
- Research matrix: [`.cursor/research/proxmox-api-coverage.md`](.cursor/research/proxmox-api-coverage.md)

External read: [I Connected AI to My Proxmox Cluster Using MCP…](https://www.virtualizationhowto.com/2026/07/i-connected-ai-to-my-proxmox-cluster-using-mcp-and-it-was-better-than-i-expected/) (Virtualization Howto).
