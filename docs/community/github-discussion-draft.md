<!-- channel: github -->
<!-- version: 1.9.0 -->
<!-- tools: 212 -->

# GitHub Discussion — draft (Announcements)

**Title:** cursor-proxmox-mcp — 212 tools (elevated mode + provision_vm)

**Body:**

## Summary

**[cursor-proxmox-mcp](https://github.com/hackmods/cursor-proxmox-mcp)** is on [PyPI](https://pypi.org/project/cursor-proxmox-mcp/) and GHCR (`ghcr.io/hackmods/cursor-proxmox-mcp`).

**212 tools** — prior surface plus optional dual-credential elevated mode (`auth_write`, D31), `provision_vm`, and Cursor `permissions.json` day-2 auto-approve docs. Console stays ticket-only; PBS is PVE storage plugin scope; Ceph OSD remains gated (dry-run + typed confirm).

## Install

```bash
uvx cursor-proxmox-mcp
```

## Docs

- [SETUP.md](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SETUP.md)
- [Wiki — Elevated mode](https://github.com/hackmods/cursor-proxmox-mcp/wiki/Elevated-mode)
- [Release notes](https://github.com/hackmods/cursor-proxmox-mcp/releases/tag/v1.9.0)
