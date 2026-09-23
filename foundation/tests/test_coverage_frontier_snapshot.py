from __future__ import annotations

import unittest

from foundation.coverage_frontier import FrontierItem
from foundation.coverage_frontier_snapshot import make_snapshot, validate_snapshot


class TestCoverageFrontierSnapshot(unittest.TestCase):
    def test_snapshot_has_stable_fingerprint(self):
        items = (
            FrontierItem("b", 10, "READY", "build"),
            FrontierItem("a", 20, "PREPARED", "verify"),
        )
        one = make_snapshot(items)
        two = make_snapshot(tuple(reversed(items)))
        self.assertEqual(one.fingerprint(), two.fingerprint())
        validate_snapshot(one)

    def test_payload_contains_recovery_metadata(self):
        snapshot = make_snapshot((
            FrontierItem("x", 1, "DISCOVERED", "triage"),
        ))
        data = snapshot.to_dict()
        self.assertIn("fingerprint", data)
        self.assertEqual(data["source"], "coverage_frontier")
        self.assertEqual(data["items"][0]["work_id"], "x")


if __name__ == "__main__":
    unittest.main()
