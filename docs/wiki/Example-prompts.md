# Example prompts

Copy-paste these into Cursor chat once the **proxmox** MCP server shows green (~155 tools). Not wired yet? Start with [Setup](Setup).

Put API tokens in `config.json` / env — not in prompts.

## Before you paste

- **Create ≠ ready:** create tools return an async UPID. The agent should call `wait_for_task` before starting the guest or reporting success.
- **LXC create ≠ app deploy:** `create_lxc` provisions an OS template only. Nesting features do not install Docker — see [Recipes](Recipes) (Nested Docker).
- **Runtime IP / guest exec:** `execute_lxc_command` and reliable runtime IPs need opt-in host SSH ([Setup](Setup)).

## Starter prompts

### 1. First connection

> Call `get_nodes` and `get_version` to confirm the Proxmox MCP connection is working. Summarize what you find.

### 2. Cluster overview

> Using the Proxmox MCP tools, give me a quick health summary of my cluster — nodes, storage pools, and what's currently running.

### 3. Deploy this project in Docker

> Analyze this workspace to determine the resource requirements and the best base OS. Then, use the Proxmox tools to spin up a new LXC container with Docker to host this project — prefer an Ubuntu template if one is available, otherwise choose the best match from `list_os_templates`. Let me know the IP address when it is ready.

**What to expect:** analyze repo → `get_next_vmid` / `list_os_templates` → `create_lxc` with `nesting=1,keyctl=1` → `wait_for_task` → `start_lxc` → install Docker → report IP. For reliable IP + install, enable host SSH in config or pass `ssh_public_keys` on create. Deeper walkthrough: [SETUP.md — Provision a nested Docker LXC](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SETUP.md#provision-a-nested-docker-lxc-end-to-end).

### 4. Simple LXC (no Docker)

> Create a small Ubuntu LXC container with 2 GB RAM on my cluster. Wait for creation to finish, start it, and tell me how to reach it.

### 5. Inventory

> List all VMs and containers on the cluster. Include status and which node each guest is on.

### 6. Storage pressure

> Which storage pools are low on space? List recent backups if you can.

### 7. Safe changes

> Create a snapshot of guest `105` named `before-changes` before we modify anything.

### 8. Recent tasks

> Show recent cluster tasks and highlight any failures.

### 9. Empty lists / permissions

> My `get_containers` list is empty but I know containers exist. Check my API token permissions and tell me what ACL fixes I need.

### 10. VM from ISO

> List available ISOs, create a new VM with an Ubuntu ISO and cloud-init SSH access, wait for creation to complete, and report the VM ID.

---

## Development & DevOps

These prompts assume MCP is connected and you are working in a Cursor workspace. They combine repo context with Proxmox ops — useful for local dev, CI, and deploy workflows.

**Cursor tip:** Open the repo you want deployed and `@`-mention key files (`Dockerfile`, `compose.yaml`, `package.json`) in the same chat so the agent can size CPU/RAM/ports correctly.

### Ephemeral dev environment from this repo

*Use when:* you want a throwaway guest sized for the current project.

> Analyze this workspace (runtime, ports, env vars, dependencies). Provision a throwaway LXC or VM on Proxmox sized for local development, install what's needed, and give me SSH/IP details to deploy this project. Name it with a `dev-` prefix so we can clean it up later.

### Snapshot before risky change

*Use when:* you are about to change a guest and want a rollback point.

> I'm about to change guest `105`. Create a snapshot named `pre-deploy-$(date)` (or today's date), confirm it succeeded, then proceed only after the snapshot task completes.

### Post-config verification

*Use when:* you edited guest config and need to know if a reboot is required.

> I just updated the config on guest `120`. Check `get_guest_pending`, tell me if a reboot is required, and reboot only if pending changes block what we need.

### Debug a failing guest

*Use when:* something is wrong and you want diagnosis before any restart or delete.

> Guest `108` isn't behaving. Pull its status, recent cluster tasks for that guest, and network info. Summarize likely causes and suggest the safest next step — don't restart or delete without asking.

### Backup before release

*Use when:* you want a backup volume before deploying.

> Create a backup of guest `105` to my default backup storage before we deploy. Wait for the task to finish and report the backup ID/volume name.

### Tear down ephemeral dev resources

*Use when:* cleaning up `dev-*` guests after experiments.

> List containers and VMs with names starting with `dev-`. For any that are stopped and older than a week (or that I confirm), delete them with `force=true` only after I approve each one.

### Multi-server cluster

*Use when:* you need several guests for a distributed app, k8s lab, database replica set, etc.

> I need **3 Ubuntu servers** for a `[describe purpose, e.g. Redis cluster / k8s control plane + workers]`. Before creating anything: check cluster capacity (`get_cluster_resources`, storage, node memory), propose VM vs LXC and sizing per node, and pick a consistent naming scheme (`redis-01`, …). Provision guests **one at a time** — `wait_for_task` after each create before starting the next. Spread across Proxmox nodes when possible. When all are up, give me a summary table: name, VMID, node, IP, role. Ask before deletes or force operations.

### Docker Swarm with scalability

*Use when:* you want orchestration across multiple Proxmox guests, not just a single Docker host.

> Design and provision a **Docker Swarm** lab on Proxmox: **1 manager + 2 workers** (Ubuntu LXC with Docker unless you recommend VMs). Analyze workspace/cluster capacity first, use nesting features where needed, install Docker on each host, initialize Swarm on the manager, join the workers, and verify with `docker node ls`. Scale pattern: name guests `swarm-mgr-01`, `swarm-wkr-01`, `swarm-wkr-02` so we can add `swarm-wkr-03` later. Report a host table (name, VMID, node, IP, role) when ready. Do not claim the stack is production-ready until nodes are healthy and joined.

#### Multi-guest tips

- Say how many nodes and what roles up front; vague “spin up a cluster” leads to wrong sizing.
- Agents should serialize creates (`wait_for_task` per guest) — parallel creates race VMIDs and obscure failures.
- For Swarm/k8s, mention whether you need nested LXC or full VMs; see [Recipes](Recipes) for LXC nesting limits.

---

## Write better prompts

- Be explicit about wait-for-ready, desired node/bridge if you care, and “don’t claim the app is live until a port responds.”
- Not everything the model *suggests* is available via the Proxmox API (host package upgrades are a common gap). Prefer prompts that match registered tools — see [API coverage](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/docs/api-coverage.md).

## See also

[Recipes](Recipes) · [Tools](Tools) · [Troubleshooting](Troubleshooting) · [SETUP.md — example prompts](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SETUP.md#5-try-it--example-prompts)
