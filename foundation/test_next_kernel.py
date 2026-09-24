"""Adversarial tests for the durable NEXT opportunity kernel."""
import json
import tempfile
import unittest
from pathlib import Path

from foundation.next_kernel import Opportunity, OpportunityStore, STATES, fingerprint


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

    def test_pipeline_ingestion_always_enters_o0_discovered(self):
        from foundation.next_kernel import ingest_pipeline_opportunities

        class Signal:
            source_ref = "primary:1"
            signal_id = "sig-1"

        class Observed:
            opportunity_id = "external-1"
            controlling_party = "Example Party"
            signals = [Signal()]

        results = ingest_pipeline_opportunities(self.store, [Observed()])
        self.assertEqual(results, ("NEW",))
        item = self.store.load()["external-1"]
        self.assertEqual(item.status, "DISCOVERED")
        self.assertEqual(item.authority, "O0")
        self.assertIn("primary:1", item.evidence_refs)

    def test_pipeline_ingestion_does_not_promote_existing_authority(self):
        from foundation.next_kernel import ingest_pipeline_opportunities

        class Signal:
            source_ref = "primary:2"
            signal_id = "sig-2"

        class Observed:
            opportunity_id = "external-2"
            controlling_party = "Example Party"
            signals = [Signal()]

        self.store.upsert(self.item(id="external-2", authority="O3", status="QUALIFIED"))
        result = ingest_pipeline_opportunities(self.store, [Observed()])
        self.assertEqual(result, ("DUPLICATE",))
        item = self.store.load()["external-2"]
        self.assertEqual(item.authority, "O3")
        self.assertEqual(item.status, "QUALIFIED")

    def test_pipeline_ingestion_rejects_blank_controlling_party_without_mutation(self):
        from foundation.next_kernel import ingest_pipeline_opportunities

        class Observed:
            opportunity_id = "blank-party"
            controlling_party = "   "
            signals = []

        self.assertEqual(ingest_pipeline_opportunities(self.store, [Observed()]), ())
        self.assertEqual(self.store.load(), {})

    def test_o0_cannot_promote_to_qualified(self):
        self.store.upsert(self.item(authority="O0"))
        with self.assertRaises(PermissionError):
            self.store.advance("op-1", "QUALIFIED")

    def test_o0_cannot_promote_to_prepared(self):
        self.store.upsert(self.item(authority="O0"))
        with self.assertRaises(PermissionError):
            self.store.advance("op-1", "PREPARED")

    def test_o1_cannot_reach_ready(self):
        self.store.upsert(self.item(authority="O1"))
        self.store.advance("op-1", "QUALIFIED")
        self.store.advance("op-1", "PREPARED")
        with self.assertRaises(PermissionError):
            self.store.advance("op-1", "READY")

    def test_new_evidence_cannot_overwrite_protected_lifecycle_fields(self):
        existing = self.item(
            status="QUALIFIED",
            authority="O3",
            next_action="protected action",
            evidence_refs=("old",),
        )
        self.store.upsert(existing)
        incoming = self.item(
            evidence_refs=("new",),
            status="DISCOVERED",
            authority="O0",
            next_action="attacker action",
        )
        self.assertEqual(self.store.upsert(incoming), "UPDATED")
        item = self.store.load()["op-1"]
        self.assertEqual(item.status, "QUALIFIED")
        self.assertEqual(item.authority, "O3")
        self.assertEqual(item.next_action, "protected action")
        self.assertEqual(item.evidence_refs, ("new", "old"))

    def test_o3_can_reach_committed_after_valid_lifecycle(self):
        self.store.upsert(self.item(authority="O3"))
        self.store.advance("op-1", "QUALIFIED")
        self.store.advance("op-1", "PREPARED")
        self.store.advance("op-1", "READY")
        result = self.store.advance("op-1", "COMMITTED")
        self.assertEqual(result.status, "COMMITTED")

    def test_concurrent_upserts_do_not_lose_evidence(self):
        import threading

        self.store.upsert(self.item(evidence_refs=("base",)))
        results = []
        errors = []
        barrier = threading.Barrier(8)

        def worker(index):
            try:
                barrier.wait(timeout=2)
                results.append(self.store.upsert(
                    self.item(evidence_refs=(f"e{index}",))
                ))
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertFalse(errors)
        self.assertEqual(set(results), {"UPDATED"})
        self.assertEqual(
            self.store.load()["op-1"].evidence_refs,
            tuple(["base"] + [f"e{i}" for i in range(8)]),
        )

    def test_concurrent_upsert_and_advance_preserve_state(self):
        import threading

        self.store.upsert(self.item(authority="O3", evidence_refs=("base",)))
        errors = []
        barrier = threading.Barrier(9)

        def upsert_worker(index):
            try:
                barrier.wait(timeout=2)
                self.store.upsert(self.item(evidence_refs=(f"race-{index}",)))
            except Exception as exc:
                errors.append(exc)

        def advance_worker():
            try:
                barrier.wait(timeout=2)
                self.store.advance("op-1", "QUALIFIED")
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=upsert_worker, args=(i,)) for i in range(8)]
        threads.append(threading.Thread(target=advance_worker))
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertFalse(errors)
        item = self.store.load()["op-1"]
        self.assertEqual(item.status, "QUALIFIED")
        self.assertEqual(item.authority, "O3")
        self.assertEqual(item.evidence_refs, tuple(["base"] + [f"race-{i}" for i in range(8)]))

    def test_failed_atomic_save_preserves_previous_state(self):
        original = self.store.item if hasattr(self.store, "item") else None
        self.store.upsert(self.item(evidence_refs=("old",)))

        original_replace = Path.replace
        def fail_replace(self_path, target):
            raise OSError("simulated replace failure")

        Path.replace = fail_replace
        try:
            with self.assertRaises(OSError):
                self.store.upsert(self.item(evidence_refs=("new",)))
        finally:
            Path.replace = original_replace

        item = self.store.load()["op-1"]
        self.assertEqual(item.evidence_refs, ("old",))

    def test_failed_atomic_save_leaves_no_temp_file(self):
        self.store.upsert(self.item())
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        original_replace = Path.replace
        def fail_replace(self_path, target):
            raise OSError("simulated replace failure")
        Path.replace = fail_replace
        try:
            with self.assertRaises(OSError):
                self.store.advance("op-1", "QUALIFIED")
        finally:
            Path.replace = original_replace
        self.assertFalse(tmp.exists())

    def test_transition_graph_is_forward_only_and_terminal(self):
        expected = {
            "DISCOVERED": {"QUALIFIED", "REJECTED", "DUPLICATE", "STALE", "BLOCKED"},
            "QUALIFIED": {"PREPARED", "REJECTED", "EXPIRED", "STALE", "BLOCKED"},
            "PREPARED": {"READY", "HUMAN-GATED", "REJECTED", "STALE", "BLOCKED"},
            "READY": {"COMMITTED", "HUMAN-GATED", "REJECTED", "EXPIRED", "STALE"},
            "COMMITTED": {"OUTCOME", "AWAITING-OUTCOME", "FAILED"},
            "AWAITING-OUTCOME": {"OUTCOME", "SUCCEEDED", "FAILED", "STALE"},
            "OUTCOME": {"SUCCEEDED", "FAILED"},
        }
        from foundation.next_kernel import FORWARD, TERMINAL
        self.assertEqual(FORWARD, expected)
        self.assertTrue(set(STATES) - set(FORWARD) == TERMINAL | {"HUMAN-GATED", "STALE", "BLOCKED"})
        self.assertTrue(all(not (target in {"DISCOVERED", "QUALIFIED", "PREPARED", "READY", "COMMITTED", "OUTCOME"}
                                 and source in {"DISCOVERED", "QUALIFIED", "PREPARED", "READY", "COMMITTED", "OUTCOME"}
                                 and target == source)
                          for source, targets in FORWARD.items() for target in targets))

    def test_every_defined_state_has_explicit_transition_policy(self):
        from foundation.next_kernel import FORWARD, TERMINAL
        nonterminal = STATES - TERMINAL - {"HUMAN-GATED", "STALE", "BLOCKED"}
        self.assertEqual(set(FORWARD), nonterminal)

    def test_illegal_lifecycle_skip_is_rejected(self):
        self.store.upsert(self.item())
        with self.assertRaises(PermissionError):
            self.store.advance("op-1", "READY")

    def test_backward_lifecycle_transition_is_rejected(self):
        self.store.upsert(self.item())
        self.store.advance("op-1", "QUALIFIED")
        with self.assertRaises(ValueError):
            self.store.advance("op-1", "DISCOVERED")

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

    def test_empty_identity_fields_are_rejected(self):
        with self.assertRaises(ValueError):
            self.item(id="")
        with self.assertRaises(ValueError):
            self.item(source="")
        with self.assertRaises(ValueError):
            self.item(title="")

    def test_invalid_value_type_is_rejected(self):
        with self.assertRaises((TypeError, ValueError)):
            self.item(value="not-a-number")

    def test_evidence_refs_must_be_sequence_of_strings(self):
        with self.assertRaises((TypeError, ValueError)):
            self.item(evidence_refs=("ok", 7))

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

    def test_actionable_orders_by_deadline_then_value_then_id(self):
        self.store.upsert(self.item(id="late", source="A", title="Late",
                                    value=100, deadline="2026-12-01"))
        self.store.upsert(self.item(id="early", source="B", title="Early",
                                    value=10, deadline="2026-09-30"))
        self.assertEqual([x.id for x in self.store.actionable()], ["early", "late"])


if __name__ == "__main__":
    unittest.main()
