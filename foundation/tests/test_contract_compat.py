import unittest
from pathlib import Path

import yaml

from foundation.contract_compat import (
    Contract, check_compatible, contract_from_top_level_keys,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestCheckCompatible(unittest.TestCase):
    def test_compatible_when_requires_is_subset_of_produces(self):
        producer = Contract("A", produces=frozenset({"x", "y"}), requires=frozenset())
        consumer = Contract("B", produces=frozenset(), requires=frozenset({"x"}))
        result = check_compatible(producer, consumer)
        self.assertTrue(result.compatible)
        self.assertEqual(result.missing, frozenset())

    def test_incompatible_when_requires_not_satisfied(self):
        producer = Contract("A", produces=frozenset({"x"}), requires=frozenset())
        consumer = Contract("B", produces=frozenset(), requires=frozenset({"x", "z"}))
        result = check_compatible(producer, consumer)
        self.assertFalse(result.compatible)
        self.assertEqual(result.missing, frozenset({"z"}))
        self.assertIn("'z'", result.reason)

    def test_empty_requires_is_always_compatible(self):
        producer = Contract("A", produces=frozenset(), requires=frozenset())
        consumer = Contract("B", produces=frozenset(), requires=frozenset())
        self.assertTrue(check_compatible(producer, consumer).compatible)

    def test_contract_from_top_level_keys(self):
        c = contract_from_top_level_keys("doc", {"foo": 1, "bar": 2})
        self.assertEqual(c.produces, frozenset({"foo", "bar"}))

    def test_contract_from_non_mapping_produces_empty(self):
        c = contract_from_top_level_keys("doc", ["not", "a", "mapping"])
        self.assertEqual(c.produces, frozenset())


class TestRealHistoricalMismatch(unittest.TestCase):
    """Reproduces the actual Cycle-2 bug this session hit: bottleneck.yaml
    was mistakenly fed to a gate that requires automation_candidate.yaml's
    shape. This is the real end-to-end GENE_A/GENE_B demo — real fixtures,
    real gate requirement, not synthetic data."""

    AUTOMATION_CANDIDATE_GATE_CONTRACT = Contract(
        name="rpa.gates.human_jurisdiction.authorize_pilot",
        produces=frozenset(),
        requires=frozenset({"automation_candidate"}),
    )

    def _load(self, fixture_name: str) -> dict:
        path = REPO_ROOT / "rpa" / "fixtures" / fixture_name
        return yaml.safe_load(path.read_text())

    def test_automation_candidate_fixture_is_compatible_with_the_gate(self):
        data = self._load("automation_candidate.yaml")
        producer = contract_from_top_level_keys("automation_candidate.yaml", data)
        result = check_compatible(producer, self.AUTOMATION_CANDIDATE_GATE_CONTRACT)
        self.assertTrue(result.compatible, result.reason)

    def test_bottleneck_fixture_reproduces_the_real_historical_mismatch(self):
        data = self._load("bottleneck.yaml")
        producer = contract_from_top_level_keys("bottleneck.yaml", data)
        result = check_compatible(producer, self.AUTOMATION_CANDIDATE_GATE_CONTRACT)
        self.assertFalse(result.compatible)
        self.assertIn("automation_candidate", result.missing)
        # This is the check that, if it had existed in Cycle 2, would have
        # caught the mismatch before the gate call was ever attempted.


if __name__ == "__main__":
    unittest.main()
