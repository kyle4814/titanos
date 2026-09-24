"""Tests for source health telemetry."""

import unittest

from foundation.source_health import SourceHealthBook


class SourceHealthTests(unittest.TestCase):
    def test_success_resets_consecutive_failure_streak(self):
        book = SourceHealthBook()
        book.record("github", success=False)
        book.record("github", success=False)
        health = book.record("github", success=True)
        self.assertEqual(health.fetches, 3)
        self.assertEqual(health.successes, 1)
        self.assertEqual(health.failures, 2)
        self.assertEqual(health.consecutive_failures, 0)
        self.assertTrue(health.healthy)

    def test_repeated_failures_mark_source_unhealthy(self):
        book = SourceHealthBook()
        for _ in range(3):
            health = book.record("github", success=False)
        self.assertFalse(health.healthy)
        self.assertEqual(health.success_rate, 0.0)

if __name__ == "__main__":
    unittest.main()
