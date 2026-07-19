# Setup Guide — Proxmox MCP in Cursor

Connect Cursor (or another MCP client) to your Proxmox VE cluster so you can query and manage infrastructure in natural language.

This guide walks through a home-lab style setup for **[hackmods/cursor-proxmox-mcp](https://github.com/hackmods/cursor-proxmox-mcp)** — a formal Cursor ↔ Proxmox integration with **128 tools** (VMs, LXC, storage, HA, firewall, access, replication, SDN, and more).

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

Tokens are the right way to authenticate MCP (and any automation) to Proxmox. You create them under a **user**; the token never uses that user’s password.

### Recommended: dedicated user + token

1. **Datacenter → Permissions → Users → Add**
   - User: e.g. `mcp@pve` (realm `pve`) or `mcp@pam`
   - Set a password (needed for UI login only; MCP uses the token)
2. **Datacenter → Permissions → Add** (ACL for the **user**)
   - Path: `/` (whole datacenter) or narrower (`/vms`, `/storage`, `/nodes/...`)
   - User: `mcp@pve`
   - Role: start with what you need (see [Roles for MCP](#roles-for-mcp) below)
3. **Datacenter → Permissions → API Tokens → Add**
   - User: `mcp@pve`
   - Token ID: e.g. `cursor` (this becomes `mcp@pve!cursor`)
   - **Privilege Separation:** leave **enabled (Yes)** for best practice — see below
   - Optional: expiration date
4. Click **Add**, then **copy the secret immediately** — Proxmox shows it once.
5. If Privilege Separation is **Yes**, grant ACLs to the **token** as well (next subsection).

Put into `config.json`:

| Config field | Example | Notes |
|--------------|---------|--------|
| `auth.user` | `mcp@pve` | User only — no `!token` |
| `auth.token_name` | `cursor` | Token ID only |
| `auth.token_value` | `uuid-secret` | The secret from the dialog |

Full token id in Proxmox is `user@realm!tokenid` (e.g. `mcp@pve!cursor`). This project’s config splits that into `user` + `token_name`.

### Privilege Separation (the gotcha)

When you create a token, Proxmox asks for **Privilege Separation**. Default is **Yes**.

| Setting | What it means |
|---------|----------------|
| **Yes** (default, recommended) | Token starts with **no** permissions of its own. You must add ACL entries for the **token** (`user@realm!tokenid`). Effective access = intersection of **user** ACLs ∩ **token** ACLs. Token can never do more than the user. |
| **No** | Token **inherits the user’s full permission set**. No separate token ACLs required. Same blast radius as leaking that user’s credentials. |

#### Why “Privilege Separation = No” feels like a bypass

If Privilege Separation stays **Yes** and you only gave roles to the **user**, the token authenticates but can do almost nothing (empty results, mysterious `401`/`403`, or `data: null`). Unchecking Privilege Separation makes things “just work” because the token suddenly has whatever the user has — including `root@pam`’s full admin if that’s the parent user.

That is a valid **lab shortcut**, not best practice. You traded a missing ACL step for “this token == this user.”

#### Best practice

1. Keep **Privilege Separation = Yes**.
2. Give the **user** the maximum the human/automation account should ever have.
3. Give the **token** only the roles MCP needs (often a subset).
4. Prefer a dedicated `mcp@pve` user over `root@pam` so a leaked token is not full cluster root.

**UI:** Datacenter → Permissions → Add → set **API Token** to `mcp@pve!cursor` (not the user) → Path `/` → Role e.g. `PVEAuditor` or `PVEVMAdmin`.

**CLI equivalent:**

```bash
# User (example)
pveum user add mcp@pve --password 'REDACTED'
pveum acl modify / -user mcp@pve -role PVEAdmin

# Token WITH privilege separation (default)
pveum user token add mcp@pve cursor --privsep 1
# Grant the TOKEN its own ACL (required when privsep=1)
pveum acl modify / -token 'mcp@pve!cursor' -role PVEAdmin

# Lab-only shortcut — token inherits all user perms (privsep off)
# pveum user token add mcp@pve cursor --privsep 0
```

### When Privilege Separation = No is OK

- Solo home lab, throwaway cluster, or first-time bring-up while you learn the tool surface.
- Parent user is already a **narrow** account (e.g. audit-only) so inheriting its perms is still limited.

Switch to privsep **Yes** + token ACLs before anything you care about surviving a leaked `config.json`.

### Roles for MCP

Match roles to what you want the agent to do. Assign them to the **token** when privsep is on (and to the user so the intersection is non-empty).

| Goal | Built-in role / privileges | Notes |
|------|----------------------------|--------|
| Read-only health / inventory | `PVEAuditor` | Safest default for daily chat |
| Create / manage VMs & LXCs | `PVEVMAdmin` or `PVEVMUser` + datastore rights | Needs template/ISO access on storage |
| Storage content / downloads | `Datastore.Audit`, `Datastore.AllocateSpace`, `Datastore.AllocateTemplate` | Often via `PVEDatastoreAdmin` |
| Broad lab automation | `PVEAdmin` on `/` for `mcp@pve!cursor` | Still better than `root@pam` token |
| HA / firewall / access admin | Often needs `Sys.Modify` / elevated roles | Many ops behave like full admin |

Split tokens if useful: one audit token (`PVEAuditor`) for health checks, one write token for create/migrate — both with privsep **Yes**.

Official reference: [Proxmox VE — User Management / API Tokens](https://pve.proxmox.com/pve-docs/chapter-pveum.html#pveum_tokens).

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
| Privilege Separation = Yes | Token gets its own ACLs; leak ≠ full user access |
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
| Auth works but empty data / odd 403 | Privilege Separation is **Yes** but the **token** has no ACL — grant roles to `user@realm!tokenid`, or (lab only) set Privilege Separation to **No** |
| 403 on HA / firewall / privileged ops | Token/user need a stronger role |
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
