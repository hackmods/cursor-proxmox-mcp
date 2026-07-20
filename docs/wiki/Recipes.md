# Recipes

Living playbooks for Cursor agents using **cursor-proxmox-mcp**. Tool names are CI-locked — see [Tools](Tools) for the full list.

## Create LXC → wait → start → network

**Prefer `provision_lxc`** when host SSH is configured: one call does create(wait) → start(wait) → optional `configure_lxc_ssh` → runtime IP → `{vmid, hostname, ip, ssh_hint}`.

Manual primitives:

1. `get_next_vmid` (best-effort; race possible before create)
2. `list_os_templates` (optional `download_url_to_storage` if none)
3. `create_lxc` — OS template only; prefer `ssh_public_keys`; optional `onboot` / `description` / `tags`; features e.g. `nesting=1,keyctl=1` when needed; optional `wait=true` to poll create UPID in-tool (default still false — else step 4)
4. **`wait_for_task(node, upid)`** until stopped — create returns UPID immediately unless `wait=true`
5. `start_lxc` (or `start_guest` with `guest_type=lxc`)
6. `get_lxc_network` — configured `netN`; runtime IPv4 needs host SSH/`pct`
7. Guest SSH: prefer keys at create; password alone often blocked on Debian — use `configure_lxc_ssh` / `set_lxc_password(enable_password_ssh=true)`
8. HTTP checks on stock Debian: prefer `wget -qO-` (curl often missing)

Do **not** claim the guest is “ready for apps” until you verify services yourself.

## Nested Docker on LXC

Supported path (D24):

1. Prefer **`bootstrap_docker_lxc`** when the user asks for a Docker LXC (create→dns→ssh→prepare→verify)
2. Or manually: `create_lxc` with `docker_ready=true` + `nameserver` + `ssh_public_keys`
3. `wait_for_task` → `start_lxc` → `configure_lxc_dns` / `configure_lxc_ssh`
4. `prepare_lxc_for_docker(docker_mode=auto, install_docker=true?, smoke_test=true?)`
5. If `restart_required`: **`stop_lxc` then `start_lxc`**
6. `get_docker_lxc_status` to re-check runtime; smoke `docker run --rm hello-world`

Do **not** claim Docker-ready with nesting-only + stock runc.

Prompt-style recipe: [SETUP.md — Provision a nested Docker LXC](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SETUP.md).

## Static nginx site on LXC (no Docker)

1. Running CT with host SSH configured
2. `deploy_static_nginx` — installs nginx; optional `content_base64` / `local_path` (html or `.tar.gz`)
3. `get_lxc_network` → `wget -qO- http://<ip>/` (curl often missing on Debian)

## Node / Next.js app on LXC (no Docker)

1. Running CT with host SSH configured
2. Prefer `push_to_lxc` / `deploy_node_app` with a **local_path** tarball for private sources (not guest HTTPS `git clone` without creds)
3. `deploy_node_app` — installs Node LTS (default 22), extracts app, `npm ci && npm run build`, systemd on port 3000
4. `get_lxc_network` → `wget -qO- http://<ip>:3000/`

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
