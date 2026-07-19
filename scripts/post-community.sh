#!/usr/bin/env bash
# Prepare / validate community announcement drafts under docs/community/.
# Usage:
#   ./scripts/post-community.sh --check
#   ./scripts/post-community.sh --channel cursor-forum
#   ./scripts/post-community.sh --channel reddit --open
#   ./scripts/post-community.sh --channel github --create-discussion
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HELPER="$ROOT/scripts/community_drafts.py"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}:$ROOT"

CHANNEL="cursor-forum"
OPEN=0
CREATE=0
CHECK=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --channel|-Channel) CHANNEL="$2"; shift 2 ;;
    --open|-Open) OPEN=1; shift ;;
    --create-discussion|-CreateDiscussion) CREATE=1; shift ;;
    --check|-Check) CHECK=1; shift ;;
    -h|--help)
      sed -n '2,8p' "$0"
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

cd "$ROOT"

if [[ "$CHECK" -eq 1 ]]; then
  echo "Checking community drafts..."
  python "$HELPER" check
  echo "OK — drafts match pyproject version and tool inventory."
  exit 0
fi

if [[ "$CREATE" -eq 1 ]]; then
  echo "Creating GitHub Discussion from github draft..."
  url="$(python "$HELPER" create-discussion)"
  echo "Created: $url"
  if [[ "$CHANNEL" == "github" ]]; then
    exit 0
  fi
fi

channels=("$CHANNEL")
if [[ "$CHANNEL" == "all" ]]; then
  channels=(cursor-forum reddit github)
fi

for ch in "${channels[@]}"; do
  json="$(python "$HELPER" show --channel "$ch")"
  title="$(python -c "import json,sys; print(json.load(sys.stdin)['title'])" <<<"$json")"
  body="$(python -c "import json,sys; print(json.load(sys.stdin)['body'])" <<<"$json")"
  url="$(python -c "import json,sys; print(json.load(sys.stdin).get('url',''))" <<<"$json")"
  path="$(python -c "import json,sys; print(json.load(sys.stdin)['path'])" <<<"$json")"
  version="$(python -c "import json,sys; print(json.load(sys.stdin).get('version'))" <<<"$json")"
  tools="$(python -c "import json,sys; print(json.load(sys.stdin).get('tools'))" <<<"$json")"

  echo ""
  echo "=== $ch ($path) ==="
  echo "Title: $title"
  echo "Version: $version  Tools: $tools"
  echo ""

  clip="Title: $title

$body"
  if command -v pbcopy >/dev/null 2>&1; then
    printf '%s' "$clip" | pbcopy
    echo "Copied title+body to clipboard (pbcopy)."
  elif command -v xclip >/dev/null 2>&1; then
    printf '%s' "$clip" | xclip -selection clipboard
    echo "Copied title+body to clipboard (xclip)."
  elif command -v wl-copy >/dev/null 2>&1; then
    printf '%s' "$clip" | wl-copy
    echo "Copied title+body to clipboard (wl-copy)."
  else
    echo "Clipboard tool not found; printing body:"
    echo "---- BODY ----"
    echo "$body"
    echo "--------------"
  fi

  if [[ "$OPEN" -eq 1 && -n "$url" ]]; then
    echo "Opening $url"
    if command -v xdg-open >/dev/null 2>&1; then
      xdg-open "$url" >/dev/null 2>&1 || true
    elif command -v open >/dev/null 2>&1; then
      open "$url" || true
    else
      echo "No opener; visit: $url"
    fi
  else
    echo "Next: paste clipboard into the compose UI ($url)"
  fi
done

echo ""
echo "Done."
