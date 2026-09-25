from __future__ import annotations
import tempfile, unittest
from pathlib import Path
from foundation.next_kernel import Opportunity, OpportunityStore
from foundation.worker_execution_contract import WorkerExecutionContract
from foundation.workforce_dispatcher import DispatchItem
from foundation.worker_cycle import prepare_worker_cycle

class TestWorkerCycle(unittest.TestCase):
    def test_prepare_claims_and_builds_invocation(self):
        with tempfile.TemporaryDirectory() as td:
            s=OpportunityStore(Path(td)/"next.json")
            s.upsert(Opportunity("o","x","x","DISCOVERED",authority="O0"))
            c=WorkerExecutionContract("w","o","research")
            i=prepare_worker_cycle(s,DispatchItem("w","x",0),c)
            self.assertEqual(i.worker_id,"w")
            self.assertEqual(s.load()["o"].lease_owner,"w")

if __name__=="__main__": unittest.main()
