from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from threading import Barrier, Thread

from foundation.next_acquire import acquire_next
from foundation.next_kernel import Opportunity, OpportunityStore


class TestNextAcquire(unittest.TestCase):
    def test_acquire_returns_highest_priority(self):
        with tempfile.TemporaryDirectory() as td:
            store = OpportunityStore(Path(td) / "next.json")
            store.upsert(Opportunity("low", "test", "low", "READY", 10, authority="O2"))
            store.upsert(Opportunity("high", "test", "high", "READY", 100, authority="O2"))
            got = acquire_next(store, "worker-a")
            self.assertEqual(got.id, "high")
            self.assertEqual(got.lease_owner, "worker-a")

    def test_no_second_worker_gets_same_live_item(self):
        with tempfile.TemporaryDirectory() as td:
            store = OpportunityStore(Path(td) / "next.json")
            store.upsert(Opportunity("only", "test", "only", "READY", 100, authority="O2"))
            barrier = Barrier(2)
            results = []

            def worker(name):
                barrier.wait()
                results.append(acquire_next(store, name))

            threads = [Thread(target=worker, args=(f"worker-{i}",)) for i in range(2)]
            for t in threads: t.start()
            for t in threads: t.join()

            acquired = [x for x in results if x is not None]
            self.assertEqual(len(acquired), 1)

    def test_empty_queue_returns_none(self):
        with tempfile.TemporaryDirectory() as td:
            store = OpportunityStore(Path(td) / "next.json")
            self.assertIsNone(acquire_next(store, "worker-a"))


if __name__ == "__main__":
    unittest.main()
