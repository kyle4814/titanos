from __future__ import annotations

import unittest

from foundation.opportunity_coverage_gaps import CoverageGap, find_gaps, rank_gaps
from foundation.source_adapter_contract import SourceAdapterContract


class TestOpportunityCoverageGaps(unittest.TestCase):
    def test_matching_adapter_removes_covered_cell(self):
        adapter = SourceAdapterContract(
            adapter_id="test.gov",
            name="Test",
            status="AVAILABLE",
            source_class="PUBLIC_PROCUREMENT",
            source_family="procurement",
            regions=("OCEANIA",),
            jurisdictions=("NATIONAL",),
            opportunity_types=("tender",),
        )
        gaps = find_gaps(
            (adapter,),
            opportunity_types=("tender",),
            regions=("OCEANIA",),
            jurisdictions=("NATIONAL",),
            source_classes=("PUBLIC_PROCUREMENT",),
            limit=None,
        )
        self.assertEqual(gaps, ())

    def test_uncovered_cell_is_emitted(self):
        gaps = find_gaps(
            (),
            opportunity_types=("tender",),
            regions=("OCEANIA",),
            jurisdictions=("NATIONAL",),
            source_classes=("PUBLIC_PROCUREMENT",),
            limit=None,
        )
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0].key, "tender:OCEANIA:NATIONAL:PUBLIC_PROCUREMENT")

    def test_disabled_adapter_does_not_claim_coverage(self):
        adapter = SourceAdapterContract(
            adapter_id="disabled",
            name="Disabled",
            status="DISABLED",
            source_class="PUBLIC_PROCUREMENT",
            source_family="procurement",
            regions=("OCEANIA",),
            jurisdictions=("NATIONAL",),
            opportunity_types=("tender",),
        )
        gaps = find_gaps(
            (adapter,),
            opportunity_types=("tender",),
            regions=("OCEANIA",),
            jurisdictions=("NATIONAL",),
            source_classes=("PUBLIC_PROCUREMENT",),
            limit=None,
        )
        self.assertEqual(len(gaps), 1)

    def test_rank_is_deterministic(self):
        gaps = (
            CoverageGap("z", "EUROPE", "NATIONAL", "OTHER_WEB"),
            CoverageGap("a", "AFRICA", "NATIONAL", "OTHER_WEB"),
        )
        self.assertEqual(rank_gaps(gaps)[0].opportunity_type, "a")


if __name__ == "__main__":
    unittest.main()
