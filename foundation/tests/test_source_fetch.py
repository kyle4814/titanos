import unittest

from foundation.source_fetch import fetch_source
from foundation.source_health import SourceHealthBook
from foundation.source_registry import SourceRegistry, SourceSpec


class GoodAdapter:
    def fetch(self):
        return ("one", "two")


class BadAdapter:
    def fetch(self):
        raise RuntimeError("upstream unavailable")


class SourceFetchTests(unittest.TestCase):
    def test_success_is_health_recorded_and_items_are_normalized_to_tuple(self):
        registry = SourceRegistry().register(SourceSpec("github", "oss", GoodAdapter()))
        health = SourceHealthBook()
        result = fetch_source(registry, health, "github")
        self.assertEqual(result.items, ("one", "two"))
        self.assertEqual(health.sources["github"].successes, 1)

    def test_failure_is_recorded_and_propagated(self):
        registry = SourceRegistry().register(SourceSpec("broken", "oss", BadAdapter()))
        health = SourceHealthBook()
        with self.assertRaises(RuntimeError):
            fetch_source(registry, health, "broken")
        self.assertEqual(health.sources["broken"].failures, 1)

    def test_disabled_source_never_calls_adapter(self):
        registry = SourceRegistry().register(SourceSpec("github", "oss", GoodAdapter()))
        registry.disable("github")
        with self.assertRaises(ValueError):
            fetch_source(registry, SourceHealthBook(), "github")


if __name__ == "__main__":
    unittest.main()
