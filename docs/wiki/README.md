# Wiki source

Markdown here is the **source of truth** for the GitHub wiki:

https://github.com/hackmods/cursor-proxmox-mcp/wiki

| File | Wiki page |
|------|-----------|
| `Home.md` | Home |
| `Setup.md` | Setup |
| `Tools.md` | Tools |
| `Troubleshooting.md` | Troubleshooting |
| `_Sidebar.md` | Sidebar |

Sync after editing:

```powershell
.\scripts\sync-wiki.ps1
```

```bash
./scripts/sync-wiki.sh
```

### First-time GitHub wiki init

GitHub does not create `*.wiki.git` until the first page exists. One-time:

1. Open https://github.com/hackmods/cursor-proxmox-mcp/wiki  
2. Click **Create the first page** (title `Home` is fine; paste can be empty).  
3. Save, then run `.\scripts\sync-wiki.ps1` (or `./scripts/sync-wiki.sh`) to overwrite with `docs/wiki/` content.

Requires `gh` auth with `repo` scope and **Settings → Features → Wikis** enabled.
