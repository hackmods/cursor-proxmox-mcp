# Setup

Full first-run guide: [SETUP.md](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SETUP.md) in the repo.

## Cursor `mcp.json` (recommended)

```json
{
  "mcpServers": {
    "proxmox": {
      "command": "uvx",
      "args": ["--from", "C:/Users/YOU/Projects/cursor-proxmox-mcp", "cursor-proxmox-mcp"],
      "env": {
        "PROXMOX_MCP_CONFIG": "C:/Users/YOU/Projects/cursor-proxmox-mcp/proxmox-config/config.json"
      }
    }
  }
}
```

Prefer **only** `PROXMOX_MCP_CONFIG` (tokens in the JSON file / `${ENV}` interpolation). Do not put token secrets in committed files.

## After `git pull` — reload checklist

1. Settings → MCP → **Disable** proxmox → **Enable**.
2. Confirm tool count ~**155**. If still ~13–14 tools, fully quit Cursor and reopen (stale catalog).
3. Avoid bare `uvx proxmox-mcp-server` — that installs a **different** PyPI project.
4. Smoke: `get_nodes`, `get_version`, `get_containers`.

## Auth / Privilege Separation

Proxmox tokens default to **privsep=Yes**: ACL must be on `user@realm!tokenid`. Empty lists often mean missing token ACL — use `get_token_permissions`.

## Opt-in host SSH (LXC exec)

`execute_lxc_command` / runtime IPs need SSH **to the Proxmox node** for `pct exec` — not the same as guest `ssh_public_keys` inside a CT.

1. Install paramiko (`cursor-proxmox-mcp[ssh]`), put the public key in the node’s `authorized_keys`, set `ssh.enabled` + `private_key_path` (and `host_overrides` if API host ≠ node SSH IP).
2. Verify: `ssh -i <key> user@host "pct version"`.
3. **Reload MCP** after editing `config.json`.

Full checklist: [SETUP.md — SSH for LXC exec](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SETUP.md#ssh-for-lxc-exec-opt-in).
