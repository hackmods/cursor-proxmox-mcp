# proxmox-config

Copy `config.example.json` → `config.json` and fill in host + API token fields.

`config.json` is **gitignored**. Never commit secrets.

## Fields

| Path | Required | Notes |
|------|----------|--------|
| `proxmox.host` | yes | Hostname or IP only (no `https://`) |
| `proxmox.port` | yes | Usually `8006` |
| `proxmox.verify_ssl` | yes | `false` for lab self-signed; `true` with trusted certs |
| `proxmox.service` | yes | `PVE` for Proxmox VE |
| `auth.user` | yes | `user@realm` only — e.g. `mcp@pve` — **not** `user@realm!token` |
| `auth.token_name` | yes | Token id only — e.g. `cursor` |
| `auth.token_value` | yes | Secret UUID shown once at token creation |
| `logging.*` | optional | `DEBUG` while bringing MCP up; `INFO` after |
| `ssh.enabled` | optional | `true` to enable host SSH for `pct` (LXC shell / push / prepare / runtime IP). Default off. |
| `ssh.user` | if enabled | SSH user on the node (often `root` or a sudo-capable user that can run `pct`) |
| `ssh.port` | optional | SSH port (default `22`) |
| `ssh.private_key_path` | recommended | Absolute path to private key; agent/`look_for_keys` also tried |
| `ssh.host_overrides` | optional | Map node name → SSH address when API host ≠ node, e.g. `{ "pve": "192.168.0.23" }` |
| `ssh.pct_path` | optional | Default `/usr/sbin/pct` |
| `ssh.timeout` | optional | Seconds (default `120` for day-2 apt/npm/Docker; override with `PROXMOX_MCP_EXEC_TIMEOUT`) |

## Privilege Separation

Proxmox tokens default to **Privilege Separation = Yes**: the token has **no** rights until you ACL `user@realm!tokenid`. Setting Privilege Separation to **No** inherits the parent user’s full permissions (lab shortcut).

Full walkthrough: [SETUP.md §1](../SETUP.md#1-create-a-proxmox-api-token).

## SSH + LXC exec (opt-in)

Proxmox has **no REST API** for LXC guest shell. `execute_lxc_command`, `set_lxc_password`, `set_lxc_ssh_keys`, `prepare_lxc_for_docker`, `push_to_lxc` / `pull_from_lxc`, and runtime IPs in `get_lxc_network` use host-side `pct` over SSH when `ssh.enabled` is true. **paramiko is a core dependency** since 1.3.0 (`[ssh]` extra is an empty back-compat alias).

**Host SSH ≠ guest SSH.** Host SSH is MCP → Proxmox node → `pct`. Guest keys inside a CT (`ssh_public_keys` / `set_lxc_ssh_keys`) are separate.

Without host SSH, set a static `ip=` on create/update and use `get_lxc_network` / list configured IP only.

### Host trust (required when enabling SSH)

Editing `config.json` alone is not enough:

1. Install the matching **public** key on the node’s `authorized_keys` (lab: often `/root/.ssh/`).
2. Set `host_overrides` when the API host differs from the node SSH address, e.g. `"host_overrides": { "pve": "192.168.0.23" }` (key = Proxmox **node name**).
3. Verify: `ssh -i <private_key> user@<override-or-host> "pct version"`.
4. **Reload** the MCP server in Cursor — config is read at process start.

Full checklist (keygen, `authorized_keys`, firewall 22/tcp): [SETUP.md — SSH for LXC exec](../SETUP.md#ssh-for-lxc-exec-opt-in).

## Point Cursor at this file

Set env `PROXMOX_MCP_CONFIG` to the **absolute** path of `config.json` in your MCP server entry (see [SETUP.md](../SETUP.md)).
