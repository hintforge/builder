#!/usr/bin/env python3
"""tier_sweep.py -- tier-consistency sweep (report-only, never edits a corpus, no network, no model call).

Run by the doctor procedure (doctor.md "Integrity check" and the tier repair in step 5). The integrity
validator checks that tags EXIST; this checks that a name a guide hides is hidden EVERYWHERE. For every
name that appears in content tagged above tier 0, it lists each other place the same name appears under
a lower tier or untagged -- the places a reader at a lower dial would see a name the guide meant to
withhold.

Why a sibling script and not a validator mode: the validator is a per-claim presence check with fixed
counts; this is a whole-guide cross-reference with its own output. It imports the validator's parser
helpers (fences, headings, metadata lines) so the two read a file the same way.

What it reads. A line's tier is (enemy-tier, puzzle-tier), taken from, strongest first:
  1. a row tier column (`tier` header, `spoiler:` vocabulary: none=0, progression=1, late-game=2,
     story=3) -- both dials get the mapped value;
  2. the `_source:` line or `- **enemy-tier:**` bullets that cover the claim, paragraph or table
     immediately ABOVE them (the reach rule in templates/claim_format.md);
  3. a standalone tier line (enemy-tier + puzzle-tier only) that governs the lines after it until the
     next H1-H3 heading or the next such line.
A heading takes the tier of the first tagged line under it before the next heading. A line none of
these reach is untagged. Missing a dial counts as 0; a `spoiler:` tag stands in for both dials when the
tiers are absent. Files whose `status` is `scaffold`, fenced code, and the metadata lines themselves
are not read.

What counts as a NAME. Only content tagged above tier 0 (enemy-tier or puzzle-tier > 0) supplies names,
and only from these name-bearing places:
  - a heading's text (parenthetical and text after ` -- ` dropped);
  - a **bold span** that is not a field label (no trailing colon);
  - the first cell of a table row;
  - a `backticked identifier` that has a capital, digit, `_` or `-` and is not a path, file name or
    `key: value`.
A name must be 4-60 characters, at most 6 words, start with a letter, contain a capital letter or `_`/`-`
(ordinary lowercase phrases are noise), hold no `:` or quote mark, and not be in STOP_NAMES (structural
words such as "Notes" or "Overview"). A leading "The"/"A"/"An" is dropped. Names match case-insensitively as whole words anywhere in the guide's corpus
files. A name defined at several tiers takes the strictest (highest) tier on each dial.

What counts as a HIT. An occurrence is a hit when it is untagged, or when its tier is below the name's
tier on either dial (a reader whose dials cover the occurrence but not the name sees the name). The
tagged content that defines the name is not a hit against itself. False positives are expected from
names that are also ordinary words; the output is for a person to read, not to gate on.

Usage:
  tier_sweep.py <guide_dir> [<guide_dir> ...] [--json out.json] [--exit-code] [--quiet] [--max-places N]

Exit 0 on a completed run (report tool, never a blocking gate); `--exit-code` makes any hit exit 1.
Exit 2 = usage error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import integrity_validator as V  # noqa: E402

RULES_REVISION = "ts-2026.10.19-1"

SPOILER_TIER = {"none": 0, "progression": 1, "late-game": 2, "story": 3}
STOP_NAMES = {
    "note", "notes", "warning", "important", "overview", "summary", "source", "sources", "claim", "claims",
    "confidence", "status", "caution", "tip", "tips", "example", "examples", "details", "detail", "todo",
    "name", "effect", "effects", "description", "trigger", "cost", "none", "true", "false", "yes", "high",
    "medium", "low", "tier", "tiers", "category", "mainline", "spoiler", "unknown", "unspecified", "default",
    "table", "section", "sections", "index", "limits", "limitations", "open", "resolved", "other", "misc",
    "general", "mechanics", "items", "enemies", "bosses", "puzzles", "locations", "lore", "story",
    "boss", "entry", "exit", "enemy", "item", "reward", "rewards", "location", "type", "goal", "objective",
    "requirement", "requirements", "prerequisite", "prereq", "result", "outcome", "puzzle", "zone", "zones",
}
BOLD_RE = re.compile(r"\*\*([^*\n]+?)\*\*")
TICK_RE = re.compile(r"`([^`\n]+)`")
IDENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.\- ]*$")


# ---------------------------------------------------------------- tier map

def body_tiers(body: str):
    """(enemy, puzzle) from an inline metadata body, or None when it carries neither tiers nor spoiler."""
    me = V.TIER_FIELD_RE["enemy-tier"].search(body)
    mp = V.TIER_FIELD_RE["puzzle-tier"].search(body)
    if me or mp:
        return int(me.group(1)) if me else 0, int(mp.group(1)) if mp else 0
    ms = re.search(r"(?<![\w-])spoiler\s*:\s*([a-z-]+)", body, re.I)
    if ms and ms.group(1).lower() in SPOILER_TIER:
        t = SPOILER_TIER[ms.group(1).lower()]
        return t, t
    return None


def map_file(lines: list[str]):
    """Per-line tiers plus the name definitions found in tagged content.
    Returns (tiers, meta, in_fence, defs) -- tiers[i] is (e, p) or None; defs is a list of (name, (e, p), i)."""
    n = len(lines)
    stripped = [ln.strip() for ln in lines]
    in_fence, heading = V.mark_structure(lines)
    tiers = [None] * n
    meta = [False] * n

    # 3. standalone section tier lines (weakest).
    cur = None
    for i in range(n):
        if heading[i] and heading[i] <= 3:
            cur = None
        if in_fence[i] or heading[i]:
            continue
        t = V.scan_tag_line(stripped[i])
        if t is not None:
            cur = t
            meta[i] = True
        elif cur is not None and stripped[i]:
            tiers[i] = cur

    def assign_above(i, tg):
        j = i - 1
        while j >= 0 and not stripped[j]:
            j -= 1
        while j >= 0 and stripped[j] and not heading[j] and not in_fence[j] and not meta[j]:
            tiers[j] = tg
            j -= 1

    # 2. per-claim metadata, covering what sits above it.
    i = 0
    while i < n:
        if in_fence[i]:
            i += 1
            continue
        s = stripped[i]
        if s.startswith("_") and V.INLINE_SOURCE_RE.match(V.inline_body(s)):
            joined, last = V.join_wrapped_metadata(lines, stripped, i, in_fence, heading)
            for k in range(i, last + 1):
                meta[k] = True
            tg = body_tiers(V.inline_body(joined))
            if tg is not None:
                assign_above(i, tg)
            i = last + 1
            continue
        if V.BULLET_FIELD_LINE_RE.match(lines[i]):
            fields, end = V.parse_bullet_run(lines, i)
            if V.tier_present(fields.get("enemy-tier")) and V.tier_present(fields.get("puzzle-tier")):
                tg = (int(re.match(r"\s*(\d)", fields["enemy-tier"]).group(1)),
                      int(re.match(r"\s*(\d)", fields["puzzle-tier"]).group(1)))
                for k in range(i, end):
                    tiers[k] = tg
            i = end
            continue
        i += 1

    # 1. row tier column (strongest).
    row_first = {}  # line index -> first cell text, for every data row of every table
    i = 0
    while i < n:
        if in_fence[i] or not V.is_table_row(stripped[i]):
            i += 1
            continue
        end = i
        while end + 1 < n and not in_fence[end + 1] and V.is_table_row(stripped[end + 1]):
            end += 1
        header = V.table_cells(stripped[i])
        sep_ok = end > i and all(V.TABLE_SEPARATOR_CELL_RE.match(c) for c in V.table_cells(stripped[i + 1]))
        if sep_ok:
            col = next((k for k, c in enumerate(header) if c.lower() == "tier"), None)
            for r in range(i + 2, end + 1):
                cells = V.table_cells(stripped[r])
                row_first[r] = cells[0] if cells else ""
                if col is not None and col < len(cells) and cells[col].lower() in SPOILER_TIER:
                    t = SPOILER_TIER[cells[col].lower()]
                    tiers[r] = (t, t)
        i = end + 1

    # headings take the tier of the first tagged line under them, before the next heading.
    for i in range(n):
        if not heading[i]:
            continue
        for j in range(i + 1, n):
            if heading[j]:
                break
            if tiers[j] is not None and not meta[j]:
                tiers[i] = tiers[j]
                break

    # names, from tagged content above tier 0.
    defs = []
    for i in range(n):
        tg = tiers[i]
        if in_fence[i] or meta[i] or tg is None or (tg[0] == 0 and tg[1] == 0):
            continue
        cands = []
        if heading[i]:
            text = re.sub(r"^\s*#+\s*|\s*#+\s*$", "", lines[i])
            text = re.sub(r"\([^)]*\)", "", text.split(" -- ")[0])
            cands.append(text)
        elif i in row_first:
            cands.append(row_first[i])
        for m in BOLD_RE.finditer(lines[i]):
            if not m.group(1).strip().endswith(":"):
                cands.append(m.group(1))
        for m in TICK_RE.finditer(lines[i]):
            tok = m.group(1).strip()
            if (IDENT_RE.match(tok) and re.search(r"[A-Z0-9_\-]", tok)
                    and not re.search(r"\.(md|py|json|txt|html|ps1|sh)$", tok, re.I)):
                cands.append(tok)
        for c in cands:
            name = re.sub(r"\s+", " ", re.sub(r"[*_`]", "", c)).strip(" .,:;-\"'")
            name = re.sub(r"^(?:the|a|an)\s+", "", name, flags=re.I)
            if usable_name(name):
                defs.append((name, tg, i))
    return tiers, meta, in_fence, defs


def usable_name(name: str) -> bool:
    """4-60 characters, at most 6 words, starts with a letter, has a capital or a `_`/`-` (game names are
    capitalized; ordinary lowercase phrases are noise), no `:` or quote mark, not a structural word."""
    return (4 <= len(name) <= 60 and len(name.split()) <= 6 and name[0].isalpha()
            and re.search(r"[A-Z_\-]", name) is not None and not re.search(r"[:\"]", name)
            and name.lower() not in STOP_NAMES)


# ------------------------------------------------------------------ sweep

def lower_than(occ, name_tier) -> bool:
    return occ is None or occ[0] < name_tier[0] or occ[1] < name_tier[1]


def fmt_tier(t) -> str:
    return "untagged" if t is None else f"tier {t[0]}/{t[1]}"


def sweep_guide(guide_dir: Path) -> dict:
    result = {"guide": guide_dir.name, "parsed": False, "error": None, "files_read": 0,
              "names_above_tier_0": 0, "hits": []}
    if V.find_manifest(guide_dir) is None:
        result["error"] = "no manifest found at nav/architecture.md or architecture_manifest.md"
        return result
    result["parsed"] = True
    files = []  # (rel, lines, tiers, meta, in_fence)
    names = {}  # lowered name -> {"name", "tier", "where": [(rel, line)]}
    for rel, path in V.iter_corpus_files(guide_dir):
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        raw, _ = V.file_status(lines)
        if raw is not None and V.status_word(raw) == "scaffold":
            continue
        tiers, meta, in_fence, defs = map_file(lines)
        files.append((rel, lines, tiers, meta, in_fence))
        for name, tg, i in defs:
            e = names.setdefault(name.lower(), {"name": name, "tier": (0, 0), "where": []})
            e["tier"] = (max(e["tier"][0], tg[0]), max(e["tier"][1], tg[1]))
            e["where"].append((rel, i + 1))
    result["files_read"] = len(files)
    result["names_above_tier_0"] = len(names)

    patterns = {k: re.compile(r"(?<![\w])" + re.escape(k) + r"(?![\w])") for k in names}
    hits = {k: [] for k in names}
    for rel, lines, tiers, meta, in_fence in files:
        for i, line in enumerate(lines):
            if in_fence[i] or meta[i] or not line.strip() or V.TABLE_SEPARATOR_CELL_RE.match(line.strip(" |")):
                continue
            low = line.lower()
            for k, info in names.items():
                if k in low and lower_than(tiers[i], info["tier"]) and patterns[k].search(low):
                    hits[k].append({"file": rel, "line": i + 1, "tier": tiers[i],
                                    "text": line.strip()[:100]})
    # strictest names first, then alphabetical, so the leaks that matter most read first
    for k, info in sorted(names.items(), key=lambda kv: (-max(kv[1]["tier"]), kv[0])):
        if hits[k]:
            result["hits"].append({
                "name": info["name"], "tier": list(info["tier"]),
                "defined_at": [f"{r}:{ln}" for r, ln in sorted(set(info["where"]))],
                "also_at": [{"file": h["file"], "line": h["line"],
                             "tier": None if h["tier"] is None else list(h["tier"]), "text": h["text"]}
                            for h in sorted(hits[k], key=lambda h: (h["file"], h["line"]))]})
    return result


def print_report(results: list[dict], quiet: bool, max_places: int):
    print(f"tier_sweep {RULES_REVISION} -- {len(results)} guide(s)")
    print("=" * 78)
    for r in results:
        if not r["parsed"]:
            print(f"[UNPARSED] {r['guide']} -- {r['error']}")
            continue
        print(f"[{r['guide']}] {r['files_read']} files read, {r['names_above_tier_0']} names above tier 0, "
              f"{len(r['hits'])} name(s) also found at a lower tier or untagged")
        if quiet:
            continue
        for h in r["hits"]:
            print(f"  - \"{h['name']}\" tier {h['tier'][0]}/{h['tier'][1]} "
                  f"(defined {', '.join(h['defined_at'][:3])}) also at:")
            for p in h["also_at"][:max_places]:
                t = "untagged" if p["tier"] is None else f"tier {p['tier'][0]}/{p['tier'][1]}"
                print(f"      {p['file']}:{p['line']} {t}  {p['text']}")
            if len(h["also_at"]) > max_places:
                print(f"      (+{len(h['also_at']) - max_places} more)")
    print("=" * 78)
    print("TOTALS: " + ", ".join(f"{r['guide']}={len(r['hits'])}" for r in results if r["parsed"]))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("guides", nargs="+", help="guide directories (each holds a corpus manifest)")
    ap.add_argument("--json", dest="json_out", help="write the full result as JSON")
    ap.add_argument("--exit-code", action="store_true", help="exit 1 when any name is reported")
    ap.add_argument("--quiet", action="store_true", help="counts only, no per-name lines")
    ap.add_argument("--max-places", type=int, default=5, help="places listed per name (default 5)")
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    if hasattr(sys.stdout, "reconfigure"):  # guide text is arbitrary Unicode; never crash on a narrow console
        sys.stdout.reconfigure(errors="replace")
    results = [sweep_guide(Path(g).resolve()) for g in args.guides]
    print_report(results, args.quiet, args.max_places)
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"rules_revision": RULES_REVISION, "results": results},
                                  indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"\nJSON written: {out}")
    bad = any(r["hits"] for r in results) or any(not r["parsed"] for r in results)
    return 1 if (args.exit_code and bad) else 0


if __name__ == "__main__":
    sys.exit(main())
