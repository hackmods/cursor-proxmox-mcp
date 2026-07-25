# Elevated mode & pipeline config

Config note for **v1.9.0+** (D31): dual credentials, Cursor auto-approve, and day-2 deploy pipelines. Full detail lives in [SETUP.md](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SETUP.md); field reference in [`proxmox-config/README.md`](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/proxmox-config/README.md).

There is no runtime “elevate” MCP tool. Write power comes from the Proxmox token ACL (and optional host SSH). This page covers how to **configure** elevated access and reduce Cursor approval prompts.

## Choose a pattern

| Pattern | When to use | How |
|---------|-------------|-----|
| **Single broad token** | Solo lab, already `PVEAdmin` on the token | Keep one `auth` block; skip `auth_write` |
| **In-process `auth_write` (D31)** | One MCP server; primary + elevated write token | Add `auth_write` in the same `config.json` |
| **Dual MCP servers** | Want Cursor to auto-approve audit only | `proxmox-audit` + `proxmox-write` with separate configs |

All tokens: **Privilege Separation = Yes** and ACL on `user@realm!tokenid` (not only the user). Verify with `get_token_permissions` / `get_permissions`. Call `get_mcp_capabilities` after reload — look for `dual_auth` when using `auth_write`.

## 1. In-process elevated mode (`auth_write`)

Optional second credential in `config.json`. When set, the MCP process uses the **write** token for Proxmox API calls (mutations succeed under the elevated identity). Omit / `null` = single-token mode (unchanged).

```json
{
  "proxmox": {
    "host": "192.168.0.23",
    "port": 8006,
    "verify_ssl": false,
    "service": "PVE"
  },
  "auth": {
    "user": "mcp@pve",
    "token_name": "audit",
    "token_value": "${PROXMOX_TOKEN_AUDIT}"
  },
  "auth_write": {
    "user": "mcp@pve",
    "token_name": "write",
    "token_value": "${PROXMOX_TOKEN_WRITE}"
  },
  "ssh": {
    "enabled": true,
    "user": "root",
    "private_key_path": "C:/Users/YOU/.ssh/proxmox_mcp",
    "host_overrides": { "pve": "192.168.0.23" },
    "timeout": 120
  },
  "logging": { "level": "INFO", "tool_calls": true }
}
```

Proxmox side (example):

```bash
# Narrow primary (optional)
pveum user token add mcp@pve audit --privsep 1
pveum acl modify / -token 'mcp@pve!audit' -role PVEAuditor

# Elevated write
pveum user token add mcp@pve write --privsep 1
pveum acl modify / -token 'mcp@pve!write' -role PVEAdmin
```

Point Cursor `PROXMOX_MCP_CONFIG` at this file, **reload MCP**, then:

> Call `get_mcp_capabilities`. Confirm `dual_auth: True` and `auth_write_identity`.

## 2. Dual MCP servers (audit + write)

Safer when you want Cursor to auto-run inventory but still prompt on writes:

```json
{
  "mcpServers": {
    "proxmox-audit": {
      "command": "uvx",
      "args": ["--from", "C:/Users/YOU/Projects/cursor-proxmox-mcp", "cursor-proxmox-mcp"],
      "env": {
        "PROXMOX_MCP_CONFIG": "C:/Users/YOU/Projects/cursor-proxmox-mcp/proxmox-config/config.audit.json"
      }
    },
    "proxmox-write": {
      "command": "uvx",
      "args": ["--from", "C:/Users/YOU/Projects/cursor-proxmox-mcp", "cursor-proxmox-mcp"],
      "env": {
        "PROXMOX_MCP_CONFIG": "C:/Users/YOU/Projects/cursor-proxmox-mcp/proxmox-config/config.write.json"
      }
    }
  }
}
```

- `config.audit.json` → `PVEAuditor` on `mcp@pve!audit`
- `config.write.json` → `PVEAdmin` / `PVEVMAdmin` on `mcp@pve!write`
- Auto-approve `proxmox-audit:*` only (see below)

## 3. Cursor approval (stop constant prompts)

Approval prompts are **Cursor**, not the connector. Typed `confirm=` for `reboot_node` / `shutdown_node` / `join_cluster` / Ceph OSD still applies even when auto-approved.

1. **Settings → Agents → Approvals & Execution** → **Auto-review** or **Allowlist** (not Ask Every Time).
2. Copy [`proxmox-config/permissions.example.json`](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/proxmox-config/permissions.example.json) to:
   - `~/.cursor/permissions.json` (Windows: `C:\Users\<you>\.cursor\permissions.json`), or
   - project `.cursor/permissions.json`
3. Match the `server:` prefix to your `mcp.json` name (`proxmox`, `proxmox-write`, `user-proxmox`, …).
4. Do **not** allowlist `reboot_node`, `shutdown_node`, `join_cluster`, `create_ceph_osd`, `destroy_ceph_osd`, `delete_ceph_pool`, or a blanket `proxmox:*` unless this is a disposable lab.

Docs: [Cursor permissions.json](https://cursor.com/docs/reference/permissions).

`get_mcp_capabilities` reports `safe_day2_tools_count` and `typed_confirm_tools` so allowlists stay aligned with the inventory.

## 4. Deploy pipeline (node `pve` example)

Inventory → guest → app:

1. `get_nodes` → `list_os_templates` / `list_isos` → `get_next_vmid`
2. **LXC:** `provision_lxc` → optional `prepare_lxc_for_docker` / `bootstrap_docker_lxc` → `push_to_lxc` → `deploy_node_app` or `deploy_static_nginx`
3. **VM:** `provision_vm` (or `bootstrap_cloudinit_vm` when cloning a cloud-init template) → `push_to_vm` / `execute_vm_command`

Host SSH (`ssh.enabled=true` + node `authorized_keys`) is required for LXC day-2. Prefer composite tools over many round-trips. See [Recipes](Recipes).

## What this does *not* change

- Typed `confirm=` on host power / cluster join / Ceph OSD (D29 / D30) — never auto-bypass in the connector.
- No free-form `execute_host_command`.
- Privsep footguns: empty maps → ACL the **token** identity (`user@realm!tokenid`).

## Related

- [Setup](Setup) — install, SSH, reload  
- [Recipes](Recipes) — playbooks  
- [Troubleshooting](Troubleshooting) — empty lists / 403 / SSH  
- Repo: [SETUP.md § Cursor approval](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SETUP.md#cursor-approval--auto-run) · decision **D31**
