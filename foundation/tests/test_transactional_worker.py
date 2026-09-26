import tempfile, unittest
from pathlib import Path
from foundation.next_kernel import Opportunity, OpportunityStore
from foundation.swarm_state import SwarmState, SwarmStateStore
from foundation.coordination_journal import CoordinationJournal, CrashRecoverableCoordinator
from foundation.tests.test_authority_result import qualified_opportunity
from foundation.transactional_worker import start_worker, finish_worker
from foundation.worker_result import WorkerResult

class TestTransactionalWorker(unittest.TestCase):
    def _fixture(self, td, opportunity):
        n=OpportunityStore(Path(td)/"next.json"); n.upsert(opportunity)
        s=SwarmStateStore(Path(td)/"s.json"); j=CoordinationJournal(Path(td)/"j.json")
        state=SwarmState("sw",queued=("o",)); s.save(state); c=CrashRecoverableCoordinator(n,s,j)
        return n,c,state
    def test_start_updates_lease_and_swarm(self):
        with tempfile.TemporaryDirectory() as td:
            n,c,state=self._fixture(td,Opportunity("o","x","x","DISCOVERED",authority="O0"))
            out=start_worker(n,c,state,"o","w")
            self.assertEqual(out.active,("o",)); self.assertEqual(n.load()["o"].lease_owner,"w")
    def test_finish_records_completed(self):
        # Completion moves the record to PREPARED: QUALIFIED with O1 on the
        # record (next_kernel FORWARD + MIN_AUTHORITY); see test_authority_result.
        with tempfile.TemporaryDirectory() as td:
            n,c,state=self._fixture(td,qualified_opportunity())
            state=start_worker(n,c,state,"o","w")
            out=finish_worker(n,c,state,WorkerResult("w","o","COMPLETED","done",("ev:1",)))
            self.assertEqual(out.completed,("o",)); self.assertFalse(n.load()["o"].lease_owner)
            self.assertEqual(n.load()["o"].status,"PREPARED")
    def test_finish_on_o0_record_is_refused_and_changes_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            n,c,state=self._fixture(td,Opportunity("o","x","x","DISCOVERED",authority="O0"))
            state=start_worker(n,c,state,"o","w")
            with self.assertRaisesRegex(PermissionError,"O1"):
                finish_worker(n,c,state,WorkerResult("w","o","COMPLETED","done",("ev:1",)))
            item=n.load()["o"]
            self.assertEqual((item.status,item.lease_owner),("DISCOVERED","w"))
            self.assertEqual(state.active,("o",)); self.assertEqual(state.completed,())

if __name__=="__main__": unittest.main()
