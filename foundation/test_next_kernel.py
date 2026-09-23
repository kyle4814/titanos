"""Adversarial tests for the durable NEXT opportunity kernel."""
import json
import tempfile
import unittest
from pathlib import Path

from foundation.next_kernel import Opportunity, OpportunityStore, fingerprint


class TestNextKernel(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "next.json"
        self.store = OpportunityStore(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def item(self, **kwargs):
        data = dict(id="op-1", source="source", title="Example")
        data.update(kwargs)
        return Opportunity(**data)

    def test_identity_collision_cannot_overwrite_existing_record(self):
        self.store.upsert(self.item())
        replacement = self.item(title="Attacker-controlled replacement")
        replacement = Opportunity(**{**replacement.__dict__, "source": "different-source"})
        with self.assertRaises(ValueError):
            self.store.upsert(replacement)
        self.assertEqual(self.store.load()["op-1"].title, "Example")

    def test_terminal_state_cannot_be_reactivated(self):
        self.store.upsert(self.item())
        self.store.advance("op-1", "REJECTED")
        with self.assertRaises(ValueError):
            self.store.advance("op-1", "DISCOVERED")

    def test_malformed_persisted_state_is_rejected(self):
        self.path.write_text(json.dumps({
            "op-1": {
                "id": "op-1", "source": "source", "title": "Example",
                "status": "NOT_A_STATE", "authority": "O0"
            }
        }), encoding="utf-8")
        with self.assertRaises(ValueError):
            self.store.load()

    def test_invalid_authority_is_rejected(self):
        with self.assertRaises(ValueError):
            self.item(authority="O9")

    def test_missing_identity_is_rejected(self):
        with self.assertRaises(ValueError):
            fingerprint("", "id")

    def test_malformed_top_level_state_is_rejected(self):
        for raw in ("[]", '"string"', "null", "123"):
            self.path.write_text(raw, encoding="utf-8")
            with self.assertRaises((ValueError, TypeError, AttributeError)):
                self.store.load()

    def test_malformed_evidence_type_is_rejected(self):
        self.path.write_text(json.dumps({
            "op-1": {
                "id": "op-1", "source": "source", "title": "Example",
                "status": "DISCOVERED", "authority": "O0",
                "evidence_refs": "not-a-sequence"
            }
        }), encoding="utf-8")
        with self.assertRaises((TypeError, ValueError)):
            self.store.load()

    def test_duplicate_semantic_record_is_not_created_by_upsert(self):
        self.store.upsert(self.item(evidence_refs=("e1",)))
        result = self.store.upsert(self.item(evidence_refs=("e1",)))
        self.assertEqual(result, "DUPLICATE")
        self.assertEqual(len(self.store.load()), 1)

    def test_persisted_key_must_match_record_identity(self):
        self.path.write_text(json.dumps({
            "wrong-key": {
                "id": "op-1", "source": "source", "title": "Example",
                "status": "DISCOVERED", "authority": "O0"
            }
        }), encoding="utf-8")
        with self.assertRaises(ValueError):
            self.store.load()

    def test_atomic_save_leaves_no_temp_file(self):
        self.store.upsert(self.item())
        self.assertTrue(self.path.exists())
        self.assertFalse(self.path.with_suffix(".json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
