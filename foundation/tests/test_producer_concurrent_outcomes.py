"""Concurrent learners must not lose legitimate outcomes (frontier 3(g)).

`InstitutionalMemoryStore.save()` is optimistic: a receipt whose `before`
no longer matches the persisted state is refused, before anything durable
is written. That is the store's serialization guarantee and it is kept.
The producers (`worker_assignment.persist_*`) used to do load -> mutate ->
save once, so the loser of a concurrent write got the refusal and its
outcome was simply gone (measured 2026-09-26: 6/12 two-writer trials lost
an outcome). They now reload and reapply on a stale transition, a bounded
number of times, then surface the conflict.
"""
import multiprocessing as mp
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from foundation.institutional_memory import InstitutionalMemoryStore, StaleMemoryTransition
from foundation.worker_assignment import (
    LearningConflict, MAX_LEARNING_ATTEMPTS, persist_opportunity_outcome,
)

OBS = "2026-09-24T00:00:00+00:00"


def _interpose(store, competitor_oids):
    """Make `store.load()` return a snapshot that a competitor then makes
    stale: after each load, another store instance persists one outcome."""
    original = store.load
    queue = list(competitor_oids)
    calls = {"n": 0}

    def load():
        memory = original()
        calls["n"] += 1
        if queue:
            oid = queue.pop(0)
            persist_opportunity_outcome(InstitutionalMemoryStore(store.path), oid, 1, 2, True, 1.0,
                                        observed_at=OBS)
        return memory

    store.load = load
    return calls


def _spawn_write(path, oid):
    persist_opportunity_outcome(InstitutionalMemoryStore(path), oid, 10, 15, True, 1.0, observed_at=OBS)


class ProducerConcurrencyTests(unittest.TestCase):
    def test_stale_transition_is_a_typed_store_signal(self):
        self.assertTrue(issubclass(StaleMemoryTransition, ValueError))

    def test_loser_of_a_concurrent_write_retries_and_both_outcomes_survive(self):
        with TemporaryDirectory() as td:
            store = InstitutionalMemoryStore(Path(td) / "memory.json")
            calls = _interpose(store, ["b"])  # "b" lands between a's load and save
            persist_opportunity_outcome(store, "a", 10, 15, True, 1.0, observed_at=OBS)
            self.assertEqual(calls["n"], 2)  # one stale attempt, one retry
            fresh = InstitutionalMemoryStore(Path(td) / "memory.json")
            records = fresh.load().opportunity_learning.records
            self.assertIn("a", records)
            self.assertIn("b", records)
            # Retry applied the outcome exactly once and recorded exactly one receipt for it.
            self.assertEqual(len(records["a"]), 1)
            rows = fresh.ledger.read()
            self.assertEqual(sum(r["receipt"]["actor"] == "opportunity:a" for r in rows), 1)
            self.assertEqual(len(rows), 2)
            self.assertTrue(fresh.ledger.verify())
            self.assertEqual(len({r["receipt"]["receipt_id"] for r in rows}), 2)

    def test_persistent_conflict_surfaces_as_bounded_learning_conflict(self):
        with TemporaryDirectory() as td:
            store = InstitutionalMemoryStore(Path(td) / "memory.json")
            calls = _interpose(store, [f"c{i}" for i in range(MAX_LEARNING_ATTEMPTS + 5)])
            with self.assertRaises(LearningConflict) as ctx:
                persist_opportunity_outcome(store, "a", 10, 15, True, 1.0, observed_at=OBS)
            self.assertIsInstance(ctx.exception.__cause__, StaleMemoryTransition)
            self.assertEqual(calls["n"], MAX_LEARNING_ATTEMPTS)  # bounded, not infinite
            fresh = InstitutionalMemoryStore(Path(td) / "memory.json")
            self.assertNotIn("a", fresh.load().opportunity_learning.records)  # nothing half-applied
            self.assertTrue(fresh.ledger.verify())

    def test_non_stale_store_errors_are_not_retried(self):
        with TemporaryDirectory() as td:
            store = InstitutionalMemoryStore(Path(td) / "memory.json")
            calls = {"n": 0}
            original = store.load

            def load():
                calls["n"] += 1
                return original()

            store.load = load
            store.save = lambda *_: (_ for _ in ()).throw(ValueError("receipt ledger integrity failure"))
            with self.assertRaisesRegex(ValueError, "ledger integrity"):
                persist_opportunity_outcome(store, "a", 10, 15, True, 1.0, observed_at=OBS)
            self.assertEqual(calls["n"], 1)

    def test_eight_spawned_learners_all_persist(self):
        with TemporaryDirectory() as td:
            path = str(Path(td) / "memory.json")
            persist_opportunity_outcome(InstitutionalMemoryStore(path), "seed", 10, 10, True, 1.0, observed_at=OBS)
            ctx = mp.get_context("spawn")
            oids = [f"w{i}" for i in range(8)]
            procs = [ctx.Process(target=_spawn_write, args=(path, oid)) for oid in oids]
            for p in procs:
                p.start()
            for p in procs:
                p.join()
            self.assertTrue(all(p.exitcode == 0 for p in procs))
            store = InstitutionalMemoryStore(path)
            records = store.load().opportunity_learning.records
            for oid in oids:
                self.assertIn(oid, records)
                self.assertEqual(len(records[oid]), 1)
            rows = store.ledger.read()
            self.assertEqual(len(rows), 9)
            self.assertEqual(len({r["receipt"]["receipt_id"] for r in rows}), 9)
            self.assertTrue(store.ledger.verify())
            self.assertIsNone(store.journal.load())


if __name__ == "__main__":
    unittest.main()
