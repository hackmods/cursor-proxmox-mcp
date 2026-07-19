"""Wiki Tools.md must list every registered MCP tool (living guide lock)."""
from __future__ import annotations

from pathlib import Path

from proxmox_mcp.tools.inventory import ALL_TOOL_NAMES

ROOT = Path(__file__).resolve().parents[1]
TOOLS_MD = ROOT / "docs" / "wiki" / "Tools.md"
BEGIN = "<!-- BEGIN GENERATED TOOLS -->"
END = "<!-- END GENERATED TOOLS -->"


def test_wiki_tools_md_has_markers_and_generated_body():
    text = TOOLS_MD.read_text(encoding="utf-8")
    assert BEGIN in text
    assert END in text
    start = text.index(BEGIN) + len(BEGIN)
    end = text.index(END)
    body = text[start:end].strip()
    assert body, "generated tools section must be non-empty — run scripts/generate-wiki-tools.py"
    assert "| Tool | Description |" in body


def test_wiki_tools_md_lists_every_inventory_tool():
    text = TOOLS_MD.read_text(encoding="utf-8")
    missing = [name for name in sorted(ALL_TOOL_NAMES) if f"`{name}`" not in text]
    assert not missing, f"docs/wiki/Tools.md missing tools: {missing}"
    assert len(ALL_TOOL_NAMES) >= 100
