#!/usr/bin/env python3
"""Regression: itemize must become a real <ul>, never visible &lt;ul&gt;."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
VIEWER = SKILL_DIR / "templates" / "viewer.html"
FIXTURE = (
    r"We summarize our contributions as follows. "
    r"\begin{itemize} \item First point. \item Second point. \end{itemize}"
)


def extract_js(html: str, label: str) -> str:
    start = html.index("function esc(")
    end = html.index("function spansHtml(")
    chunk = html[start:end]
    if r"\0L" not in chunk or "lists.push(" not in chunk:
        raise SystemExit(f"{label}: texToHtml must park itemize as \\0L before texInline/esc")
    return chunk


def check_render(html: str, label: str) -> None:
    js = extract_js(html, label)
    harness = (
        js
        + "\nconst src = "
        + repr(FIXTURE)
        + ";\nconst out = latexHtml(src);\n"
        + "if (!out.includes('<ul class=\"tex-list\">') || out.includes('&lt;ul')) {\n"
        + "  console.error(out);\n  process.exit(1);\n}\n"
        + "process.stdout.write(out);\n"
    )
    try:
        proc = subprocess.run(
            ["node", "-e", harness],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print(f"ok: {label} list source contract (node not found)")
        return
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or proc.stdout or "node test failed\n")
        raise SystemExit(proc.returncode)
    if not re.search(r"<ul class=\"tex-list\">", proc.stdout):
        raise SystemExit(f"{label}: expected a real <ul class=\"tex-list\">")
    if "&lt;ul" in proc.stdout:
        raise SystemExit(f"{label}: list tags were escaped")
    print(f"ok: {label} itemize renders as <ul class=\"tex-list\">")


def main() -> None:
    check_render(VIEWER.read_text(encoding="utf-8"), "templates/viewer.html")
    for arg in sys.argv[1:]:
        check_render(Path(arg).read_text(encoding="utf-8"), arg)


if __name__ == "__main__":
    main()
