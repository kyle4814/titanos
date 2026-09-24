import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from foundation.institutional_memory import InstitutionalMemoryStore, InstitutionalMemory
from foundation.learning_receipt import LearningReceipt
from foundation.opportunity_feedback import OutcomeFeedback

class TransactionPhaseMatrixTests(unittest.TestCase):
    def _case(self, phase):
        with TemporaryDirectory() as td:
            store=InstitutionalMemoryStore(Path(td)/"memory.json")
            memory=InstitutionalMemory()
            before=store._payload(memory)
            memory.opportunity_learning.record(OutcomeFeedback("x",10,15,True,1.0,"2026-09-24T00:00:00+00:00"))
            after=store._payload(memory)
            receipt=LearningReceipt.create("matrix-"+phase,"matrix",("x",),before,after,
                                           observed_at="2026-09-24T00:00:00+00:00")
            original_write,original_commit,original_mark=store._write_memory,store.ledger.commit,store.journal.mark_committed
            if phase=="WRITE": store._write_memory=lambda *_: (_ for _ in ()).throw(RuntimeError("crash"))
            elif phase=="COMMIT": store.ledger.commit=lambda *_: (_ for _ in ()).throw(RuntimeError("crash"))
            elif phase=="MARK": store.journal.mark_committed=lambda: (_ for _ in ()).throw(RuntimeError("crash"))
            with self.assertRaises(RuntimeError): store.save(memory,receipt)
            store._write_memory,store.ledger.commit,store.journal.mark_committed=original_write,original_commit,original_mark
            status=store.reconcile()
            self.assertIn(status,("ROLLED_BACK","FINALIZED","COMMITTED_CLEARED"))
            self.assertTrue(store.ledger.verify())
            if phase=="WRITE": self.assertFalse(store.path.exists())
            else: self.assertEqual(store.load().opportunity_learning.records["x"][0].realized_value,15)

    def test_all_transaction_phases(self):
        for phase in ("WRITE","COMMIT","MARK"):
            with self.subTest(phase=phase): self._case(phase)

if __name__=="__main__": unittest.main()
