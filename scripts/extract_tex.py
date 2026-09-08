#!/usr/bin/env python3
"""Extract section/paragraph/equation units from a LaTeX file or git revision."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

BEGIN_DOC = re.compile(r"\\begin\{document\}")
END_DOC = re.compile(r"\\end\{document\}")
COMMENT = re.compile(r"(?<!\\)%.*", re.M)
ENV_DROP = re.compile(
    r"\\begin\{(figure\*?|table\*?|CCSXML)\}.*?\\end\{\1\}",
    re.S,
)
SECTION = re.compile(
    r"\\(section|subsection|subsubsection)\*?\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}"
)
PARAGRAPH_CMD = re.compile(r"\\paragraph\*?\{([^{}]*)\}")
EQ_ENV = re.compile(
    r"\\begin\{(equation\*?|align\*?|displaymath)\}(.*?)\\end\{\1\}",
    re.S,
)
EQ_BRAK = re.compile(r"\\\[(.*?)\\\]", re.S)
ABSTRACT = re.compile(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", re.S)
SKIP_LINE = re.compile(
    r"^\\(maketitle|tableofcontents|bibliography|bibliographystyle|"
    r"keywords|ccsdesc|label|input|FloatBarrier)(\b|\{)"
)
FRONT_CMDS = [
    re.compile(r"\\title(\[[^\]]*\])?\{(?:[^{}]|\{[^{}]*\})*\}", re.S),
    re.compile(r"\\author(\[[^\]]*\])?\{(?:[^{}]|\{[^{}]*\})*\}", re.S),
    re.compile(r"\\affiliation\{(?:[^{}]|\{[^{}]*\})*\}", re.S),
    re.compile(r"\\renewcommand\{[^}]*\}\{[^}]*\}"),
    re.compile(r"\\ccsdesc(\[[^\]]*\])?\{[^}]*\}"),
    re.compile(r"\\keywords\{[^}]*\}"),
    re.compile(r"\\input\{[^}]+\}"),
]


def strip_comments(src: str) -> str:
    return COMMENT.sub("", src)


def load_tex(path: Path, git_rev: str | None) -> str:
    if git_rev:
        rel = path.as_posix()
        proc = subprocess.run(
            ["git", "show", f"{git_rev}:{rel}"],
            cwd=path.parent if path.is_absolute() else Path.cwd(),
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            proc = subprocess.run(
                ["git", "show", f"{git_rev}:{path.name}"],
                capture_output=True,
                text=True,
            )
        if proc.returncode != 0:
            raise SystemExit(proc.stderr or f"git show failed for {git_rev}:{path}")
        return proc.stdout
    return path.read_text(encoding="utf-8")


def body_only(src: str) -> str:
    m0 = BEGIN_DOC.search(src)
    if m0:
        src = src[m0.end() :]
    m1 = END_DOC.search(src)
    if m1:
        src = src[: m1.start()]
    src = strip_comments(src)
    src = ENV_DROP.sub("\n\n", src)
    for rx in FRONT_CMDS:
        src = rx.sub("\n\n", src)
    return src


def clean_inline(s: str) -> str:
    s = PARAGRAPH_CMD.sub(lambda m: m.group(1).strip() + " ", s)
    s = re.sub(r"\\label\{[^}]*\}", "", s)
    s = re.sub(r"[ \t]+\n", "\n", s)
    return s.strip()


def section_number_tracker():
    counts = [0, 0, 0]

    def feed(level: str) -> str:
        idx = {"section": 0, "subsection": 1, "subsubsection": 2}[level]
        counts[idx] += 1
        for j in range(idx + 1, 3):
            counts[j] = 0
        if level == "section":
            return str(counts[0])
        if level == "subsection":
            return f"{counts[0]}.{counts[1]}"
        return f"{counts[0]}.{counts[1]}.{counts[2]}"

    return feed


def extract(src: str, section_filter: set[str] | None) -> list[dict]:
    src = body_only(src)
    units: list[dict] = []
    feed = section_number_tracker()
    counters = {"para": 0, "eq": 0}

    def want(num: str) -> bool:
        if section_filter is None:
            return True
        filt = { {"abstract": "abs"}.get(s, s) for s in section_filter }
        top = num.split(".")[0]
        return num in filt or top in filt

    def add_text_block(sec: str, text: str) -> None:
        text = clean_inline(text)
        if not text:
            return
        eqs: list[str] = []

        def park_env(m: re.Match) -> str:
            eqs.append(m.group(0).strip())
            return f"\n\n@@EQ{len(eqs)-1}@@\n\n"

        def park_brak(m: re.Match) -> str:
            eqs.append("\\[" + m.group(1).strip() + "\\]")
            return f"\n\n@@EQ{len(eqs)-1}@@\n\n"

        combined = EQ_ENV.sub(park_env, text)
        combined = EQ_BRAK.sub(park_brak, combined)
        for block in re.split(r"\n{2,}", combined):
            block = block.strip()
            if not block:
                continue
            parked = re.fullmatch(r"@@EQ(\d+)@@", block)
            if parked:
                counters["eq"] += 1
                units.append(
                    {
                        "id": f"{sec}-eq{counters['eq']}",
                        "kind": "eq",
                        "sec": sec,
                        "en": eqs[int(parked.group(1))],
                        "zh": "",
                    }
                )
                continue
            lines = [ln for ln in block.splitlines() if not SKIP_LINE.match(ln.strip())]
            block = "\n".join(lines).strip()
            if re.match(r"^\\[a-zA-Z]+(\[[^\]]*\])?\{[^}]*\}\s*$", block):
                continue
            if len(re.sub(r"\s+", "", block)) < 2:
                continue
            counters["para"] += 1
            units.append(
                {
                    "id": f"{sec}-p{counters['para']}",
                    "kind": "para",
                    "sec": sec,
                    "en": block,
                    "zh": "",
                }
            )

    abs_m = ABSTRACT.search(src)
    if abs_m and want("abs"):
        units.append(
            {"id": "abs-h", "kind": "sec", "sec": "abs", "en": "Abstract", "zh": "", "title": "Abstract"}
        )
        counters["para"] = 0
        counters["eq"] = 0
        add_text_block("abs", abs_m.group(1))
    src = ABSTRACT.sub("\n\n", src)

    parts = SECTION.split(src)
    i = 1
    while i + 2 < len(parts):
        level, title, text = parts[i], parts[i + 1], parts[i + 2]
        num = feed(level)
        title_plain = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", title).strip()
        i += 3
        if not want(num):
            continue
        kind = "sec" if level == "section" else "sub"
        units.append(
            {
                "id": f"{num}-h",
                "kind": kind,
                "sec": num,
                "en": f"{num} {title_plain}",
                "zh": "",
                "title": title_plain,
            }
        )
        counters["para"] = 0
        counters["eq"] = 0
        add_text_block(num, text)

    return units


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tex")
    ap.add_argument("--git", dest="git_rev")
    ap.add_argument("--sections", help="comma-separated section numbers, e.g. 4,5")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    path = Path(args.tex)
    src = load_tex(path, args.git_rev)
    filt = None
    if args.sections:
        filt = {s.strip() for s in args.sections.split(",") if s.strip()}
    units = extract(src, filt)
    out = {
        "title": path.stem,
        "source": str(path),
        "old_ref": args.git_rev,
        "units": units,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {args.out} ({len(units)} units)")


if __name__ == "__main__":
    main()
