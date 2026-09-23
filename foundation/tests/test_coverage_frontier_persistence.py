from __future__ import annotations

import unittest

from foundation.coverage_frontier import FrontierItem
from foundation.coverage_frontier_persistence import InMemoryFrontierPersistence
from foundation.coverage_frontier_snapshot import make_snapshot


class TestCoverageFrontierPersistence(unittest.TestCase):
    def test_round_trip(self):
        store = InMemoryFrontierPersistence()
        snapshot = make_snapshot((
            FrontierItem("x", 10, "READY", "verify"),
        ))
        store.save(snapshot)
        loaded = store.load()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.fingerprint(), snapshot.fingerprint())

    def test_empty_store_is_explicit(self):
        self.assertIsNone(InMemoryFrontierPersistence().load())


if __name__ == "__main__":
    unittest.main()
