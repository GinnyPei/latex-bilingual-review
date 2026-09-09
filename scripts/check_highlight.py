#!/usr/bin/env python3
"""Regression: comment highlights must span cite/math/diff nodes, not one text node."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
VIEWER = SKILL_DIR / "templates" / "viewer.html"
SMOKE = {
    "title": "highlight-smoke",
    "source": "smoke.tex",
    "units": [
        {
            "id": "1-p1",
            "kind": "para",
            "sec": "1",
            "en": r"Frames with $\Phi_t$ and \cite{clip,prumerge} stay.",
            "zh": r"含 $\Phi_t$ 与 \cite{clip,prumerge} 的帧。",
        }
    ],
}


def extract_find() -> str:
    html = VIEWER.read_text(encoding="utf-8")
    start = html.index("function normSpace(")
    end = html.index("function isHiddenText(")
    chunk = html[start:end]
    if "function findQuoteOffsets(" not in chunk:
        raise SystemExit("viewer.html missing findQuoteOffsets")
    return chunk


def check_source(html: str, label: str) -> None:
    need = (
        "function visibleTextNodes(",
        "function findQuoteOffsets(",
        "CSS.highlights",
        "katex-mathml",
        "applyMarkWrap",
        "::highlight(lbr-comment)",
    )
    missing = [n for n in need if n not in html]
    if missing:
        raise SystemExit(f"{label}: missing {missing}")
    old = (
        "const i = node.nodeValue.indexOf(c.quote);\n"
        "      if (i < 0) continue;\n"
        "      const range = document.createRange();\n"
        "      range.setStart(node, i);"
    )
    if old in html and "findQuoteOffsets" not in html:
        raise SystemExit(f"{label}: still single-node surroundContents only")
    render_at = html.find("function render()")
    typeset_at = html.find("function typesetMath()")
    if render_at < 0 or typeset_at < 0 or "paintHighlights()" not in html[render_at:typeset_at]:
        raise SystemExit(f"{label}: render() must call paintHighlights on first draw")
    print(f"ok: {label} highlight spans markup")


def first_build_smoke() -> None:
    build = SKILL_DIR / "scripts" / "build_review.py"
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        review = td_path / "review.json"
        review.write_text(json.dumps(SMOKE, ensure_ascii=False), encoding="utf-8")
        comments = td_path / "smoke_comments.json"
        comments.write_text("[]\n", encoding="utf-8")
        out = td_path / "smoke.html"
        proc = subprocess.run(
            [
                sys.executable,
                str(build),
                str(review),
                "--out",
                str(out),
                "--comments",
                str(comments),
                "--title",
                "highlight-smoke",
            ],
            cwd=str(SKILL_DIR),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            sys.stderr.write(proc.stdout or "")
            sys.stderr.write(proc.stderr or "")
            raise SystemExit("first-build smoke: build_review.py failed")
        if not out.exists():
            raise SystemExit("first-build smoke: no HTML written")
        print("ok: first-build smoke")


def main() -> None:
    check_source(VIEWER.read_text(encoding="utf-8"), "templates/viewer.html")
    js = extract_find()
    harness = (
        js
        + """
function ok(cond, msg) { if (!cond) { console.error(msg); process.exit(1); } }
let r = findQuoteOffsets("say hello world now", "hello world");
ok(r && r.start === 4 && r.end === 15, "exact");
r = findQuoteOffsets("some frames [clip] stay put", "frames [clip] stay");
ok(r && r.start === 5 && r.end === 23, "cite span concat");
r = findQuoteOffsets("foo bar baz", "foo  bar");
ok(r && r.start === 0 && r.end === 7, "whitespace");
r = findQuoteOffsets("Phi_t is large here", "Phi_t is large Phi_t leftover mathml");
ok(r && r.start === 0 && "Phi_t is large here".slice(r.start, r.end).trim() === "Phi_t is large", "mathml prefix fallback");
process.stdout.write("ok: findQuoteOffsets");
"""
    )
    try:
        proc = subprocess.run(
            ["node", "-e", harness],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print("skip: node not found; source contract only")
        proc = None
    if proc is not None and proc.returncode != 0:
        sys.stderr.write(proc.stderr or proc.stdout or "node test failed\n")
        raise SystemExit(proc.returncode)
    if proc is not None:
        print(proc.stdout)
    html_args = [a for a in sys.argv[1:] if not a.startswith("-")]
    for arg in html_args:
        check_source(Path(arg).read_text(encoding="utf-8"), arg)
    if "--smoke" in sys.argv[1:] or not html_args:
        first_build_smoke()


if __name__ == "__main__":
    main()
