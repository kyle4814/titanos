import unittest
from foundation.batch_planner import BatchPlan, ActiveBatch
from foundation.swarm_planner import PlannedAssignment
from foundation.worker_health import WorkerHealthBook

class ActiveBatchHealthTests(unittest.TestCase):
    def _batch(self):
        return ActiveBatch(BatchPlan((PlannedAssignment("a","security",("w1",)),),()))
    def test_valid_heartbeat(self):
        b=self._batch(); b.start("a")
        self.assertTrue(b.heartbeat("a","w1"))
    def test_wrong_heartbeat_rejected(self):
        b=self._batch(); b.start("a")
        with self.assertRaises(ValueError): b.heartbeat("a","w2")
    def test_timeout_releases_and_records_retry(self):
        b=self._batch(); b.start("a"); h=WorkerHealthBook()
        self.assertEqual(b.timeout("a",h),"w1")
        self.assertEqual(b.capacity_used,0)
        self.assertEqual(h.workers["w1"].retries,1)
        self.assertEqual(h.workers["w1"].failed,1)

if __name__=="__main__": unittest.main()
