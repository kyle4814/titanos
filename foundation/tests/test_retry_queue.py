import unittest
from foundation.batch_planner import RetryPolicy, RetryQueue

class RetryQueueTests(unittest.TestCase):
    def test_exponential_backoff_is_bounded(self):
        q=RetryQueue(RetryPolicy(max_attempts=4,base_backoff=2,max_backoff=5))
        self.assertTrue(q.schedule("x",10)); self.assertEqual(q.ready_at["x"],12)
        self.assertTrue(q.schedule("x",12)); self.assertEqual(q.ready_at["x"],16)
        self.assertTrue(q.schedule("x",16)); self.assertEqual(q.ready_at["x"],21)
        self.assertFalse(q.schedule("x",21))
    def test_ready_is_deterministic_and_release_removes(self):
        q=RetryQueue(); q.schedule("b",0); q.schedule("a",0)
        self.assertEqual(q.ready(1),("a","b"))
        q.release("a")
        self.assertEqual(q.ready(1),("b",))
    def test_invalid_policy_rejected(self):
        with self.assertRaises(ValueError): RetryPolicy(base_backoff=0).delay(1)

if __name__=="__main__": unittest.main()
