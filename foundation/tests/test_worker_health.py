import unittest
from foundation.worker_health import WorkerHealthBook
class TestWorkerHealth(unittest.TestCase):
    def test_metrics(self):
        b=WorkerHealthBook(); b.record("a",status="COMPLETED",latency_ms=1000)
        b.record("a",status="FAILED",latency_ms=1000,heartbeat=True)
        self.assertEqual(b.workers["a"].throughput,1.0)
        self.assertEqual(b.workers["a"].failure_rate,.5)
    def test_rank_prefers_throughput_then_failure_rate(self):
        b=WorkerHealthBook()
        b.record("slow",status="COMPLETED",latency_ms=2000)
        b.record("fast",status="COMPLETED",latency_ms=1000)
        self.assertEqual(b.rank(("slow","fast")),("fast","slow"))
if __name__=="__main__": unittest.main()
