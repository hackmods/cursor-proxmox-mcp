# Publishing guide

How to ship `cursor-proxmox-mcp` to PyPI, GHCR, the official MCP Registry, and Glama.

## PyPI (Trusted Publishing)

`proxmox-mcp-server` on PyPI is a **different** project. This repo publishes as **`cursor-proxmox-mcp`**.

### Status (v1.4.0+)

| Workflow | Environment | Trusted Publisher | Notes |
|----------|-------------|-------------------|--------|
| `publish.yml` | `pypi` | **Registered** | Manual / retry path |
| `release.yml` | `pypi` | **Registered** (2026-07-19) | Tag-push primary path |

GitHub environment `pypi` already exists on `hackmods/cursor-proxmox-mcp`.

### One-time: register trusted publishers

Both GitHub publishers for `cursor-proxmox-mcp` should exist with these claims (already configured):

| Field | `release.yml` | `publish.yml` |
|-------|---------------|---------------|
| PyPI project name | `cursor-proxmox-mcp` | `cursor-proxmox-mcp` |
| Owner | `hackmods` | `hackmods` |
| Repository | `cursor-proxmox-mcp` | `cursor-proxmox-mcp` |
| Workflow name | **`release.yml`** | **`publish.yml`** |
| Environment name | **`pypi`** | **`pypi`** |

Manage at [PyPI publishing](https://pypi.org/manage/account/publishing/). If a future tag hits `invalid-publisher`, re-check the row for that workflow filename + environment `pypi`. GHCR + GitHub Release still ship when the PyPI step uses `continue-on-error`.

**Historical debug claims from a failed `release.yml` OIDC exchange (v1.4.0 before the publisher was added):**

| Claim | Expected |
|-------|----------|
| Owner | `hackmods` |
| Repository | `cursor-proxmox-mcp` |
| Workflow name | `release.yml` |
| Environment | `pypi` |
| `workflow_ref` (example) | `hackmods/cursor-proxmox-mcp/.github/workflows/release.yml@refs/tags/v1.4.0` |

3. In GitHub → **Settings → Environments → `pypi`**, keep the environment (no secrets needed for OIDC).

### Publish a version

1. Bump `version` in `pyproject.toml` and `server.json` (and GHCR identifier in `server.json` if present).
2. Move `[Unreleased]` notes in `CHANGELOG.md` under the new version heading; keep tool count / community drafts (`docs/community/`) aligned (`.\scripts\post-community.ps1 -Check`).
3. Sync GitHub wiki from `docs/wiki/`: `./scripts/sync-wiki.sh` or `.\scripts\sync-wiki.ps1`.
4. Tag and push: `git tag v1.1.0 && git push fork v1.1.0` (use your release remote).
5. `release.yml` (with `environment: pypi`) builds the wheel, uploads to PyPI, pushes GHCR, and creates the GitHub Release.
6. Announce: `.\scripts\post-community.ps1 -Check` then `-Channel cursor-forum -Open` (or `-CreateDiscussion` for GitHub).

> **Gotcha:** GitHub does not re-trigger `release: published` workflows when the Release is created by `GITHUB_TOKEN` inside Actions. That is why PyPI publish lives in `release.yml`, not only in `publish.yml`.

Verify:

```bash
uvx cursor-proxmox-mcp --help
# or
pip index versions cursor-proxmox-mcp
```

## GHCR

Images: `ghcr.io/hackmods/cursor-proxmox-mcp:{tag|latest}`

OCI label `io.modelcontextprotocol.server.name=io.github.hackmods/cursor-proxmox-mcp` is set for registry ownership checks.

```bash
docker pull ghcr.io/hackmods/cursor-proxmox-mcp:latest
docker run --rm -v /path/to/config.json:/config/config.json:ro \
  -e PROXMOX_MCP_CONFIG=/config/config.json \
  ghcr.io/hackmods/cursor-proxmox-mcp:latest
```

## Official MCP Registry

Prerequisites: package on PyPI (README must contain `<!-- mcp-name: io.github.hackmods/cursor-proxmox-mcp -->`).
OCI images need label `io.modelcontextprotocol.server.name=io.github.hackmods/cursor-proxmox-mcp` (set in `release.yml`).

### Automated (preferred)

`publish-mcp.yml` runs on `v*` tags (and `workflow_dispatch`) using GitHub OIDC:

1. Ensure `server.json` version + package identifiers match artifacts already on PyPI/GHCR.
2. Push a release tag (or **Actions → Publish to MCP Registry → Run workflow**).

### Manual

```bash
# Install publisher (see https://modelcontextprotocol.io/registry/quickstart)
mcp-publisher login github
mcp-publisher publish   # uses ./server.json
```

Namespace must be `io.github.hackmods/...` when authenticating as GitHub user/org `hackmods`.

Verify:

```bash
curl "https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.hackmods/cursor-proxmox-mcp"
```

## Glama.ai

`glama.json` is in the repo root. Submit the GitHub URL at [glama.ai MCP servers](https://glama.ai/mcp/servers) → **Add MCP Server**, or wait for Glama’s GitHub crawl after the file is on `main`.

## Community announcements

Drafts live in [`docs/community/`](docs/community/). Tooling:

```powershell
.\scripts\post-community.ps1 -Check
.\scripts\post-community.ps1 -Channel cursor-forum -Open
.\scripts\post-community.ps1 -Channel github -CreateDiscussion
```

```bash
./scripts/post-community.sh --check
./scripts/post-community.sh --channel reddit --open
```

See [`docs/community/README.md`](docs/community/README.md) for the full checklist.

## Repo hardening (manual)

- **Branch protection** on `main`: require CI job `test` (matrix 3.10 / 3.12), disallow force pushes.
- **Secret scanning** + **push protection**: Settings → Code security.
- Prefer GitHub Security Advisories for vulnerability reports (see `SECURITY.md`).
