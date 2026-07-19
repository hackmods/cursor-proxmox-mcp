#!/usr/bin/env bash
# Sync docs/wiki/*.md to the GitHub wiki for hackmods/cursor-proxmox-mcp.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/docs/wiki"
TMP="${TMPDIR:-/tmp}/cursor-proxmox-mcp-wiki-$$"
REMOTE="https://github.com/hackmods/cursor-proxmox-mcp.wiki.git"

test -d "$SRC" || { echo "Missing $SRC" >&2; exit 1; }

if ! git clone --depth 1 "$REMOTE" "$TMP" 2>/dev/null; then
  cat <<'EOF' >&2
ERROR: Wiki remote not found.

GitHub only creates the wiki git repo after the first page exists.
1. Open https://github.com/hackmods/cursor-proxmox-mcp/wiki
2. Click 'Create the first page' and save (content can be temporary).
3. Re-run this script.

Source markdown remains in docs/wiki/ in the main repo.
EOF
  exit 1
fi

cp "$SRC"/*.md "$TMP"/
cd "$TMP"
git add *.md
if git diff --cached --quiet; then
  echo "Wiki already up to date."
  rm -rf "$TMP"
  exit 0
fi
git -c user.email="wiki-bot@local" -c user.name="wiki-sync" commit -m "docs: sync wiki from docs/wiki"
git push -u origin HEAD:master
rm -rf "$TMP"
echo "Wiki synced."
