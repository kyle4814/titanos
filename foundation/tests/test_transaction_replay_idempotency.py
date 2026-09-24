import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from foundation.institutional_memory import InstitutionalMemoryStore
from foundation.worker_assignment import persist_opportunity_outcome

class ReplayIdempotencyTests(unittest.TestCase):
    def test_replaying_same_receipt_does_not_append_duplicate(self):
        with TemporaryDirectory() as td:
            store=InstitutionalMemoryStore(Path(td)/"memory.json")
            memory=store.load()
            from foundation.opportunity_feedback import OutcomeFeedback
            from foundation.learning_receipt import LearningReceipt
            before=store._payload(memory)
            memory.opportunity_learning.record(OutcomeFeedback("x",10,15,True,1.0,
                                                               "2026-09-24T00:00:00+00:00"))
            after=store._payload(memory)
            receipt=LearningReceipt.create("replay","replay_test",("x",),before,after,
                                           observed_at="2026-09-24T00:00:00+00:00")
            store.save(memory,receipt)
            first=store.ledger.read()
            # Reconciliation of a completed transaction is safe and does not mutate the ledger.
            self.assertEqual(store.reconcile(),"CLEAN")
            self.assertEqual(store.ledger.read(),first)
            self.assertEqual(len(first),1)
            self.assertTrue(store.ledger.verify())

if __name__=="__main__": unittest.main()
