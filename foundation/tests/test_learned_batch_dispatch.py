import unittest
from foundation.priority_scheduler import OpportunityPriority
from foundation.opportunity_feedback import OpportunityFeedbackBook, OutcomeFeedback
from foundation.specialization import SpecializationBook
from foundation.worker_health import WorkerHealthBook
from foundation.workforce_registry import WorkforceRegistry, WorkerSpec
from foundation.worker_assignment import dispatch_learned_batch

class LearnedBatchDispatchTests(unittest.TestCase):
    def test_learned_order_flows_into_bounded_batch(self):
        f=OpportunityFeedbackBook()
        f.record(OutcomeFeedback("high",10,30,True,1.0,"2026-09-24T00:00:00+00:00"))
        reg=WorkforceRegistry().register(WorkerSpec("worker","security",("web",)))
        out=dispatch_learned_batch(
            reg,WorkerHealthBook(),SpecializationBook(),
            (("low","security",{"web"}),("high","security",{"web"})),
            (OpportunityPriority("low"),OpportunityPriority("high")),
            f,1)
        self.assertEqual(out.assignments[0].opportunity_id,"high")
        self.assertEqual(out.assignments[0].workers,("worker",))
        self.assertEqual(out.deferred,("low",))

if __name__=="__main__": unittest.main()
