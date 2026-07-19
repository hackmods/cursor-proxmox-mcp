# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 1.x     | Yes       |
| < 1.0   | No        |

## Reporting a vulnerability

Do **not** open a public GitHub issue for security-sensitive reports.

Email: **security@hackmods.dev** (or open a private [GitHub security advisory](https://github.com/hackmods/cursor-proxmox-mcp/security/advisories/new) on this repository).

Please include:

- Affected version / commit
- Description of the issue and impact
- Steps to reproduce (or a proof of concept)
- Whether you believe credentials or cluster data were exposed

We aim to acknowledge reports within 7 days and to ship a fix or mitigation for confirmed issues in the supported 1.x line as soon as practical.

## Operator guidance (summary)

This MCP server is a privileged automation client for Proxmox VE. Treat it like Terraform/Ansible credentials:

1. Use a dedicated `mcp@pve` (or similar) user — not `root@pam` when avoidable.
2. Keep **Privilege Separation = Yes** on API tokens and grant ACLs to the **token**.
3. Prefer `verify_ssl: true` with a trusted CA; disabling SSL verification is for labs only.
4. Keep `token_value` out of git. Prefer env interpolation in config (see SETUP.md).
5. Tools such as `execute_vm_command` / `execute_lxc_command` can run arbitrary guest commands within token permissions — scope the token accordingly.
6. Destructive tools (`delete_*`, restore-overwrite, ACL/firewall changes) are irreversible; review agent plans before approving.

Full findings and remediation tracking: [`.cursor/research/security-review.md`](.cursor/research/security-review.md).
