# Revision log (living)

Chronological record of meaningful MCP / agent-UX revisions for future Cursor sessions.
Pair with [changelog-notes.md](changelog-notes.md) (research “why”) and root `CHANGELOG.md` (user-facing).

| Date | Rev | Summary | Tools | Key files / decisions |
|------|-----|---------|-------|------------------------|
| 2026-07-19 | r1 | Phase E baseline: LXC parity, `*_guest`, ops completeness | 152 | D1, next-expansion Phase E |
| 2026-07-19 | r2 | Agent feedback: fix LXC exec (SSH+pct), guest IP, QEMU/LXC UX | **153** | D4 revised; `get_lxc_network`; see [agent-feedback-log.md](agent-feedback-log.md) |

## How to update

When shipping a behavior change that agents will feel:

1. Append a row here (`rN`).
2. Add a dated section to `changelog-notes.md`.
3. If feedback-driven, append to `agent-feedback-log.md` (symptoms → root cause → fix → out of scope).
4. Update `proxmox-api-coverage.md` / `next-expansion.md` / `decisions.md` as needed.
5. Keep `tests/expected_tools.py` / `inventory.py` / README tool count in lockstep (D5).
