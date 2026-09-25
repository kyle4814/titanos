import json,tempfile,unittest
from pathlib import Path
from foundation.institutional_memory import InstitutionalMemory,InstitutionalMemoryStore
from foundation.learning_receipt import LearningReceipt

class TestReceiptBoundMemory(unittest.TestCase):
    def test_write_requires_and_persists_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"m.json"; store=InstitutionalMemoryStore(p); memory=InstitutionalMemory()
            payload=store._payload(memory)
            # `before` is the store's own persisted-state view (an absent
            # store reads as the canonical empty payload, same as load()),
            # not a hand-written `{}`.
            receipt=LearningReceipt.create("human:kyle","initial_memory",(),store._raw_payload(),payload,"2026-09-24T00:00:00+00:00")
            store.save(memory,receipt)
            raw=json.loads(p.read_text())
            self.assertEqual(raw["receipt"]["receipt_id"],receipt.receipt_id)
            store.load()
    def test_all_learning_domains_reload_and_round_trip_exactly(self):
        # Pins two defects: the stored receipt was included in the checksum
        # recomputed on load (every reload failed), and specialization was
        # serialised as a dict the workforce loader rejects.
        from foundation.opportunity_feedback import OutcomeFeedback
        with tempfile.TemporaryDirectory() as td:
            store=InstitutionalMemoryStore(Path(td)/"m.json"); memory=InstitutionalMemory()
            memory.opportunity_learning.record(OutcomeFeedback("o1",10,20,True,1.0,"2026-09-24T00:00:00+00:00"))
            memory.specialization.record("w2","research",completed=True,evidence_count=2)
            memory.specialization.record("w1","ops",completed=False)
            memory.worker_health.record("w1",status="SUCCESS",latency_ms=5.0)
            store.save(memory,LearningReceipt.create("human:kyle","seed",(),store._raw_payload(),store._payload(memory)))
            restored=store.load()
            self.assertEqual(store._payload(restored),store._raw_payload())
            self.assertEqual(restored.specialization.records[("w2","research")].evidence_count,2)
            stale=LearningReceipt.create("worker:a","stale",(),{"not":"the persisted state"},store._payload(restored))
            with self.assertRaises(ValueError): store.save(restored,stale)
    def test_unbound_receipt_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            store=InstitutionalMemoryStore(Path(td)/"m.json")
            receipt=LearningReceipt.create("worker:a","bad",(),{},{"wrong":1})
            with self.assertRaises(ValueError): store.save(InstitutionalMemory(),receipt)

if __name__=="__main__": unittest.main()
