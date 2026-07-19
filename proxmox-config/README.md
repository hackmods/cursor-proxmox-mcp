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
| `ssh.enabled` | optional | `true` to enable host SSH for `pct exec` (LXC shell / runtime IP). Default off. |
| `ssh.user` | if enabled | SSH user on the node (often `root` or a sudo-capable user that can run `pct`) |
| `ssh.port` | optional | SSH port (default `22`) |
| `ssh.private_key_path` | recommended | Absolute path to private key; agent/`look_for_keys` also tried |
| `ssh.host_overrides` | optional | Map `{ "pve1": "10.0.0.5" }` when API host ≠ node SSH address |
| `ssh.pct_path` | optional | Default `/usr/sbin/pct` |
| `ssh.timeout` | optional | Seconds (default `30`) |

## Privilege Separation

Proxmox tokens default to **Privilege Separation = Yes**: the token has **no** rights until you ACL `user@realm!tokenid`. Setting Privilege Separation to **No** inherits the parent user’s full permissions (lab shortcut).

Full walkthrough: [SETUP.md §1](../SETUP.md#1-create-a-proxmox-api-token).

## SSH + LXC exec (opt-in)

Proxmox has **no REST API** for LXC guest shell. `execute_lxc_command` and runtime IPs in `get_lxc_network` use host-side `pct exec` over SSH when `ssh.enabled` is true. Install the optional dependency: `pip install 'cursor-proxmox-mcp[ssh]'` (paramiko).

Without SSH, set a static `ip=` on create/update and use `get_lxc_network` / list configured IP only.

## Point Cursor at this file

Set env `PROXMOX_MCP_CONFIG` to the **absolute** path of `config.json` in your MCP server entry (see [SETUP.md](../SETUP.md)).
