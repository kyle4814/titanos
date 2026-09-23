import tempfile, unittest
from pathlib import Path
from foundation.institutional_memory import InstitutionalMemory, InstitutionalMemoryStore
from foundation.opportunity_feedback import OutcomeFeedback
class TestInstitutionalMemory(unittest.TestCase):
    def test_round_trip_preserves_all_learning_domains(self):
        with tempfile.TemporaryDirectory() as td:
            m=InstitutionalMemory()
            m.opportunity_learning.record(OutcomeFeedback("o",10,14,True,.9,"2026-09-24T00:00:00+00:00"))
            m.worker_health.record("w",status="COMPLETED",latency_ms=250)
            m.specialization.record("w","security",completed=True,evidence_count=3)
            p=Path(td)/"institutional.json"; s=InstitutionalMemoryStore(p); s.save(m)
            out=s.load()
            self.assertEqual(out.opportunity_learning.records,m.opportunity_learning.records)
            self.assertEqual(out.worker_health.workers,m.worker_health.workers)
            self.assertEqual(out.specialization.records,m.specialization.records)
if __name__=="__main__": unittest.main()
