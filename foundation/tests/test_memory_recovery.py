import tempfile,unittest
from pathlib import Path
from foundation.institutional_memory import InstitutionalMemory,InstitutionalMemoryStore
from foundation.learning_receipt import LearningReceipt

class TestMemoryRecovery(unittest.TestCase):
    def test_clean_reconcile(self):
        with tempfile.TemporaryDirectory() as td:
            s=InstitutionalMemoryStore(Path(td)/"memory.json")
            self.assertEqual(s.reconcile(),"CLEAN")
    def test_completed_transaction_is_cleared(self):
        with tempfile.TemporaryDirectory() as td:
            s=InstitutionalMemoryStore(Path(td)/"memory.json")
            s.journal.begin("t","r","old","new","head")
            s.journal.mark_committed()
            self.assertEqual(s.reconcile(),"COMMITTED_CLEARED")
            self.assertIsNone(s.journal.load())
    def test_unresolved_transaction_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            s=InstitutionalMemoryStore(Path(td)/"memory.json")
            s.journal.begin("t","r","old","new","head")
            with self.assertRaises(ValueError): s.reconcile()

if __name__=="__main__": unittest.main()
