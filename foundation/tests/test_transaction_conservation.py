import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from foundation.institutional_memory import InstitutionalMemoryStore, InstitutionalMemory
from foundation.learning_receipt import LearningReceipt
from foundation.opportunity_feedback import OutcomeFeedback

class TransactionConservationTests(unittest.TestCase):
    def test_each_failure_phase_conserves_receipt_and_memory_invariants(self):
        for phase in ("WRITE","COMMIT","MARK"):
            with self.subTest(phase=phase), TemporaryDirectory() as td:
                store=InstitutionalMemoryStore(Path(td)/"memory.json")
                memory=InstitutionalMemory()
                before=store._payload(memory)
                memory.opportunity_learning.record(OutcomeFeedback("x",10,15,True,1.0,"2026-09-24T00:00:00+00:00"))
                after=store._payload(memory)
                receipt=LearningReceipt.create("conserve-"+phase,"matrix",("x",),before,after,
                                               observed_at="2026-09-24T00:00:00+00:00")
                original=(store._write_memory,store.ledger.commit,store.journal.mark_committed)
                if phase=="WRITE": store._write_memory=lambda *_: (_ for _ in ()).throw(RuntimeError("crash"))
                elif phase=="COMMIT": store.ledger.commit=lambda *_: (_ for _ in ()).throw(RuntimeError("crash"))
                else: store.journal.mark_committed=lambda: (_ for _ in ()).throw(RuntimeError("crash"))
                with self.assertRaises(RuntimeError): store.save(memory,receipt)
                store._write_memory,store.ledger.commit,store.journal.mark_committed=original
                store.reconcile()
                rows=store.ledger.read()
                self.assertTrue(store.ledger.verify())
                self.assertLessEqual(sum(r["receipt"]["receipt_id"]==receipt.receipt_id for r in rows),1)
                tx=store.journal.load()
                self.assertIsNone(tx)
                if store.path.exists():
                    restored=store.load()
                    self.assertEqual(restored.opportunity_learning.records["x"][0].realized_value,15)
                else:
                    self.assertEqual(rows,[])

if __name__=="__main__": unittest.main()
