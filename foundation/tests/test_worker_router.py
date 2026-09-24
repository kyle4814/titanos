import unittest
from foundation.worker_router import route
from foundation.worker_health import WorkerHealthBook
from foundation.specialization import SpecializationBook
from foundation.workforce_registry import WorkforceRegistry, WorkerSpec

class TestWorkerRouter(unittest.TestCase):
    def test_combines_domain_capability_health_and_specialization(self):
        r = WorkforceRegistry().register(
            WorkerSpec("a", "security", ("security",), authority_ceiling="O2")
        ).register(
            WorkerSpec("b", "security", ("security",), authority_ceiling="O1")
        ).register(
            WorkerSpec("x", "finance", ("finance",), authority_ceiling="O2")
        )
        s = SpecializationBook()
        s.record("a", "security", completed=True, evidence_count=3)
        s.record("b", "security", completed=False)
        h = WorkerHealthBook()
        h.record("a", status="COMPLETED", latency_ms=1000)
        h.record("b", status="COMPLETED", latency_ms=2000)
        self.assertEqual(route(r, h, s, ("x", "b", "a"), "security"), ("a", "b"))

    def test_minimum_authority_filters_workers(self):
        r = WorkforceRegistry().register(
            WorkerSpec("o1", "security", ("security",), authority_ceiling="O1")
        ).register(
            WorkerSpec("o2", "security", ("security",), authority_ceiling="O2")
        )
        self.assertEqual(
            route(r, WorkerHealthBook(), SpecializationBook(), ("o1", "o2"), "security", min_authority="O2"),
            ("o2",),
        )

    def test_invalid_authority_is_rejected(self):
        r = WorkforceRegistry().register(WorkerSpec("a", "security", ("security",)))
        with self.assertRaises(ValueError):
            route(r, WorkerHealthBook(), SpecializationBook(), ("a",), "security", min_authority="O9")

if __name__ == "__main__":
    unittest.main()
