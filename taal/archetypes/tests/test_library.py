"""
Tests for taal/archetypes/library.yaml.

Proves every one of the 12 threat_archetype records in the library
individually validates VALID via the same public
taal.validators.validate_threat_archetype.validate_threat_archetype()
function used on any other threat_archetype document — no library-specific
validation path.

Container shape: library.yaml is a top-level `archetypes:` list, where
each entry IS the threat_archetype body (not pre-wrapped in
`threat_archetype:`). Each entry is re-wrapped under a top-level
`threat_archetype:` key and re-serialised to YAML text before being handed
to the validator, exactly mirroring how any other single threat_archetype
document is presented to that function.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import yaml  # noqa: E402

from taal.validators.validate_threat_archetype import (  # noqa: E402
    validate_threat_archetype,
)

_LIBRARY_PATH = Path(__file__).resolve().parents[1] / "library.yaml"

EXPECTED_ARCHETYPE_NAMES = {
    "THE DECEIVER", "THE PARASITE", "THE IMPERSONATOR", "THE INVADER",
    "THE CORRUPTER", "THE ESCALATOR", "THE SHADOW", "THE PERSISTOR",
    "THE EXTRACTOR", "THE SABOTEUR", "THE DIVIDER", "THE MANIPULATOR",
}


def _load_library() -> list[dict]:
    with open(_LIBRARY_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["archetypes"]


class TestLibraryShape(unittest.TestCase):
    def test_library_file_parses(self):
        entries = _load_library()
        self.assertIsInstance(entries, list)

    def test_library_has_exactly_twelve_records(self):
        entries = _load_library()
        self.assertEqual(len(entries), 12)

    def test_library_covers_all_twelve_symbolic_archetype_names(self):
        entries = _load_library()
        names = {e["symbolic_layer"]["archetype_name"] for e in entries}
        self.assertEqual(names, EXPECTED_ARCHETYPE_NAMES)

    def test_library_ids_are_unique(self):
        entries = _load_library()
        ids = [e["id"] for e in entries]
        self.assertEqual(len(ids), len(set(ids)), msg=f"duplicate ids: {ids}")


class TestEachRecordValidatesIndividually(unittest.TestCase):
    """The core proof: every one of the 12 records, taken in isolation and
    re-wrapped exactly as a standalone document, validates VALID with zero
    issues through the real public validator function."""

    @classmethod
    def setUpClass(cls):
        cls.entries = _load_library()

    def test_all_twelve_entries_present_for_subtests(self):
        self.assertEqual(len(self.entries), 12)

    def test_each_record_validates_individually(self):
        for entry in self.entries:
            archetype_name = entry["symbolic_layer"]["archetype_name"]
            entry_id = entry["id"]
            text = yaml.safe_dump({"threat_archetype": entry}, sort_keys=False)
            with self.subTest(archetype_name=archetype_name, id=entry_id):
                result = validate_threat_archetype(text)
                self.assertEqual(
                    result.status, "VALID",
                    msg=f"{archetype_name} ({entry_id}) failed: "
                        f"{[i.to_dict() for i in result.issues]}",
                )
                self.assertEqual(result.issues, [])
                self.assertEqual(result.archetype_id, entry_id)


class TestEachRecordMapsToADeclaredThreatClass(unittest.TestCase):
    """Each of the 12 symbolic archetypes must map to exactly one
    technical_layer.threat_class, and no two archetypes may silently share
    the same mapping without that being a deliberate, visible choice."""

    def test_threat_class_values_are_distinct_across_the_library(self):
        entries = _load_library()
        threat_classes = [e["technical_layer"]["threat_class"] for e in entries]
        self.assertEqual(
            len(threat_classes), len(set(threat_classes)),
            msg=f"expected 12 distinct threat_class mappings, got: {threat_classes}",
        )

    def test_every_entry_has_metaphor_status_symbolic_only(self):
        entries = _load_library()
        for e in entries:
            self.assertEqual(
                e["symbolic_layer"]["metaphor_status"], "SYMBOLIC_ONLY",
                msg=f"{e['id']} violates the structural symbolic/technical firewall",
            )


if __name__ == "__main__":
    unittest.main()
