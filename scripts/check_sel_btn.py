#!/usr/bin/env python3
"""Regression: comment button must be fixed to mouseup, not scrollY+range rect."""
from __future__ import annotations

import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
VIEWER = SKILL_DIR / "templates" / "viewer.html"
OLD_PLACE = re.compile(
    r"window\.scroll[XY].*getBoundingClientRect|getBoundingClientRect\(\)[\s\S]{0,120}window\.scroll",
    re.M,
)


def check(html: str, label: str) -> None:
    if not re.search(r"#sel-btn\s*\{[^}]*position\s*:\s*fixed", html):
        raise SystemExit(f"{label}: #sel-btn must be position:fixed")
    if re.search(r"#sel-btn\s*\{[^}]*position\s*:\s*absolute", html):
        raise SystemExit(f"{label}: #sel-btn must not be position:absolute")
    if "placeSelBtn" not in html or "clientX" not in html or "pairFromSelection" not in html:
        raise SystemExit(f"{label}: missing placeSelBtn / clientX / pairFromSelection")
    if OLD_PLACE.search(html):
        raise SystemExit(f"{label}: reverted to window.scroll + getBoundingClientRect placement")
    print(f"ok: {label} sel-btn is fixed to mouseup")


def main() -> None:
    check(VIEWER.read_text(encoding="utf-8"), "templates/viewer.html")
    for arg in sys.argv[1:]:
        p = Path(arg)
        check(p.read_text(encoding="utf-8"), str(p))


if __name__ == "__main__":
    main()
