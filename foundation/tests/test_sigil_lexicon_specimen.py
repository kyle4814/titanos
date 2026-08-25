"""
INVARIANT_METABOLISM_001 — proof that one proven structural invariant
(cross-record referential integrity, first proven in rpa/, independently
transferred and reproven in narrative/) is durably represented in
SIGIL_LEXICON.md's existing canonical-invariant table, using that
table's own pre-existing schema and Uniqueness Law -- no new registry,
resolver, or parser was built. This does not generalize into a
SIGIL_LEXICON.md structural validator (unlike PARETO_FRONTIER.md's
check_frontier_schema()) -- no repeated real drift has ever been
observed in this file, so building one now would be speculative
infrastructure with no demonstrated need, the same class of overreach
this session has consistently declined.
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LEXICON = REPO_ROOT / "SIGIL_LEXICON.md"

_ROW_PATTERN = re.compile(r"^\|\s*(SIGIL\.\S+)\s*\|\s*(\S+)\s*\|", re.MULTILINE)


class TestReferentialIntegrityInvariantIsRegistered(unittest.TestCase):
    def setUp(self):
        self.text = LEXICON.read_text()
        self.rows = _ROW_PATTERN.findall(self.text)

    def test_1_entry_present_and_well_formed(self):
        matching = [r for r in self.text.splitlines() if "SIGIL.REF_INTEGRITY" in r]
        self.assertEqual(len(matching), 1)
        row = matching[0]
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        self.assertEqual(len(cells), 9)  # ID, Glyph, Name, Meaning, Class, Status, Source, Proof, Version
        for cell in cells:
            self.assertTrue(cell, f"empty cell in row: {row}")

    def test_2_stable_id_is_unique(self):
        ids = [r[0] for r in self.rows]
        self.assertEqual(ids.count("SIGIL.REF_INTEGRITY"), 1)

    def test_3_glyph_is_unique_among_existing_entries(self):
        glyphs = [r[1] for r in self.rows]
        self.assertEqual(glyphs.count("🔗"), 1)
        # Uniqueness Law: no other row may already claim this glyph.
        self.assertEqual(len(glyphs), len(set(glyphs)), "duplicate glyph found")

    def test_4_proof_references_resolve_to_real_files(self):
        self.assertTrue((REPO_ROOT / "rpa/composition/tests/test_checker.py").exists())
        self.assertTrue((REPO_ROOT / "narrative/composition/tests/test_checker.py").exists())

    def test_5_entry_names_both_transfer_domains_not_a_universal_claim(self):
        matching = [r for r in self.text.splitlines() if "SIGIL.REF_INTEGRITY" in r]
        row = matching[0]
        self.assertIn("rpa/composition/checker.py", row)
        self.assertIn("narrative/composition/checker.py", row)
        self.assertNotIn("universal", row.lower())
        self.assertNotIn("all domains", row.lower())

    def test_6_status_is_active_not_unproven(self):
        matching = [r for r in self.text.splitlines() if "SIGIL.REF_INTEGRITY" in r]
        row = matching[0]
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        status = cells[5]
        self.assertEqual(status, "ACTIVE")

    def test_7_all_stable_ids_in_file_remain_unique(self):
        """Existing unrelated entries are unaffected by this addition —
        the file-wide uniqueness invariant still holds across all 10
        rows, not just the new one."""
        ids = [r[0] for r in self.rows]
        self.assertEqual(len(ids), len(set(ids)))

    def test_8_repeated_read_is_deterministic(self):
        text_2 = LEXICON.read_text()
        self.assertEqual(self.text, text_2)


if __name__ == "__main__":
    unittest.main()
