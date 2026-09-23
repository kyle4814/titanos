import tempfile, unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from foundation.next_kernel import Opportunity, OpportunityStore
from foundation.next_leases import claim
from foundation.worker_watchdog import inspect
class TestWatchdog(unittest.TestCase):
    def test_recovers_expired_and_preserves_healthy(self):
        with tempfile.TemporaryDirectory() as td:
            s=OpportunityStore(Path(td)/"n.json")
            s.upsert(Opportunity("dead","x","x","DISCOVERED",authority="O0"))
            s.upsert(Opportunity("live","x","x","DISCOVERED",authority="O0"))
            claim(s,"dead","w1",ttl_seconds=1); claim(s,"live","w2",ttl_seconds=600)
            future=datetime.now(timezone.utc)+timedelta(seconds=2)
            r=inspect(s,now=future)
            self.assertEqual(r.expired,("dead",)); self.assertEqual(r.recovered,("dead",)); self.assertEqual(r.healthy,("live",))
if __name__=="__main__": unittest.main()
