import multiprocessing as mp
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from foundation.institutional_memory import InstitutionalMemoryStore
from foundation.worker_assignment import persist_opportunity_outcome

def _write(path, oid):
    store=InstitutionalMemoryStore(path)
    persist_opportunity_outcome(
        store, oid, 10, 15, True, 1.0,
        observed_at="2026-09-24T00:00:00+00:00",
    )

class InstitutionalMemoryConcurrencyTests(unittest.TestCase):
    def test_concurrent_learners_preserve_valid_memory_and_receipts(self):
        with TemporaryDirectory() as td:
            path=Path(td)/"memory.json"
            # Seed a valid state so both processes exercise real load/save locking.
            store=InstitutionalMemoryStore(path)
            persist_opportunity_outcome(store,"seed",10,10,True,1.0,
                                        observed_at="2026-09-24T00:00:00+00:00")
            ctx=mp.get_context("spawn")
            workers=[ctx.Process(target=_write,args=(str(path),oid)) for oid in ("a","b")]
            for p in workers:p.start()
            for p in workers:p.join()
            self.assertTrue(all(p.exitcode==0 for p in workers))
            restored=store.load()
            self.assertIn("a",restored.opportunity_learning.records)
            self.assertIn("b",restored.opportunity_learning.records)
            self.assertIn("seed",restored.opportunity_learning.records)
            self.assertTrue(store.ledger.verify())

if __name__=="__main__":
    unittest.main()
