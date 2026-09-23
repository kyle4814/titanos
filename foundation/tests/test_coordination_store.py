import tempfile, unittest
from pathlib import Path
from foundation.next_kernel import Opportunity, OpportunityStore
from foundation.swarm_state import SwarmState, SwarmStateStore
from foundation.coordination_store import CoordinationStore

class TestCoordinationStore(unittest.TestCase):
    def test_persists_canonical_next_then_swarm(self):
        with tempfile.TemporaryDirectory() as td:
            n=OpportunityStore(Path(td)/"next.json")
            n.upsert(Opportunity("o","x","x","DISCOVERED",authority="O0"))
            ss=SwarmStateStore(Path(td)/"swarm.json")
            r=CoordinationStore(n,ss).snapshot("op1",SwarmState("s1",queued=("o",)))
            self.assertTrue(r.next_persisted and r.swarm_persisted)
            self.assertEqual(ss.load("s1").queued,("o",))
if __name__=="__main__": unittest.main()
