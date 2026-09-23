from __future__ import annotations

import unittest

from foundation.coverage_opportunity_bridge import (
    project_state,
    record_outcome,
)
from foundation.coverage_work_queue import CoverageWorkItem
from foundation.opportunity_coverage_gaps import CoverageGap
from foundation.receipt import Claim, Receipt


class TestCoverageOpportunityBridge(unittest.TestCase):
    def _work(self):
        return CoverageWorkItem(
            work_id="gap-bridge-1",
            gap=CoverageGap("tender", "OCEANIA", "NATIONAL", "PUBLIC_PROCUREMENT"),
            score=42,
            state="OUTCOME",
            receipt_refs=("old-receipt",),
        )

    def test_state_projection_uses_existing_opportunity_vocabulary(self):
        self.assertEqual(project_state(self._work()), "QUALIFIED")

    def test_outcome_requires_real_receipt(self):
        receipt = Receipt(
            receipt_id="receipt-1",
            target="gap-bridge-1",
            question="Was the coverage adapter built and verified?",
            verdict="COVERAGE_GAP_RECORDED",
            claims=(Claim("Adapter coverage was verified.", "PROVEN", "test run"),),
            evidence_refs=("test-run-1",),
        )
        outcome = record_outcome(self._work(), receipt)
        self.assertTrue(outcome.outcome_recorded)
        self.assertEqual(
            outcome.receipt_refs,
            ("old-receipt", "receipt-1"),
        )

    def test_non_outcome_cannot_record(self):
        work = self._work()
        work = work.transition("READY", controlling_party="system")
        receipt = Receipt(
            receipt_id="receipt-2",
            target="gap-bridge-1",
            question="test",
            verdict="COVERAGE_GAP_RECORDED",
            claims=(Claim("Observed.", "PROVEN", "evidence"),),
        )
        with self.assertRaises(ValueError):
            record_outcome(work, receipt)


if __name__ == "__main__":
    unittest.main()
