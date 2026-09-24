import unittest
from foundation.batch_planner import BatchPlan, ActiveBatch, RetryQueue
from foundation.swarm_planner import PlannedAssignment
from foundation.worker_health import WorkerHealthBook

class RetryReassignmentTests(unittest.TestCase):
    def test_ready_retry_can_be_reassigned_and_consumed(self):
        b=ActiveBatch(BatchPlan((),()))
        q=RetryQueue(); q.schedule("opp",0,"failed")
        h=WorkerHealthBook()
        self.assertEqual(b.reassign_retry("opp","backup",q,h,1),"backup")
        self.assertEqual(b.active["opp"],"backup")
        self.assertEqual(q.ready(1),())
    def test_quarantined_reassignment_rejected(self):
        b=ActiveBatch(BatchPlan((),()))
        q=RetryQueue(); q.schedule("opp",0,"failed")
        h=WorkerHealthBook(); h.quarantine("backup")
        with self.assertRaises(ValueError): b.reassign_retry("opp","backup",q,h,1)

if __name__=="__main__": unittest.main()
