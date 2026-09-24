import unittest

from foundation.source_registry import SourceRegistry, SourceSpec


class Adapter:
    def fetch(self):
        return ()


class SourceRegistryTests(unittest.TestCase):
    def test_registry_is_modular_and_deterministic(self):
        registry = SourceRegistry()
        registry.register(SourceSpec("github", "oss", Adapter()))
        registry.register(SourceSpec("bugbounty", "security", Adapter()))
        self.assertEqual(
            [s.source_id for s in registry.active()],
            ["bugbounty", "github"],
        )

    def test_disabled_source_is_excluded_without_destroying_registration(self):
        registry = SourceRegistry().register(
            SourceSpec("github", "oss", Adapter())
        )
        registry.disable("github")
        self.assertEqual(registry.active(), ())
        self.assertFalse(registry.get("github").enabled)
        registry.enable("github")
        self.assertEqual([s.source_id for s in registry.active()], ["github"])

    def test_duplicate_source_ids_are_rejected(self):
        registry = SourceRegistry().register(
            SourceSpec("github", "oss", Adapter())
        )
        with self.assertRaises(ValueError):
            registry.register(SourceSpec("github", "security", Adapter()))


if __name__ == "__main__":
    unittest.main()
