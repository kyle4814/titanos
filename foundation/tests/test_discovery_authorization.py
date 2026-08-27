import unittest

from foundation.communication_gate import CommunicationDenied
from foundation.discovery_authorization import (
    DiscoveryPolicy, UnboundedDiscoveryObjective,
    authorize_discovery, standing_switch_for,
)


class TestStandingSwitch(unittest.TestCase):
    def test_authorized_scope_evaluates_true(self):
        switch = standing_switch_for("READ_URL")
        policy = DiscoveryPolicy(
            objective="find the current stable release URL for PyYAML",
            requested_scope="READ_URL",
        )
        self.assertTrue(authorize_discovery(policy))
        # standing_switch_for itself performs no evaluation
        self.assertEqual(switch.requested_scope, "READ_URL")

    def test_read_api_also_authorized(self):
        policy = DiscoveryPolicy(
            objective="check GitHub releases API for repo X's latest tag",
            requested_scope="READ_API",
        )
        self.assertTrue(authorize_discovery(policy))


class TestUnauthorizedScope(unittest.TestCase):
    def test_webhook_never_authorized(self):
        policy = DiscoveryPolicy(
            objective="listen for inbound events",
            requested_scope="RECEIVE_WEBHOOK",
        )
        with self.assertRaises(CommunicationDenied):
            authorize_discovery(policy)

    def test_unknown_scope_refused(self):
        policy = DiscoveryPolicy(objective="do something", requested_scope="WRITE_API")
        with self.assertRaises(CommunicationDenied):
            authorize_discovery(policy)


class TestObjectiveMustBeConcrete(unittest.TestCase):
    def test_empty_objective_refused(self):
        policy = DiscoveryPolicy(objective="   ", requested_scope="READ_URL")
        with self.assertRaises(UnboundedDiscoveryObjective):
            authorize_discovery(policy)

    def test_generic_wandering_objective_refused(self):
        policy = DiscoveryPolicy(
            objective="search for anything interesting",
            requested_scope="READ_URL",
        )
        with self.assertRaises(UnboundedDiscoveryObjective):
            authorize_discovery(policy)

    def test_keep_searching_refused(self):
        policy = DiscoveryPolicy(objective="keep searching until you find something", requested_scope="READ_URL")
        with self.assertRaises(UnboundedDiscoveryObjective):
            authorize_discovery(policy)

    def test_objective_check_runs_before_scope_check(self):
        # even an unauthorized scope should fail on the objective first,
        # since that's the cheaper/earlier check
        policy = DiscoveryPolicy(objective="", requested_scope="RECEIVE_WEBHOOK")
        with self.assertRaises(UnboundedDiscoveryObjective):
            authorize_discovery(policy)


class TestPolicyIsBounded(unittest.TestCase):
    def test_default_budget_fields_are_finite(self):
        policy = DiscoveryPolicy(objective="x", requested_scope="READ_URL")
        self.assertGreater(policy.max_queries, 0)
        self.assertGreater(policy.max_wall_clock_seconds, 0)
        self.assertGreater(policy.max_results, 0)

    def test_to_dict_round_trips_fields(self):
        policy = DiscoveryPolicy(objective="x", requested_scope="READ_URL")
        d = policy.to_dict()
        self.assertEqual(d["objective"], "x")
        self.assertEqual(d["requested_scope"], "READ_URL")


class TestNoNetworkIO(unittest.TestCase):
    def test_module_imports_no_network_libraries(self):
        import foundation.discovery_authorization as mod
        with open(mod.__file__) as f:
            source = f.read()
        for forbidden in ("urllib.request", "requests", "socket", "http.client"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
