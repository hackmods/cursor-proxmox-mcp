# Troubleshooting

| Symptom | Fix |
|---------|-----|
| Green MCP but only ~13–14 tools | Stale Cursor catalog or wrong package. Disable/Enable proxmox; quit Cursor fully; use `uvx --from <checkout> cursor-proxmox-mcp` |
| Empty VM/CT lists | Token privsep with no ACL on `user@realm!tokenid` — call `get_token_permissions` |
| Config change “did nothing” | Call `get_guest_pending`; reboot guest to apply hotplug-limited keys |
| `execute_lxc_command` fails | Needs opt-in `ssh` config + paramiko (`pct exec` on the host). Proxmox has no REST LXC exec API. Without SSH, use static `ip=` + `get_lxc_network`. |
| LXC suspend/resume fails | CRIU best-effort; prefer `shutdown_lxc` / `shutdown_guest` |
| Wrong package installed | Uninstall `proxmox-mcp-server` from Gethos; install **`cursor-proxmox-mcp`** |
| SSL errors | Lab: `verify_ssl: false` in config (warned at startup); prod: fix CA / enable verify |

More: [SETUP.md troubleshooting](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SETUP.md) · [SECURITY.md](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SECURITY.md).
