# Troubleshooting

| Symptom | Fix |
|---------|-----|
| Green MCP but only ~13–14 tools | Stale Cursor catalog or wrong package. Disable/Enable proxmox; quit Cursor fully; use `uvx --from <checkout> cursor-proxmox-mcp` |
| Empty VM/CT lists | Token privsep with no ACL on `user@realm!tokenid` — call `get_token_permissions` |
| Config change “did nothing” | Call `get_guest_pending`; reboot guest to apply hotplug-limited keys |
| `execute_lxc_command` fails / HTTP 501 | Needs opt-in `ssh` + paramiko (`pct exec`). **501 on `/lxc/.../exec` = stale MCP (pre-1.1.1)** — reload/`uvx --from` checkout. Without SSH use `ssh_public_keys` at create or static IP only. |
| Guest SSH auth failed after `password=` | Many templates block root *password* SSH. Pass `ssh_public_keys` on create, or `set_lxc_password(enable_password_ssh=true)` after start (needs host SSH). |
| LXC suspend/resume fails | CRIU best-effort; prefer `shutdown_lxc` / `shutdown_guest` |
| Wrong package installed | Uninstall `proxmox-mcp-server` from Gethos; install **`cursor-proxmox-mcp`** |
| SSL errors | Lab: `verify_ssl: false` in config (warned at startup); prod: fix CA / enable verify |

More: [SETUP.md troubleshooting](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SETUP.md) · [SECURITY.md](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SECURITY.md).
