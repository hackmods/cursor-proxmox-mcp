"""Community announcement draft checks."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.community_drafts import (  # noqa: E402
    CHANNEL_FILES,
    check_all_drafts,
    load_channel,
    package_version,
)


def test_package_version_matches_pyproject():
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore

    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert package_version() == data["project"]["version"]


def test_all_channels_parse():
    for ch in CHANNEL_FILES:
        d = load_channel(ch)
        assert d.title
        assert d.body
        assert d.version
        assert d.tools


def test_check_all_drafts_clean():
    errs = check_all_drafts()
    assert errs == [], errs
