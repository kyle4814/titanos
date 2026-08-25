"""
Tests for rpa/composition/checker.py — the cross-file referential
integrity gap named in rpa/BUILD_REPORT.md's next-work-cell section.
"""

import sys, unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from rpa.composition.checker import check_chain_integrity  # noqa: E402

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


def _load(name: str) -> dict:
    return yaml.safe_load((FIXTURES / name).read_text())


class TestRealFixtureChainIsIntact(unittest.TestCase):
    """The exact fixture chain from rpa/tests/test_end_to_end.py — every
    document was independently schema-valid; this proves the cross-file
    promises they make to each other are also kept."""

    def test_full_chain_intact(self):
        report = check_chain_integrity(
            map_doc=_load("legacy_map.yaml"),
            bottleneck_docs=[_load("bottleneck.yaml")],
            candidate_docs=[_load("automation_candidate.yaml")],
            pilot_docs=[_load("pilot_simulation.yaml")],
            rollback_docs=[_load("rollback_contract.yaml")],
            measurement_docs=[_load("before_after_measurement.yaml")],
        )
        self.assertEqual(report.verdict, "INTACT", report.findings)
        self.assertEqual(report.findings, [])


class TestDanglingReferencesRefused(unittest.TestCase):
    def test_bottleneck_citing_nonexistent_node_is_refused(self):
        map_doc = _load("legacy_map.yaml")
        bottleneck = _load("bottleneck.yaml")
        bottleneck["institutional_bottleneck"]["involved_node_ids"] = ["node-does-not-exist"]
        report = check_chain_integrity(map_doc=map_doc, bottleneck_docs=[bottleneck])
        self.assertEqual(report.verdict, "REFUSED")
        self.assertTrue(any(f.check == "bottleneck_involved_node_ids" for f in report.findings))
        self.assertIn("node-does-not-exist", report.findings[0].involved_ids)

    def test_bottleneck_wrong_map_ref_is_refused(self):
        map_doc = _load("legacy_map.yaml")
        bottleneck = _load("bottleneck.yaml")
        bottleneck["institutional_bottleneck"]["system_map_ref"] = "map-that-does-not-exist"
        report = check_chain_integrity(map_doc=map_doc, bottleneck_docs=[bottleneck])
        self.assertEqual(report.verdict, "REFUSED")
        self.assertTrue(any(f.check == "bottleneck_system_map_ref" for f in report.findings))

    def test_candidate_citing_nonexistent_bottleneck_is_refused(self):
        bottleneck = _load("bottleneck.yaml")
        candidate = _load("automation_candidate.yaml")
        candidate["automation_candidate"]["bottleneck_ref"] = "bottleneck-that-does-not-exist"
        report = check_chain_integrity(bottleneck_docs=[bottleneck], candidate_docs=[candidate])
        self.assertEqual(report.verdict, "REFUSED")
        self.assertTrue(any(f.check == "candidate_bottleneck_ref" for f in report.findings))

    def test_pilot_citing_nonexistent_candidate_is_refused(self):
        candidate = _load("automation_candidate.yaml")
        pilot = _load("pilot_simulation.yaml")
        pilot["pilot_simulation"]["automation_candidate_ref"] = "candidate-that-does-not-exist"
        report = check_chain_integrity(candidate_docs=[candidate], pilot_docs=[pilot])
        self.assertEqual(report.verdict, "REFUSED")
        self.assertTrue(any(f.check == "pilot_candidate_ref" for f in report.findings))

    def test_pilot_citing_nonexistent_rollback_is_refused(self):
        rollback = _load("rollback_contract.yaml")
        pilot = _load("pilot_simulation.yaml")
        pilot["pilot_simulation"]["rollback_plan_ref"] = "rollback-that-does-not-exist"
        report = check_chain_integrity(rollback_docs=[rollback], pilot_docs=[pilot])
        self.assertEqual(report.verdict, "REFUSED")
        self.assertTrue(any(f.check == "pilot_rollback_ref" for f in report.findings))

    def test_pilot_citing_nonexistent_measurement_is_refused(self):
        measurement = _load("before_after_measurement.yaml")
        pilot = _load("pilot_simulation.yaml")
        pilot["pilot_simulation"]["measurement_plan_ref"] = "measurement-that-does-not-exist"
        report = check_chain_integrity(measurement_docs=[measurement], pilot_docs=[pilot])
        self.assertEqual(report.verdict, "REFUSED")
        self.assertTrue(any(f.check == "pilot_measurement_ref" for f in report.findings))

    def test_measurement_citing_nonexistent_pilot_is_refused(self):
        measurement = _load("before_after_measurement.yaml")
        measurement["before_after_measurement"]["pilot_simulation_ref"] = "pilot-that-does-not-exist"
        pilot = _load("pilot_simulation.yaml")
        report = check_chain_integrity(measurement_docs=[measurement], pilot_docs=[pilot])
        self.assertEqual(report.verdict, "REFUSED")
        self.assertTrue(any(f.check == "measurement_pilot_ref" for f in report.findings))
        self.assertIn("pilot-that-does-not-exist", report.findings[0].involved_ids)

    def test_measurement_pilot_ref_not_checked_without_pilot_docs_supplied(self):
        """Absence of pilot_docs must not itself trigger a finding —
        mirrors TestPartialInputsDoNotFalsePositive's existing pattern
        for every other _ref check in this file."""
        measurement = _load("before_after_measurement.yaml")
        report = check_chain_integrity(measurement_docs=[measurement])
        self.assertEqual(report.verdict, "INTACT")
        self.assertEqual(report.findings, [])

    def test_multiple_broken_references_all_reported_not_just_first(self):
        map_doc = _load("legacy_map.yaml")
        bottleneck = _load("bottleneck.yaml")
        bottleneck["institutional_bottleneck"]["involved_node_ids"] = ["nope"]
        bottleneck["institutional_bottleneck"]["system_map_ref"] = "nope-map"
        report = check_chain_integrity(map_doc=map_doc, bottleneck_docs=[bottleneck])
        self.assertEqual(report.verdict, "REFUSED")
        self.assertEqual(len(report.findings), 2)


class TestPartialInputsDoNotFalsePositive(unittest.TestCase):
    """Absence of a document type must not itself trigger findings — a
    checker run with only a map and no bottlenecks yet is not broken."""

    def test_map_only_is_intact(self):
        report = check_chain_integrity(map_doc=_load("legacy_map.yaml"))
        self.assertEqual(report.verdict, "INTACT")

    def test_no_documents_at_all_is_intact(self):
        report = check_chain_integrity()
        self.assertEqual(report.verdict, "INTACT")
        self.assertEqual(report.findings, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
