import tempfile, unittest
from pathlib import Path
from foundation.next_kernel import Opportunity, OpportunityStore
from foundation.swarm_state import SwarmState, SwarmStateStore
from foundation.coordination_journal import CoordinationJournal, CrashRecoverableCoordinator
from foundation.transactional_worker import start_worker, finish_worker
from foundation.worker_result import WorkerResult

class TestTransactionalWorker(unittest.TestCase):
    def test_start_updates_lease_and_swarm(self):
        with tempfile.TemporaryDirectory() as td:
            n=OpportunityStore(Path(td)/"next.json"); n.upsert(Opportunity("o","x","x","DISCOVERED",authority="O0"))
            s=SwarmStateStore(Path(td)/"s.json"); j=CoordinationJournal(Path(td)/"j.json")
            state=SwarmState("sw",queued=("o",)); s.save(state)
            c=CrashRecoverableCoordinator(n,s,j)
            out=start_worker(n,c,state,"o","w")
            self.assertEqual(out.active,("o",)); self.assertEqual(n.get("o").lease_owner,"w")
    def test_finish_records_completed(self):
        with tempfile.TemporaryDirectory() as td:
            n=OpportunityStore(Path(td)/"next.json"); n.upsert(Opportunity("o","x","x","DISCOVERED",authority="O0"))
            s=SwarmStateStore(Path(td)/"s.json"); j=CoordinationJournal(Path(td)/"j.json")
            state=SwarmState("sw",queued=("o",)); s.save(state); c=CrashRecoverableCoordinator(n,s,j)
            state=start_worker(n,c,state,"o","w")
            out=finish_worker(n,c,state,WorkerResult("w","o","COMPLETED","done",("ev:1",)))
            self.assertEqual(out.completed,("o",)); self.assertFalse(n.get("o").lease_owner)

if __name__=="__main__": unittest.main()
