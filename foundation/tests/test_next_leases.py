from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from foundation.next_kernel import Opportunity, OpportunityStore
from foundation.next_leases import claim, recover_expired, release


class TestNextLeases(unittest.TestCase):
    def _store(self):
        td = tempfile.TemporaryDirectory()
        store = OpportunityStore(Path(td.name) / "next.json")
        store.upsert(Opportunity(
            id="lease-1",
            source="test",
            title="Lease test",
            status="READY",
            authority="O2",
        ))
        return td, store

    def test_second_worker_cannot_take_live_lease(self):
        td, store = self._store()
        try:
            claim(store, "lease-1", "claude-1", ttl_seconds=900)
            with self.assertRaises(RuntimeError):
                claim(store, "lease-1", "claude-2", ttl_seconds=900)
        finally:
            td.cleanup()

    def test_owner_can_release(self):
        td, store = self._store()
        try:
            claim(store, "lease-1", "claude-1")
            release(store, "lease-1", "claude-1")
            self.assertEqual(store.load()["lease-1"].lease_owner, "")
        finally:
            td.cleanup()

    def test_expired_lease_is_recoverable(self):
        td, store = self._store()
        try:
            claim(store, "lease-1", "claude-1")
            current = store.load()["lease-1"]
            expired = datetime.now(timezone.utc) - timedelta(seconds=1)
            store._mutation_lock.acquire()
            try:
                items = store.load()
                from dataclasses import replace
                items["lease-1"] = replace(current, lease_until=expired.isoformat())
                store.save(items)
            finally:
                store._mutation_lock.release()
            recovered = recover_expired(store)
            self.assertEqual(recovered[0].lease_owner, "")
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
