from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from foundation.lease_aware_frontier import available_frontier
from foundation.next_kernel import Opportunity, OpportunityStore
from foundation.next_leases import claim


class TestLeaseAwareFrontier(unittest.TestCase):
    def _store(self):
        td = tempfile.TemporaryDirectory()
        store = OpportunityStore(Path(td.name) / "next.json")
        for oid, value in (("low", 10), ("high", 90), ("leased", 100)):
            store.upsert(Opportunity(
                id=oid, source="test", title=oid,
                status="READY", authority="O2", value=value,
            ))
        return td, store

    def test_live_lease_is_excluded(self):
        td, store = self._store()
        try:
            claim(store, "leased", "claude-1", ttl_seconds=900)
            result = available_frontier(store, limit=2)
            self.assertEqual([x.id for x in result], ["high", "low"])
        finally:
            td.cleanup()

    def test_order_is_deterministic(self):
        td, store = self._store()
        try:
            result = available_frontier(store, limit=3)
            self.assertEqual([x.id for x in result], ["leased", "high", "low"])
        finally:
            td.cleanup()

    def test_zero_limit(self):
        td, store = self._store()
        try:
            self.assertEqual(available_frontier(store, limit=0), ())
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
