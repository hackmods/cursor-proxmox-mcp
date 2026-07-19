# Design decisions

## D1 — guest_type for cross-cutting tools

Snapshots, backups (restore), migrate, and guest firewall use `guest_type=qemu|lxc` instead of doubling every tool name. Existing power tools stay as `*_vm` / `*_lxc` for compatibility with earlier Cursor workflows.

## D2 — Destructive ops

Delete VM/LXC/storage/backup/snapshot/user require clear warning text in tool descriptions and responses. Running guests need `force=True` to delete (stop then delete).

## D3 — Token secrets

`create_token` returns the secret in the tool response once. Do not log secrets at INFO; callers must store immediately.

## D4 — LXC exec

Proxmox does not expose `pct exec` as universally as QEMU guest-agent. `execute_lxc_command` calls the `/exec` API path when present; clusters without it will error clearly.

## D5 — Docs / inventory lockstep

`tests/expected_tools.py` must equal registered tool names. CI fails on drift. README + coverage matrix update in the same change.

## D6 — VNC/SPICE ticket-only, no proxy

MCP request/response does not fit long-lived websocket console streams. Tools mint `vncproxy` / `spiceproxy` / `termproxy` tickets and return JSON; external viewers connect. Full proxy remains Phase C / excluded.

## D7 — uvx as recommended install path

Cursor MCP reliability improved when using `uvx` (or `uv run`) with console script `proxmox-mcp-server` instead of a fragile system Python + manual `PYTHONPATH`. Keep `python -m proxmox_mcp.server` as documented fallback. Both `proxmox-mcp` and `proxmox-mcp-server` map to `server:main`.

## D8 — API tokens default to Privilege Separation

Proxmox creates tokens with **Privilege Separation = Yes** (`privsep=1`). Separated tokens start with **no** ACLs; effective permissions are the intersection of user ACLs and token ACLs. Disabling privsep (`privsep=0`) makes the token inherit the user’s full permission set — a common lab “make it work” bypass when operators forget to ACL the token, but a larger blast radius if the secret leaks.

**Project stance:** Document privsep=Yes + explicit token ACL as best practice in `SETUP.md` / `proxmox-auth` rule. Document privsep=No as an explicit lab shortcut, not the recommended default. `create_token` keeps `privsep=True` by default to match Proxmox.

Operators hitting empty results after a “successful” token create should check token ACLs (`pveum user token permissions …` / UI Permissions for `user@realm!tokenid`) before disabling privsep.

## D9 — Setup guide is first-run source of truth

`SETUP.md` is the primary first-run path (token, Cursor `mcp.json`, prompts, security). README stays the inventory + short install reference and links into SETUP for auth depth. `proxmox-config/README.md` covers the config file only.

## D10 — Prefer Phase D QOL over Phase C surface

After the 128-tool baseline, expand create/wait paths before exotic admin APIs. Agents lose more time to racing UPIDs and hardcoded `vmbr0`/missing ISO/cloud-init than to missing SDN zone CRUD. Roadmap: `.cursor/research/next-expansion.md`.

## D11 — Create tools should not hardcode lab assumptions forever

`create_vm` / `create_lxc` currently assume `vmbr0` and DHCP-style net. Treat bridge/IP/ISO/cloud-init as first-class optional params in Phase D so multi-bridge labs work without post-create config edits.
