# Publishing guide

How to ship `cursor-proxmox-mcp` to PyPI, GHCR, the official MCP Registry, and Glama.

## PyPI (Trusted Publishing)

`proxmox-mcp-server` on PyPI is a **different** project. This repo publishes as **`cursor-proxmox-mcp`**.

### One-time: register a trusted publisher

1. Create a blank project (or pending publisher) at [PyPI publishing](https://pypi.org/manage/account/publishing/).
2. Use these exact claims:

| Field | Value |
|-------|--------|
| PyPI project name | `cursor-proxmox-mcp` |
| Owner | `hackmods` |
| Repository | `cursor-proxmox-mcp` |
| Workflow name | `publish.yml` |
| Environment name | `pypi` |

3. In GitHub → **Settings → Environments → `pypi`**, create the environment (no secrets needed for OIDC).

### Publish a version

1. Bump `version` in `pyproject.toml` and `server.json`.
2. Update `CHANGELOG.md`.
3. Tag and push: `git tag v1.0.1 && git push origin v1.0.1`.
4. `release.yml` builds the wheel, pushes GHCR, and creates/updates the GitHub Release.
5. Publishing the Release triggers `publish.yml` → PyPI upload.

Manual retry: Actions → **Publish to PyPI** → **Run workflow**.

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

```bash
# Install publisher (see https://modelcontextprotocol.io/registry/quickstart)
mcp-publisher login github
mcp-publisher publish   # uses ./server.json
```

Namespace must be `io.github.hackmods/...` when authenticating as GitHub user/org `hackmods`.

## Glama.ai

`glama.json` is in the repo root. Submit the GitHub URL at [glama.ai MCP servers](https://glama.ai/mcp/servers) → **Add MCP Server**, or wait for Glama’s GitHub crawl after the file is on `main`.

## Community announcements (drafts)

See [`docs/community/`](docs/community/) for Cursor forum and Reddit post drafts.

## Repo hardening (manual)

- **Branch protection** on `main`: require CI job `test` (matrix 3.10 / 3.12), disallow force pushes.
- **Secret scanning** + **push protection**: Settings → Code security.
- Prefer GitHub Security Advisories for vulnerability reports (see `SECURITY.md`).
