#!/usr/bin/env python3
"""Tests for citation_receipt.py. Standard library only.

Run:  python tools/test_citation_receipt.py        (or: python -m unittest)

Fixture: tools/fixtures/citation_receipt/ -- a hand-written result file. Tests never touch a real guide.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import citation_receipt as C  # noqa: E402

FIX = HERE / "fixtures" / "citation_receipt"


class LabelTests(unittest.TestCase):
    def test_label_accepts_confirmed_single_source_and_corroborated(self):
        for text in (
            "[Confirmed: 3 sources, 1 language]",
            "[Single source -- verify · class:forum]",
            "[Corroborated: 2 sources, 1 language -- below floor]",
        ):
            self.assertTrue(C.LABEL.search(text), text)

    def test_bare_corroborated_label_is_a_head_count_not_a_named_source(self):
        self.assertFalse(C.names_sources("[Corroborated: 2 sources, 1 language]"))
        self.assertFalse(C.names_sources("[Confirmed: 2 sources, 1 language]"))

    def test_label_rejects_other_brackets(self):
        self.assertFalse(C.LABEL.search("[Hypothesis -- unverified]"))

    def test_corroborated_facts_are_counted_and_resolved(self):
        r = C.receipt(FIX / "mixed_labels.md")
        self.assertEqual(r["facts"], 4)
        self.assertEqual(r["footnote"], 3)
        self.assertEqual(r["url"], 1)
        self.assertEqual(r["count-only"], 0)
        self.assertEqual(r["traceable"], 4)
        self.assertEqual(r["unresolved"], 0)


class ReferenceShapeTests(unittest.TestCase):
    def test_r_style_ids_ranges_and_table_rows_resolve(self):
        r = C.receipt(FIX / "r_style_refs.md")
        self.assertEqual(r["reference_entries"], 5)
        self.assertEqual(r["facts"], 7)
        self.assertEqual(r["footnote"], 7)
        self.assertEqual(r["unresolved"], 0)
        self.assertEqual(r["unresolved_ids"], [])
        # Rows with a Ref column and no source label: two cite entries, one ("key: unknown", "-") cites none.
        self.assertEqual(r["table_rows"], 3)
        self.assertEqual(r["table_rows_resolved"], 2)

    def test_chained_markers_are_each_read(self):
        # The pinned brief format cites "[1][4]"; both ids count, so a missing [4] is reported.
        # A Markdown reference link "[map][1]" is not a citation chain.
        r = C.receipt(FIX / "multi_marker.md")
        self.assertEqual(r["facts"], 2)
        self.assertEqual(r["unresolved_ids"], [4])
        self.assertEqual(C.ids_in_text("[map][1]"), set())

    def test_labelled_table_row_is_a_fact_not_a_reference_entry(self):
        # A numbered fact row whose second cell is a URL carries a source label, so it is a fact:
        # it is counted, its R99 is reported missing, and its row number invents no reference 1.
        r = C.receipt(FIX / "fact_table_url.md")
        self.assertEqual(r["reference_entries"], 1)
        self.assertEqual(r["facts"], 2)
        self.assertEqual(r["unresolved_ids"], [99])

    def test_unresolved_references_are_listed_by_id(self):
        r = C.receipt(FIX / "unresolved_refs.md")
        self.assertEqual(r["facts"], 4)
        self.assertEqual(r["footnote"], 4)
        self.assertEqual(r["unresolved_ids"], [7, 9, 10, 12, 13])
        self.assertEqual(r["unresolved"], 5)
        self.assertEqual(r["table_rows"], 1)
        self.assertEqual(r["table_rows_resolved"], 0)

    def test_id_helpers(self):
        self.assertEqual(C.ids_in_text("see R31-R33 and [^4]"), {31, 32, 33, 4})
        self.assertEqual(C.ids_in_text("(corroborated: refs 3, 5, 9-11; more prose 12)"), {3, 5, 9, 10, 11})
        self.assertEqual(C.ref_cell_ids("1, 4-6"), {1, 4, 5, 6})
        self.assertEqual(C.ref_cell_ids("a 5-card hand"), set())

    def test_table_prints_unresolved_column(self):
        out = C.table([C.receipt(FIX / "unresolved_refs.md")])
        self.assertIn("Unresolved references", out)
        self.assertIn("7, 9, 10, 12, 13", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
