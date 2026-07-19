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

## Privilege Separation

Proxmox tokens default to **Privilege Separation = Yes**: the token has **no** rights until you ACL `user@realm!tokenid`. Setting Privilege Separation to **No** inherits the parent user’s full permissions (lab shortcut).

Full walkthrough: [SETUP.md §1](../SETUP.md#1-create-a-proxmox-api-token).

## Point Cursor at this file

Set env `PROXMOX_MCP_CONFIG` to the **absolute** path of `config.json` in your MCP server entry (see [SETUP.md](../SETUP.md)).
