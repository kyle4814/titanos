from __future__ import annotations
import tempfile, unittest
from pathlib import Path
from foundation.next_kernel import Opportunity, OpportunityStore
from foundation.authority_result import apply_worker_result
from foundation.worker_result import WorkerResult

class TestAuthorityResult(unittest.TestCase):
    def test_completed_can_prepare_but_not_commit(self):
        with tempfile.TemporaryDirectory() as td:
            s=OpportunityStore(Path(td)/"next.json")
            s.upsert(Opportunity("o","x","x","DISCOVERED",authority="O0"))
            r=WorkerResult("w","o","COMPLETED","prepared",("ev:1",))
            item=apply_worker_result(s,r)
            self.assertEqual(item.status,"PREPARED")
    def test_escalation_enters_human_gate(self):
        with tempfile.TemporaryDirectory() as td:
            s=OpportunityStore(Path(td)/"next.json")
            s.upsert(Opportunity("o","x","x","PREPARED",authority="O1"))
            r=WorkerResult("w","o","ESCALATED","needs approval",("ev:1",),escalation="commit")
            item=apply_worker_result(s,r)
            self.assertEqual(item.status,"HUMAN-GATED")

if __name__=="__main__": unittest.main()
