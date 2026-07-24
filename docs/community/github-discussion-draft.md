<!-- channel: github -->
<!-- version: 1.8.0 -->
<!-- tools: 211 -->

# GitHub Discussion — draft (Announcements)

**Title:** cursor-proxmox-mcp — 211 tools (gated Ceph OSD)

**Body:**

## Summary

**[cursor-proxmox-mcp](https://github.com/hackmods/cursor-proxmox-mcp)** is on [PyPI](https://pypi.org/project/cursor-proxmox-mcp/) and GHCR (`ghcr.io/hackmods/cursor-proxmox-mcp`).

**211 tools** — prior Phase C surface plus carefully gated Ceph OSD: `list_node_disks` → `propose_ceph_osd` → `create_ceph_osd` (default dry-run + typed `/dev` confirm) / `destroy_ceph_osd`. Console stays ticket-only; PBS is PVE storage plugin scope.

## Install

```bash
uvx cursor-proxmox-mcp
```

## Docs

- [SETUP.md](https://github.com/hackmods/cursor-proxmox-mcp/blob/main/SETUP.md)
- [Wiki](https://github.com/hackmods/cursor-proxmox-mcp/wiki)
- [Release notes](https://github.com/hackmods/cursor-proxmox-mcp/releases/tag/v1.8.0)
