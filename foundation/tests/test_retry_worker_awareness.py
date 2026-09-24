import unittest
from foundation.batch_planner import RetryQueue, ActiveBatch, BatchPlan
from foundation.swarm_planner import PlannedAssignment
from foundation.worker_health import WorkerHealthBook

class RetryWorkerAwareTests(unittest.TestCase):
    def test_quarantined_retry_is_not_ready_for_dispatch(self):
        q=RetryQueue(); q.schedule("opp",0,"w1")
        h=WorkerHealthBook(); h.quarantine("w1")
        b=ActiveBatch(BatchPlan((PlannedAssignment("opp","security",("w1",)),),()))
        self.assertEqual(b.ready_retries(q,1,h),())
    def test_healthy_retry_is_ready(self):
        q=RetryQueue(); q.schedule("opp",0,"w1")
        h=WorkerHealthBook()
        b=ActiveBatch(BatchPlan((PlannedAssignment("opp","security",("w1",)),),()))
        self.assertEqual(b.ready_retries(q,1,h),("opp",))

if __name__=="__main__": unittest.main()
