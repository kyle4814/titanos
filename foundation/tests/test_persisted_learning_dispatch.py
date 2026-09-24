import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from foundation.institutional_memory import InstitutionalMemoryStore
from foundation.worker_assignment import plan_from_persisted_learning, persist_opportunity_outcome
from foundation.workforce_registry import WorkforceRegistry, WorkerSpec
from foundation.worker_health import WorkerHealthBook
from foundation.specialization import SpecializationBook
from foundation.priority_scheduler import OpportunityPriority

class PersistedLearningDispatchTests(unittest.TestCase):
    def test_reloaded_feedback_changes_next_batch_order(self):
        with TemporaryDirectory() as td:
            store=InstitutionalMemoryStore(Path(td)/"memory.json")
            persist_opportunity_outcome(store,"a",10,2,True,1.0,
                                        observed_at="2026-09-24T00:00:00+00:00")
            persist_opportunity_outcome(store,"b",10,20,True,1.0,
                                        observed_at="2026-09-24T00:00:00+00:00")
            reg=WorkforceRegistry().register(WorkerSpec("w","security",("web",)))
            priorities=(OpportunityPriority("a"),OpportunityPriority("b"))
            ops=(("a","security",{"web"}),("b","security",{"web"}))
            plan=plan_from_persisted_learning(
                store,reg,WorkerHealthBook(),SpecializationBook(),ops,priorities,1,
                now=__import__("datetime").datetime.fromisoformat("2026-09-24T00:00:00+00:00"))
            self.assertEqual(plan.assignments[0].opportunity_id,"b")
            self.assertEqual(plan.deferred,("a",))

if __name__=="__main__": unittest.main()
