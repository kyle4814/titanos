import tempfile, unittest
from pathlib import Path
from foundation.worker_health import WorkerHealthBook
from foundation.specialization import SpecializationBook
from foundation.workforce_memory import WorkforceMemoryStore
class TestWorkforceMemory(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            h=WorkerHealthBook(); h.record("w",status="COMPLETED",latency_ms=100)
            s=SpecializationBook(); s.record("w","security",completed=True,evidence_count=4)
            p=Path(td)/"workforce.json"; WorkforceMemoryStore(p).save(h,s)
            hh,ss=WorkforceMemoryStore(p).load()
            self.assertEqual(hh.workers["w"],h.workers["w"])
            self.assertEqual(ss.records[("w","security")],s.records[("w","security")])
if __name__=="__main__": unittest.main()
