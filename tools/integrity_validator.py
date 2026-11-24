#!/usr/bin/env python3
"""integrity_validator.py -- deterministic corpus-integrity validator
(report-only, never edits a corpus, no network, no model call).

Run by the doctor procedure (doctor.md "Integrity check"). Contract it
enforces: docs/corpus-format.md sections 4 and 6.

Exactly THREE checks are wired:
  source -- every claim entry has a non-empty `source`.
  tier   -- every claim entry carries both `enemy-tier` and `puzzle-tier`
            (own metadata, or a governing shape described below).
  status -- every claim-bearing file's top-of-file `status` field is one of
            scaffold | research-integrated | live-observed | reconciled.
            `status: scaffold` files are skipped for source/tier (SS6).

Two things count as a `source` violation because they mean claim metadata the parser cannot read:
  - a non-scaffold file that has a top-of-file `status`, mentions claim metadata fields (`_source:`,
    `enemy-tier:`, `puzzle-tier:`) outside code fences, and yet parses ZERO claims -- a content file
    whose metadata is shared per section passes the other checks by having nothing to check. A file with
    no `status`, or with status but no metadata field anywhere (an index, a manifest, a README), is not
    treated as a content file and is not flagged;
  - a `_source:` that is not at the start of its own line (trailing the claim, behind a bullet or a
    `>` quote marker, inside a table row) and is followed by another metadata key or a closing
    underscore. Prose that only names the field (`_source:` directly followed by a backtick) and
    instruction text whose metadata holds a `<placeholder>` are not flagged.

Spoiler marks the reader cannot see (text inside backticks is ignored). The reader gates on `_source:` lines
only, so a `_spoiler:` mark written any other way carries no tier. Two findings, named in the detail text:
  - `spoiler-mark-line` (a `source` violation, a format problem): a line that opens with `_spoiler: <tier> ..._`
    instead of `_source:`. Repair: convert it to a full `_source:` line.
  - `spoiler-mark-undercovered` (a `tier` violation): an inline `_spoiler: <tier> ..._` fragment at the end of a
    claim line or in a table cell whose covering `_source:` line (the reach rule: the line below the claim,
    paragraph or table) is at a lower tier, or that has no covering line. The covering line's tier is the
    highest of its `enemy-tier`, `puzzle-tier` and `spoiler:` values (a tier axis the line does not state comes
    from the section tag in force). Every mark on a line is ranked. A mark inside a bullet-field entry block that
    carries its own tier or spoiler fields is compared with those fields instead. Repair:
    give the marked text its own `_source:` line at the mark's tier. `dlc:` and free-text marks are not ranked.
  - `tier-mark-undercovered` (a `tier` violation): the same for an `_enemy-tier: N ..._` or `_puzzle-tier: N ..._`
    mark (inline, in a table cell, or on a line of its own), compared with the covering line's value on the SAME
    axis (its `enemy-tier` / `puzzle-tier` field, else the section tag in force, else 0).
A `spoiler:` or tier field inside a normal `_source:` line is the correct form and is never flagged.

NOT wired, deliberately: whether each source citation resolves.

Parser shapes. Two guide-format questions are still open, so every shape
below parses and the validator does not pick one. The choice plugs in at
ACCEPTED_SHAPES below (default: all accepted) or `--reject-shape NAME`:
  section-tier-tag      -- question 1 (section tags). A standalone line carrying
        enemy-tier + puzzle-tier governs the claims after it, until the next
        H1-H3 heading or the next such line; a section-opening `_source:`
        citation that sits directly above headings whose sections carry
        those tag lines is a container citation, not a claim.
  table-citation        -- question 2 (achievements as a table). A `_source:`
        line directly under a markdown table cites the whole table and is not
        a per-claim metadata line.
  entry-block-container -- question 2, template side. A section-opening
        `_source:` line directly above headings whose sections hold per-entry
        bullet blocks carrying their own tiers is a container citation.
Reject a shape and the claims it excused fall through to the plain tier check.

Row tier column (templates/claim_format.md "Tables"). In a table with a `_source:` table tag directly
under it, a column headed `tier` must hold `spoiler:` vocabulary (none | progression | late-game | story |
dlc:<name>) or be empty (inherit the table tag). Any other text is a `tier` violation on that row. A
purely numeric value (`2`, `0 / 0`) is left alone: numeric `Tier` columns exist for meanings that are not
spoiler tiers (tech-tree tiers) and for the older `enemy / puzzle` pair.

Parse tolerance (not shape choices): inline metadata separators are middle-dot, pipe and
spaced hyphen; the status value is the first word (trailing free text is
allowed); `artifacts/` is outside the corpus-format file set.

Usage:
  integrity_validator.py <guide_dir> [<guide_dir> ...] [--json out.json]
        [--only REL_PATH ...] [--reject-shape NAME ...] [--exit-code] [--quiet]

Exit 0 on a completed run (a report tool, never a blocking gate: report,
route, log; never block); `--exit-code` makes violations or an
unparsed guide exit 1. Exit 2 = usage error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RULES_REVISION = "iv-2026.11.24-2"
KNOWN_MAX_CORE = 6

CHECKS = ("source", "tier", "status")
# Per-check floor on corpus-core-version. All three apply from v1; the table exists so a later version-gated
# check has one obvious place to be declared.
CHECK_MIN_CORE = {"source": 1, "tier": 1, "status": 1}

STATUS_LIFECYCLE = ("scaffold", "research-integrated", "live-observed", "reconciled")

ALL_SHAPES = ("section-tier-tag", "table-citation", "entry-block-container")
# >>> CANONICAL-SHAPE PLUG-IN POINT. <<<  Which guide shapes are accepted.
# Default accepts every shape seen in published guides. When a canonical
# shape is chosen, drop the losing shape's name from this tuple (question 1: "section-tier-tag"; question 2:
# "table-citation" and/or "entry-block-container"). Nothing else changes.
ACCEPTED_SHAPES = ALL_SHAPES

# Directories outside the published corpus (corpus-format.md SS1) plus
# `artifacts/` (tool specs with their own status vocabulary).
EXCLUDED_DIR_NAMES = {
    "research_briefs", "research_inbox", "ptt", "save_state", ".claude",
    ".git", "__pycache__", "archive", "reference", "roster", "artifacts",
}

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})\s+\S")
INLINE_SOURCE_RE = re.compile(r"^\s*source\s*:\s*(.*)$", re.I | re.S)
# Separators between inline metadata fields: middle dot, pipe, or a spaced
# hyphen/dash that introduces another `key:`.
SEP_RE = re.compile(r"\s*·\s*|\s+\|\s+|\s+[-–—]\s+(?=[A-Za-z][A-Za-z_-]*\s*:)")
TIER_FIELD_RE = {
    "enemy-tier": re.compile(r"(?<![\w-])enemy-tier\s*:\s*(\d)", re.I),
    "puzzle-tier": re.compile(r"(?<![\w-])puzzle-tier\s*:\s*(\d)", re.I),
}
# Section tag lines: colon optional (`enemy-tier 2`), value must be a digit.
TIER_TAG_RE = {
    "enemy-tier": re.compile(r"(?<![\w-])enemy-tier\W{0,3}(\d)", re.I),
    "puzzle-tier": re.compile(r"(?<![\w-])puzzle-tier\W{0,3}(\d)", re.I),
}
BULLET_FIELD_LINE_RE = re.compile(r"^\s*[-*]\s+\*\*_?[A-Za-z][\w-]*\s*:\*\*")
BULLET_FIELD_RE = re.compile(r"\*\*(_?[A-Za-z][\w-]*)\s*:\*\*")
FILE_STATUS_RE = re.compile(r"^(?:\*\*status:\*\*|status:)\s*(.*)$", re.I)
STATUS_WORD_RE = re.compile(r"[A-Za-z][A-Za-z_-]*")
# A file that mentions claim metadata fields (outside code fences) was meant to carry claims.
METADATA_SIGNAL_RE = re.compile(r"(?<![\w])_source\s*:|(?<![\w-])(?:enemy|puzzle)-tier\s*:", re.I)
# A `_source:` that sits anywhere but the start of its own line (trailing a claim, behind a bullet or
# quote marker, inside a table row). `_source:` directly followed by a backtick is a bare mention of
# the field name, not metadata.
MIDLINE_SOURCE_RE = re.compile(r"(?<![\w])_source\s*:(?!`)(.*)$", re.I)
METADATA_KEY_RE = re.compile(
    r"(?<![\w-])(?:enemy-tier|puzzle-tier|capture|confidence|spoiler|category)\s*:", re.I)
# Row tier column (templates/claim_format.md "Tables"): `spoiler:` vocabulary.
ROW_TIER_RE = re.compile(r"^(?:none|progression|late-game|story|dlc:\S.*)$", re.I)
NUMERIC_TIER_RE = re.compile(r"^\d+(?:\s*/\s*\d+)?$")
TABLE_SEPARATOR_CELL_RE = re.compile(r"^:?-{1,}:?$")
# A `_spoiler: <word> ..._` mark written outside a `_source:` line. The reader gates on `_source:` lines only,
# so a mark it cannot see is a tier the reader never applies.
SPOILER_MARK_RE = re.compile(r"(?<![\w])_spoiler\s*:", re.I)
# `_enemy-tier: N ..._` / `_puzzle-tier: N ..._` written as a mark (leading underscore), not a field of a `_source:` line.
TIER_MARK_RE = re.compile(r"(?<![\w])_(enemy|puzzle)-tier\s*:\s*(\d(?:\s*[/-]\s*\d)*)", re.I)
CODE_SPAN_RE =re.compile(r"(`+).+?\1")
SPOILER_RANK = {"none": 0, "progression": 1, "late-game": 2, "story": 3}
SPOILER_WORD_RE = re.compile(r"\s*(none|progression|late-game|story)(?![\w-])", re.I)
SOURCE_SPOILER_RE = re.compile(r"(?<![\w-])spoiler\s*:\s*(none|progression|late-game|story)(?![\w-])", re.I)


# ---------------------------------------------------------------- manifest

def find_manifest(guide_dir: Path):
    for rel in ("nav/architecture.md", "architecture_manifest.md"):
        p = guide_dir / rel
        if p.exists():
            return p
    return None


def parse_core_version(manifest_text: str):
    m = re.search(r"^corpus-core-version:\s*(\d+)", manifest_text, re.M)
    return int(m.group(1)) if m else None


def iter_corpus_files(guide_dir: Path):
    found = []
    for p in guide_dir.rglob("*.md"):
        rel_parts = p.relative_to(guide_dir).parts
        if any(part in EXCLUDED_DIR_NAMES for part in rel_parts):
            continue
        found.append((p.relative_to(guide_dir).as_posix(), p))
    found.sort(key=lambda t: t[0])
    return found


# ---------------------------------------------------------- line primitives

def is_table_row(stripped: str) -> bool:
    return len(stripped) >= 2 and stripped.startswith("|") and stripped.endswith("|")


def file_status(lines: list[str]):
    """(raw_value, 1-based line) of the first top-of-file status field in the
    first 15 lines, or (None, None). SS6: status sits near the top."""
    for i, line in enumerate(lines[:15], start=1):
        m = FILE_STATUS_RE.match(line.strip())
        if m:
            return m.group(1).strip(), i
    return None, None


def status_word(raw: str):
    m = STATUS_WORD_RE.match(raw)
    return m.group(0) if m else None


def inline_body(stripped: str) -> str:
    body = re.sub(r"^_+", "", stripped)
    body = re.sub(r"\s*\[[^\]]*\]\s*$", "", body)
    body = re.sub(r"_+\s*$", "", body)
    return body


CLOSING_UNDERSCORE_RE = re.compile(r"(?<=\S)_+(?=\s|$|\[)")
WRAP_MAX_LINES = 8


def join_wrapped_metadata(lines, stripped, i, in_fence, heading):
    """An italic `_source: ..._` metadata line may wrap across lines. If the first line has no closing
    underscore, join following lines up to the one that closes it; give up
    (single line) at a blank line, heading, fence, or WRAP_MAX_LINES."""
    first = re.sub(r"\s*\[[^\]]*\]\s*$", "", stripped[i])
    if CLOSING_UNDERSCORE_RE.search(first[1:]):
        return stripped[i], i
    parts = [stripped[i]]
    for j in range(i + 1, min(len(lines), i + WRAP_MAX_LINES)):
        if not stripped[j] or in_fence[j] or heading[j]:
            break
        parts.append(stripped[j])
        if CLOSING_UNDERSCORE_RE.search(re.sub(r"\s*\[[^\]]*\]\s*$", "", stripped[j])):
            return " ".join(parts), j
    return stripped[i], i


def trial_strict_has(body: str, key: str) -> bool:
    """The strict presence test: split on middle-dot only, key
    must be a part's `key:` prefix with non-empty text. Used ONLY to
    attribute claims the tolerant separators rescued."""
    for part in re.split(r"\s*·\s*", body):
        part = part.strip()
        if ":" in part:
            k, _, v = part.partition(":")
            if k.strip().lower() == key and v.strip():
                return True
    return False


def scan_tag_line(stripped: str):
    """(enemy, puzzle) if this line is a standalone section tier tag."""
    if not stripped or stripped[0] in "_-*|#":
        return None
    me = TIER_TAG_RE["enemy-tier"].search(stripped)
    mp = TIER_TAG_RE["puzzle-tier"].search(stripped)
    if me and mp:
        return int(me.group(1)), int(mp.group(1))
    return None


def parse_bullet_run(lines: list[str], i: int):
    """Contiguous `- **key:** value` lines starting at i -> (fields, end_i)."""
    fields: dict[str, str] = {}
    n = len(lines)
    while i < n and BULLET_FIELD_LINE_RE.match(lines[i]):
        line = lines[i]
        ms = list(BULLET_FIELD_RE.finditer(line))
        for k, m in enumerate(ms):
            key = m.group(1).strip("_").lower()
            end = ms[k + 1].start() if k + 1 < len(ms) else len(line)
            val = line[m.end():end].strip().rstrip("|").strip()
            fields[key] = (fields[key] + ", " + val) if key in fields else val
        i += 1
    return fields, i


def tier_present(val: str | None) -> bool:
    return bool(val) and re.match(r"\s*\d", val) is not None


def midline_source(stripped: str) -> bool:
    """True when this (non-fenced) line carries claim metadata that is not at the start of its own
    line, so the claim parser never sees it. Only counts when the text after `_source:` looks like
    metadata (another metadata key, or a closing underscore); prose that merely names the field does not."""
    if stripped.startswith("_"):
        return False
    m = MIDLINE_SOURCE_RE.search(stripped)
    if not m:
        return False
    rest = m.group(1)
    if re.search(r"<[^<>\s][^<>]*>", rest):  # `<placeholder>` text: a template or instruction example
        return False
    return bool(METADATA_KEY_RE.search(rest) or re.search(r"\S_\s*(?:\[[^\]]*\]\s*)?$", rest))


def blank_code_spans(s: str) -> str:
    """Text inside backticks is prose about the format, not a mark: blank it out."""
    return CODE_SPAN_RE.sub(lambda m: " " * len(m.group(0)), s)


def spoiler_mark_rank(rest: str):
    """Strictest tier named by the text after `_spoiler:` (up to the closing underscore), reading the first
    word of each item split on middle-dot, semicolon or pipe. None when no item names a tier word
    (a `dlc:` mark or free text), so the mark is not ranked."""
    body = re.split(r"_(?=\s|$|\[)", rest, maxsplit=1)[0]
    ranks = []
    for part in re.split(r"\s*[·;|]\s*", body):
        m = SPOILER_WORD_RE.match(part)
        if m:
            ranks.append(SPOILER_RANK[m.group(1).lower()])
    return max(ranks) if ranks else None


def covering_source_index(i: int, n: int, stripped, in_fence, heading, source_idx):
    """Index of the `_source:` line that covers line i under the reach rule (a `_source:` line covers the
    claim, paragraph or table immediately above it), or None. Scans the contiguous block holding line i
    for a `_source:` line, then looks at the first non-blank line after the block."""
    j = i + 1
    while j < n and stripped[j] and not in_fence[j] and not heading[j]:
        if j in source_idx:
            return j
        j += 1
    while j < n and not stripped[j]:
        j += 1
    return j if j < n and j in source_idx and not in_fence[j] else None


def table_cells(row: str) -> list[str]:
    # Markdown's escaped `\|` is a literal pipe inside a cell, not a column break.
    return [c.strip().strip("*`").strip() for c in re.split(r"(?<!\\)\|", row.strip().strip("|"))]


# ------------------------------------------------------------ file analysis

def mark_structure(lines: list[str]):
    """(in_fence, heading) per line: in_fence is True on fenced lines and the fence markers; heading is
    the 1-6 heading level of a non-fenced heading line, else 0."""
    n = len(lines)
    in_fence = [False] * n
    fence = None  # (char, length) of the open fence, or None
    for i, ln in enumerate(lines):
        m = FENCE_RE.match(ln)
        if m:
            run, rest = m.group(1), m.group(2)
            if fence is None:
                if not (run[0] == "`" and "`" in rest):  # backtick info string has no backtick
                    fence = (run[0], len(run))
            elif run[0] == fence[0] and len(run) >= fence[1] and not rest.strip():
                fence = None
            in_fence[i] = True  # fence marker line itself is not content
            continue
        in_fence[i] = fence is not None

    heading = [0] * n
    for i in range(n):
        if not in_fence[i]:
            m = HEADING_RE.match(lines[i])
            if m:
                heading[i] = len(m.group(1))
    return in_fence, heading


def analyze_file(rel: str, lines: list[str], accepted: set[str], result: dict):
    n = len(lines)
    # A leading blockquote marker is dropped: claim_format.md shows the metadata line as `> _source: ...`.
    stripped = [re.sub(r"^(?:>\s*)+", "", ln.strip()) for ln in lines]
    in_fence, heading = mark_structure(lines)

    tag = [None] * n
    for i in range(n):
        if not in_fence[i] and not heading[i]:
            tag[i] = scan_tag_line(stripped[i])

    # governing section tag in force at each line (resets at H1-H3).
    gov_tag = [None] * n
    cur = None
    for i in range(n):
        if heading[i] and heading[i] <= 3:
            cur = None
        gov_tag[i] = cur
        if tag[i] is not None:
            cur = (tag[i][0], tag[i][1], i + 1)

    # claim candidates
    inline_claims = []  # (i, body, source_val)
    block_runs = []     # (i, fields)
    i = 0
    while i < n:
        if in_fence[i]:
            i += 1
            continue
        s = stripped[i]
        if s.startswith("_"):
            if INLINE_SOURCE_RE.match(inline_body(s)):
                joined, last = join_wrapped_metadata(lines, stripped, i, in_fence, heading)
                body = inline_body(joined)
                m = INLINE_SOURCE_RE.match(body)
                # Leading space restored: `\s*` in INLINE_SOURCE_RE ate the
                # whitespace a leading `| ` / `- ` separator needs (empty source).
                source_val = SEP_RE.split(" " + m.group(1), 1)[0].strip()
                inline_claims.append((i, body, source_val))
                i = last + 1
                continue
            i += 1
            continue
        if BULLET_FIELD_LINE_RE.match(lines[i]):
            fields, end = parse_bullet_run(lines, i)
            block_runs.append((i, fields))
            i = end
            continue
        i += 1

    claim_lines = {i for i, _, _ in inline_claims} | {
        i for i, f in block_runs if "claim" in f or "source" in f}

    shapes = result["shapes"]
    shapes["section_tier_tag_lines"] += sum(1 for t in tag if t is not None)

    def tiered_block(fields):
        return tier_present(fields.get("enemy-tier")) and tier_present(fields.get("puzzle-tier"))

    shapes["tiered_entry_blocks"] += sum(
        1 for _, f in block_runs if tiered_block(f) and "claim" not in f and "source" not in f)

    def prev_nonblank(i):
        j = i - 1
        while j >= 0 and not stripped[j]:
            j -= 1
        return j

    def next_nonblank(i):
        j = i + 1
        while j < n and not stripped[j]:
            j += 1
        return j

    def excused(line_no, rule, detail):
        result["excused"].append({"file": rel, "line": line_no, "rule": rule, "detail": detail})

    def violation(line_no, claim, check, detail):
        result["violations"].append({
            "file": rel, "line": line_no, "claim": claim, "check": check, "detail": detail})
        result["counts"][check] += 1

    def resolve_container(i):
        """Citation at line index i is excused as a container? -> rule or None."""
        # (a) table-level citation: directly under a markdown table.
        if "table-citation" in accepted:
            j = prev_nonblank(i)
            if j >= 0 and not in_fence[j] and is_table_row(stripped[j]):
                k = j
                while k - 1 >= 0 and is_table_row(stripped[k - 1]):
                    k -= 1
                has_col = "tier" in stripped[k].lower()
                shapes["table_citations_with_row_tier_column" if has_col
                       else "table_citations_without_row_tier_column"] += 1
                return "table-citation"
        # (b) section-opening citation directly above a heading whose subtree
        # carries the tier information.
        # Must be the FIRST claim in its section (a citation after other claims
        # is an ordinary claim, not a section-opening container) and must sit
        # directly above a deeper heading.
        j = next_nonblank(i)
        if j < n and heading[j]:
            level = 0
            section_start = -1
            for k in range(i - 1, -1, -1):
                if heading[k]:
                    level = heading[k]
                    section_start = k
                    break
            if any(k in claim_lines for k in range(section_start + 1, i)):
                return None
            if level and heading[j] <= level:
                return None
            end = n
            if level:
                for k in range(j, n):
                    if heading[k] and heading[k] <= level:
                        end = k
                        break
            if "section-tier-tag" in accepted and any(tag[k] is not None for k in range(j, end)):
                shapes["container_citations_over_tag_sections"] += 1
                return "section-tier-tag"
            if "entry-block-container" in accepted and any(
                    f is not None and tiered_block(f) and i < bi < end
                    for bi, f in block_runs):
                shapes["container_citations_over_entry_blocks"] += 1
                return "entry-block-container"
        return None

    def check_tiers(i, line_no, ident, own, strict_ok, body):
        """own = {'enemy-tier': bool, 'puzzle-tier': bool}. Applies the tier
        check, honouring accepted governing shapes."""
        missing = [t for t in ("enemy-tier", "puzzle-tier") if not own[t]]
        if not missing:
            if body is not None and not (strict_ok["enemy-tier"] and strict_ok["puzzle-tier"]):
                excused(line_no, "tolerant-separator",
                        "tiers present only under the pipe / spaced-hyphen separator parse")
            return
        g = gov_tag[i]
        if "section-tier-tag" in accepted and g is not None:
            shapes["claims_tier_from_section_tag"] += 1
            excused(line_no, "section-tier-tag",
                    f"missing {', '.join(missing)} supplied by section tag at line {g[2]}")
            return
        rule = resolve_container(i) if body is not None else None
        if rule:
            excused(line_no, rule, f"container citation; missing {', '.join(missing)} carried by its entries")
            return
        violation(line_no, ident, "tier", f"missing {', '.join(missing)}")

    # Metadata the claim parser cannot see: a `_source:` that is not at the start of its own line.
    for i in range(n):
        if not in_fence[i] and not heading[i] and midline_source(stripped[i]):
            violation(i + 1, stripped[i][:60], "source",
                      "`_source:` is not at the start of its own line, so it is not read as claim metadata")

    # `_spoiler:` marks the reader cannot see. (1) `spoiler-mark-line` (reported under `source`): a line that
    # opens with `_spoiler:` is not a `_source:` line, so no claim carries it. (2) `spoiler-mark-undercovered`
    # (reported under `tier`): an inline mark at the end of a claim line or in a table cell whose covering
    # `_source:` line (reach rule) sits at a lower tier, or that has none. Text inside backticks is ignored.
    source_idx = {i for i, _, _ in inline_claims}
    source_body = {i: body for i, body, _ in inline_claims}
    block_at = {}  # line index -> fields of the bullet-field entry block holding that line
    for start, fields in block_runs:
        _, end = parse_bullet_run(lines, start)
        for j in range(start, end):
            block_at[j] = fields
    for i in range(n):
        if in_fence[i]:
            continue
        text = blank_code_spans(stripped[i])
        marks = []  # (finding name, label, axis, rank)
        sm_marks = list(SPOILER_MARK_RE.finditer(text))
        if SPOILER_MARK_RE.match(text.lstrip()):
            violation(i + 1, stripped[i][:60], "source",
                      "spoiler-mark-line: a line that opens with `_spoiler:` is not a `_source:` line, so a reader "
                      "that keys on `_source:` never sees its tier. Convert it to a full `_source:` line "
                      "(`_source: <where it came from> · capture: <method> · enemy-tier: N · puzzle-tier: N · "
                      "spoiler: <tier>_`) under the claim it marks")
            continue
        for sm_mark in sm_marks:  # every mark on the line, each read up to its own closing underscore
            rank = spoiler_mark_rank(text[sm_mark.end():])
            if rank is not None:
                marks.append(("spoiler-mark-undercovered", "`_spoiler:`", None, rank))
        for tm in TIER_MARK_RE.finditer(text):
            axis = tm.group(1).lower() + "-tier"
            rank = max(int(d) for d in re.findall(r"\d", tm.group(2)))
            marks.append(("tier-mark-undercovered", f"`_{axis}:`", axis, rank))
        if not marks:
            continue
        block = block_at.get(i)
        if block is not None and (any(tier_present(block.get(k)) for k in ("enemy-tier", "puzzle-tier"))
                                  or block.get("spoiler")):
            # A mark inside an entry block that carries its own tiers: the block's fields are its cover.
            def block_tier(key):  # the strictest digit, as a mark's rank is read
                digits = re.findall(r"\d", block.get(key) or "") if tier_present(block.get(key)) else []
                return max(int(d) for d in digits) if digits else 0
            block_spoiler = spoiler_mark_rank(block.get("spoiler") or "") or 0
            for name, label, axis, rank in marks:
                covered = (max(block_tier("enemy-tier"), block_tier("puzzle-tier"), block_spoiler)
                           if axis is None else block_tier(axis))
                if covered < rank:
                    violation(i + 1, stripped[i][:60], "tier",
                              f"{name}: inline {label} mark is tier {rank} but its entry block is tier {covered}"
                              + ("" if axis is None else f" on {axis}")
                              + f", so a reader below tier {rank} sees this text. Set the block's own "
                              "enemy-tier / puzzle-tier / spoiler fields to the mark's tier, then drop the mark")
            continue
        cover = covering_source_index(i, n, stripped, in_fence, heading, source_idx)
        body = source_body[cover] if cover is not None else None
        for name, label, axis, rank in marks:
            if body is None:
                violation(i + 1, stripped[i][:60], "tier",
                          f"{name}: inline {label} mark (tier {rank}) has no covering `_source:` line (a "
                          "`_source:` line covers only what is above it). Add a `_source:` line for this claim, "
                          "paragraph or table at the mark's tier")
                continue
            if axis is None:  # a spoiler mark: the covering line's highest tier on any axis
                values = []
                for k, t in enumerate(("enemy-tier", "puzzle-tier")):  # its own field, else the tag in force
                    fm = TIER_FIELD_RE[t].search(body)
                    if fm:
                        values.append(int(fm.group(1)))
                    elif gov_tag[cover] is not None:
                        values.append(gov_tag[cover][k])
                sm = SOURCE_SPOILER_RE.search(body)
                if sm:
                    values.append(SPOILER_RANK[sm.group(1).lower()])
                covered = max(values, default=0)
            else:  # an enemy-tier / puzzle-tier mark: the covering line's value on the same axis
                fm = TIER_FIELD_RE[axis].search(body)
                if fm:
                    covered = int(fm.group(1))
                elif gov_tag[cover] is not None:
                    covered = gov_tag[cover][0 if axis == "enemy-tier" else 1]
                else:
                    covered = 0
            if covered < rank:
                violation(i + 1, stripped[i][:60], "tier",
                          f"{name}: inline {label} mark is tier {rank} but its covering `_source:` line "
                          f"(line {cover + 1}) is tier {covered}"
                          + ("" if axis is None else f" on {axis}")
                          + f", so a reader below tier {rank} sees this text. Give the marked claim, paragraph "
                          "or table its own `_source:` line at the mark's tier (enemy-tier / puzzle-tier / "
                          "spoiler), then drop the inline mark")

    # Row tier column: a tagged table (a `_source:` line directly under it) whose header has a `tier`
    # cell must hold `spoiler:` vocabulary in that column (empty = inherit the table tag).
    inline_idx = {i for i, _, _ in inline_claims}
    i = 0
    while i < n:
        if in_fence[i] or not is_table_row(stripped[i]):
            i += 1
            continue
        end = i
        while end + 1 < n and not in_fence[end + 1] and is_table_row(stripped[end + 1]):
            end += 1
        header = table_cells(stripped[i])
        sep_ok = end > i and all(TABLE_SEPARATOR_CELL_RE.match(c) for c in table_cells(stripped[i + 1]))
        tagged = next_nonblank(end) in inline_idx
        col = next((k for k, c in enumerate(header) if c.lower() == "tier"), None)
        if sep_ok and tagged and col is not None:
            for r in range(i + 2, end + 1):
                cells = table_cells(stripped[r])
                val = cells[col] if col < len(cells) else ""
                if val and not ROW_TIER_RE.match(val) and not NUMERIC_TIER_RE.match(val):
                    violation(r + 1, (cells[0] if cells else "")[:60], "tier",
                              f"row tier '{val[:30]}' is not none | progression | late-game | story | dlc:<name>")
        i = end + 1

    for i, body, source_val in inline_claims:
        result["claims_checked"] += 1
        result["claim_index"].append(f"{rel}:{i + 1}:inline")
        shapes["inline_claims"] += 1
        ident = (source_val or body)[:60]
        if not source_val:
            violation(i + 1, ident, "source", "missing or empty source field")
        own = {t: TIER_FIELD_RE[t].search(body) is not None for t in ("enemy-tier", "puzzle-tier")}
        strict_ok = {t: trial_strict_has(body, t) for t in ("enemy-tier", "puzzle-tier")}
        check_tiers(i, i + 1, ident, own, strict_ok, body)

    for i, fields in block_runs:
        if "claim" not in fields and "source" not in fields:
            continue
        result["claims_checked"] += 1
        result["claim_index"].append(f"{rel}:{i + 1}:block")
        shapes["block_claims"] += 1
        ident = (fields.get("claim") or fields.get("source") or "")[:60]
        if not fields.get("source", "").strip():
            violation(i + 1, ident, "source", "missing or empty source field")
        own = {t: tier_present(fields.get(t)) for t in ("enemy-tier", "puzzle-tier")}
        check_tiers(i, i + 1, ident, own, {t: True for t in own}, None)

    return any(not in_fence[k] and METADATA_SIGNAL_RE.search(lines[k]) for k in range(n))


# --------------------------------------------------------------- guide level

def validate_guide(guide_dir: Path, accepted_shapes=None, only=None) -> dict:
    accepted = set(ACCEPTED_SHAPES if accepted_shapes is None else accepted_shapes)
    result = {
        "guide": guide_dir.name,
        "parsed": False,
        "error": None,
        "corpus_core_version": None,
        "manifest_path": None,
        "notes": [],
        "counts": {c: 0 for c in CHECKS},
        "claims_checked": 0,
        "files_checked": 0,
        "files_skipped_scaffold": 0,
        "shapes": {k: 0 for k in (
            "inline_claims", "block_claims", "section_tier_tag_lines",
            "tiered_entry_blocks", "claims_tier_from_section_tag",
            "table_citations_with_row_tier_column",
            "table_citations_without_row_tier_column",
            "container_citations_over_tag_sections",
            "container_citations_over_entry_blocks")},
        "violations": [],
        "excused": [],
        "claim_index": [],
    }
    manifest_path = find_manifest(guide_dir)
    if manifest_path is None:
        result["error"] = "no manifest found at nav/architecture.md or architecture_manifest.md"
        return result
    try:
        core = parse_core_version(manifest_path.read_text(encoding="utf-8", errors="ignore"))
    except Exception as e:  # unreadable manifest is reported, not raised
        result["error"] = f"could not read manifest: {e}"
        return result
    if core is None:
        result["error"] = "manifest has no corpus-core-version field"
        return result
    result["parsed"] = True
    result["corpus_core_version"] = core
    result["manifest_path"] = manifest_path.relative_to(guide_dir).as_posix()
    if core > KNOWN_MAX_CORE:
        result["notes"].append(
            f"corpus-core-version {core} is newer than this validator knows "
            f"(max {KNOWN_MAX_CORE}); checks run unchanged")
    active = {c for c in CHECKS if core >= CHECK_MIN_CORE[c]}

    only_set = None if only is None else {o.replace("\\", "/") for o in only}
    for rel, path in iter_corpus_files(guide_dir):
        if only_set is not None and rel not in only_set:
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception as e:
            result["violations"].append({
                "file": rel, "line": None, "claim": None,
                "check": "read-error", "detail": str(e)})
            continue
        result["files_checked"] += 1
        raw, status_line = file_status(lines)
        word = status_word(raw) if raw is not None else None
        if raw is not None and "status" in active and word not in STATUS_LIFECYCLE:
            result["violations"].append({
                "file": rel, "line": status_line, "claim": None, "check": "status",
                "detail": f"status '{raw[:40]}' not in lifecycle {sorted(STATUS_LIFECYCLE)}"})
            result["counts"]["status"] += 1
        if word == "scaffold":
            result["files_skipped_scaffold"] += 1
            continue
        claims_before = result["claims_checked"]
        mentions_metadata = analyze_file(rel, lines, accepted, result)
        if (word is not None and "source" in active and mentions_metadata
                and result["claims_checked"] == claims_before):
            result["violations"].append({
                "file": rel, "line": status_line, "claim": None, "check": "source",
                "detail": "non-scaffold file mentions claim metadata but parses no claim: write one "
                          "`_source:` line per claim, at the start of its own line (templates/claim_format.md)"})
            result["counts"]["source"] += 1
        if (raw is None and "status" in active
                and result["claims_checked"] > claims_before):
            result["violations"].append({
                "file": rel, "line": None, "claim": None, "check": "status",
                "detail": f"claim-bearing file has no top-of-file status; lifecycle is {sorted(STATUS_LIFECYCLE)}"})
            result["counts"]["status"] += 1

    # Drop violations of checks not active at this core version (none today).
    result["violations"] = [v for v in result["violations"]
                            if v["check"] in active or v["check"] == "read-error"]
    result["violations"].sort(key=lambda v: (v["file"], v["line"] or 0, v["check"]))
    result["excused"].sort(key=lambda v: (v["file"], v["line"] or 0, v["rule"]))
    result["claim_index"].sort()
    return result


def print_report(results: list[dict], quiet: bool):
    print(f"integrity_validator {RULES_REVISION} -- {len(results)} guide(s)")
    print("=" * 78)
    for r in results:
        if not r["parsed"]:
            print(f"[UNPARSED] {r['guide']} -- {r['error']}")
            continue
        print(f"[{r['guide']}] core v{r['corpus_core_version']} -- "
              f"{r['files_checked']} files ({r['files_skipped_scaffold']} scaffold-skipped), "
              f"{r['claims_checked']} claims, {len(r['excused'])} excused by shape/tolerance")
        for note in r["notes"]:
            print(f"    note: {note}")
        for c in CHECKS:
            print(f"    {c:8s} {r['counts'][c]} violation(s)")
        if not quiet:
            for v in r["violations"]:
                where = f"{v['file']}:{v['line']}" if v["line"] else v["file"]
                print(f"      - {where} [{v['check']}] {v['detail']}")
    print("=" * 78)
    total = {c: sum(r["counts"][c] for r in results if r["parsed"]) for c in CHECKS}
    print("TOTALS: " + ", ".join(f"{c}={n}" for c, n in total.items()))
    unparsed = [r["guide"] for r in results if not r["parsed"]]
    if unparsed:
        print("UNPARSED: " + ", ".join(unparsed))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("guides", nargs="+", help="guide directories (each holds a corpus manifest)")
    ap.add_argument("--json", dest="json_out", help="write the full result as JSON")
    ap.add_argument("--only", nargs="+", metavar="REL_PATH",
                    help="scoped run: check only these corpus-relative files (doctor post-edit use)")
    ap.add_argument("--reject-shape", action="append", default=[], choices=ALL_SHAPES,
                    metavar="NAME", help=f"stop accepting a guide shape; one of {', '.join(ALL_SHAPES)}")
    ap.add_argument("--exit-code", action="store_true",
                    help="exit 1 when any violation or unparsed guide is reported")
    ap.add_argument("--quiet", action="store_true", help="counts only, no per-violation lines")
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    accepted = [s for s in ACCEPTED_SHAPES if s not in args.reject_shape]
    results = [validate_guide(Path(g).resolve(), accepted, args.only) for g in args.guides]
    print_report(results, args.quiet)
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = {"rules_revision": RULES_REVISION, "accepted_shapes": accepted, "results": results}
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"\nJSON written: {out}")
    bad = any(r["violations"] for r in results) or any(not r["parsed"] for r in results)
    return 1 if (args.exit_code and bad) else 0


if __name__ == "__main__":
    sys.exit(main())
