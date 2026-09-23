from __future__ import annotations

import unittest

from foundation.opportunity_scope import (
    OPPORTUNITY_DOMAINS,
    OPPORTUNITY_SCOPE,
    OPPORTUNITY_SCOPE_VERSION,
)


class TestOpportunityScope(unittest.TestCase):
    def test_global_scope_is_non_empty_and_versioned(self):
        self.assertEqual(OPPORTUNITY_SCOPE.version, OPPORTUNITY_SCOPE_VERSION)
        self.assertGreaterEqual(len(OPPORTUNITY_SCOPE.domains), 20)
        self.assertGreaterEqual(len(OPPORTUNITY_SCOPE.opportunity_types), 100)
        self.assertGreaterEqual(len(OPPORTUNITY_SCOPE.signals), 30)
        self.assertGreaterEqual(len(OPPORTUNITY_SCOPE.channels), 20)

    def test_domain_types_are_in_global_registry(self):
        for types in OPPORTUNITY_DOMAINS.values():
            for opportunity_type in types:
                self.assertIn(opportunity_type, OPPORTUNITY_SCOPE.opportunity_types)

    def test_blind_spot_detection(self):
        blind = OPPORTUNITY_SCOPE.blind_spots(
            covered_types={"bug_bounty"},
            covered_channels={"github"},
        )
        self.assertNotIn("bug_bounty", blind["opportunity_types"])
        self.assertIn("tender", blind["opportunity_types"])
        self.assertNotIn("github", blind["channels"])
        self.assertIn("government_portal", blind["channels"])


if __name__ == "__main__":
    unittest.main()
