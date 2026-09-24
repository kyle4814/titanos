import unittest
from foundation.batch_planner import BatchPlan, ActiveBatch
from foundation.swarm_planner import PlannedAssignment

class ActiveBatchTests(unittest.TestCase):
    def _batch(self):
        return ActiveBatch(BatchPlan((
            PlannedAssignment("a","security",("w1",)),
            PlannedAssignment("b","security",("w2",)),
        ),()))
    def test_start_and_complete_release_capacity(self):
        b=self._batch()
        self.assertEqual(b.start("a"),"w1")
        self.assertEqual(b.capacity_used,1)
        self.assertEqual(b.complete("a"),"w1")
        self.assertEqual(b.capacity_used,0)
    def test_same_worker_cannot_be_active_twice(self):
        b=ActiveBatch(BatchPlan((
            PlannedAssignment("a","security",("w1",)),
            PlannedAssignment("b","security",("w1",)),
        ),()))
        b.start("a")
        with self.assertRaises(ValueError): b.start("b")
    def test_duplicate_start_rejected(self):
        b=self._batch()
        b.start("a")
        with self.assertRaises(ValueError): b.start("a")

if __name__=="__main__": unittest.main()
