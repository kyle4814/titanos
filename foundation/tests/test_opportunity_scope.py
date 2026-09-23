from __future__ import annotations

import unittest

from foundation.opportunity_scope import (
    OPPORTUNITY_ACTION_CLASSES,
    OPPORTUNITY_CHANNELS,
    OPPORTUNITY_DOMAINS,
    OPPORTUNITY_SCOPE,
    OPPORTUNITY_SCOPE_VERSION,
    OPPORTUNITY_TYPES,
)


class TestOpportunityScope(unittest.TestCase):
    def test_global_scope_is_broad_and_versioned(self):
        self.assertEqual(OPPORTUNITY_SCOPE.version, OPPORTUNITY_SCOPE_VERSION)
        self.assertGreaterEqual(len(OPPORTUNITY_SCOPE.domains), 40)
        self.assertGreaterEqual(len(OPPORTUNITY_SCOPE.opportunity_types), 250)
        self.assertGreaterEqual(len(OPPORTUNITY_SCOPE.signals), 30)
        self.assertGreaterEqual(len(OPPORTUNITY_SCOPE.channels), 20)

    def test_domain_types_are_in_global_registry(self):
        for types in OPPORTUNITY_DOMAINS.values():
            for opportunity_type in types:
                self.assertIn(opportunity_type, OPPORTUNITY_TYPES)

    def test_high_value_blind_spots_are_first_class(self):
        blind = OPPORTUNITY_SCOPE.blind_spots(
            covered_types={"bug_bounty"},
            covered_channels={"github"},
        )
        self.assertNotIn("bug_bounty", blind["opportunity_types"])
        self.assertIn("tender", blind["opportunity_types"])
        self.assertNotIn("github", blind["channels"])
        self.assertIn("government_portal", blind["channels"])

    def test_emerging_and_second_order_are_covered(self):
        self.assertIn("unknown", OPPORTUNITY_SCOPE.opportunity_types)
        self.assertIn("second_order", OPPORTUNITY_SCOPE.opportunity_types)
        self.assertIn("cross_domain", OPPORTUNITY_SCOPE.opportunity_types)

    def test_execution_dimensions_are_present(self):
        self.assertIn("submit", OPPORTUNITY_ACTION_CLASSES)
        self.assertIn("authorized_security_scope", OPPORTUNITY_SCOPE.access_models)
        self.assertIn("value_mechanism", OPPORTUNITY_SCOPE.coverage_axes)
        data = OPPORTUNITY_SCOPE.to_dict()
        self.assertIn("value_mechanisms", data)
        self.assertIn("action_classes", data)
        self.assertIn("access_models", data)
        self.assertIn("coverage_axes", data)


if __name__ == "__main__":
    unittest.main()
