from __future__ import annotations
import tempfile, unittest
from pathlib import Path
from foundation.next_kernel import Opportunity, OpportunityStore
from foundation.next_leases import claim
from foundation.worker_result import WorkerResult
from foundation.worker_lifecycle import complete_worker

class TestWorkerLifecycle(unittest.TestCase):
    def test_completed_worker_records_evidence_and_releases(self):
        with tempfile.TemporaryDirectory() as td:
            s=OpportunityStore(Path(td)/"next.json")
            s.upsert(Opportunity("o1","test","x","READY",10,authority="O2"))
            claim(s,"o1","w1")
            complete_worker(s,"o1","w1",WorkerResult("w1","o1","COMPLETED","verified",("ev:1",)))
            item=s.get("o1")
            self.assertEqual(item.evidence_refs,("ev:1",))
            self.assertFalse(item.lease_owner)
    def test_wrong_worker_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            s=OpportunityStore(Path(td)/"next.json")
            s.upsert(Opportunity("o1","test","x","READY",10,authority="O2"))
            claim(s,"o1","w1")
            with self.assertRaises(PermissionError):
                complete_worker(s,"o1","w2",WorkerResult("w2","o1","COMPLETED","x",("ev",)))

if __name__=="__main__": unittest.main()
