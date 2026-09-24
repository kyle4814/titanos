import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from foundation.institutional_memory import InstitutionalMemoryStore, InstitutionalMemory
from foundation.learning_receipt import LearningReceipt

class FailureRecoveryTests(unittest.TestCase):
    def _receipt(self, store, before, after):
        return LearningReceipt.create("failure-test","recovery",("x",),before,after,
                                      observed_at="2026-09-24T00:00:00+00:00")

    def test_interruption_after_memory_write_is_reconciled(self):
        with TemporaryDirectory() as td:
            store=InstitutionalMemoryStore(Path(td)/"memory.json")
            memory=InstitutionalMemory()
            before=store._payload(memory)
            memory.opportunity_learning.record(
                __import__("foundation.opportunity_feedback",fromlist=["OutcomeFeedback"]).OutcomeFeedback(
                    "x",10,15,True,1.0,"2026-09-24T00:00:00+00:00"))
            after=store._payload(memory)
            receipt=self._receipt(store,before,after)
            original=store.ledger.commit
            def crash(_staged): raise RuntimeError("injected commit interruption")
            store.ledger.commit=crash
            with self.assertRaises(RuntimeError): store.save(memory,receipt)
            store.ledger.commit=original
            self.assertEqual(store.reconcile(),"FINALIZED")
            self.assertEqual(store.load().opportunity_learning.records["x"][0].realized_value,15)

    def test_interruption_before_memory_write_rolls_back_journal(self):
        with TemporaryDirectory() as td:
            store=InstitutionalMemoryStore(Path(td)/"memory.json")
            memory=InstitutionalMemory()
            before=store._payload(memory)
            memory.opportunity_learning.record(
                __import__("foundation.opportunity_feedback",fromlist=["OutcomeFeedback"]).OutcomeFeedback(
                    "x",10,15,True,1.0,"2026-09-24T00:00:00+00:00"))
            after=store._payload(memory)
            receipt=self._receipt(store,before,after)
            original=store._write_memory
            def crash(*_args): raise RuntimeError("injected write interruption")
            store._write_memory=crash
            with self.assertRaises(RuntimeError): store.save(memory,receipt)
            store._write_memory=original
            self.assertEqual(store.reconcile(),"ROLLED_BACK")
            self.assertFalse(store.path.exists())

if __name__=="__main__":
    unittest.main()
