import tempfile, unittest
from pathlib import Path
from foundation.next_kernel import OpportunityStore
from foundation.swarm_state import SwarmState, SwarmStateStore
from foundation.coordination_journal import CoordinationJournal, CrashRecoverableCoordinator

class TestCoordinationJournal(unittest.TestCase):
    def test_prepare_is_recoverable(self):
        with tempfile.TemporaryDirectory() as td:
            n=OpportunityStore(Path(td)/"next.json"); s=SwarmStateStore(Path(td)/"swarm.json")
            j=CoordinationJournal(Path(td)/"coord.json")
            c=CrashRecoverableCoordinator(n,s,j)
            state=SwarmState("s1",queued=("o1",))
            j.prepare(__import__("foundation.coordination_journal",fromlist=["CoordinationRecord"]).CoordinationRecord("op","s1","PREPARED",state))
            r=c.recover()
            self.assertEqual(r.phase,"COMMITTED"); self.assertEqual(s.load("s1"),state); self.assertIsNone(j.load())
    def test_commit_clears_journal(self):
        with tempfile.TemporaryDirectory() as td:
            n=OpportunityStore(Path(td)/"next.json"); s=SwarmStateStore(Path(td)/"swarm.json")
            j=CoordinationJournal(Path(td)/"coord.json"); c=CrashRecoverableCoordinator(n,s,j)
            r=c.commit("op",SwarmState("s1",active=("o",)))
            self.assertEqual(r.phase,"COMMITTED"); self.assertIsNone(j.load())
if __name__=="__main__": unittest.main()
