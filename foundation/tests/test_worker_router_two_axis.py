"""A worker's domain and its capabilities are two axes (2026-09-26).

`WorkforceRegistry.match(capabilities, domain=...)` (1e1cf93b) selects by
domain equality AND capability superset. `worker_router.route()` then
re-filtered with `domain in worker.capabilities`, so a worker registered as
WorkerSpec("w", "security", ("web",)) matched the registry and was silently
dropped by the router: plan_assignment -> LookupError("no eligible worker"),
plan_batch -> empty assignments, and every consumer indexing
plan.assignments[0] raised IndexError (test_swarm_planner, test_batch_planner,
test_learned_batch_dispatch, test_persisted_learning_dispatch,
test_calibration_once; CI run 36199728136). No test anywhere required the
domain name to also be a capability. This pins the registry's contract at
the router.
"""
import unittest

from foundation.specialization import SpecializationBook
from foundation.worker_health import WorkerHealthBook
from foundation.worker_router import route
from foundation.workforce_registry import WorkerSpec, WorkforceRegistry


class TwoAxisRoutingTests(unittest.TestCase):
    def test_domain_match_does_not_require_the_domain_to_be_a_capability(self):
        reg = WorkforceRegistry().register(WorkerSpec("w", "security", ("web",)))
        self.assertEqual(route(reg, WorkerHealthBook(), SpecializationBook(), ("w",), "security"), ("w",))

    def test_domain_mismatch_is_still_refused(self):
        reg = WorkforceRegistry().register(WorkerSpec("w", "finance", ("web",)))
        self.assertEqual(route(reg, WorkerHealthBook(), SpecializationBook(), ("w",), "security"), ())

    def test_authority_ceiling_is_still_enforced(self):
        reg = WorkforceRegistry().register(WorkerSpec("w", "security", ("web",), authority_ceiling="O0"))
        self.assertEqual(route(reg, WorkerHealthBook(), SpecializationBook(), ("w",), "security", min_authority="O1"), ())

    def test_registry_match_and_router_agree(self):
        reg = WorkforceRegistry().register(WorkerSpec("w", "security", ("web",)))
        matched = tuple(w.worker_id for w in reg.match({"web"}, domain="security"))
        self.assertEqual(matched, ("w",))
        self.assertEqual(route(reg, WorkerHealthBook(), SpecializationBook(), matched, "security"), matched)


if __name__ == "__main__":
    unittest.main()
