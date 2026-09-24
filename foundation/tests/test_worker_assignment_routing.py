import unittest
from datetime import datetime, timezone
from foundation.opportunity import OpportunityReceipt, SignalEvidence
from foundation.specialization import SpecializationBook
from foundation.worker_health import WorkerHealthBook
from foundation.worker_assignment import AssignmentRefused, route_opportunity


class WorkerAssignmentRoutingTests(unittest.TestCase):
    def _opportunity(self):
        return OpportunityReceipt(
            "OPP-route", "owner/repo", "2026-09-24T00:00:00+00:00",
            (
                SignalEvidence("DEMAND", "maintainer requested work", "PRIMARY", "issue"),
                SignalEvidence("CODE_PRESSURE", "measured pressure", "PRIMARY", "code"),
            ),
            activity_class="ACTIVE", locally_reproducible="YES",
            observed_at="2026-09-24T00:00:00+00:00",
        )

    def test_routes_to_best_healthy_specialist(self):
        s = SpecializationBook()
        h = WorkerHealthBook()
        s.record("general", "security", completed=True, evidence_count=1)
        s.record("expert", "security", completed=True, evidence_count=5)
        a = route_opportunity(
            self._opportunity(), ("general", "expert"), "security", s, h,
            next_cheapest_experiment="reproduce the pressure",
            what_would_disprove_value="pressure is not reproducible",
            now=datetime(2026, 9, 24, 1, tzinfo=timezone.utc),
        )
        self.assertEqual(a.worker_id, "expert")
        self.assertEqual(a.opportunity_id, "OPP-route")

    def test_quarantined_specialist_is_not_selected(self):
        s = SpecializationBook()
        h = WorkerHealthBook()
        s.record("expert", "security", completed=True, evidence_count=10)
        h.quarantine("expert")
        a = route_opportunity(
            self._opportunity(), ("expert", "general"), "security", s, h,
            next_cheapest_experiment="reproduce the pressure",
            what_would_disprove_value="pressure is not reproducible",
        )
        self.assertEqual(a.worker_id, "general")

    def test_gate_refuses_non_investigate_opportunity(self):
        with self.assertRaises(AssignmentRefused):
            route_opportunity(
                OpportunityReceipt(
                    "OPP-watch", "owner/repo", "2026-09-24T00:00:00+00:00",
                    (SignalEvidence("DEMAND", "request", "THIRD_PARTY", "x"),),
                ),
                ("worker",), "security", SpecializationBook(),
                WorkerHealthBook(),
                next_cheapest_experiment="test",
                what_would_disprove_value="failure",
            )


if __name__ == "__main__":
    unittest.main()
