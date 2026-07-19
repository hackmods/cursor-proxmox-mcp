# Security review — v1.0

Pre-release security review for `cursor-proxmox-mcp`. Status reflects remediation planned/done in the v1.0 hardening pass.

## Findings

| ID | Severity | Finding | Remediation | Phase |
|----|----------|---------|-------------|-------|
| S1 | High | API `token_value` stored plaintext in JSON config | Env-var interpolation `${PROXMOX_TOKEN_VALUE}` in loader; document in SETUP | 2 |
| S2 | Medium | Example config ships `verify_ssl: false` | Example default `true`; startup WARN when false; optional `ca_cert_path` | 2 |
| S3 | Medium | Example log level `DEBUG`; console manager logs commands/agent payloads | Example → `INFO`; redacting log filter | 2 |
| S4 | High | `execute_vm_command` / `execute_lxc_command` = arbitrary guest shell | WARN log + optional `PROXMOX_MCP_EXEC_ALLOWLIST`; document in SECURITY.md | 2 |
| S5 | Medium | `_handle_error` re-emits raw exception strings (host/token leakage risk) | Typed errors + sanitize messages | 2 |
| S6 | Medium | `create_token` returns secret in tool response (required by Proxmox) | Banner in response; never log secret | 2 |
| S7 | Low | Destructive tools may lack strong "irreversible" description text | Audit `definitions.py` | 2 |
| S8 | Low | Example MCP configs at repo root | Move to `docs/examples/` | 4 |
| S9 | Medium | No pip-audit / CodeQL / Dependabot | Add in CI | 3 |
| S10 | Low | Fixed 1s sleep on guest exec may truncate / race | Poll `exec-status` with timeout | 2 |

## Threat model (brief)

- **Trust boundary:** Local MCP client (Cursor) → this process → Proxmox API (HTTPS).
- **Assets:** API token secret, cluster inventory, guest shells, firewall/ACL state.
- **Attackers:** Malicious or confused agent prompts; leaked config.json; MITM if SSL verify off; compromised dependency.
- **Out of scope for v1.0:** MCP client sandboxing; human confirmation UX (client-side).

## Operator checklist before production use

- [ ] Dedicated user + privsep token with least-privilege ACLs
- [ ] `verify_ssl: true` (or documented lab exception)
- [ ] Secrets via env interpolation, not committed files
- [ ] Log level INFO or higher in production
- [ ] Review which destructive / exec tools the token can reach

## Related

- [SECURITY.md](../../SECURITY.md)
- [decisions.md](decisions.md) (D2, D3, D8)
- [design-audit.md](design-audit.md)
