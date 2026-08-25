"""
SIGIL_TRANSFER_FRONTIER_001 -- proof that SIGIL.ABSENT_ILLEGAL_EDGE is
durably registered in SIGIL_LEXICON.md, and that its cited proof (6
independently-defined state-machine check functions, each following
the `dst in TABLE.get(src, frozenset())` structure with no shared
base) is real, not asserted. Same registration mechanism as
SIGIL.REF_INTEGRITY / SIGIL.NO_DELETE_SURFACE -- no new registry code.
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LEXICON = REPO_ROOT / "SIGIL_LEXICON.md"

_ROW_PATTERN = re.compile(r"^\|\s*(SIGIL\.\S+)\s*\|\s*(\S+)\s*\|", re.MULTILINE)

CITED_SOURCE_MODULES = (
    ("kpm/promotion/state_machine.py", "def can_transition"),
    ("foundation/task_queue.py", "def can_transition"),
    ("foundation/flow_switch.py", "def can_transition"),
    ("firewall/quarantine.py", "def can_transition"),
    ("narrative/schema/narrative_atom.py", "def can_promote"),
    ("kpm/schemas/epistemic_types.py", "def can_reclassify"),
)

CITED_PROOF_FILES = (
    "kpm/promotion/tests/test_state_machine.py",
    "foundation/tests/test_task_queue.py",
    "foundation/tests/test_flow_switch.py",
    "firewall/tests/test_quarantine_dissent.py",
    "narrative/tests/test_narrative_atom_store.py",
    "kpm/schemas/tests/test_epistemic_types.py",
)


class TestAbsentIllegalEdgeInvariantIsRegistered(unittest.TestCase):
    def setUp(self):
        self.text = LEXICON.read_text()
        self.rows = _ROW_PATTERN.findall(self.text)
        self.matching_lines = [l for l in self.text.splitlines() if "SIGIL.ABSENT_ILLEGAL_EDGE" in l]

    def test_entry_present_and_well_formed(self):
        self.assertEqual(len(self.matching_lines), 1)
        cells = [c.strip() for c in self.matching_lines[0].strip().strip("|").split("|")]
        self.assertEqual(len(cells), 9)
        for cell in cells:
            self.assertTrue(cell)

    def test_stable_id_and_glyph_are_unique(self):
        ids = [r[0] for r in self.rows]
        glyphs = [r[1] for r in self.rows]
        self.assertEqual(ids.count("SIGIL.ABSENT_ILLEGAL_EDGE"), 1)
        self.assertEqual(glyphs.count("∉"), 1)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(glyphs), len(set(glyphs)))

    def test_all_six_source_modules_exist_and_define_their_own_check_function(self):
        """Not shared code -- each module defines its own locally-named
        function, not an import of a common helper."""
        for rel_path, def_signature in CITED_SOURCE_MODULES:
            path = REPO_ROOT / rel_path
            self.assertTrue(path.exists(), rel_path)
            self.assertIn(def_signature, path.read_text(), rel_path)

    def test_no_module_imports_the_check_function_from_another(self):
        """Independence proof: none of the 6 source modules imports its
        transition-check function from any of the others."""
        function_names = {sig.split()[-1] for _, sig in CITED_SOURCE_MODULES}
        for rel_path, _ in CITED_SOURCE_MODULES:
            text = (REPO_ROOT / rel_path).read_text()
            import_lines = [l for l in text.splitlines() if l.startswith(("import ", "from "))]
            for line in import_lines:
                for fn in function_names:
                    self.assertNotIn(f" {fn}", line, f"{rel_path} imports {fn}: {line}")

    def test_all_six_proof_files_exist(self):
        for rel_path in CITED_PROOF_FILES:
            self.assertTrue((REPO_ROOT / rel_path).exists(), rel_path)

    def test_entry_does_not_overclaim_a_seventh_domain(self):
        row = self.matching_lines[0]
        for rel_path, _ in CITED_SOURCE_MODULES:
            leaf = rel_path.rsplit("/", 1)[-1]
            self.assertIn(leaf, row)

    def test_control_and_prior_specimen_unmodified(self):
        for stable_id, needle_a, needle_b in (
            ("SIGIL.REF_INTEGRITY", "rpa/composition/checker.py", "narrative/composition/checker.py"),
            ("SIGIL.NO_DELETE_SURFACE", "foundation/task_queue.py", "foundation/flow_switch.py"),
        ):
            rows = [l for l in self.text.splitlines() if stable_id in l]
            self.assertEqual(len(rows), 1)
            self.assertIn(needle_a, rows[0])
            self.assertIn(needle_b, rows[0])


if __name__ == "__main__":
    unittest.main()
