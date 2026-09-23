import json,tempfile,unittest
from pathlib import Path
from foundation.institutional_memory import InstitutionalMemory,InstitutionalMemoryStore
from foundation.learning_receipt import LearningReceipt

class TestReceiptBoundMemory(unittest.TestCase):
    def test_write_requires_and_persists_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"m.json"; store=InstitutionalMemoryStore(p); memory=InstitutionalMemory()
            payload=store._payload(memory)
            receipt=LearningReceipt.create("human:kyle","initial_memory",(),{},payload,"2026-09-24T00:00:00+00:00")
            store.save(memory,receipt)
            raw=json.loads(p.read_text())
            self.assertEqual(raw["receipt"]["receipt_id"],receipt.receipt_id)
            store.load()
    def test_unbound_receipt_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            store=InstitutionalMemoryStore(Path(td)/"m.json")
            receipt=LearningReceipt.create("worker:a","bad",(),{},{"wrong":1})
            with self.assertRaises(ValueError): store.save(InstitutionalMemory(),receipt)

if __name__=="__main__": unittest.main()
