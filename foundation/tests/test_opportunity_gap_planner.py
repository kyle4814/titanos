from __future__ import annotations

import unittest

from foundation.opportunity_coverage_gaps import CoverageGap
from foundation.opportunity_gap_planner import plan_gap, prioritize_gaps
from foundation.source_adapter_contract import SourceAdapterContract


class TestOpportunityGapPlanner(unittest.TestCase):
    def test_reuse_changes_plan(self):
        gap = CoverageGap("tender", "OCEANIA", "NATIONAL", "PUBLIC_PROCUREMENT")
        adapter = SourceAdapterContract(
            adapter_id="procurement-base",
            name="Base procurement",
            status="AVAILABLE",
            source_class="PUBLIC_PROCUREMENT",
            source_family="procurement",
            regions=("OCEANIA",),
            jurisdictions=("NATIONAL",),
            opportunity_types=("tender", "rfq"),
        )
        plan = plan_gap(gap, (adapter,))
        self.assertIn("procurement-base", plan.reusable_adapters)
        self.assertGreater(plan.score, 0)

    def test_planner_is_deterministic(self):
        gaps = (
            CoverageGap("z", "EUROPE", "NATIONAL", "OTHER_WEB"),
            CoverageGap("a", "AFRICA", "NATIONAL", "OTHER_WEB"),
        )
        plans = prioritize_gaps(gaps, (), limit=None)
        self.assertEqual(len(plans), 2)
        self.assertEqual(
            [p.gap.key for p in plans],
            sorted(p.gap.key for p in plans),
        )

    def test_output_is_serializable(self):
        gap = CoverageGap("tender", "OCEANIA", "NATIONAL", "PUBLIC_PROCUREMENT")
        self.assertIn("rationale", plan_gap(gap).to_dict())


if __name__ == "__main__":
    unittest.main()
