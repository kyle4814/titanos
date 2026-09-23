from __future__ import annotations

import unittest

from foundation.coverage_work_queue import (
    CoverageWorkItem,
    STATE_AUTHORITY,
    WORK_STATES,
    work_item_from_plan,
)
from foundation.opportunity_coverage_gaps import CoverageGap
from foundation.opportunity_gap_planner import GapPlan


class TestCoverageWorkQueue(unittest.TestCase):
    def test_plan_becomes_discovered_work_item(self):
        gap = CoverageGap("tender", "OCEANIA", "NATIONAL", "PUBLIC_PROCUREMENT")
        plan = GapPlan(gap=gap, score=42, blockers=("source adapter needed",))
        item = work_item_from_plan(plan, work_id="gap-001")
        self.assertEqual(item.state, "DISCOVERED")
        self.assertEqual(item.required_authority, "O0")
        self.assertEqual(item.next_action, "discover adapter")

    def test_agent_can_prepare_but_not_commit(self):
        item = CoverageWorkItem(
            work_id="gap-002",
            gap=CoverageGap("tender", "OCEANIA", "NATIONAL", "PUBLIC_PROCUREMENT"),
            score=42,
        )
        prepared = item.transition("PREPARED", controlling_party="system")
        self.assertEqual(prepared.required_authority, "O1")
        with self.assertRaises(PermissionError):
            prepared.transition("COMMITTED", controlling_party="system")

    def test_human_commit_is_explicit(self):
        item = CoverageWorkItem(
            work_id="gap-003",
            gap=CoverageGap("tender", "OCEANIA", "NATIONAL", "PUBLIC_PROCUREMENT"),
            score=42,
            state="READY",
        )
        committed = item.transition("COMMITTED", controlling_party="human")
        self.assertEqual(committed.required_authority, "O3")
        self.assertEqual(committed.controlling_party, "human")

    def test_evidence_and_receipts_are_deduplicated(self):
        item = CoverageWorkItem(
            work_id="gap-004",
            gap=CoverageGap("tender", "OCEANIA", "NATIONAL", "PUBLIC_PROCUREMENT"),
            score=42,
        )
        item = item.add_evidence("ev1", "ev1").add_receipt("r1", "r1")
        self.assertEqual(item.evidence_refs, ("ev1",))
        self.assertEqual(item.receipt_refs, ("r1",))


if __name__ == "__main__":
    unittest.main()
