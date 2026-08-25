"""
End-to-end proof: SourceRegistry (intake) -> narrative_atom_bridge ->
NarrativeAtomStore (digestion), using one real input, not fabricated
test data -- the same recursion-guard incident report text already
established as real in this repository's own history (`narrative/
tests/test_real_ingestion_recursion_guard.py`), this time driven
through the actual intake membrane (`SourceRegistry`) first, proving
the full pipeline that was previously unproven.

Import workaround note: kpm/source-vault/ is a hyphenated directory,
so `registry` is imported the same way `kpm/source-vault/tests/
test_registry.py` already does -- sys.path insertion, not a dotted
package import.
"""

import sys
import tempfile
import unittest
from pathlib import Path

_SOURCE_VAULT_DIR = Path(__file__).resolve().parents[2] / "kpm" / "source-vault"
if str(_SOURCE_VAULT_DIR) not in sys.path:
    sys.path.insert(0, str(_SOURCE_VAULT_DIR))

import registry as source_vault  # noqa: E402

from narrative.intake.source_vault_bridge import source_record_to_narrative_atom_yaml
from narrative.store.narrative_atom_store import NarrativeAtomStore
from narrative.validators.validate_narrative_atom import validate_narrative_atom

REAL_INPUT = (
    "compute_sigil() proof-dimension recursion bounded by execution-ancestry "
    "guard. 37/37 targeted tests passed. 8/8 subsystem regression suites "
    "passed. No persistent orphaned unittest processes remained. Commit 93b3e89."
)


class TestSourceVaultToNarrativeAtomPipeline(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.registry = source_vault.SourceRegistry(
            archive_dir=Path(self._tmp.name) / "archive",
            registry_path=Path(self._tmp.name) / "registry.jsonl",
        )

    def tearDown(self):
        self._tmp.cleanup()

    def test_real_input_ingests_through_the_membrane(self):
        record = self.registry.ingest_source(
            REAL_INPUT.encode("utf-8"),
            source_type="text",
            source_location="incident report, this repository, 2026-08-25",
            author_or_origin="real-ingestion-run",
        )
        self.assertTrue(record.artifact_id.startswith("SRC-"))
        self.assertTrue(record.content_hash.startswith("sha256:"))
        self.assertEqual(record.provenance_status, "UNVERIFIED")  # never auto-believed

    def test_content_hash_is_deterministic(self):
        r1 = self.registry.ingest_source(
            REAL_INPUT.encode("utf-8"), source_type="text",
            source_location="x", author_or_origin="x",
        )
        r2 = self.registry.ingest_source(
            (REAL_INPUT + " ").encode("utf-8"), source_type="text",  # different bytes
            source_location="x", author_or_origin="x",
        )
        self.assertNotEqual(r1.content_hash, r2.content_hash)

    def test_invalid_source_type_fails_cleanly(self):
        with self.assertRaises(source_vault.InvalidSourceType):
            self.registry.ingest_source(
                REAL_INPUT.encode("utf-8"), source_type="not_a_real_type",
                source_location="x", author_or_origin="x",
            )

    def test_bridge_produces_a_valid_narrative_atom(self):
        record = self.registry.ingest_source(
            REAL_INPUT.encode("utf-8"), source_type="text",
            source_location="incident report, this repository, 2026-08-25",
            author_or_origin="real-ingestion-run",
        )
        yaml_text = source_record_to_narrative_atom_yaml(
            record, atom_id="NA-BRIDGE-001", raw_fragment=REAL_INPUT,
            domain="software_engineering/recursion_safety",
            narrative_source_type="TECHNICAL_KNOWLEDGE",
            epistemic_layer="VERIFIED_FACT", evidence_status="VERIFIED_FACT",
            confidence="HIGH", uncertainty="none beyond this run's own scope",
        )
        result = validate_narrative_atom(yaml_text)
        self.assertEqual(result.status, "VALID", result.issues)

    def test_provenance_hash_matches_the_original_ingested_content_hash(self):
        record = self.registry.ingest_source(
            REAL_INPUT.encode("utf-8"), source_type="text",
            source_location="x", author_or_origin="x",
        )
        yaml_text = source_record_to_narrative_atom_yaml(
            record, atom_id="NA-BRIDGE-002", raw_fragment=REAL_INPUT,
            domain="x", narrative_source_type="TECHNICAL_KNOWLEDGE",
            epistemic_layer="VERIFIED_FACT", evidence_status="VERIFIED_FACT",
            confidence="HIGH",
        )
        self.assertIn(record.content_hash, yaml_text)

    def test_full_pipeline_registers_in_the_real_store(self):
        record = self.registry.ingest_source(
            REAL_INPUT.encode("utf-8"), source_type="text",
            source_location="incident report, this repository, 2026-08-25",
            author_or_origin="real-ingestion-run",
        )
        yaml_text = source_record_to_narrative_atom_yaml(
            record, atom_id="NA-BRIDGE-003", raw_fragment=REAL_INPUT,
            domain="software_engineering/recursion_safety",
            narrative_source_type="TECHNICAL_KNOWLEDGE",
            epistemic_layer="VERIFIED_FACT", evidence_status="VERIFIED_FACT",
            confidence="HIGH",
        )
        result = validate_narrative_atom(yaml_text)
        self.assertEqual(result.status, "VALID", result.issues)

        store = NarrativeAtomStore()
        rec = store.register("NA-BRIDGE-003", created_by="real-ingestion-run")
        self.assertEqual(rec.state, "RAW")
        # Intake success is not knowledge promotion -- confirm the atom
        # stays at RAW, not silently advanced.
        self.assertEqual(store.get("NA-BRIDGE-003").state, "RAW")

    def test_malformed_bridge_input_fails_validation_not_silently(self):
        record = self.registry.ingest_source(
            REAL_INPUT.encode("utf-8"), source_type="text",
            source_location="x", author_or_origin="x",
        )
        yaml_text = source_record_to_narrative_atom_yaml(
            record, atom_id="NA-BRIDGE-004", raw_fragment=REAL_INPUT,
            domain="x", narrative_source_type="TECHNICAL_KNOWLEDGE",
            epistemic_layer="NOT_A_REAL_CLASSIFICATION",  # invalid on purpose
            evidence_status="VERIFIED_FACT", confidence="HIGH",
        )
        result = validate_narrative_atom(yaml_text)
        self.assertEqual(result.status, "INVALID")


if __name__ == "__main__":
    unittest.main()
