from __future__ import annotations

import unittest

from foundation.opportunity_discovery_scope import (
    DISCOVERY_SURFACE_CLASSES,
    GLOBAL_REGION_GROUPS,
    JURISDICTION_TIERS,
    SOURCE_FAMILIES,
    coverage_matrix,
)


class TestOpportunityDiscoveryScope(unittest.TestCase):
    def test_global_discovery_dimensions_exist(self):
        self.assertGreaterEqual(len(DISCOVERY_SURFACE_CLASSES), 40)
        self.assertGreaterEqual(len(GLOBAL_REGION_GROUPS), 10)
        self.assertGreaterEqual(len(JURISDICTION_TIERS), 10)
        self.assertGreaterEqual(len(SOURCE_FAMILIES), 8)

    def test_coverage_matrix_is_machine_readable(self):
        matrix = coverage_matrix()
        for key in (
            "regions", "jurisdiction_tiers", "surface_classes",
            "source_families", "domain_keys", "geography_tiers",
        ):
            self.assertIn(key, matrix)
            self.assertTrue(matrix[key])

    def test_critical_source_classes_are_present(self):
        expected = {
            "PUBLIC_PROCUREMENT", "PUBLIC_GRANTS", "REGULATOR",
            "SECURITY_PROGRAM_REGISTRY", "BUG_BOUNTY_PLATFORM",
            "OPEN_SOURCE_HOSTING", "INVESTOR_DATABASE", "BUSINESS_MARKETPLACE",
            "DEVELOPER_ECOSYSTEM", "INTERNATIONAL_ORGANIZATION",
            "PHYSICAL_ASSET_MARKET", "DIRECT_SUBMISSION",
        }
        self.assertTrue(expected.issubset(set(DISCOVERY_SURFACE_CLASSES)))


if __name__ == "__main__":
    unittest.main()
