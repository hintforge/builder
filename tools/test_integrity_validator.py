#!/usr/bin/env python3
"""Tests for integrity_validator.py. Standard library only.

Run:  python tools/test_integrity_validator.py        (or: python -m unittest)

Fixtures: tools/fixtures/integrity_validator/synthetic/ -- hand-written
cases, one behaviour per file. Tests never touch a real guide.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import integrity_validator as V  # noqa: E402

FIX = HERE / "fixtures" / "integrity_validator"
SYN = FIX / "synthetic"
TOOL = HERE / "integrity_validator.py"


def line_of(root: Path, rel: str, marker: str, nth: int = 1) -> int:
    """1-based line number of the nth line containing marker."""
    hits = [i for i, ln in enumerate((root / rel).read_text(encoding="utf-8").splitlines(), 1) if marker in ln]
    return hits[nth - 1]


def flagged(result):
    return {(v["file"], v["line"], v["check"]) for v in result["violations"]}


def excused(result):
    return {(e["file"], e["line"]): e["rule"] for e in result["excused"]}


class SyntheticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = V.validate_guide(SYN)
        cls.f = flagged(cls.r)
        cls.x = excused(cls.r)

    def test_parses_and_reads_core_version(self):
        self.assertTrue(self.r["parsed"])
        self.assertEqual(self.r["corpus_core_version"], 6)
        self.assertEqual(self.r["manifest_path"], "nav/architecture.md")

    def test_clean_file_has_no_violations_and_every_variant_is_counted(self):
        self.assertFalse({v for v in self.f if v[0] == "claims_ok.md"})
        counted = [c for c in self.r["claim_index"] if c.startswith("claims_ok.md:")]
        # 5 inline variants + 1 block; the fenced example is not content.
        self.assertEqual(len(counted), 6, counted)

    def test_tolerant_separator_and_wrap_are_not_violations(self):
        tol = {k for k, rule in self.x.items() if k[0] == "claims_ok.md" and rule == "tolerant-separator"}
        self.assertEqual(len(tol), 2)  # pipe and spaced-hyphen; the wrap parses natively

    def test_bad_claims_flagged_exactly(self):
        bad = "claims_bad.md"
        expect = {
            (bad, line_of(SYN, bad, "Empty source.") + 1, "source"),
            (bad, line_of(SYN, bad, "Missing puzzle-tier.") + 1, "tier"),
            (bad, line_of(SYN, bad, "Missing both tiers.") + 1, "tier"),
            (bad, line_of(SYN, bad, "- **claim:** c"), "source"),
            (bad, line_of(SYN, bad, "- **claim:** d"), "tier"),
        }
        self.assertEqual({v for v in self.f if v[0] == bad}, expect)
        details = {(v["line"], v["check"]): v["detail"] for v in self.r["violations"] if v["file"] == bad}
        self.assertEqual(details[(line_of(SYN, bad, "Missing puzzle-tier.") + 1, "tier")], "missing puzzle-tier")
        self.assertEqual(details[(line_of(SYN, bad, "- **claim:** d"), "tier")], "missing enemy-tier")

    def test_scaffold_skipped_for_source_and_tier(self):
        self.assertFalse({v for v in self.f if v[0] == "scaffold.md"})
        self.assertEqual(self.r["files_skipped_scaffold"], 1)

    def test_status_check(self):
        status = {v for v in self.f if v[2] == "status"}
        self.assertEqual(status, {("status_bad.md", 2, "status")})  # prefix word, plain form, scaffold all pass

    def test_artifacts_dir_excluded(self):
        self.assertFalse({v for v in self.f if v[0].startswith("artifacts/")})

    def test_section_tier_tag_governs_until_heading(self):
        f = "shape_section_tag.md"
        for marker in ("Governed by the bare", "Governed by the blockquote", "Own enemy-tier"):
            ln = line_of(SYN, f, marker) + 1
            self.assertEqual(self.x.get((f, ln)), "section-tier-tag", marker)
        reset = line_of(SYN, f, "Heading reset") + 1
        self.assertEqual({v for v in self.f if v[0] == f}, {(f, reset, "tier")})

    def test_preamble_citation_over_tagged_subsections_is_container(self):
        f = "shape_preamble_tag.md"
        ln = line_of(SYN, f, "_source:")
        self.assertEqual(self.x.get((f, ln)), "section-tier-tag")
        self.assertFalse({v for v in self.f if v[0] == f})

    def test_table_citation_excused_prose_citation_flagged(self):
        f = "shape_table.md"
        for i in (1, 2):
            self.assertEqual(self.x.get((f, line_of(SYN, f, "_source:", i))), "table-citation")
        self.assertEqual({v for v in self.f if v[0] == f}, {(f, line_of(SYN, f, "_source:", 3), "tier")})
        self.assertEqual(self.r["shapes"]["table_citations_with_row_tier_column"], 1)
        self.assertEqual(self.r["shapes"]["table_citations_without_row_tier_column"], 1)

    def test_entry_block_container_needs_tiered_entries(self):
        ok, bad = "shape_entry_blocks.md", "shape_entry_blocks_untiered.md"
        self.assertEqual(self.x.get((ok, line_of(SYN, ok, "_source:"))), "entry-block-container")
        self.assertFalse({v for v in self.f if v[0] == ok})
        self.assertEqual({v for v in self.f if v[0] == bad}, {(bad, line_of(SYN, bad, "_source:"), "tier")})

    def test_row_tier_column_vocabulary(self):
        ok, bad = "row_tier_ok.md", "row_tier_bad.md"
        self.assertFalse({v for v in self.f if v[0] == ok})
        self.assertEqual(
            {v for v in self.f if v[0] == bad},
            {(bad, line_of(SYN, bad, "late game"), "tier"), (bad, line_of(SYN, bad, "endgame"), "tier")})
        # A numeric row tier (legacy `E / P` pair, tech-tree tiers) is left alone: shape_table.md has one.
        self.assertFalse({v for v in self.f if v[0] == "shape_table.md" and v[1] == line_of(SYN, "shape_table.md", "Pick the left door")})

    def test_totals(self):
        self.assertEqual(self.r["counts"], {"source": 2, "tier": 8, "status": 1})


class CanonicalShapePlugInTests(unittest.TestCase):
    """Rejecting a shape makes exactly the claims that shape excused fall
    through to the plain tier check."""

    def run_rejecting(self, *shapes):
        keep = [s for s in V.ALL_SHAPES if s not in shapes]
        return V.validate_guide(SYN, accepted_shapes=keep)

    def test_default_accepts_all(self):
        self.assertEqual(tuple(V.ACCEPTED_SHAPES), V.ALL_SHAPES)

    def test_reject_section_tier_tag(self):
        base = flagged(V.validate_guide(SYN))
        new = flagged(self.run_rejecting("section-tier-tag")) - base
        files = {v[0] for v in new}
        self.assertEqual(files, {"shape_section_tag.md", "shape_preamble_tag.md"})
        self.assertEqual(len([v for v in new if v[0] == "shape_section_tag.md"]), 3)

    def test_reject_table_citation(self):
        new = flagged(self.run_rejecting("table-citation")) - flagged(V.validate_guide(SYN))
        self.assertEqual({v[0] for v in new}, {"shape_table.md"})
        self.assertEqual(len(new), 2)

    def test_reject_entry_block_container(self):
        new = flagged(self.run_rejecting("entry-block-container")) - flagged(V.validate_guide(SYN))
        self.assertEqual({v[0] for v in new}, {"shape_entry_blocks.md"})


class DeterminismAndCliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-I", str(TOOL), *args], capture_output=True, text=True, timeout=120)

    def test_same_input_same_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            a, b = Path(td) / "a.json", Path(td) / "b.json"
            self.assertEqual(self.run_cli(str(SYN), "--json", str(a), "--quiet").returncode, 0)
            self.assertEqual(self.run_cli(str(SYN), "--json", str(b), "--quiet").returncode, 0)
            self.assertEqual(a.read_bytes(), b.read_bytes())

    def test_exit_codes(self):
        self.assertEqual(self.run_cli(str(SYN), "--quiet").returncode, 0)  # report tool: never blocks
        self.assertEqual(self.run_cli(str(SYN), "--quiet", "--exit-code").returncode, 1)
        self.assertEqual(self.run_cli("--no-such-flag").returncode, 2)

    def test_only_scopes_to_listed_files(self):
        r = V.validate_guide(SYN, only=["claims_bad.md"])
        self.assertEqual({v["file"] for v in r["violations"]}, {"claims_bad.md"})
        self.assertEqual(r["files_checked"], 1)

    def test_unparsed_guide_is_reported_not_raised(self):
        with tempfile.TemporaryDirectory() as td:
            r = V.validate_guide(Path(td))
            self.assertFalse(r["parsed"])
            self.assertIn("no manifest", r["error"])

    def test_reject_shape_flag(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "o.json"
            self.run_cli(str(SYN), "--quiet", "--reject-shape", "table-citation", "--json", str(out))
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertNotIn("table-citation", data["accepted_shapes"])


class EdgeCaseTests(unittest.TestCase):
    """Edge cases, each reproduced on a one-file temp guide."""

    def _run(self, text):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "nav").mkdir()
            (root / "nav" / "architecture.md").write_text("corpus-core-version: 6\n", encoding="utf-8")
            (root / "c.md").write_text(text, encoding="utf-8")
            return V.validate_guide(root)

    def test_missing_status_on_claim_bearing_file_is_a_violation(self):
        r = self._run("# T\n\n_source: https://e.org/a · enemy-tier: 0 · puzzle-tier: 0_\n")
        self.assertEqual(r["counts"], {"source": 0, "tier": 0, "status": 1})

    def test_missing_status_on_file_without_claims_is_not_a_violation(self):
        r = self._run("# T\n\nJust prose.\n")
        self.assertEqual(r["counts"]["status"], 0)

    def test_empty_source_before_leading_pipe_is_flagged(self):
        r = self._run("**status:** research-integrated\n\n_source: | enemy-tier: 0 | puzzle-tier: 0_\n")
        self.assertEqual(r["counts"]["source"], 1)

    def test_empty_source_before_leading_spaced_hyphen_is_flagged(self):
        r = self._run("**status:** research-integrated\n\n_source: - enemy-tier: 0 · puzzle-tier: 0_\n")
        self.assertEqual(r["counts"]["source"], 1)

    def test_inner_three_backtick_does_not_close_four_backtick_fence(self):
        text = ("**status:** research-integrated\n\n````markdown\n```\ninner\n```\n"
                "_source: · enemy-tier: 0_\n````\n")
        r = self._run(text)
        self.assertEqual(r["counts"], {"source": 0, "tier": 0, "status": 0})
        self.assertEqual(r["claims_checked"], 0)

    def test_claim_line_inside_inner_example_of_longer_fence_is_not_content(self):
        text = ("**status:** research-integrated\n\n````markdown\n```\n"
                "_source: · enemy-tier: 0_\n```\n````\n")
        r = self._run(text)
        self.assertEqual(r["counts"], {"source": 0, "tier": 0, "status": 0})
        self.assertEqual(r["claims_checked"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
