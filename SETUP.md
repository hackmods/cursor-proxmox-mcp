# Setup Guide — Proxmox MCP in Cursor

Connect Cursor (or another MCP client) to your Proxmox VE cluster so you can query and manage infrastructure in natural language.

This guide walks through a home-lab style setup for **[hackmods/cursor-proxmox-mcp](https://github.com/hackmods/cursor-proxmox-mcp)** — a formal Cursor ↔ Proxmox integration with **155 tools** (VMs, LXC, storage, HA, firewall, access, replication, SDN, and more).

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

### Realms (`@pve` vs `@pam`)

| Realm | Typical use |
|-------|-------------|
| `user@pve` | Proxmox-only account (recommended for MCP). Password lives in PVE, not the Linux host. |
| `user@pam` | Linux PAM users (including `root@pam`). Convenient for labs; a leaked root token is full host+cluster admin. |

Match the realm in `auth.user` exactly. `mcp@pve` ≠ `mcp@pam`.

### Verify the token actually has rights

After creation (and after wiring MCP), confirm permissions three ways:

1. **UI:** Datacenter → Permissions — you should see rows for both the **user** and (if privsep=Yes) the **API Token** `user@realm!tokenid`.
2. **CLI:** `pveum user token permissions mcp@pve cursor` and `pveum acl list | grep mcp`
3. **In Cursor (once MCP is up):** ask *“Call `get_token_permissions` for userid `mcp@pve` and tokenid `cursor`, and also `get_permissions` for the current identity.”* Empty or tiny maps usually mean privsep=Yes with no ACL on `user@realm!tokenid`.

### Rotate / revoke

- **Revoke fast:** Datacenter → Permissions → API Tokens → remove the token (or disable the user).
- **Rotate:** create a new token → update `config.json` → restart MCP in Cursor → delete the old token.
- Prefer an **expiration date** on tokens used from laptops that leave the house.

### Proxmox limits that surprise people

- **Interactive consoles:** Proxmox documents that some VM/system **console** endpoints require a real user session and **cannot** be used via API token. This MCP still **mints** VNC/SPICE/termproxy *tickets* where the API allows; opening a full interactive console may still need UI/password auth depending on version and endpoint.
- **Guest agent exec** (`execute_vm_command`) needs the QEMU guest agent inside the VM — permissions alone are not enough.
- **LXC exec** (`execute_lxc_command`) needs opt-in **SSH + `pct exec`** on the node (Proxmox has no REST LXC exec API). See [SSH for LXC exec](#ssh-for-lxc-exec-opt-in) below.
- **`keyctl` / nested features on LXC** often need privileges beyond a narrow VM role (often elevated / historically `root@pam`). The tool does **not** silently strip unsupported flags — on 403 you get structured `feature_acl_denied` with `recommended_fallback: crun`. Use `prepare_lxc_for_docker(docker_mode=auto|crun)` or `pct_set_lxc` when host SSH is root-capable.

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

### Option A — PyPI + uvx (no clone)

After a GitHub Release publishes the package:

```bash
uvx cursor-proxmox-mcp
```

You still need a `config.json` somewhere (copy from [`proxmox-config/config.example.json`](proxmox-config/config.example.json) in the repo or the gist you keep for the lab). Point Cursor’s `PROXMOX_MCP_CONFIG` at that absolute path.

### Option B — Clone (developing / offline)

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

Do **not** commit `config.json` — it holds credentials. It is gitignored (`proxmox-config/config.json`). Keep using `config.example.json` as the template. See also [`proxmox-config/README.md`](proxmox-config/README.md).

### Network / SSL checklist

| Check | Detail |
|-------|--------|
| Reachability | From the machine running Cursor: `https://HOST:8006` must open (or at least TCP 8006). VPN/Tailscale if the cluster is remote. |
| Host firewall | Allow your client IP to port **8006/tcp** on the Proxmox node(s). |
| `verify_ssl` | Lab self-signed → `false`. Production with a trusted cert (ACME) → `true`. |
| Which host? | Any cluster node’s management IP usually works; prefer a stable VIP/DNS name if you have one. |

### Common config mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| `user` set to `mcp@pve!cursor` | Auth errors | Split: `user=mcp@pve`, `token_name=cursor` |
| `token_value` is the token **id** not the secret | 401 | Paste the UUID secret from the create dialog |
| Relative `PROXMOX_MCP_CONFIG` in Cursor | Server can’t find file | Use an **absolute** path |
| Backslashes only on Windows paths in JSON | Flaky startup | Prefer `C:/Users/...` forward slashes |
| Edited `config.example.json` only | Still using empty/defaults | Copy to `config.json` and edit that |

### SSH for LXC exec (opt-in)

Proxmox **does not** expose a REST API to run shell inside LXC (unlike QEMU guest-agent). `execute_lxc_command`, `set_lxc_password`, `set_lxc_ssh_keys`, `prepare_lxc_for_docker`, `configure_lxc_dns`, `pct_set_lxc`, `push_to_lxc` / `pull_from_lxc`, and runtime IPs from `get_lxc_network` use host-side `pct` over SSH from the machine running Cursor. Call `get_mcp_capabilities` after reload to verify.

**Host SSH ≠ guest SSH.** This section is about SSH **to the Proxmox node** so MCP can run `pct`. Guest access into a CT (`ssh root@<ct-ip>`) uses `ssh_public_keys` on `create_lxc` or `set_lxc_ssh_keys` — that is separate and does **not** replace host SSH below.

#### Checklist

1. **Paramiko is a core dependency** (since 1.3.0). Plain `uvx --from <checkout> cursor-proxmox-mcp` includes it. The `[ssh]` extra remains as an empty back-compat alias.

2. **Generate a dedicated keypair** on the machine that runs Cursor (lab example):

   ```powershell
   ssh-keygen -t ed25519 -f $env:USERPROFILE\.ssh\proxmox_mcp_ed25519 -C "cursor-proxmox-mcp"
   ```

3. **Install the public key on each Proxmox node** the MCP will use. From a shell that already has host access (console, existing SSH, etc.):

   ```bash
   mkdir -p /root/.ssh && chmod 700 /root/.ssh
   echo 'ssh-ed25519 AAAA... cursor-proxmox-mcp' >> /root/.ssh/authorized_keys
   chmod 600 /root/.ssh/authorized_keys
   ```

   Paste the contents of `proxmox_mcp_ed25519.pub` (not the private key). Lab setups often use `root`; production should prefer a dedicated user that can run `/usr/sbin/pct` (sudoers restricted to `pct` is better than full root).

4. **Allow SSH from the Cursor host** — node firewall must permit **22/tcp** (or your custom `ssh.port`) from that client, in addition to **8006** for the API.

5. **Add `ssh` to `config.json`.** Use `host_overrides` when the API `proxmox.host` is not the address you SSH to (common: API VIP/DNS vs node management IP, or node name `pve` ≠ `192.168.x.x`):

   ```json
   "ssh": {
     "enabled": true,
     "user": "root",
     "port": 22,
     "private_key_path": "C:/Users/YOU/.ssh/proxmox_mcp_ed25519",
     "host_overrides": {
       "pve": "192.168.0.23"
     },
     "pct_path": "/usr/sbin/pct",
     "timeout": 120
   }
   ```

   | Field | Meaning |
   |-------|---------|
   | `enabled` | Must be `true` or LXC exec/push/prepare tools refuse with a clear error |
   | `private_key_path` | Absolute path to the **private** key (forward slashes on Windows are fine) |
   | `host_overrides` | Map Proxmox **node name** → SSH hostname/IP. If omitted/empty, MCP SSHs to `proxmox.host` |
   | `user` / `port` / `pct_path` / `timeout` | Defaults: root / 22 / `/usr/sbin/pct` / **120**. Override with `PROXMOX_MCP_EXEC_TIMEOUT` for one-off long installs |

6. **Verify outside Cursor** before expecting MCP tools to work:

   ```powershell
   ssh -i $env:USERPROFILE\.ssh\proxmox_mcp_ed25519 root@192.168.0.23 "pct version"
   ```

   Use the override IP (or `proxmox.host` if overrides are empty). Success prints a `pct` version line.

7. **Reload the Proxmox MCP server in Cursor** (Disable → Enable, or fully quit Cursor). Config is read at process start — editing `config.json` alone does nothing until reload.

Without host SSH, prefer static `ip=` on `create_lxc` / `update_lxc_config`, then `get_lxc_network` for the configured address only. Always call `wait_for_task` after create before start (or pass `wait=true` on create). Field reference: [`proxmox-config/README.md`](proxmox-config/README.md).

### Smoke-test outside Cursor

From the repo root:

```bash
# Windows paths work with forward slashes in the env value
uvx --from . cursor-proxmox-mcp
```

Or with an explicit config path:

```powershell
$env:PROXMOX_MCP_CONFIG = "C:\Users\YOU\Projects\cursor-proxmox-mcp\proxmox-config\config.json"
uvx --from . cursor-proxmox-mcp
```

The first run downloads dependencies into an isolated env. If the process starts without an immediate auth error, you’re ready for Cursor.

---

## 4. Wire it into Cursor

Open Cursor MCP settings, or edit the MCP config file:

| Scope | Path |
|-------|------|
| **User (global)** — all projects | Windows: `C:\Users\<you>\.cursor\mcp.json` · macOS/Linux: `~/.cursor/mcp.json` |
| **Project** — this repo only | `.cursor/mcp.json` in the workspace (optional; use if you don’t want Proxmox tools in every chat) |

Prefer **project** MCP config if the token is lab-only and you work on many unrelated repos.

### Recommended — uvx from a local checkout

```json
{
  "mcpServers": {
    "proxmox": {
      "command": "uvx",
      "args": [
        "--from",
        "C:/Users/YOU/Projects/cursor-proxmox-mcp",
        "cursor-proxmox-mcp"
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

> **Note vs older articles:** some guides set `PROXMOX_HOST`, `PROXMOX_TOKEN_VALUE`, etc. directly in `mcp.json`. This project expects **`PROXMOX_MCP_CONFIG`** pointing at the JSON file above.

### After `git pull` — live Cursor MCP reload checklist

Cursor caches the MCP process and tool list. After pulling new tools:

1. Save any open work; note your `mcp.json` still points at this checkout (or at `uvx cursor-proxmox-mcp` if you switched to PyPI).
2. Open **Cursor Settings → MCP**.
3. Find the **proxmox** server → **Disable** → wait until it shows disconnected → **Enable** (or use Restart if shown).
4. Confirm the tool count matches the README inventory (~155). If Cursor still shows ~13–14 tools after Enable, the catalog snapshot is stale — **fully quit Cursor** (all windows) and reopen. Prefer `uvx --from <checkout> cursor-proxmox-mcp` with only `PROXMOX_MCP_CONFIG` (avoid leftover `uvx proxmox-mcp-server`, which is a different PyPI project).
5. Smoke in chat: *“Call `get_nodes` and `get_version`.”* Then *“Call `get_containers` and `get_token_permissions` for my MCP user/token.”*
6. If you use `uvx --from <checkout>`, a restart is enough (uvx rebuilds the env). If you use an editable `pip install -e .`, reinstall after large dependency changes: `uv pip install -e ".[dev]"`.

### Other MCP clients

**Claude Desktop** can use the same server; see [`claude_desktop_config.json`](claude_desktop_config.json) in the repo as a starting point. Point `PROXMOX_MCP_CONFIG` at an absolute `config.json` and prefer `uvx --from <repo> cursor-proxmox-mcp` over bare `python` when possible.

---

## 5. Try it — example prompts

Once the green MCP indicator is on, ask in chat. Wiki copy-paste starters (including DevOps prompts): [Example prompts](https://github.com/hackmods/cursor-proxmox-mcp/wiki/Example-prompts). Examples that map well to this server’s tools:

### Cluster health / discovery

> Using the Proxmox MCP server, give me interesting information about my cluster and cluster health — nodes, storage, and workload distribution.

Useful tools behind the scenes: `get_cluster_status`, `get_nodes`, `get_node_status`, `get_storage`, `get_cluster_resources`, SDN list tools.

### Capacity and leftovers

> Which node currently has the most available memory?  
> Which VMs have been powered off the longest?  
> Show me snapshots older than two weeks.

### Create an LXC (same idea as the Virtualization Howto demo)

> Download the Ubuntu LXC template if needed, then create a new container on node `pve1` on bridge `vmbr0` with 2GB RAM, set the root password, and start it.

**Prefer `provision_lxc`** when host SSH is configured (one call: create→start→optional SSH bootstrap→IP). Manual flow:

1. `get_next_vmid`
2. `list_os_templates` (or `download_url_to_storage` with `content=vztmpl` if missing)
3. `list_node_networks`
4. `create_lxc` (optional `ostemplate_filter=ubuntu`; prefer `ssh_public_keys`; optional `onboot`/`description`/`tags`)
5. `wait_for_task` → `start_lxc` → `get_lxc_network`

Note: create-time `password` alone often does **not** enable guest password SSH on Debian templates — use `provision_lxc` / `configure_lxc_ssh` or keys. For HTTP checks, prefer `wget -qO-` (curl often missing).

### Provision a nested Docker LXC (end-to-end)

`create_lxc` only provisions an OS template. Nesting/features do **not** install Docker or publish :80. Use `prepare_lxc_for_docker` for Proxmox-side prep (D24): **Path A** `nesting+keyctl` + stock runc when ACL allows; **Path B** `docker_mode=auto|crun` installs modern **crun** as Docker `default-runtime` when keyctl is denied (typical privsep tokens). Smoke with **`docker run`**, not merely `docker --version`. Do not claim Docker-ready with nesting-only + stock runc.

**Prerequisites:** config `ssh.enabled=true` + host key trust (paramiko is core). Prefer `ssh_public_keys` on create for guest SSH. Call `get_mcp_capabilities` after reload.

Example prompt:

> Using Proxmox MCP tools only: on node `pve1`, pick the next free VMID, list OS templates and prefer Ubuntu if available, create an unprivileged LXC with `docker_ready=true`, `nameserver=8.8.8.8 9.9.9.9`, bridge `vmbr0`, and my OpenSSH public key via `ssh_public_keys`. Wait for create with `wait_for_task`, start the container, confirm IP with `get_lxc_network`, optionally `configure_lxc_dns`, call `prepare_lxc_for_docker(docker_mode=auto, install_docker=true, smoke_test=true)`, **stop then start** the CT if restart_required, and re-run smoke if needed. Prefer crun fallback automatically if keyctl is denied. Use `pct_set_lxc` only when REST cannot set features/nameserver but host SSH is root-capable.

Expected tool sequence:

1. `get_mcp_capabilities` (optional probe_node) → `get_nodes` / `get_next_vmid`
2. `list_os_templates` (`filter=ubuntu`) → optional `download_url_to_storage`
3. `create_lxc` with **`docker_ready=true`**, prefer **`nameserver=8.8.8.8 9.9.9.9`**, **`ssh_public_keys=...`**
4. `wait_for_task` on the create UPID
5. `start_lxc` → `get_lxc_network` → optional `configure_lxc_dns`
6. If password SSH needed: `set_lxc_password(..., enable_password_ssh=true)`
7. `prepare_lxc_for_docker(docker_mode=auto, install_docker=true?, smoke_test=true?)` → if `restart_required`: `stop_lxc` → `start_lxc` (full stop/start, not reboot alone)
8. Confirm status `docker_path` is `keyctl` or `crun`; smoke `docker run --rm hello-world`
9. `push_to_lxc` for app tarball → extract/build via `execute_lxc_command`

If host `lxc-pve` is older than **6.0.5-2**, prepare applies the dual AppArmor workaround. Prefer upgrading the host. Do **not** set bare `lxc.apparmor.profile: unconfined` without the `/dev/null` AppArmor bind.

**If you still see HTTP 501 on `/lxc/.../exec`:** Cursor is running a pre-1.1.1 MCP — Disable/Enable proxmox MCP or `uvx --from <checkout> cursor-proxmox-mcp`, then enable config `ssh`.

### Create a blank VM with ISO + cloud-init

> List ISOs on the cluster, create VM with the Ubuntu ISO attached, boot order CDROM first, cloud-init user `ubuntu` + my SSH public key, bridge `vmbr0`, then `wait_for_task` and report the UPID result.

Tools: `list_isos` → `get_next_vmid` → `create_vm` (`iso`, `ciuser`, `sshkeys`, `bridge`) → `wait_for_task`.

### Ops beyond “list stuff”

> Create a snapshot of VM 105 named `pre-upgrade`.  
> List failed or recent tasks on the cluster.  
> Show SDN zones and apply pending SDN config if safe.

Not everything the model *suggests* is available via the Proxmox API (host package upgrades are a common limitation). Prefer prompts that match [registered tools](README.md#mcp-tools); see [API coverage](docs/api-coverage.md) for gaps.

---

## 6. Suggested agent workflow

For create / change tasks, steer the agent toward this order:

1. `get_next_vmid` → `list_os_templates` / `list_isos` → `list_node_networks`
2. `provision_lxc` (preferred one-shot small CT) or `create_lxc` / `create_vm` → `wait_for_task` → start
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
| Rotate / expire tokens | Revoke in UI if laptop lost; set token expiration when practical |
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
| `get_permissions` / `get_token_permissions` nearly empty | Same as above — fix token ACL / privsep (ACL must target `user@realm!tokenid`) |
| 403 on HA / firewall / privileged ops | Token/user need a stronger role |
| SSL / connection errors | Ping `:8006`; set `verify_ssl` correctly; check host firewall / VPN |
| Tools missing after pull | Follow [MCP reload checklist](#after-git-pull--live-cursor-mcp-reload-checklist) |
| `ModuleNotFoundError: proxmox_mcp` | Prefer `uvx cursor-proxmox-mcp` or `uvx --from <repo>`; or set `PYTHONPATH` to `.../src` |
| Green MCP but agent never calls tools | Explicitly say “use the Proxmox MCP tools”; confirm tool list is long (~155) in Cursor MCP settings |
| Green MCP but only ~13–14 tools | Stale Cursor catalog or wrong package (`uvx proxmox-mcp-server` ≠ this repo). Disable/Enable proxmox, quit Cursor fully, use `uvx --from <checkout> cursor-proxmox-mcp` |
| Host SSH auth failed / permission denied | Public key missing on the **node** `authorized_keys` (not guest CT keys). Verify `ssh -i <key> user@host "pct version"` — see [SSH for LXC exec](#ssh-for-lxc-exec-opt-in) |
| Enabled `ssh` in config but tools still say not configured | Reload MCP (config is process-start only); confirm `ssh.enabled: true` and paramiko/`[ssh]` extra |
| `pct` SSH timeout / wrong host | Set `host_overrides` (node name → SSH IP); allow **22/tcp** from the Cursor host |

Local verification:

```powershell
.\scripts\ci-local.ps1
```

```bash
./scripts/ci-local.sh
```

---

## What’s next

**Product roadmap (what we build next in this repo):** [.cursor/research/next-expansion.md](.cursor/research/next-expansion.md)

- **Phase D (agent QOL):** `wait_for_task`, richer create (ISO / cloud-init / net), token ACL smoke, optional PyPI
- **Phase C (deferred):** SDN write, ACME order, Ceph, cluster join, websocket console proxy

**Things you can do with the MCP today:**

- Daily health prompts (cluster status, storage pressure, odd SDN / HA state)
- Template → clone → configure flows for disposable lab VMs
- More MCP servers alongside Proxmox (Docker, GitHub, monitoring) as your home-lab agent surface grows

Project docs:

- [README](README.md) — tool inventory and install paths
- [API coverage](docs/api-coverage.md) — what’s implemented vs planned + knowledge pointers
- [Next expansion](.cursor/research/next-expansion.md) — Phase D / C roadmap and insights
- Research matrix: [`.cursor/research/proxmox-api-coverage.md`](.cursor/research/proxmox-api-coverage.md)
- Decisions: [`.cursor/research/decisions.md`](.cursor/research/decisions.md)

External read: [I Connected AI to My Proxmox Cluster Using MCP…](https://www.virtualizationhowto.com/2026/07/i-connected-ai-to-my-proxmox-cluster-using-mcp-and-it-was-better-than-i-expected/) (Virtualization Howto).
