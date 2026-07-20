# Setup

Full first-run guide: [SETUP.md](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SETUP.md) in the repo. This page is the short living checklist for Cursor + the MCP connector.

## Install paths

### Published (PyPI)

```bash
uvx cursor-proxmox-mcp
```

Cursor `mcp.json`:

```json
{
  "mcpServers": {
    "proxmox": {
      "command": "uvx",
      "args": ["cursor-proxmox-mcp"],
      "env": {
        "PROXMOX_MCP_CONFIG": "C:/Users/YOU/proxmox-config/config.json"
      }
    }
  }
}
```

### Local checkout (dev)

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

Prefer **only** `PROXMOX_MCP_CONFIG` (tokens in the JSON file / `${ENV}` interpolation). Do not put token secrets in committed files. Example schema: [`proxmox-config/README.md`](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/proxmox-config/README.md).

> Avoid bare `uvx proxmox-mcp-server` — that installs a **different** PyPI project.

## After `git pull` — reload checklist

1. Settings → MCP → **Disable** proxmox → **Enable**.
2. Confirm tool count ~**171**. If still ~13–14 tools or missing day-2 tools (`push_to_lxc`, `deploy_node_app`), fully quit Cursor and reopen (stale catalog). Call `get_mcp_capabilities` after reload.
3. Smoke: `get_nodes`, `get_version`, `get_containers` / `get_vms`.

## Auth / Privilege Separation

Proxmox tokens default to **privsep=Yes**: ACL must be on `user@realm!tokenid`. Empty lists often mean missing token ACL — use `get_token_permissions`.

## Opt-in host SSH (LXC exec)

`execute_lxc_command` / runtime IPs need SSH **to the Proxmox node** for `pct exec` — not the same as guest `ssh_public_keys` inside a CT.

1. Install paramiko (`pip install 'cursor-proxmox-mcp[ssh]'` or editable `[ssh]` extra), put the public key in the node’s `authorized_keys`, set `ssh.enabled` + `private_key_path` (and `host_overrides` if API host ≠ node SSH IP).
2. Verify: `ssh -i <key> user@host "pct version"`.
3. **Reload MCP** after editing `config.json`.

Full checklist: [SETUP.md — SSH for LXC exec](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SETUP.md#ssh-for-lxc-exec-opt-in).

## Next

- [Example prompts](Example-prompts) — copy-paste starters + DevOps  
- [Tools](Tools) — full inventory  
- [Recipes](Recipes) — create / Docker / ACL playbooks  
- [Troubleshooting](Troubleshooting)
