from __future__ import annotations

import unittest

from foundation.source_adapter_contract import (
    AdapterRegistry,
    SourceAdapterContract,
)


class TestSourceAdapterContract(unittest.TestCase):
    def test_adapter_round_trip(self):
        adapter = SourceAdapterContract(
            adapter_id="example.public.procurement",
            name="Example procurement feed",
            status="AVAILABLE",
            source_class="PUBLIC_PROCUREMENT",
            source_family="procurement",
            regions=("OCEANIA",),
            jurisdictions=("NATIONAL",),
            opportunity_types=("tender", "rfq"),
            auth_mode="PUBLIC",
            retrieval_methods=("API",),
            update_cadence="daily",
            evidence_fields=("title", "deadline", "buyer", "source_url"),
            parser_version="1",
        )
        data = adapter.to_dict()
        self.assertEqual(data["adapter_id"], adapter.adapter_id)
        self.assertTrue(data["evidence_fields"])

    def test_registry_rejects_conflicting_duplicate(self):
        registry = AdapterRegistry()
        adapter = SourceAdapterContract(
            adapter_id="x",
            name="X",
            status="PLANNED",
            source_class="OTHER_WEB",
            source_family="commercial",
        )
        registry.register(adapter)
        with self.assertRaises(ValueError):
            registry.register(
                SourceAdapterContract(
                    adapter_id="x",
                    name="Different X",
                    status="AVAILABLE",
                    source_class="OTHER_WEB",
                    source_family="commercial",
                )
            )

    def test_coverage_counts_are_machine_readable(self):
        registry = AdapterRegistry()
        registry.register(
            SourceAdapterContract(
                adapter_id="planned",
                name="Planned",
                status="PLANNED",
                source_class="OTHER_WEB",
                source_family="commercial",
            )
        )
        registry.register(
            SourceAdapterContract(
                adapter_id="available",
                name="Available",
                status="AVAILABLE",
                source_class="GITHUB",
                source_family="github",
                retrieval_methods=("API", "GIT"),
            )
        )
        self.assertEqual(registry.coverage()["adapters"], 2)
        self.assertEqual(registry.coverage()["available"], 1)
        self.assertEqual(registry.coverage()["planned"], 1)


if __name__ == "__main__":
    unittest.main()
