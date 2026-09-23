from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from foundation.coverage_next_store_adapter import (
    persist_work,
    recover_actionable,
)
from foundation.coverage_work_queue import CoverageWorkItem
from foundation.next_kernel import OpportunityStore
from foundation.opportunity_coverage_gaps import CoverageGap


class TestCoverageNextStoreAdapter(unittest.TestCase):
    def test_round_trip_uses_canonical_store(self):
        with tempfile.TemporaryDirectory() as td:
            store = OpportunityStore(Path(td) / "next.json")
            item = CoverageWorkItem(
                work_id="gap-store-1",
                gap=CoverageGap("tender", "OCEANIA", "NATIONAL", "PUBLIC_PROCUREMENT"),
                score=42,
                next_action="discover adapter",
            )
            self.assertEqual(persist_work(store, item), "NEW")
            recovered = recover_actionable(store)
            self.assertEqual(len(recovered), 1)
            self.assertEqual(recovered[0].id, "gap-store-1")
            self.assertEqual(recovered[0].authority, "O0")
            self.assertEqual(recovered[0].status, "DISCOVERED")

    def test_repeat_persistence_does_not_duplicate(self):
        with tempfile.TemporaryDirectory() as td:
            store = OpportunityStore(Path(td) / "next.json")
            item = CoverageWorkItem(
                work_id="gap-store-2",
                gap=CoverageGap("tender", "OCEANIA", "NATIONAL", "PUBLIC_PROCUREMENT"),
                score=10,
            )
            self.assertEqual(persist_work(store, item), "NEW")
            self.assertEqual(persist_work(store, item), "DUPLICATE")
            self.assertEqual(len(store.load()), 1)


if __name__ == "__main__":
    unittest.main()
