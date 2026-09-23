import tempfile,unittest
from pathlib import Path
from foundation.learning_receipt import LearningReceipt
from foundation.receipt_ledger import ReceiptLedger
class TestReceiptLedger(unittest.TestCase):
    def test_append_and_verify_chain(self):
        with tempfile.TemporaryDirectory() as td:
            l=ReceiptLedger(Path(td)/"receipts.jsonl")
            a=LearningReceipt.create("w1","m1",("e1",),{},{"x":1},"2026-09-24T00:00:00+00:00")
            b=LearningReceipt.create("w2","m2",("e2",),{"x":1},{"x":2},"2026-09-24T00:01:00+00:00")
            l.append(a); l.append(b)
            self.assertTrue(l.verify()); self.assertEqual(len(l.read()),2)
    def test_tampering_breaks_chain(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"receipts.jsonl"; l=ReceiptLedger(p)
            a=LearningReceipt.create("w","m",(),{},{"x":1})
            l.append(a); row=l.read()[0]; row["receipt"]["actor"]="tampered"
            p.write_text(json.dumps(row)+"\n")
            self.assertFalse(l.verify())
if __name__=="__main__": unittest.main()
