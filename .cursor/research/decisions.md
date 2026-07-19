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
