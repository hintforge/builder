#!/usr/bin/env python3
"""changelog_move.py -- byte-exact CHECKPOINT changelog move
(stdlib only, no network, no model call; writes at most two files).

Performs the changelog move in docs/corpus-format.md section 1 ("CHECKPOINT size and the changelog
archive"), the step doctor.md Branch A step 7 calls for. Run it right after the procedure has written
its new entry at the top of the `## Harness changelog` section.

    python tools/changelog_move.py <guide-dir> [--dry-run] [--reverse-if-oldest-first]

What it does:
  - Splits the `## Harness changelog` section of <guide-dir>/CHECKPOINT.md into entries. An entry is a
    `### ` heading and every line up to the next `### ` or `## ` heading or the `Older entries:` line,
    which belongs to no entry. Trailing blank lines belong to the entry they follow.
  - Keeps the newest 3 entries, then also moves older ones while CHECKPOINT.md is over 24,000 bytes,
    always keeping the newest one.
  - Prepends the moved entries, newest first, to <guide-dir>/archive/harness_changelog.md (created
    with `# Harness changelog archive` and a blank line when absent).
  - Leaves exactly one `Older entries: archive/harness_changelog.md` line as the section's last line
    once an archive exists. With no archive and nothing to move, it adds none.
  - Works on raw bytes: line endings, encoding and every entry's bytes are preserved, and no other
    section is touched.
  - Verifies before writing that every entry appears exactly once across the two outputs, and that
    everything outside the section is unchanged. Any problem exits non-zero with nothing written.

Entry order: the section must read newest first. An oldest-first section (leading `vN` numbers or
dates rising down the section) is refused unless --reverse-if-oldest-first is given, which reverses
the entry order without changing any entry's bytes. With that flag, an order it cannot tell (two or
more entries, no usable rising or falling numbers or dates, or numbers and dates that disagree) is
refused too.

Exit codes: 0 done (or dry run complete), 1 refused or verification failed, 2 bad usage.
"""
import argparse
import hashlib
import os
import re
import sys

LIMIT = 24000
KEEP = 3
ARCHIVE_REL = "archive/harness_changelog.md"
POINTER = b"Older entries: archive/harness_changelog.md"
ARCHIVE_HEADER = b"# Harness changelog archive"
SECTION = b"## Harness changelog"


UNKNOWN_ORDER = ("cannot tell whether the section is oldest first or newest first "
                 "(the headings give no one consistent direction in version numbers and dates); "
                 "not touching it")


class Refuse(Exception):
    pass


def _is_h2(line):
    return line.startswith(b"## ") or line.rstrip(b"\r\n") == b"##"


def _is_entry_head(line):
    return line.startswith(b"### ")


def _is_older(line):
    return line.startswith(b"Older entries:")


def _strip_eol(line):
    return line.rstrip(b"\r\n")


def parse_entries(lines):
    """Split lines (the section body) into (preamble, entries, older_lines, tail).

    entries: list of byte strings. older_lines: the `Older entries:` lines seen. tail: lines after the
    last `Older entries:` line (blank lines before the next section)."""
    preamble, entries, older, tail = [], [], [], []
    cur = None
    for ln in lines:
        if _is_entry_head(ln):
            if tail:
                raise Refuse("lines between an `Older entries:` line and a later `### ` entry; "
                             "the section is not in the expected shape")
            cur = [ln]
            entries.append(cur)
        elif _is_older(ln):
            cur = None
            older.append(ln)
            tail = []
        elif cur is not None:
            cur.append(ln)
        elif older:
            tail.append(ln)
        else:
            preamble.append(ln)
    return preamble, [b"".join(e) for e in entries], older, tail


def split_checkpoint(data):
    lines = data.splitlines(keepends=True)
    starts = [i for i, ln in enumerate(lines) if _strip_eol(ln) == SECTION]
    if len(starts) != 1:
        raise Refuse("expected exactly one `## Harness changelog` heading, found %d" % len(starts))
    s = starts[0]
    e = len(lines)
    for i in range(s + 1, len(lines)):
        if _is_h2(lines[i]):
            e = i
            break
    return lines[: s + 1], lines[s + 1: e], lines[e:]


def _key_version(entry):
    m = re.match(rb"###\s+[vV](\d+)\b", entry)
    return int(m.group(1)) if m else None


def _key_date(entry):
    first = entry.split(b"\n", 1)[0]
    m = re.search(rb"(\d{4}-\d{2}-\d{2})", first)
    return m.group(1) if m else None


def _direction(keys, strict):
    """'oldest' (rising), 'newest' (falling) or None (a key missing, not monotone, or no information)."""
    if any(k is None for k in keys):
        return None
    up = all((a < b) if strict else (a <= b) for a, b in zip(keys, keys[1:]))
    down = all((a > b) if strict else (a >= b) for a, b in zip(keys, keys[1:]))
    if not strict and up and down:  # all equal: no information
        return None
    if up == down:
        return None
    return "oldest" if up else "newest"


def detect_order(entries):
    """'oldest', 'newest' or None (cannot tell).

    Version numbers `vN` decide when every heading has one and they run strictly one way; any date
    present must then agree. With no version numbers anywhere, dates decide (equal dates tell nothing).
    Mixed or missing version numbers, a non-monotone run, or numbers and dates that disagree: None."""
    if len(entries) < 2:
        return "newest"
    vers = [_key_version(x) for x in entries]
    dates = [_key_date(x) for x in entries]
    if any(v is not None for v in vers):
        by_ver = _direction(vers, True)
        if by_ver is None:
            return None
        have = [d for d in dates if d is not None]
        if have and len(have) != len(dates):
            return None
        if have:
            up = all(a <= b for a, b in zip(dates, dates[1:]))
            down = all(a >= b for a, b in zip(dates, dates[1:]))
            if not ((by_ver == "oldest" and up) or (by_ver == "newest" and down)):
                return None
        return by_ver
    return _direction(dates, False)


def detect_eol(data):
    return b"\r\n" if b"\r\n" in data else b"\n"


def build_checkpoint(head, preamble, kept, pointer_line, tail, rest, eol):
    body = list(preamble)
    out = b"".join(head) + b"".join(body) + b"".join(kept)
    if pointer_line is not None:
        if kept and not kept[-1].endswith((b"\n", b"\r")):
            out += eol
        out += pointer_line
        if not pointer_line.endswith((b"\n", b"\r")) and (tail or rest):
            out += eol
        out += b"".join(tail)
    else:
        out += b"".join(tail)
    return out + b"".join(rest)


def split_archive(data):
    """-> (header_line, lead_blank_lines, body_bytes)."""
    lines = data.splitlines(keepends=True)
    if not lines or _strip_eol(lines[0]) != ARCHIVE_HEADER:
        raise Refuse("archive/harness_changelog.md must start with `# Harness changelog archive`")
    i = 1
    while i < len(lines) and _strip_eol(lines[i]) == b"":
        i += 1
    return lines[0], b"".join(lines[1:i]), b"".join(lines[i:])


def archive_entries(body):
    return parse_entries(body.splitlines(keepends=True))[1]


def heading(entry):
    return _strip_eol(entry.split(b"\n", 1)[0]).decode("utf-8", "replace")


def plan(guide, reverse_flag):
    cp_path = os.path.join(guide, "CHECKPOINT.md")
    ar_path = os.path.join(guide, "archive", "harness_changelog.md")
    if not os.path.isfile(cp_path):
        raise Refuse("no CHECKPOINT.md in %s" % guide)
    with open(cp_path, "rb") as f:
        cp = f.read()
    head, sect, rest = split_checkpoint(cp)
    if not rest and cp and not cp.endswith((b"\n", b"\r")):
        raise Refuse("CHECKPOINT.md ends mid-line inside the changelog section; add a final line break first")
    preamble, entries, older, tail = parse_entries(sect)
    eol = detect_eol(cp)

    order = detect_order(entries)
    reversed_now = False
    if order == "oldest":
        if not reverse_flag:
            raise Refuse("the section reads oldest first; rerun with --reverse-if-oldest-first")
        entries = entries[::-1]
        reversed_now = True
    elif order is None and reverse_flag:
        raise Refuse(UNKNOWN_ORDER)
    if not entries:
        raise Refuse("the changelog section holds no `### ` entries")
    if older and any(_strip_eol(x) != POINTER for x in older):
        raise Refuse("an `Older entries:` line names a target other than archive/harness_changelog.md "
                     "(a legacy archive); migrate it by hand per doctor.md Branch A step 7, then rerun")
    if any(not e.endswith((b"\n", b"\r")) for e in entries[1:]) or \
            (entries and not entries[-1].endswith((b"\n", b"\r")) and (older or tail or rest or reversed_now)):
        raise Refuse("an entry ends mid-line; not touching it")

    ar_exists = os.path.isfile(ar_path)
    ar = b""
    if ar_exists:
        with open(ar_path, "rb") as f:
            ar = f.read()
        split_archive(ar)  # validates the header
    elif older:
        raise Refuse("CHECKPOINT.md has an `Older entries:` line but archive/harness_changelog.md does not "
                     "exist; fix the pointer or restore the archive first")

    reuse = older[0] if (len(older) == 1 and _strip_eol(older[0]) == POINTER) else None

    def render(k):
        if not (ar_exists or older or k < len(entries)):
            return build_checkpoint(head, preamble, entries[:k], None, tail, rest, eol)
        pl = reuse if reuse is not None else POINTER + eol
        return build_checkpoint(head, preamble, entries[:k], pl, tail, rest, eol)

    k = min(KEEP, len(entries))
    out = render(k)
    while len(out) > LIMIT and k > 1:
        k -= 1
        out = render(k)
    moved = entries[k:]
    if moved and order is None:
        raise Refuse(UNKNOWN_ORDER)
    if ar_exists and moved:
        already = set(archive_entries(split_archive(ar)[2]))
        dup = [heading(e) for e in moved if e in already]
        if dup:
            raise Refuse("entries to move already appear in the archive (a partial earlier run?): %s; "
                         "nothing written" % "; ".join(dup))

    new_ar = ar
    if moved:
        if ar_exists:
            hdr, lead, body = split_archive(ar)
            new_ar = hdr + (lead or eol) + b"".join(moved) + body
        else:
            new_ar = ARCHIVE_HEADER + eol + eol + b"".join(moved)

    return dict(cp_path=cp_path, ar_path=ar_path, cp=cp, out=out, ar=ar, new_ar=new_ar, ar_exists=ar_exists,
                entries=entries, kept=entries[:k], moved=moved, eol=eol, reversed=reversed_now,
                head=head, rest=rest, preamble=preamble, had_older=bool(older))


def verify(p):
    """Re-read both outputs the way a later reader would; raise Refuse on any difference."""
    out, new_ar, entries, moved = p["out"], p["new_ar"], p["entries"], p["moved"]
    head, sect, rest = split_checkpoint(out)
    if b"".join(head) != b"".join(p["head"]) or b"".join(rest) != b"".join(p["rest"]):
        raise Refuse("verification: bytes outside the changelog section changed")
    _, got_kept, got_older, _ = parse_entries(sect)
    if got_kept != p["kept"]:
        raise Refuse("verification: entries left in CHECKPOINT.md differ from the planned set")
    if got_older:
        after = sect[[i for i, x in enumerate(sect) if _is_older(x)][-1] + 1:]
        if any(_strip_eol(x) != b"" for x in after):
            raise Refuse("verification: the `Older entries:` line is not the section's last line")
    want_older = 1 if (p["ar_exists"] or moved or p["had_older"]) else 0
    if len(got_older) != want_older or any(_strip_eol(x) != POINTER for x in got_older):
        raise Refuse("verification: expected %d `Older entries:` line(s), found %d" % (want_older, len(got_older)))
    if moved or p["ar_exists"]:
        _, lead, body = split_archive(new_ar)
        got_ar = archive_entries(body)
        old_ar = archive_entries(split_archive(p["ar"])[2]) if p["ar_exists"] else []
        if got_ar != moved + old_ar:
            raise Refuse("verification: the archive does not hold the moved entries once, ahead of the old ones")
    seen = got_kept + moved
    if seen != entries:
        raise Refuse("verification: an entry is missing or duplicated across the two files")


def write_atomic(path, data):
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp"
    try:
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    except OSError:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def main(argv=None):
    ap = argparse.ArgumentParser(description="Byte-exact CHECKPOINT changelog move to archive/harness_changelog.md.")
    ap.add_argument("guide_dir")
    ap.add_argument("--dry-run", action="store_true", help="report only; write nothing")
    ap.add_argument("--reverse-if-oldest-first", action="store_true",
                    help="reverse an oldest-first section to newest first (refuses if the order cannot be told)")
    a = ap.parse_args(argv)
    try:
        p = plan(a.guide_dir, a.reverse_if_oldest_first)
        verify(p)
    except Refuse as e:
        print("REFUSED: %s" % e, file=sys.stderr)
        return 1
    changed_cp = p["out"] != p["cp"]
    changed_ar = p["new_ar"] != p["ar"] or (not p["ar_exists"] and bool(p["moved"]))
    print("CHECKPOINT.md bytes before: %d" % len(p["cp"]))
    print("CHECKPOINT.md bytes after:  %d" % len(p["out"]))
    if p["reversed"]:
        print("section was oldest first; order reversed")
    print("entries moved: %d" % len(p["moved"]))
    for e in p["moved"]:
        print("  %s  %s" % (hashlib.sha256(e).hexdigest(), heading(e)))
    if a.dry_run:
        print("dry run: nothing written")
        return 0
    ar_dir = os.path.dirname(p["ar_path"])
    dir_existed = os.path.isdir(ar_dir)
    wrote_ar = False
    try:
        if changed_ar:
            write_atomic(p["ar_path"], p["new_ar"])
            wrote_ar = True
        if changed_cp:
            write_atomic(p["cp_path"], p["out"])
    except OSError as e:
        msg = "FAILED while writing: %s" % e
        if wrote_ar:
            try:
                with open(p["ar_path"], "rb") as f:
                    current = f.read()
            except OSError:
                current = None
            if current != p["new_ar"]:
                msg += ("; CHECKPOINT.md was not written, and archive/harness_changelog.md changed since this "
                        "run wrote it, so it was left untouched; both files need a manual check")
                print(msg, file=sys.stderr)
                return 1
            try:
                if p["ar_exists"]:
                    write_atomic(p["ar_path"], p["ar"])
                else:
                    os.remove(p["ar_path"])
                    if not dir_existed:
                        os.rmdir(ar_dir)
                msg += "; the archive was restored to its original state and CHECKPOINT.md was not changed"
            except OSError as e2:
                msg += ("; ROLLBACK FAILED (%s): archive/harness_changelog.md now holds the moved entries "
                        "while CHECKPOINT.md still holds them too; restore the archive by hand before rerunning"
                        % e2)
        else:
            msg += "; nothing was changed"
        print(msg, file=sys.stderr)
        return 1
    print("wrote: %s" % ", ".join(n for n, c in (("archive/harness_changelog.md", changed_ar),
                                                   ("CHECKPOINT.md", changed_cp)) if c) or "nothing (already in shape)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
