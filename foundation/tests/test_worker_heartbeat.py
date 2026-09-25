import tempfile, unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from foundation.next_kernel import Opportunity, OpportunityStore
from foundation.next_leases import claim
from foundation.worker_heartbeat import renew

class TestHeartbeat(unittest.TestCase):
    def test_owner_can_renew(self):
        with tempfile.TemporaryDirectory() as td:
            s=OpportunityStore(Path(td)/"n.json"); s.upsert(Opportunity("o","x","x","DISCOVERED",authority="O0"))
            now=datetime.now(timezone.utc); claim(s,"o","w",ttl_seconds=60)
            before=s.load()["o"].lease_until
            out=renew(s,"o","w",ttl_seconds=600,now=now)
            self.assertNotEqual(out.lease_until,before)
    def test_non_owner_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            s=OpportunityStore(Path(td)/"n.json"); s.upsert(Opportunity("o","x","x","DISCOVERED",authority="O0")); claim(s,"o","w")
            with self.assertRaises(PermissionError): renew(s,"o","x")
if __name__=="__main__": unittest.main()
