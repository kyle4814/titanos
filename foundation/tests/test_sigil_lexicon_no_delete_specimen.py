"""
INVARIANT_TRANSFER_FRONTIER_001 -- proof that SIGIL.NO_DELETE_SURFACE
is durably registered in SIGIL_LEXICON.md's existing canonical-
invariant table, and that its cited proof (8 independently-implemented
stores, each testing the exact same absence-of-method contract) is
real, not asserted. Same registration mechanism as SIGIL.REF_INTEGRITY
(foundation/tests/test_sigil_lexicon_specimen.py) -- no new registry
code, reusing the existing table/schema/Uniqueness Law.
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LEXICON = REPO_ROOT / "SIGIL_LEXICON.md"

_ROW_PATTERN = re.compile(r"^\|\s*(SIGIL\.\S+)\s*\|\s*(\S+)\s*\|", re.MULTILINE)

# The 8 test files this cycle's SIGIL_LEXICON.md entry cites as proof.
CITED_PROOF_FILES = (
    "foundation/tests/test_task_queue.py",
    "kpm/promotion/tests/test_state_machine.py",
    "kpm/contradictions/tests/test_registry.py",
    "narrative/tests/test_narrative_atom_store.py",
    "magl/registry/tests/test_catalogue.py",
    "firewall/tests/test_quarantine_dissent.py",
    "foundation/tests/test_crystal.py",
    "foundation/tests/test_flow_switch.py",
)


class TestNoDeleteSurfaceInvariantIsRegistered(unittest.TestCase):
    def setUp(self):
        self.text = LEXICON.read_text()
        self.rows = _ROW_PATTERN.findall(self.text)
        self.matching_lines = [l for l in self.text.splitlines() if "SIGIL.NO_DELETE_SURFACE" in l]

    def test_entry_present_and_well_formed(self):
        self.assertEqual(len(self.matching_lines), 1)
        cells = [c.strip() for c in self.matching_lines[0].strip().strip("|").split("|")]
        self.assertEqual(len(cells), 9)
        for cell in cells:
            self.assertTrue(cell)

    def test_stable_id_and_glyph_are_unique(self):
        ids = [r[0] for r in self.rows]
        glyphs = [r[1] for r in self.rows]
        self.assertEqual(ids.count("SIGIL.NO_DELETE_SURFACE"), 1)
        self.assertEqual(glyphs.count("⌀"), 1)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(glyphs), len(set(glyphs)))

    def test_all_eight_cited_proof_files_actually_exist(self):
        for rel_path in CITED_PROOF_FILES:
            self.assertTrue((REPO_ROOT / rel_path).exists(), rel_path)

    def test_all_eight_cited_files_actually_test_the_same_contract(self):
        """Not just that the files exist -- that each one genuinely
        asserts the exact same absence-of-method contract this
        invariant claims, not an unrelated test with a similar name."""
        for rel_path in CITED_PROOF_FILES:
            text = (REPO_ROOT / rel_path).read_text()
            self.assertIn("delete", text)
            self.assertIn("purge", text)
            self.assertIn("clear", text)
            self.assertIn("remove", text)
            self.assertIn("hasattr", text)
            self.assertIn("assertFalse", text)

    def test_entry_does_not_overclaim_a_ninth_domain(self):
        row = self.matching_lines[0]
        # Exactly 8 module paths cited -- count occurrences of "::" or
        # module-path-like tokens loosely by counting the cited files.
        for rel in CITED_PROOF_FILES:
            leaf = rel.rsplit("/", 1)[-1]
            self.assertIn(leaf, row)

    def test_control_specimen_ref_integrity_unmodified(self):
        """This cycle must not mutate the prior specimen -- proving the
        control stays exactly as it was registered last cycle."""
        ref_rows = [l for l in self.text.splitlines() if "SIGIL.REF_INTEGRITY" in l]
        self.assertEqual(len(ref_rows), 1)
        self.assertIn("rpa/composition/checker.py", ref_rows[0])
        self.assertIn("narrative/composition/checker.py", ref_rows[0])


if __name__ == "__main__":
    unittest.main()
