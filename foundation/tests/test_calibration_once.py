import unittest
from foundation.worker_assignment import plan_from_persisted_learning
from foundation.institutional_memory import InstitutionalMemoryStore
from foundation.workforce_registry import WorkforceRegistry, WorkerSpec
from foundation.worker_health import WorkerHealthBook
from foundation.specialization import SpecializationBook
from foundation.priority_scheduler import OpportunityPriority
from foundation.worker_assignment import persist_opportunity_outcome
from tempfile import TemporaryDirectory
from pathlib import Path

class CalibrationOnceTests(unittest.TestCase):
    def test_persisted_calibration_is_applied_once(self):
        with TemporaryDirectory() as td:
            store=InstitutionalMemoryStore(Path(td)/"memory.json")
            persist_opportunity_outcome(store,"a",10,20,True,1.0,
                                        observed_at="2026-09-24T00:00:00+00:00")
            reg=WorkforceRegistry().register(WorkerSpec("w","security",("web",)))
            plan=plan_from_persisted_learning(
                store,reg,WorkerHealthBook(),SpecializationBook(),
                (("a","security",{"web"}),("b","security",{"web"})),
                (OpportunityPriority("a",expected_value=10),OpportunityPriority("b",expected_value=15)),
                1)
            self.assertEqual(plan.assignments[0].opportunity_id,"a")

if __name__=="__main__":
    unittest.main()
