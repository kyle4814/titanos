from __future__ import annotations
import tempfile, unittest
from pathlib import Path
from foundation.next_kernel import Opportunity, OpportunityStore
from foundation.next_leases import claim
from foundation.worker_result import WorkerResult
from foundation.worker_result_ingest import ingest_worker_result

class TestWorkerResultIngest(unittest.TestCase):
    def test_result_merges_evidence_and_releases_lease(self):
        with tempfile.TemporaryDirectory() as td:
            s=OpportunityStore(Path(td)/"next.json")
            s.upsert(Opportunity("o","test","op","READY",authority="O2",evidence_refs=("old",)))
            claim(s,"o","w")
            got=ingest_worker_result(s,WorkerResult("w","o","COMPLETED","done",("new",)))
            self.assertEqual(got.lease_owner,"")
            self.assertEqual(set(got.evidence_refs),{"old","new"})
    def test_non_owner_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            s=OpportunityStore(Path(td)/"next.json")
            s.upsert(Opportunity("o","test","op","READY",authority="O2"))
            claim(s,"o","w")
            with self.assertRaises(PermissionError):
                ingest_worker_result(s,WorkerResult("other","o","FAILED","no"))
if __name__=="__main__": unittest.main()
