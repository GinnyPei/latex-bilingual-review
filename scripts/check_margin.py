#!/usr/bin/env python3
"""First HTML: one global comment rail, toggled as a whole, cards align to quotes."""
from __future__ import annotations

import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
VIEWER = SKILL_DIR / "templates" / "viewer.html"


def check(html: str, label: str) -> None:
    need = (
        'id="margin"',
        'id="margin-cards"',
        "function layoutMarginComments(",
        "function quoteRangeForComment(",
        "notes-hidden",
        "隐藏批注栏",
    )
    missing = [n for n in need if n not in html]
    if missing:
        raise SystemExit(f"{label}: missing {missing}")
    if 'class="pair-notes"' in html:
        raise SystemExit(f"{label}: comments belong in the global #margin rail, not per-pair gutters")
    print(f"ok: {label} global comment rail")


def main() -> None:
    check(VIEWER.read_text(encoding="utf-8"), "templates/viewer.html")
    for arg in sys.argv[1:]:
        check(Path(arg).read_text(encoding="utf-8"), arg)


if __name__ == "__main__":
    main()
