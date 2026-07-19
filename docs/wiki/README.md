# Wiki source

Markdown here is the **source of truth** for the GitHub wiki:

https://github.com/hackmods/cursor-proxmox-mcp/wiki

| File | Wiki page |
|------|-----------|
| `Home.md` | Home |
| `Setup.md` | Setup |
| `Example-prompts.md` | Example prompts |
| `Tools.md` | Tools (full inventory; generated section) |
| `Recipes.md` | Recipes |
| `Troubleshooting.md` | Troubleshooting |
| `_Sidebar.md` | Sidebar |
| `_Footer.md` | Footer (every page) |

## After adding or renaming MCP tools

1. Update `src/proxmox_mcp/tools/inventory.py` / `register.py` / `definitions.py` as usual.
2. If the tool belongs to a new domain bucket, edit `DOMAIN_GROUPS` in `scripts/generate-wiki-tools.py`.
3. Regenerate:

```bash
python scripts/generate-wiki-tools.py
```

4. CI (`tests/test_wiki_tools.py`) asserts every `ALL_TOOL_NAMES` entry appears in `Tools.md`.
5. Sync the live wiki (below).

## Sync after editing

```powershell
.\scripts\sync-wiki.ps1
```

```bash
./scripts/sync-wiki.sh
```

Copies all `*.md` except this `README.md` into the wiki git repo (including `_Sidebar.md` and `_Footer.md`).

### First-time GitHub wiki init

GitHub does not create `*.wiki.git` until the first page exists. One-time:

1. Open https://github.com/hackmods/cursor-proxmox-mcp/wiki  
2. Click **Create the first page** (title `Home` is fine; paste can be empty).  
3. Save, then run `.\scripts\sync-wiki.ps1` (or `./scripts/sync-wiki.sh`) to overwrite with `docs/wiki/` content.

Requires `gh` auth with `repo` scope and **Settings → Features → Wikis** enabled.
