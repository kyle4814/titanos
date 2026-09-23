import tempfile, unittest
from pathlib import Path
from foundation.next_kernel import Opportunity, OpportunityStore
from foundation.dispatcher_state import DispatcherState, DispatcherStateStore
from foundation.dispatcher_recovery import reconcile_dispatcher

class TestDispatcherRecovery(unittest.TestCase):
    def test_stale_active_is_removed_and_duplicates_are_collapsed(self):
        with tempfile.TemporaryDirectory() as td:
            n=OpportunityStore(Path(td)/"next.json")
            n.upsert(Opportunity("live","x","x","DISCOVERED",authority="O0"))
            # No lease => stale.
            n.upsert(Opportunity("missing","x","x","DISCOVERED",authority="O0"))
            s=DispatcherStateStore(Path(td)/"d.json")
            state=DispatcherState("p",active=("live","missing","live"),queued=("live","q","q"))
            out=reconcile_dispatcher(n,s,state)
            self.assertEqual(out.active,())
            self.assertEqual(out.queued,("live","q"))
            self.assertEqual(s.load("p"),out)
if __name__=="__main__": unittest.main()
