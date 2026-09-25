"""An absent institutional-memory store IS the empty memory (2026-09-26).

`InstitutionalMemoryStore.load()` returns `InstitutionalMemory()` for a file
that does not exist, so every producer (`worker_assignment.persist_*`, and
the tests modelled on it) derives a learning receipt's `before` from
`_payload(load())` -- the canonical, schema-versioned empty payload. The
validator in `save()` used to represent the same absent state as `{}`, so
the two hashes never matched and the first write into a fresh store could
not be made at all (14 identical
"learning receipt does not bind this memory transition" errors, CI run
36188217313). This file pins the single convention.
"""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from foundation.institutional_memory import InstitutionalMemory, InstitutionalMemoryStore
from foundation.learning_receipt import LearningReceipt
from foundation.opportunity_feedback import OutcomeFeedback


class EmptyStateConventionTests(unittest.TestCase):
    def test_absent_store_reads_as_the_canonical_empty_payload(self):
        with TemporaryDirectory() as td:
            store = InstitutionalMemoryStore(Path(td) / "memory.json")
            self.assertFalse(store.path.exists())
            self.assertEqual(store._raw_payload(), store._payload(InstitutionalMemory()))
            self.assertNotEqual(store._raw_payload(), {})
            # And it is what a producer observes through the public surface.
            self.assertEqual(store._raw_payload(), store._payload(store.load()))

    def test_first_write_into_a_fresh_store_binds_via_the_producer_contract(self):
        with TemporaryDirectory() as td:
            store = InstitutionalMemoryStore(Path(td) / "memory.json")
            memory = store.load()
            before = store._payload(memory)
            memory.opportunity_learning.record(
                OutcomeFeedback("opp-1", 10, 15, True, 1.0, "2026-09-26T00:00:00+00:00"))
            after = store._payload(memory)
            receipt = LearningReceipt.create("test", "first_write", ("opp-1",), before, after)
            store.save(memory, receipt)  # used to raise "does not bind"
            self.assertEqual(store._payload(store.load()), after)
            self.assertEqual(len(store.ledger.read()), 1)

    def test_a_reloaded_memory_rebinds_after_a_real_write(self):
        # Second cause behind the same error: OutcomeFeedback recorded with
        # ints was persisted as ints and reloaded as floats, so a receipt
        # built from load() could never bind against the file it came from.
        with TemporaryDirectory() as td:
            store = InstitutionalMemoryStore(Path(td) / "memory.json")
            memory = store.load()
            before = store._payload(memory)
            memory.opportunity_learning.record(
                OutcomeFeedback("opp-1", 10, 15, True, 1, "2026-09-26T00:00:00+00:00"))  # ints
            store.save(memory, LearningReceipt.create("test", "w1", ("opp-1",), before, store._payload(memory)))

            reloaded = store.load()
            self.assertEqual(store._payload(reloaded), store._raw_payload())
            before2 = store._payload(reloaded)
            reloaded.opportunity_learning.record(
                OutcomeFeedback("opp-2", 20, 25, False, 0.5, "2026-09-26T01:00:00+00:00"))
            store.save(reloaded, LearningReceipt.create("test", "w2", ("opp-2",), before2, store._payload(reloaded)))
            self.assertEqual(len(store.ledger.read()), 2)

    def test_a_receipt_bound_to_the_legacy_empty_dict_is_refused(self):
        # One canonical encoding of "before": `{}` is not a memory payload
        # (no schema_version) and must not be accepted as the pre-state.
        with TemporaryDirectory() as td:
            store = InstitutionalMemoryStore(Path(td) / "memory.json")
            memory = store.load()
            memory.opportunity_learning.record(
                OutcomeFeedback("opp-1", 10, 15, True, 1.0, "2026-09-26T00:00:00+00:00"))
            receipt = LearningReceipt.create("test", "legacy", (), {}, store._payload(memory))
            with self.assertRaisesRegex(ValueError, "does not bind"):
                store.save(memory, receipt)
            self.assertFalse(store.path.exists())
            self.assertEqual(len(store.ledger.read()), 0)


if __name__ == "__main__":
    unittest.main()
