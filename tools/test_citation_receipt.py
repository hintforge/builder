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

    def test_label_rejects_other_brackets(self):
        self.assertFalse(C.LABEL.search("[Hypothesis -- unverified]"))

    def test_corroborated_facts_are_counted_and_resolved(self):
        r = C.receipt(FIX / "mixed_labels.md")
        self.assertEqual(r["facts"], 4)
        self.assertEqual(r["footnote"], 3)
        self.assertEqual(r["url"], 1)
        self.assertEqual(r["count-only"], 0)
        self.assertEqual(r["traceable"], 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
