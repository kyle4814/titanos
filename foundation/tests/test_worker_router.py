import unittest
from foundation.worker_router import route
from foundation.worker_health import WorkerHealthBook
from foundation.specialization import SpecializationBook
from foundation.workforce_registry import WorkforceRegistry, WorkerSpec
class TestWorkerRouter(unittest.TestCase):
    def test_combines_eligibility_and_signals(self):
        r=WorkforceRegistry()
        r.register(WorkerSpec("a",("security",),"O1")); r.register(WorkerSpec("b",("security",),"O1")); r.register(WorkerSpec("x",("finance",),"O1"))
        s=SpecializationBook(); s.record("a","security",completed=True,evidence_count=3); s.record("b","security",completed=False)
        h=WorkerHealthBook(); h.record("a",status="COMPLETED",latency_ms=1000); h.record("b",status="COMPLETED",latency_ms=2000)
        self.assertEqual(route(r,h,s,("x","b","a"),"security"),("a","b"))
if __name__=="__main__": unittest.main()
