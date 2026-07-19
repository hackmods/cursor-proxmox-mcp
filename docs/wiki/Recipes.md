# Recipes

Living playbooks for Cursor agents using **cursor-proxmox-mcp**. Tool names are CI-locked — see [Tools](Tools) for the full list.

## Create LXC → wait → start → network

1. `get_next_vmid` (best-effort; race possible before create)
2. `list_os_templates` (optional `download_url_to_storage` if none)
3. `create_lxc` — OS template only; prefer `ssh_public_keys`; features e.g. `nesting=1,keyctl=1` when needed; optional `wait=true` to poll create UPID in-tool (default still false — else step 4)
4. **`wait_for_task(node, upid)`** until stopped — create returns UPID immediately unless `wait=true`
5. `start_lxc` (or `start_guest` with `guest_type=lxc`)
6. `get_lxc_network` — configured `netN`; runtime IPv4 needs host SSH/`pct`

Do **not** claim the guest is “ready for apps” until you verify services yourself.

## Nested Docker on LXC

Supported path (Phase F):

1. `create_lxc` with `docker_ready=true` (or `features=nesting=1,keyctl=1`) + `ssh_public_keys`
2. `wait_for_task` (or `wait=true` on create) → `start_lxc` → confirm IP
3. `prepare_lxc_for_docker` — host `lxc-pve` gate + dual AppArmor workaround if unpatched
4. If `restart_required`: **`stop_lxc` then `start_lxc`** (not reboot alone)
5. Install Docker if needed (`install_docker=true` or `execute_lxc_command`)
6. Smoke: `docker run --rm nginx:alpine` — **not** merely `docker --version`
7. `push_to_lxc` for app files

Prompt-style recipe: [SETUP.md — Provision a nested Docker LXC](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SETUP.md).

## Static nginx site on LXC (no Docker)

1. Running CT with host SSH configured
2. `deploy_static_nginx` — installs nginx; optional `content_base64` / `local_path` (html or `.tar.gz`)
3. `get_lxc_network` → `curl http://<ip>/`

## Create VM (ISO / cloud-init)

1. `list_isos` / `list_node_networks` / `get_next_vmid`
2. `create_vm` with `iso`, optional `ciuser` / `sshkeys` / `ipconfig0`, `bridge`; optional `wait=true`
3. **`wait_for_task`** (unless `wait=true`)
4. `start_vm` — finish OS install via console ticket or cloud-init; guest agent needed for `execute_vm_command` / `get_vm_network` / `push_to_vm`

## Config change → pending → reboot

1. `update_vm_config` / `update_lxc_config` / `update_lxc_features`
2. `get_guest_pending` — some keys need reboot
3. `reboot_guest` / `reboot_vm` / `reboot_lxc` as appropriate

## Force-delete a running guest

1. `delete_vm` / `delete_lxc` / `delete_guest` with `force=true` — server waits for stop UPID, then starts delete
2. Still **`wait_for_task`** on the delete UPID before assuming the guest is gone

## Token ACL smoke

1. `get_token_permissions` for `userid` + token id
2. If lists are empty (`get_vms` / `get_containers` / `get_storage`), fix ACL on `user@realm!tokenid` (privsep), not only the user

## Snapshot before risk

1. `create_snapshot` (note `guest_type`)
2. Make changes
3. `rollback_snapshot` only if needed (destructive)

## See also

[Example prompts](Example-prompts) · [Setup](Setup) · [Troubleshooting](Troubleshooting) · [Home](Home)
