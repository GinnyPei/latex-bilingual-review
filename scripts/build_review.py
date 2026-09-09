#!/usr/bin/env python3
"""Build the bilingual / track-changes review HTML from review JSON."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

MATH_FIELD = ("en", "zh", "old_en")
DOUBLED_CMD = re.compile(r"\\{2,}([a-zA-Z]+)")


def fix_math_inner(inner: str) -> str:
    """$\\\\lambda$ (two backslashes) → $\\lambda$ so KaTeX sees a command, not a linebreak."""
    return DOUBLED_CMD.sub(r"\\\1", inner)


def normalize_math(s: str) -> str:
    """Undo JS-string over-escaping and prefer $...$ like extracted English."""
    if not s:
        return s
    for _ in range(4):
        if r"\\(" not in s and r"\\[" not in s and r"\\)" not in s:
            break
        s = (
            s.replace(r"\\(", r"\(")
            .replace(r"\\)", r"\)")
            .replace(r"\\[", r"\[")
            .replace(r"\\]", r"\]")
        )
    s = re.sub(r"\\\((.+?)\\\)", r"$\1$", s, flags=re.S)
    s = re.sub(r"\$([^$]+)\$", lambda m: "$" + fix_math_inner(m.group(1)) + "$", s)
    s = re.sub(
        r"\\\[(.+?)\\\]",
        lambda m: "\\[" + fix_math_inner(m.group(1)) + "\\]",
        s,
        flags=re.S,
    )
    return s


def clean_units(units: list) -> None:
    for u in units:
        for key in MATH_FIELD:
            if isinstance(u.get(key), str):
                u[key] = normalize_math(u[key])
        spans = u.get("spans")
        if isinstance(spans, list):
            for sp in spans:
                if isinstance(sp.get("text"), str):
                    sp["text"] = normalize_math(sp["text"])

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "templates" / "viewer.html"


def ensure_katex(html_out: Path) -> None:
    dest = html_out.parent / "vendor" / "katex"
    if (dest / "katex.min.js").exists():
        return
    src = SKILL_DIR / "vendor" / "katex"
    if not (src / "katex.min.js").exists():
        print("warning: no vendor/katex next to HTML or in the skill; formulas may not render")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest)
    print(f"copied KaTeX to {dest}")


def verify_generated(html_out: Path) -> None:
    """First build must ship working highlight/button code; do not wait for a second pass."""
    checks = (
        SKILL_DIR / "scripts" / "check_list_html.py",
        SKILL_DIR / "scripts" / "check_sel_btn.py",
        SKILL_DIR / "scripts" / "check_highlight.py",
        SKILL_DIR / "scripts" / "check_margin.py",
    )
    for script in checks:
        if not script.exists():
            raise SystemExit(f"missing {script.name}; first-build verify cannot run")
        proc = subprocess.run(
            [sys.executable, str(script), str(html_out)],
            cwd=str(SKILL_DIR),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            sys.stderr.write(proc.stdout or "")
            sys.stderr.write(proc.stderr or "")
            raise SystemExit(f"first-build check failed: {script.name}")
        extra = (proc.stdout or "").strip()
        if extra:
            print(extra)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("review_json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="")
    ap.add_argument("--comments", default="")
    args = ap.parse_args()
    review_path = Path(args.review_json)
    doc = json.loads(review_path.read_text(encoding="utf-8"))
    clean_units(doc.get("units") or [])
    review_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.title:
        doc["title"] = args.title
    has_diff = any(u.get("spans") for u in doc.get("units", []))
    doc["has_diff"] = has_diff
    stem = Path(args.out).stem
    doc["storage_key"] = "lbr-" + stem
    comments_path = Path(args.comments) if args.comments else Path(args.out).with_name(stem + "_comments.json")
    if comments_path.exists():
        try:
            loaded = json.loads(comments_path.read_text(encoding="utf-8"))
            doc["comments"] = loaded if isinstance(loaded, list) else []
        except json.JSONDecodeError:
            doc["comments"] = []
    else:
        comments_path.write_text("[]\n", encoding="utf-8")
        doc["comments"] = []
    doc["comments_file"] = comments_path.name

    html = TEMPLATE.read_text(encoding="utf-8")
    payload = json.dumps(doc, ensure_ascii=False)
    html = html.replace("/*__REVIEW_DATA__*/null", payload)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    ensure_katex(out)
    verify_generated(out)
    print(f"wrote {out}")
    print(f"comments sidecar: {comments_path}")


if __name__ == "__main__":
    main()
