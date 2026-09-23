from __future__ import annotations

import unittest

from foundation.coverage_frontier import select_frontier, snapshot_frontier
from foundation.coverage_work_queue import CoverageWorkItem
from foundation.opportunity_coverage_gaps import CoverageGap


def item(work_id, score, state="DISCOVERED", blockers=()):
    return CoverageWorkItem(
        work_id=work_id,
        gap=CoverageGap("tender", "OCEANIA", "NATIONAL", "PUBLIC_PROCUREMENT"),
        score=score,
        state=state,
        blockers=blockers,
    )


class TestCoverageFrontier(unittest.TestCase):
    def test_highest_score_is_selected(self):
        result = select_frontier((item("low", 10), item("high", 90)))
        self.assertEqual(result[0].work_id, "high")

    def test_ties_are_deterministic(self):
        result = select_frontier((item("z", 50), item("a", 50)), limit=2)
        self.assertEqual([x.work_id for x in result], ["a", "z"])

    def test_blocked_and_terminal_items_are_excluded(self):
        result = select_frontier((
            item("blocked", 100, blockers=("needs adapter",)),
            item("committed", 95, state="COMMITTED"),
            item("ready", 20, state="READY"),
        ))
        self.assertEqual(result[0].work_id, "ready")

    def test_snapshot_is_serializable(self):
        snapshot = snapshot_frontier((item("x", 1),))
        self.assertEqual(snapshot[0]["work_id"], "x")


if __name__ == "__main__":
    unittest.main()
