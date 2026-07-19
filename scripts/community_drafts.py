"""Parse and validate docs/community announcement drafts."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMUNITY_DIR = REPO_ROOT / "docs" / "community"

CHANNEL_FILES = {
    "cursor-forum": "cursor-forum-draft.md",
    "reddit": "reddit-draft.md",
    "github": "github-discussion-draft.md",
}

COMPOSE_URLS = {
    "cursor-forum": "https://forum.cursor.com/",
    "reddit": "https://www.reddit.com/submit",
    "github": "https://github.com/hackmods/cursor-proxmox-mcp/discussions/new?category=announcements",
}


@dataclass
class CommunityDraft:
    channel: str
    path: Path
    version: Optional[str]
    tools: Optional[int]
    title: str
    body: str


def _meta(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for m in re.finditer(r"<!--\s*([a-zA-Z0-9_-]+):\s*([^>]+?)\s*-->", text):
        out[m.group(1).strip().lower()] = m.group(2).strip()
    return out


def _section(text: str, name: str) -> str:
    # **Title:** rest of line OR **Body:** then remainder until EOF
    if name.lower() == "title":
        m = re.search(r"\*\*Title:\*\*\s*(.+)", text)
        return (m.group(1).strip() if m else "").strip()
    m = re.search(r"\*\*Body:\*\*\s*\n(.*)\Z", text, re.DOTALL | re.IGNORECASE)
    if not m:
        return ""
    return m.group(1).strip()


def parse_draft(path: Path) -> CommunityDraft:
    text = path.read_text(encoding="utf-8")
    meta = _meta(text)
    channel = meta.get("channel") or path.stem.replace("-draft", "")
    tools_raw = meta.get("tools")
    tools = int(tools_raw) if tools_raw and tools_raw.isdigit() else None
    return CommunityDraft(
        channel=channel,
        path=path,
        version=meta.get("version"),
        tools=tools,
        title=_section(text, "title"),
        body=_section(text, "body"),
    )


def load_channel(channel: str) -> CommunityDraft:
    key = channel.strip().lower()
    if key not in CHANNEL_FILES:
        raise ValueError(f"Unknown channel {channel!r}; expected one of {sorted(CHANNEL_FILES)}")
    path = COMMUNITY_DIR / CHANNEL_FILES[key]
    if not path.is_file():
        raise FileNotFoundError(path)
    return parse_draft(path)


def package_version() -> str:
    pyproject = REPO_ROOT / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not m:
        raise RuntimeError("version not found in pyproject.toml")
    return m.group(1)


def inventory_tool_count() -> int:
    from proxmox_mcp.tools.inventory import ALL_TOOL_NAMES

    return len(ALL_TOOL_NAMES)


def check_all_drafts() -> list[str]:
    """Return list of error strings (empty = ok)."""
    errors: list[str] = []
    ver = package_version()
    count = inventory_tool_count()
    for channel in CHANNEL_FILES:
        draft = load_channel(channel)
        if not draft.title:
            errors.append(f"{channel}: missing Title")
        if not draft.body:
            errors.append(f"{channel}: missing Body")
        if draft.version != ver:
            errors.append(
                f"{channel}: version meta {draft.version!r} != pyproject {ver!r}"
            )
        if draft.tools != count:
            errors.append(
                f"{channel}: tools meta {draft.tools!r} != inventory {count}"
            )
        # Body should mention tool count and version somewhere
        if str(count) not in draft.body and str(count) not in draft.title:
            errors.append(f"{channel}: tool count {count} not mentioned in title/body")
        if ver not in draft.body and ver not in draft.title:
            errors.append(f"{channel}: version {ver} not mentioned in title/body")
    return errors


def create_github_discussion(
    *,
    owner: str = "hackmods",
    repo: str = "cursor-proxmox-mcp",
    preferred_category: str = "Announcements",
) -> str:
    """Create a GitHub Discussion from the github draft. Returns discussion URL.

    Requires ``gh`` authenticated with permission to create discussions.
    """
    import json
    import shutil
    import subprocess

    if not shutil.which("gh"):
        raise RuntimeError("gh CLI not found on PATH")

    draft = load_channel("github")
    if not draft.title or not draft.body:
        raise RuntimeError("github draft missing title or body")

    cat_q = """
    query($owner:String!, $name:String!) {
      repository(owner:$owner, name:$name) {
        id
        discussionCategories(first:30) { nodes { id name } }
      }
    }
    """
    cat_raw = subprocess.check_output(
        [
            "gh",
            "api",
            "graphql",
            "-f",
            f"query={cat_q}",
            "-f",
            f"owner={owner}",
            "-f",
            f"name={repo}",
        ],
        text=True,
    )
    cat_data = json.loads(cat_raw)["data"]["repository"]
    if not cat_data:
        raise RuntimeError(f"Repository {owner}/{repo} not found or inaccessible")
    repo_id = cat_data["id"]
    nodes = (cat_data.get("discussionCategories") or {}).get("nodes") or []
    if not nodes:
        raise RuntimeError(
            f"No discussion categories on {owner}/{repo}. Enable Discussions first."
        )
    category = next(
        (n for n in nodes if n["name"].lower() == preferred_category.lower()),
        None,
    )
    if category is None:
        category = next((n for n in nodes if "announce" in n["name"].lower()), nodes[0])

    mut = """
    mutation($repositoryId:ID!, $categoryId:ID!, $title:String!, $body:String!) {
      createDiscussion(input:{
        repositoryId:$repositoryId,
        categoryId:$categoryId,
        title:$title,
        body:$body
      }) { discussion { url } }
    }
    """
    mut_raw = subprocess.check_output(
        [
            "gh",
            "api",
            "graphql",
            "-f",
            f"query={mut}",
            "-f",
            f"repositoryId={repo_id}",
            "-f",
            f"categoryId={category['id']}",
            "-f",
            f"title={draft.title}",
            "-f",
            f"body={draft.body}",
        ],
        text=True,
    )
    url = json.loads(mut_raw)["data"]["createDiscussion"]["discussion"]["url"]
    return url


def main(argv: Optional[list[str]] = None) -> int:
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="Community draft helper")
    parser.add_argument(
        "command",
        choices=["check", "show", "create-discussion"],
        help="check | show | create-discussion",
    )
    parser.add_argument(
        "--channel",
        default="cursor-forum",
        choices=list(CHANNEL_FILES.keys()) + ["all"],
    )
    args = parser.parse_args(argv)

    if args.command == "check":
        errs = check_all_drafts()
        if errs:
            print("\n".join(errs), file=sys.stderr)
            return 1
        print("OK")
        return 0

    if args.command == "create-discussion":
        url = create_github_discussion()
        print(url)
        return 0

    channels = list(CHANNEL_FILES) if args.channel == "all" else [args.channel]
    for ch in channels:
        d = load_channel(ch)
        print(
            json.dumps(
                {
                    "channel": d.channel,
                    "title": d.title,
                    "body": d.body,
                    "version": d.version,
                    "tools": d.tools,
                    "url": COMPOSE_URLS.get(ch, ""),
                    "path": str(d.path),
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
