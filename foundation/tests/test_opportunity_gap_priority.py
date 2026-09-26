from __future__ import annotations

import unittest

from foundation.opportunity_coverage_gaps import CoverageGap
from foundation.opportunity_gap_priority import prioritize_gaps
from foundation.source_adapter_contract import SourceAdapterContract


class TestOpportunityGapPriority(unittest.TestCase):
    def test_reuse_can_increase_engineering_priority(self):
        gap = CoverageGap("tender", "OCEANIA", "NATIONAL", "PUBLIC_PROCUREMENT")
        adapter = SourceAdapterContract(
            adapter_id="procurement",
            name="Procurement",
            status="AVAILABLE",
            source_class="PUBLIC_PROCUREMENT",
            source_family="procurement",
            regions=("OCEANIA",),
            jurisdictions=("NATIONAL",),
            opportunity_types=("rfq", "tender"),
            evidence_fields=("title", "deadline"),
            update_cadence="daily",
        )
        result = prioritize_gaps((gap,), (adapter,))
        self.assertEqual(len(result), 1)
        self.assertGreater(result[0].score, 0)
        # _overlap: type +1, region +1, jurisdiction +1, same source class
        # +2 -- 5 for a full match, since the module's birth (5897e052).
        # The former "=4" failed at this test's own birth (051e5871).
        self.assertIn("reusable_adapter_overlap=5", result[0].reasons)
        self.assertIn("effort_proxy=1", result[0].reasons)
        self.assertEqual(prioritize_gaps((gap,))[0].score, 0)

    def test_output_is_deterministic(self):
        gaps = (
            CoverageGap("z", "EUROPE", "PRIVATE", "OTHER_WEB"),
            CoverageGap("a", "AFRICA", "PRIVATE", "OTHER_WEB"),
        )
        result = prioritize_gaps(gaps)
        self.assertEqual(result[0].gap.opportunity_type, "a")

    def test_priority_is_explicitly_engineering_only(self):
        gap = CoverageGap("x", "GLOBAL", "PRIVATE", "OTHER_WEB")
        result = prioritize_gaps((gap,))
        self.assertEqual(result[0].score, 0)


if __name__ == "__main__":
    unittest.main()
