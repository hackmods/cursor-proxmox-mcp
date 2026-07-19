# Community announcements

Operator-facing drafts for announcing **cursor-proxmox-mcp** releases. Do **not** put secrets, tokens, or lab IPs in these files.

## Drafts

| File | Channel |
|------|---------|
| [cursor-forum-draft.md](cursor-forum-draft.md) | Cursor forum |
| [reddit-draft.md](reddit-draft.md) | Reddit (r/Proxmox, r/selfhosted, …) |
| [github-discussion-draft.md](github-discussion-draft.md) | GitHub Discussions (Announcements) |

Each draft has HTML comment headers (`channel`, `version`, `tools`) plus `**Title:**` / `**Body:**` for [`scripts/post-community`](../../scripts/post-community.ps1).

## When to post

After a tagged release when:

1. PyPI shows the new version (`pip index versions cursor-proxmox-mcp`)
2. Wiki is synced (`.\scripts\sync-wiki.ps1`)
3. Draft `-Check` passes (`.\scripts\post-community.ps1 -Check`)
4. Tool count / version in drafts match `inventory` + `pyproject.toml`

## How to post

```powershell
# Sanity-check drafts vs package version / tool inventory
.\scripts\post-community.ps1 -Check

# Copy Cursor forum body to clipboard and print next steps
.\scripts\post-community.ps1 -Channel cursor-forum

# Same + open compose URLs
.\scripts\post-community.ps1 -Channel reddit -Open

# Create a GitHub Discussion from the github draft (Discussions must be enabled)
.\scripts\post-community.ps1 -Channel github -CreateDiscussion
```

Linux/macOS: `./scripts/post-community.sh` (same flags).

## Checklist

- [ ] Version on PyPI matches draft `<!-- version: -->`
- [ ] Tool count matches `len(ALL_TOOL_NAMES)`
- [ ] No secrets / private hostnames in body
- [ ] SETUP + wiki links work
- [ ] Cross-post sparingly (one primary venue; avoid identical spam)
