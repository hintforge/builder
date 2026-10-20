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

# "Corroborated" is read-side tolerance only: results written before the label set was fixed to
# Confirmed / Single source used it. Briefs must not ask for it.
LABEL = re.compile(r"\[(?:Confirmed|Corroborated|Single[ -]source)[^\]]*\]", re.IGNORECASE)
URL = re.compile(r"https?://[^\s)\]>\"']+", re.IGNORECASE)
MARKER = re.compile(r"\\\[(\d{1,3})\\\]|(?<![\w\]])\[(\d{1,3})\](?!\()|\[\^(\d{1,3})\]")
# A chain of numbered markers after the first ("[1][4]", the brief's pinned form): each id counts.
# The chain must start at a marker MARKER itself accepts, so a reference link "[map][1]" stays out.
MARKER_CHAIN = re.compile(r"(?<![\w\]])\[\d{1,3}\]((?:\[\d{1,3}\])+)(?!\()")
REF_NUMBERED = re.compile(r"^\s*(?:\\\[|\[)?(\d{1,3})(?:\\\]|\]|\.|\))\s+.*https?://", re.IGNORECASE)
REF_FOOTNOTE = re.compile(r"^\s*\[\^(\d{1,3})\]:\s*.*https?://", re.IGNORECASE)
# Reference entries written with an R prefix: "R12 https://...", "R12. https://...", "[R12] https://...",
# "R12: https://...", or a table row whose first cell is the id and second cell the address.
REF_R_ENTRY = re.compile(r"^\s*(?:\\\[|\[)?R(\d{1,3})(?:\\\]|\])?[.:)]?\s+.*https?://")
REF_TABLE_ENTRY = re.compile(r"^\s*\|\s*R?(\d{1,3})\s*\|\s*<?https?://")
# Reference mentions on a fact line: R12, R31-R48, and "refs 3, 5, 9-11".
R_TOKEN = re.compile(r"(?<![A-Za-z0-9])R(\d{1,3})(?:\s*[-–]\s*R?(\d{1,3}))?(?![A-Za-z0-9])")
REFS_PHRASE = re.compile(r"\brefs?\.?\s+((?:R?\d{1,3}(?:\s*[-–]\s*R?\d{1,3})?(?:\s*(?:,|&|and)\s*)?)+)", re.IGNORECASE)
NUM_RANGE = re.compile(r"R?(\d{1,3})(?:\s*[-–]\s*R?(\d{1,3}))?")
TABLE_SEP = re.compile(r"^\s*\|[\s:|-]+\|?\s*$")
REF_HEADER = re.compile(r"\brefs?\b", re.IGNORECASE)
IDS_ONLY = re.compile(r"[R\d,&\s–-]+")
MAX_RANGE = 200
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


def span(lo: str, hi: str | None) -> list[int]:
    a = int(lo)
    b = int(hi) if hi else a
    if b < a or b - a > MAX_RANGE:
        return [a]
    return list(range(a, b + 1))


def ids_in_text(text: str) -> set[int]:
    """Reference ids a line of prose points at: [3], [^3], R3, R31-R48, 'refs 3, 5, 9-11'."""
    found: set[int] = set()
    for m in MARKER.finditer(text):
        found.add(int(next(g for g in m.groups() if g)))
    for m in MARKER_CHAIN.finditer(text):
        found.update(int(n) for n in re.findall(r"\d{1,3}", m.group(1)))
    for m in R_TOKEN.finditer(text):
        found.update(span(m.group(1), m.group(2)))
    for m in REFS_PHRASE.finditer(text):
        for n in NUM_RANGE.finditer(m.group(1)):
            found.update(span(n.group(1), n.group(2)))
    return found


def split_cells(line: str) -> list[str]:
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", body)]


def ref_cell_ids(cell: str) -> set[int]:
    """A cell under a Ref / Refs header: R-prefixed ids anywhere; bare numbers only when the cell is just ids."""
    found = ids_in_text(cell)
    if IDS_ONLY.fullmatch(cell.replace("and", " ")) and cell.strip():
        for n in NUM_RANGE.finditer(cell):
            found.update(span(n.group(1), n.group(2)))
    return found


def receipt(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    refs = set()
    entry_lines = set()
    for i, line in enumerate(lines):
        m = REF_NUMBERED.match(line) or REF_FOOTNOTE.match(line) or REF_R_ENTRY.match(line) or REF_TABLE_ENTRY.match(line)
        if m and not LABEL.search(line):  # a line carrying a source label is a fact, not a reference entry
            refs.add(int(m.group(1)))
            entry_lines.add(i)
    counts = {"url": 0, "footnote": 0, "site-named": 0, "count-only": 0}
    off_list: dict[str, int] = {}
    unresolved: dict[int, int] = {}
    table_rows = 0
    table_rows_resolved = 0
    header: list[str] | None = None
    for i, line in enumerate(lines):
        is_table = line.lstrip().startswith("|")
        ref_ids: set[int] = set()
        row_has_ref_col = False
        if is_table:
            if TABLE_SEP.match(line):
                header = split_cells(lines[i - 1]) if i > 0 and lines[i - 1].lstrip().startswith("|") else None
                continue
            if header and i + 1 < len(lines) and TABLE_SEP.match(lines[i + 1]):
                continue  # the header row itself
            if header and i not in entry_lines:
                for col, cell in zip(range(len(header)), split_cells(line)):
                    if REF_HEADER.search(header[col]):
                        row_has_ref_col = True
                        ref_ids |= ref_cell_ids(cell)
        else:
            header = None
        labels = LABEL.findall(line)
        if i in entry_lines:
            continue
        ref_ids |= ids_in_text(line) if (labels or row_has_ref_col) else set()
        if row_has_ref_col and not labels:
            table_rows += 1
            if ref_ids and all(n in refs for n in ref_ids):
                table_rows_resolved += 1
        for n in ref_ids:
            if n not in refs:
                unresolved[n] = unresolved.get(n, 0) + 1
        if not labels:
            continue
        if URL.search(line):
            kind = "url"
        elif ref_ids & refs:
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
        "table_rows": table_rows,
        "table_rows_resolved": table_rows_resolved,
        "unresolved": sum(unresolved.values()),
        "unresolved_ids": sorted(unresolved),
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
            "| Head-count only | Traceable | Addresses in file | Reference-column rows | Unresolved references |")
    out = [head, "|" + "---|" * 10]
    tot = {k: 0 for k in ("facts", "url", "footnote", "site-named", "count-only", "traceable", "file_urls",
                          "table_rows", "unresolved")}
    for r in rows:
        out.append(f"| {short_name(r['file'])} | {r['facts']} | {r['url']} | {r['footnote']} | {r['site-named']} "
                   f"| {r['count-only']} | {r['traceable']} | {r['file_urls']} | {r['table_rows']} | {r['unresolved']} |")
        for k in tot:
            tot[k] += r[k]
    out.append(f"| **All {len(rows)} files** | **{tot['facts']}** | **{tot['url']}** | **{tot['footnote']}** "
               f"| **{tot['site-named']}** | **{tot['count-only']}** | **{tot['traceable']}** | **{tot['file_urls']}** "
               f"| **{tot['table_rows']}** | **{tot['unresolved']}** |")
    for r in rows:
        if r["unresolved_ids"]:
            out.append("")
            out.append(f"Unresolved in {short_name(r['file'])}: " + ", ".join(str(n) for n in r["unresolved_ids"]))
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
