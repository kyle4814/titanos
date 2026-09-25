import tempfile, unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from foundation.next_kernel import Opportunity, OpportunityStore
from foundation.next_leases import claim
from foundation.swarm_state import SwarmState, SwarmStateStore
from foundation.swarm_recovery import reconcile_swarm

class TestSwarmRecovery(unittest.TestCase):
    def test_expired_active_work_returns_to_queue(self):
        with tempfile.TemporaryDirectory() as td:
            s=OpportunityStore(Path(td)/"next.json")
            o=Opportunity("o1","x","x","DISCOVERED",authority="O0")
            s.upsert(o); claim(s,"o1","dead-worker",ttl_seconds=1)
            state=SwarmState("sw1",active=("o1",))
            ss=SwarmStateStore(Path(td)/"swarm.json"); ss.save(state)
            future=datetime.now(timezone.utc)+timedelta(seconds=2)
            repaired=reconcile_swarm(s,ss,state,now=future)
            self.assertEqual(repaired.active,())
            self.assertEqual(repaired.queued,("o1",))
            self.assertFalse(s.load()["o1"].lease_owner)

if __name__=="__main__": unittest.main()
