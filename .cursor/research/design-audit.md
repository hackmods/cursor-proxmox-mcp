# Code design audit — v1.0

Module-by-module review of `src/proxmox_mcp/`. Verdicts: **keep** | **fix-now** | **defer**.

## Module table

| Module | LOC | Responsibility | Issues | Verdict |
|--------|-----|----------------|--------|---------|
| `server.py` | 940 | Construct deps + register all MCP tools | God file; hand-rolled registration drifts from inventory | **fix-now** — declarative register module; thin server |
| `config/loader.py` | 66 | Load JSON → Config | No env interpolation for secrets | **fix-now** |
| `config/models.py` | 72 | Pydantic config models | No `ca_cert_path`; unused NodeStatus/VMCommand | **fix-now** (ca_cert); **defer** unused models cleanup |
| `core/proxmox.py` | 98 | ProxmoxAPI connect | No SSL-off WARN | **fix-now** |
| `core/logging.py` | 87 | Live logging setup | No redaction filter | **fix-now** |
| `utils/logging.py` | 41 | Duplicate unused logging | Dead code (no imports) | **fix-now** — delete |
| `utils/auth.py` | 70 | Env-based auth helper | Unused by server (JSON path only) | **fix-now** — delete; JSON+env-interp is canonical |
| `tools/base.py` | 91 | Shared format/error | Raw exception leakage | **fix-now** |
| `tools/guest.py` | 19 | qemu/lxc routing | Good; underused in some paths | **keep** — mandate usage |
| `tools/definitions.py` | 158 | Tool description strings | Some destructive tools weak on warnings | **fix-now** |
| `tools/vm.py` | 606 | QEMU lifecycle | God methods; emoji responses; duplicated storage detect; fragile exists-check | **fix-now** helpers; **defer** emoji rewrite |
| `tools/container.py` | 434 | LXC lifecycle | Same duplication as vm | **fix-now** helpers |
| `tools/console/manager.py` | 162 | Guest agent exec | Fixed 1s sleep; noisy DEBUG logs | **fix-now** |
| `tools/storage.py` | 235 | Storage CRUD | Clear; password param logged risk low | **keep** |
| `tools/firewall.py` | 211 | FW rules | Uses guest.py | **keep** |
| `tools/access.py` | 167 | Users/ACL/tokens | Token secret in response (required) | **fix-now** banner only |
| `tools/node.py` | 164 | Node info | Fine | **keep** |
| `tools/cluster.py` | 108 | Cluster info | Fine | **keep** |
| `tools/ha.py` | 83 | HA CRUD | Fine | **keep** |
| `tools/backup.py` | 77 | Backups | Fine | **keep** |
| `tools/snapshot.py` | 60 | Snapshots | Uses guest.py | **keep** |
| `tools/replication.py` | 54 | Replication | Fine | **keep** |
| `tools/sdn.py` | 43 | SDN read | Fine | **keep** |
| `tools/migrate.py` | 39 | Migrate | Uses guest.py | **keep** |
| `tools/pool.py` | 33 | Pools | Fine | **keep** |
| `tools/acme.py` | 24 | ACME read | Fine | **keep** |
| `tools/network.py` | 12 | Node networks | Fine | **keep** |
| `tools/tasks.py` | 62 | Tasks | Fine | **keep** |
| `formatting/*` | ~750 | Presentation | Couples emoji/theme; used by base | **keep** for v1.0 (no bulk rewrite) |

## Cross-cutting decisions (locked for v1.0)

| Topic | Decision | Decision ID |
|-------|----------|-------------|
| Registration | Move wrappers to `tools/register.py`; each domain exports `TOOL_SPECS` metadata; server calls `register_all` | D19 |
| VM/LXC symmetry | Keep parallel classes; share helpers (`pick_storage`, `assert_guest_absent`) | D13 |
| Response contract | Keep existing user-visible strings; new helpers may use plain text | D14 |
| Auth/config | JSON config + optional `${ENV}` interpolation only; remove unused utils/auth | D15 |
| Logging | `core/logging.py` only; delete `utils/logging.py` | D16 |
| Guest routing | Snapshot/migrate/firewall continue via `guest.py`; enforce in tests | D17 |
| Existence checks | Shared helper treating proxmoxer 500/404 "does not exist" | D13 |
| Task UPID wait | Defer public wait tool (D10) | — |
| Lab defaults (`vmbr0`) | Extract constants; no new public params (D11) | D18 |

## Design invariants (test locks)

1. Registered tool names == `EXPECTED_TOOLS` exactly.
2. Union of all `TOOL_SPECS` names == `EXPECTED_TOOLS`.
3. Every registered tool has non-empty description.
4. Destructive tools' descriptions contain irreversible/warning language.
5. Server uses only `core.logging.setup_logging`.
6. Auth comes only from `load_config` → `Config.auth`.
7. Snapshot/migrate/firewall import `guest_resource` / `normalize_guest_type`.
8. Tool classes construct with injected API (no FastMCP required).
9. No imports of deleted `utils.logging` / `utils.auth`.

## Fix-now backlog (ordered)

1. Typed errors + sanitize `_handle_error`
2. Log redaction + example config defaults
3. Exec polling timeout
4. Shared helpers (storage pick, guest absent)
5. Declarative `TOOL_SPECS` + `register.py`
6. Delete dead utils; constants for defaults
7. Full test suite (≥90% line cov)
8. Cruft removal + version 1.0.0
