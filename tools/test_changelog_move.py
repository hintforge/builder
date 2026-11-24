"""Tests for tools/changelog_move.py. Entry text is invented and game-agnostic."""
import hashlib
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import changelog_move as cm  # noqa: E402

POINTER = "Older entries: archive/harness_changelog.md"


def entry(n, body="Changed things.", blanks=1, eol="\n"):
    return f"### v{n} -- 2026-11-{n:02d} 10:00 UTC (test){eol}{body} entry {n}{eol}" + eol * blanks


def checkpoint(entries, tail="", eol="\n", pointer=False, after=""):
    parts = [f"# Status{eol}{eol}## Status{eol}Playing.{eol}{eol}## Harness changelog{eol}"]
    parts += entries
    if pointer:
        parts.append(POINTER + eol)
    parts.append(tail)
    parts.append(after)
    return "".join(parts)


def setup(tmp, cp_text, archive_text=None):
    with open(os.path.join(tmp, "CHECKPOINT.md"), "wb") as f:
        f.write(cp_text.encode())
    if archive_text is not None:
        os.makedirs(os.path.join(tmp, "archive"), exist_ok=True)
        with open(os.path.join(tmp, "archive", "harness_changelog.md"), "wb") as f:
            f.write(archive_text.encode())


def rd(tmp, *p):
    with open(os.path.join(tmp, *p), "rb") as f:
        return f.read()


def run(tmp, *flags):
    return cm.main([tmp, *flags])


@pytest.fixture
def tmp():
    with tempfile.TemporaryDirectory() as d:
        yield d


def test_under_three_entries_is_noop(tmp):
    text = checkpoint([entry(2), entry(1)], after="## Next step\nGo.\n")
    setup(tmp, text)
    assert run(tmp) == 0
    assert rd(tmp, "CHECKPOINT.md") == text.encode()
    assert not os.path.exists(os.path.join(tmp, "archive"))


def test_five_entries_newest_first(tmp):
    es = [entry(n) for n in (5, 4, 3, 2, 1)]
    text = checkpoint(es, after="## Next step\nGo.\n")
    setup(tmp, text)
    assert run(tmp) == 0
    cp = rd(tmp, "CHECKPOINT.md").decode()
    assert cp == checkpoint(es[:3], pointer=True, after="## Next step\nGo.\n")
    ar = rd(tmp, "archive", "harness_changelog.md").decode()
    assert ar == "# Harness changelog archive\n\n" + es[3] + es[4]
    assert cp.count("Older entries:") == 1


def test_oldest_first_refused_without_flag(tmp):
    es = [entry(n) for n in (1, 2, 3, 4, 5)]
    text = checkpoint(es)
    setup(tmp, text)
    assert run(tmp) == 1
    assert rd(tmp, "CHECKPOINT.md") == text.encode()
    assert not os.path.exists(os.path.join(tmp, "archive"))


def test_oldest_first_with_flag(tmp):
    es = [entry(n) for n in (1, 2, 3, 4, 5)]
    setup(tmp, checkpoint(es, after="## Next step\nGo.\n"))
    assert run(tmp, "--reverse-if-oldest-first") == 0
    cp = rd(tmp, "CHECKPOINT.md").decode()
    assert cp == checkpoint([es[4], es[3], es[2]], pointer=True, after="## Next step\nGo.\n")
    ar = rd(tmp, "archive", "harness_changelog.md").decode()
    assert ar == "# Harness changelog archive\n\n" + es[1] + es[0]


def test_flag_on_newest_first_does_not_reverse(tmp):
    es = [entry(n) for n in (4, 3, 2, 1)]
    setup(tmp, checkpoint(es))
    assert run(tmp, "--reverse-if-oldest-first") == 0
    assert rd(tmp, "archive", "harness_changelog.md").decode().endswith(es[3])


def test_flag_refuses_when_order_unknowable(tmp):
    es = ["### alpha\ntext\n\n", "### beta\ntext\n\n", "### gamma\ntext\n"]
    text = checkpoint(es)
    setup(tmp, text)
    assert run(tmp, "--reverse-if-oldest-first") == 1
    assert rd(tmp, "CHECKPOINT.md") == text.encode()


def test_existing_archive_and_pointer(tmp):
    old = [entry(2), entry(1)]
    es = [entry(n) for n in (6, 5, 4, 3)]
    archive = "# Harness changelog archive\n\n" + "".join(old)
    setup(tmp, checkpoint(es, pointer=True, tail="\n", after="## Next step\nGo.\n"), archive)
    assert run(tmp) == 0
    cp = rd(tmp, "CHECKPOINT.md").decode()
    assert cp == checkpoint(es[:3], pointer=True, tail="\n", after="## Next step\nGo.\n")
    assert rd(tmp, "archive", "harness_changelog.md").decode() == \
        "# Harness changelog archive\n\n" + es[3] + "".join(old)


def test_noop_with_existing_archive_is_idempotent(tmp):
    es = [entry(n) for n in (3, 2, 1)]
    text = checkpoint(es, pointer=True)
    archive = "# Harness changelog archive\n\n" + entry(0)
    setup(tmp, text, archive)
    assert run(tmp) == 0
    assert rd(tmp, "CHECKPOINT.md") == text.encode()
    assert rd(tmp, "archive", "harness_changelog.md") == archive.encode()


def test_duplicate_pointers_collapse_to_one(tmp):
    es = [entry(n) for n in (3, 2, 1)]
    text = checkpoint(es, pointer=True).replace(POINTER + "\n", POINTER + "\n" + POINTER + "\n")
    setup(tmp, text, "# Harness changelog archive\n\n")
    assert run(tmp) == 0
    assert rd(tmp, "CHECKPOINT.md").decode().count("Older entries:") == 1


def test_over_limit_moves_more_but_keeps_newest(tmp):
    big = "x" * 9000
    es = [entry(3, body=big), entry(2, body=big), entry(1, body=big)]
    text = checkpoint(es)
    assert len(text) > 24000
    setup(tmp, text)
    assert run(tmp) == 0
    cp = rd(tmp, "CHECKPOINT.md")
    assert len(cp) <= 24000
    assert b"### v3 " in cp and b"### v2 " in cp and b"### v1 " not in cp
    assert rd(tmp, "archive", "harness_changelog.md").decode().endswith(es[2])


def test_over_limit_never_drops_newest(tmp):
    big = "x" * 30000
    es = [entry(2, body=big), entry(1, body="small")]
    setup(tmp, checkpoint(es))
    assert run(tmp) == 0
    assert b"### v2 " in rd(tmp, "CHECKPOINT.md")
    assert b"### v1 " not in rd(tmp, "CHECKPOINT.md")


def test_crlf_preserved(tmp):
    es = [entry(n, eol="\r\n") for n in (5, 4, 3, 2, 1)]
    setup(tmp, checkpoint(es, eol="\r\n", after="## Next step\r\nGo.\r\n"))
    assert run(tmp) == 0
    cp = rd(tmp, "CHECKPOINT.md")
    assert cp.replace(b"\r\n", b"").count(b"\n") == 0 and cp.count(b"\r\n") == cp.count(b"\n")
    assert POINTER.encode() + b"\r\n" in cp
    ar = rd(tmp, "archive", "harness_changelog.md")
    assert ar == b"# Harness changelog archive\r\n\r\n" + es[3].encode() + es[4].encode()


def test_trailing_blank_lines_and_whitespace_stay_with_entry(tmp):
    e5 = entry(5, blanks=1)
    e4 = entry(4, blanks=3)
    e3 = entry(3, body="Ends with spaces   ", blanks=2)
    e2 = entry(2, body="Tail  \t", blanks=4)
    e1 = entry(1, blanks=0)
    setup(tmp, checkpoint([e5, e4, e3, e2, e1], after="## Next step\nGo.\n"))
    assert run(tmp) == 0
    ar = rd(tmp, "archive", "harness_changelog.md").decode()
    assert ar == "# Harness changelog archive\n\n" + e2 + e1
    assert e2.endswith("\n\n\n\n\n")


def test_dry_run_writes_nothing(tmp, capsys):
    es = [entry(n) for n in (5, 4, 3, 2, 1)]
    text = checkpoint(es)
    setup(tmp, text)
    assert run(tmp, "--dry-run") == 0
    assert rd(tmp, "CHECKPOINT.md") == text.encode()
    assert not os.path.exists(os.path.join(tmp, "archive"))
    out = capsys.readouterr().out
    assert "entries moved: 2" in out
    assert hashlib.sha256(es[3].encode()).hexdigest() in out
    assert "bytes before" in out and "bytes after" in out


def test_other_sections_untouched(tmp):
    es = [entry(n) for n in (5, 4, 3, 2, 1)]
    after = "## Next step\nKeep ### v9 text here.\n\nOlder entries: not mine\n"
    setup(tmp, checkpoint(es, after=after))
    assert run(tmp) == 0
    cp = rd(tmp, "CHECKPOINT.md").decode()
    assert cp.startswith("# Status\n\n## Status\nPlaying.\n\n## Harness changelog\n")
    assert cp.endswith(after)


def _refused_unchanged(tmp, text, *flags, archive=None):
    setup(tmp, text, archive)
    assert run(tmp, *flags) == 1
    assert rd(tmp, "CHECKPOINT.md") == text.encode()
    if archive is None:
        assert not os.path.exists(os.path.join(tmp, "archive"))
    else:
        assert rd(tmp, "archive", "harness_changelog.md") == archive.encode()


def _h(title, n=3):
    return f"### {title}\nbody\n\n"


def test_default_refuses_non_monotone_versions(tmp):
    es = [entry(n) for n in (5, 2, 4, 3, 1)]
    _refused_unchanged(tmp, checkpoint(es))


def test_default_refuses_contradictory_version_and_date(tmp):
    es = [f"### v{n} -- 2026-11-{d:02d}\nbody\n\n" for n, d in ((5, 1), (4, 2), (3, 3), (2, 4), (1, 5))]
    _refused_unchanged(tmp, checkpoint(es))


def test_default_refuses_missing_or_mixed_keys(tmp):
    es = [_h("v5 -- 2026-11-05"), _h("note -- 2026-11-04"), _h("v3 -- 2026-11-03"),
          _h("v2 -- 2026-11-02"), _h("v1 -- 2026-11-01")]
    _refused_unchanged(tmp, checkpoint(es))


def test_default_refuses_same_day_entries_without_versions(tmp):
    es = [_h("fix four -- 2026-11-01"), _h("fix three -- 2026-11-01"), _h("fix two -- 2026-11-01"),
          _h("fix one -- 2026-11-01")]
    _refused_unchanged(tmp, checkpoint(es))


def test_default_refuses_dates_only_non_monotone(tmp):
    es = [_h(f"x -- 2026-11-{d:02d}") for d in (5, 2, 4, 3)]
    _refused_unchanged(tmp, checkpoint(es))


def test_unknown_order_is_fine_when_nothing_moves(tmp):
    es = [_h("alpha"), _h("beta")]
    text = checkpoint(es)
    setup(tmp, text)
    assert run(tmp) == 0
    assert rd(tmp, "CHECKPOINT.md") == text.encode()


def test_pointer_without_archive_refused(tmp):
    es = [entry(n) for n in (3, 2, 1)]
    _refused_unchanged(tmp, checkpoint(es, pointer=True))


def test_legacy_pointer_refused(tmp):
    es = [entry(n) for n in (3, 2, 1)]
    text = checkpoint(es).replace("## Next", "## Next") + "Older entries: docs/old_log.md\n"
    _refused_unchanged(tmp, text, archive="# Harness changelog archive\n\n")


def _fail_second_write(monkeypatch):
    real = cm.write_atomic

    def fake(path, data):
        if os.path.basename(path) == "CHECKPOINT.md":
            raise OSError("locked")
        return real(path, data)
    monkeypatch.setattr(cm, "write_atomic", fake)


def test_second_write_failure_rolls_back_existing_archive(tmp, monkeypatch, capsys):
    es = [entry(n) for n in (5, 4, 3, 2, 1)]
    text = checkpoint(es[:4] + [es[4]], pointer=False)
    archive = "# Harness changelog archive\n\n" + entry(0)
    setup(tmp, text, archive)
    _fail_second_write(monkeypatch)
    assert run(tmp) == 1
    assert rd(tmp, "CHECKPOINT.md") == text.encode()
    assert rd(tmp, "archive", "harness_changelog.md") == archive.encode()
    assert "restored" in capsys.readouterr().err


def test_second_write_failure_removes_new_archive(tmp, monkeypatch):
    es = [entry(n) for n in (5, 4, 3, 2, 1)]
    text = checkpoint(es)
    setup(tmp, text)
    _fail_second_write(monkeypatch)
    assert run(tmp) == 1
    assert rd(tmp, "CHECKPOINT.md") == text.encode()
    assert not os.path.exists(os.path.join(tmp, "archive"))


def test_rerun_after_partial_write_refused(tmp):
    es = [entry(n) for n in (5, 4, 3, 2, 1)]
    text = checkpoint(es)
    # the state a crash between the two writes leaves: archive updated, CHECKPOINT not
    archive = "# Harness changelog archive\n\n" + es[3] + es[4]
    _refused_unchanged(tmp, text, archive=archive)


def test_missing_section_fails_closed(tmp):
    setup(tmp, "# Status\n\n## Next step\nGo.\n")
    assert run(tmp) == 1


def test_bad_archive_header_fails_closed(tmp):
    es = [entry(n) for n in (5, 4, 3, 2, 1)]
    text = checkpoint(es)
    setup(tmp, text, "not the header\n")
    assert run(tmp) == 1
    assert rd(tmp, "CHECKPOINT.md") == text.encode()
