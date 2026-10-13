"""Count research facts with page URLs or resolvable numbered references.

Read-only. Run: python tools/citation_receipt.py RESULT.md [RESULT.md ...] --json
A reference match measures traceability, not whether the source supports the claim.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

KNOWN_KINDS = {"forum", "community-wiki", "editorial-en", "editorial-non-en", "datamining", "official-pr"}

LABEL = re.compile(r"\[(?:Confirmed|Single[ -]source)[^\]]*\]", re.IGNORECASE)
URL = re.compile(r"https?://[^\s)\]>\"']+", re.IGNORECASE)
MARKER = re.compile(r"\\\[(\d{1,3})\\\]|(?<![\w\]])\[(\d{1,3})\](?!\()|\[\^(\d{1,3})\]")
REF_NUMBERED = re.compile(r"^\s*(?:\\\[|\[)?(\d{1,3})(?:\\\]|\]|\.|\))\s+.*https?://", re.IGNORECASE)
REF_FOOTNOTE = re.compile(r"^\s*\[\^(\d{1,3})\]:\s*.*https?://", re.IGNORECASE)
KIND = re.compile(r"class:\s*([A-Za-z][A-Za-z-]*)")
DOMAIN = re.compile(r"\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|org|net|ru|gg|io|wiki|de|fr|jp|cn|co|uk|tv|info|ws)\b", re.IGNORECASE)
# Words a bare head-count label is made of; anything else in the label is taken as a named source.
TEMPLATE_WORDS = {
    "confirmed", "single", "source", "sources", "verify", "language", "languages", "lang", "official",
    "en", "ru", "and", "plus", "independent", "class", "s", "multiple", "community", "unverified",
}


def names_sources(label: str) -> bool:
    inner = label.strip("[]")
    inner = KIND.sub(" ", inner)
    if DOMAIN.search(inner) or ";" in inner:
        return True
    words = [w.lower() for w in re.findall(r"[A-Za-z]+", inner)]
    return any(w not in TEMPLATE_WORDS for w in words)


def receipt(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    refs = set()
    for line in lines:
        m = REF_NUMBERED.match(line) or REF_FOOTNOTE.match(line)
        if m:
            refs.add(int(m.group(1)))
    counts = {"url": 0, "footnote": 0, "site-named": 0, "count-only": 0}
    off_list: dict[str, int] = {}
    for line in lines:
        labels = LABEL.findall(line)
        if not labels:
            continue
        if URL.search(line):
            kind = "url"
        elif any(int(next(g for g in m.groups() if g)) in refs for m in MARKER.finditer(line)):
            kind = "footnote"
        elif any(names_sources(lb) for lb in labels):
            kind = "site-named"
        else:
            kind = "count-only"
        counts[kind] += 1
        for lb in labels:
            for k in KIND.findall(lb):
                k = k.lower()
                if k not in KNOWN_KINDS:
                    off_list[k] = off_list.get(k, 0) + 1
    urls = URL.findall(text)
    facts = sum(counts.values())
    return {
        "file": str(path),
        "facts": facts,
        **counts,
        "traceable": counts["url"] + counts["footnote"],
        "file_urls": len(urls),
        "distinct_urls": len(set(urls)),
        "reference_entries": len(refs),
        "off_list_kinds": off_list,
    }


def short_name(path: str) -> str:
    parts = Path(path).parts
    try:
        i = parts.index("Guides")
        game, phase = parts[i + 1], parts[i + 3]
        return f"{game} {phase} ({Path(path).name[:28]})"
    except (ValueError, IndexError):
        return Path(path).name


def table(rows: list[dict]) -> str:
    head = ("| File | Facts | Page address on the line | Via numbered reference | Sites named, no address "
            "| Head-count only | Traceable | Addresses in file |")
    out = [head, "|" + "---|" * 8]
    tot = {k: 0 for k in ("facts", "url", "footnote", "site-named", "count-only", "traceable", "file_urls")}
    for r in rows:
        out.append(f"| {short_name(r['file'])} | {r['facts']} | {r['url']} | {r['footnote']} | {r['site-named']} "
                   f"| {r['count-only']} | {r['traceable']} | {r['file_urls']} |")
        for k in tot:
            tot[k] += r[k]
    out.append(f"| **All {len(rows)} files** | **{tot['facts']}** | **{tot['url']}** | **{tot['footnote']}** "
               f"| **{tot['site-named']}** | **{tot['count-only']}** | **{tot['traceable']}** | **{tot['file_urls']}** |")
    kinds: dict[str, int] = {}
    for r in rows:
        for k, n in r["off_list_kinds"].items():
            kinds[k] = kinds.get(k, 0) + n
    if kinds:
        out.append("")
        out.append("Source-kind labels outside the six-value list: " +
                   ", ".join(f"`{k}` ({n})" for k, n in sorted(kinds.items(), key=lambda kv: -kv[1])))
    no_url = [short_name(r["file"]) for r in rows if r["file_urls"] == 0]
    out.append("")
    out.append(f"Files with no web address anywhere: {len(no_url)} of {len(rows)}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    files = []
    for value in a.paths:
        path = Path(value)
        files.extend(sorted(path.rglob("*.md")) if path.is_dir() else [path])
    if not files:
        print("no result files found", file=sys.stderr)
        return 1
    rows = [receipt(f) for f in files]
    if a.json:
        print(json.dumps(rows, indent=1))
    else:
        print(table(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
