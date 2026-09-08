#!/usr/bin/env python3
"""Align extracted units and attach Word-style word-level spans."""
from __future__ import annotations

import argparse
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

TOKEN = re.compile(
    r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^{}]*\})*"
    r"|\$[^$]+\$"
    r"|[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*"
    r"|[^\sA-Za-z0-9\\]"
)


def tokenize(text: str) -> list[str]:
    return TOKEN.findall(text) or ([text] if text else [])


def word_spans(old: str, new: str) -> list[dict]:
    if old == new:
        return [{"op": "eq", "text": new}]
    a, b = tokenize(old), tokenize(new)
    sm = SequenceMatcher(a=a, b=b, autojunk=False)
    spans: list[dict] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            spans.append({"op": "eq", "text": restore(b[j1:j2], new)})
        elif tag == "delete":
            spans.append({"op": "del", "text": restore(a[i1:i2], old)})
        elif tag == "insert":
            spans.append({"op": "ins", "text": restore(b[j1:j2], new)})
        else:
            spans.append({"op": "del", "text": restore(a[i1:i2], old)})
            spans.append({"op": "ins", "text": restore(b[j1:j2], new)})
    return merge_spans(spans)


def restore(tokens: list[str], original: str) -> str:
    """Join tokens with a single space except around punctuation."""
    if not tokens:
        return ""
    out = tokens[0]
    for t in tokens[1:]:
        if t in ",.;:!?)" or out.endswith("(") or out.endswith("\\"):
            out += t
        elif t.startswith("\\") or t.startswith("$"):
            out += " " + t
        else:
            out += " " + t
    return out


def merge_spans(spans: list[dict]) -> list[dict]:
    merged: list[dict] = []
    for s in spans:
        if not s["text"]:
            continue
        if merged and merged[-1]["op"] == s["op"]:
            merged[-1]["text"] += s["text"] if s["text"].startswith((" ", ",", ".")) else " " + s["text"]
        else:
            merged.append(dict(s))
    return merged


def norm(u: dict) -> str:
    return re.sub(r"\s+", " ", (u.get("en") or "")).strip()


def align(old_units: list[dict], new_units: list[dict]) -> list[dict]:
    old_by_id = {u["id"]: u for u in old_units}
    used_old: set[str] = set()
    out: list[dict] = []

    def attach(new_u: dict, old_u: dict | None) -> dict:
        item = dict(new_u)
        if old_u is None:
            item["old_en"] = None
            item["spans"] = [{"op": "ins", "text": new_u.get("en") or ""}]
            return item
        used_old.add(old_u["id"])
        item["old_en"] = old_u.get("en")
        if new_u.get("kind") == "eq":
            if norm(old_u) == norm(new_u):
                item["spans"] = [{"op": "eq", "text": new_u["en"]}]
            else:
                item["spans"] = [
                    {"op": "del", "text": old_u["en"]},
                    {"op": "ins", "text": new_u["en"]},
                ]
        else:
            item["spans"] = word_spans(old_u.get("en") or "", new_u.get("en") or "")
        return item

    # 1) same id
    for nu in new_units:
        if nu["id"] in old_by_id:
            out.append(attach(nu, old_by_id[nu["id"]]))
            continue
        # 2) same kind+sec+title or similar text
        candidates = [
            ou
            for ou in old_units
            if ou["id"] not in used_old
            and ou.get("kind") == nu.get("kind")
            and ou.get("sec") == nu.get("sec")
        ]
        best = None
        best_r = 0.55
        for ou in candidates:
            r = SequenceMatcher(None, norm(ou), norm(nu)).ratio()
            if r > best_r:
                best, best_r = ou, r
        if best is None:
            # global leftover
            for ou in old_units:
                if ou["id"] in used_old or ou.get("kind") != nu.get("kind"):
                    continue
                r = SequenceMatcher(None, norm(ou), norm(nu)).ratio()
                if r > best_r:
                    best, best_r = ou, r
        out.append(attach(nu, best))

    for ou in old_units:
        if ou["id"] in used_old:
            continue
        out.append(
            {
                **ou,
                "id": ou["id"] + "-removed",
                "en": "",
                "old_en": ou.get("en"),
                "zh": "",
                "spans": [{"op": "del", "text": ou.get("en") or ""}],
            }
        )
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("old_json")
    ap.add_argument("new_json")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    old = json.loads(Path(args.old_json).read_text(encoding="utf-8"))
    new = json.loads(Path(args.new_json).read_text(encoding="utf-8"))
    units = align(old["units"], new["units"])
    doc = {
        "title": new.get("title") or old.get("title"),
        "source": new.get("source"),
        "old_ref": old.get("old_ref") or old.get("source"),
        "units": units,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {args.out} ({len(units)} units)")


if __name__ == "__main__":
    main()
