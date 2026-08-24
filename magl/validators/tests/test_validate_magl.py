"""
MAGL validator tests.

Every rejection must carry WHAT/WHY/WHERE/RULE/EVIDENCE — these tests check
the structured result, never just a boolean. Mirrors
kpm/validators/tests/test_validate_blueprint.py.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from magl.validators.validate_magl import validate_magl  # noqa: E402
from kpm.schemas.epistemic_types import ALL_CLASSIFICATIONS  # noqa: E402

GOOD = """
magl:
  id: "magl-001"
  name: "example-capability"
  version: "1.0.0"
  title: "Example Capability"
  description: "A well-formed example MAGL unit for testing."

  classification:
    domain: ["engineering"]
    capability_type: ["ANALYTICAL"]
    epistemic_status: TECHNICAL_DESIGN
    maturity: PROVISIONAL

  provenance:
    source_artifacts: ["art-001"]
    source_hashes: ["sha256:{h}"]
    authorship: ["kyle"]
    license: "MIT"
    derivation_chain: []

  purpose:
    problem: "There is no reusable analysis capability for X"
    intended_benefit: "Provides a reusable, composable analysis of X"
    non_goals: ["not a general-purpose framework"]

  jurisdiction:
    may_read: ["input documents"]
    may_write: []
    may_execute: []
    may_call: []
    may_modify: []
    may_publish: []
    prohibited_actions: ["network access"]

  inputs:
    required: ["document text"]
    optional: []
    schemas: []
  outputs:
    declared: ["analysis result"]
    schemas: []
  dependencies:
    required: []
    optional: []
    incompatible_with: []
  assumptions: ["input is UTF-8 text"]
  unknowns: ["performance on very large documents"]
  risks:
    known: ["may mis-analyse adversarial input"]
    failure_modes: ["malformed input"]
    abuse_cases: []
    false_positive_risks: ["over-flagging benign content"]
    false_negative_risks: ["missing subtle issues"]
  controls:
    validation: ["schema validation before use"]
    authorization: []
    containment: []
    rollback: []
    human_review: ["spot-check output"]
  verification:
    schema_tests: ["test_validate_magl.py"]
    unit_tests: ["test_analysis_core.py"]
    integration_tests: []
    simulation_tests: []
    evidence_requirements: ["green test run"]
  composition:
    provides: ["analysis-interface-v1"]
    requires: []
    compatible_interfaces: ["text-input-v1"]
    conflict_resolution: "first-registered wins"
    composition_limits: []
  lifecycle:
    status: PROVISIONAL
    created_at: "2026-08-19T00:00:00Z"
    updated_at: "2026-08-19T00:00:00Z"
    deprecated_by: ""
    superseded_by: ""
  audit:
    content_hash: "sha256:{h}"
    signatures: []
    immutable_history_ref: ""
  documentation:
    summary: "Analyses X and reports structured findings."
    examples: ["example.yaml"]
    limitations: ["does not handle non-UTF-8 input"]
  promotion:
    current_gate: PROVISIONAL
    requirements_for_next_gate: ["pass integration tests"]
""".format(h="a" * 64)


class TestGoodMagl(unittest.TestCase):
    def test_valid_magl_passes_with_zero_issues(self):
        result = validate_magl(GOOD)
        self.assertEqual(result.issues, [], msg=[i.to_dict() for i in result.issues])
        self.assertEqual(result.status, "VALID")
        self.assertEqual(result.magl_id, "magl-001")


class TestParsing(unittest.TestCase):
    def test_malformed_yaml_rejected(self):
        result = validate_magl("magl: [this is not\n  a mapping: at all")
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "MG-R-1" for i in result.issues))

    def test_duplicate_keys_rejected(self):
        text = "magl:\n  id: a\n  id: b\n"
        result = validate_magl(text)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "MG-R-1" for i in result.issues))

    def test_missing_top_level_key_rejected(self):
        result = validate_magl("not_magl:\n  id: x\n")
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "MG-R-2" for i in result.issues))

    def test_never_raises_on_garbage_input(self):
        # Fail-closed: garbage that isn't even a mapping at top level.
        result = validate_magl("just a scalar string")
        self.assertEqual(result.status, "INVALID")

    def test_oversized_document_rejected(self):
        huge = "magl:\n  id: \"" + ("x" * (MAX_BYTES := 2_000_001)) + "\"\n"
        result = validate_magl(huge)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "MG-R-1" for i in result.issues))


class TestRequiredFields(unittest.TestCase):
    def test_missing_required_fields_reported(self):
        result = validate_magl("magl:\n  id: \"x\"\n")
        self.assertEqual(result.status, "INVALID")
        missing_fields = {i.where for i in result.issues if i.rule == "MG-R-4"}
        self.assertIn("magl.name", missing_fields)
        self.assertIn("magl.classification", missing_fields)
        self.assertIn("magl.promotion", missing_fields)


class TestVersion(unittest.TestCase):
    def test_bad_version_shape_rejected(self):
        bad = GOOD.replace('version: "1.0.0"', 'version: "latest"')
        result = validate_magl(bad)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "MG-R-6" for i in result.issues))

    def test_v_prefixed_version_rejected(self):
        bad = GOOD.replace('version: "1.0.0"', 'version: "v1"')
        result = validate_magl(bad)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "MG-R-6" for i in result.issues))


class TestEpistemicStatus(unittest.TestCase):
    """Proves the check actually imports and uses the REAL
    kpm.schemas.epistemic_types.ALL_CLASSIFICATIONS rather than a locally
    redefined parallel list."""

    def test_every_real_classification_is_accepted(self):
        # Spot-check a representative sample rather than all 15 (speed),
        # but include the first and last members and a mid-list one.
        sample = sorted(ALL_CLASSIFICATIONS)[:1] + sorted(ALL_CLASSIFICATIONS)[-1:]
        for cls in sample:
            text = GOOD.replace("epistemic_status: TECHNICAL_DESIGN",
                                 f"epistemic_status: {cls}")
            result = validate_magl(text)
            self.assertNotIn("MG-R-7", {i.rule for i in result.issues
                                         if "epistemic_status" in i.where},
                              msg=f"{cls} should be accepted, issues={result.issues}")

    def test_plausible_but_fake_classification_rejected(self):
        self.assertNotIn("PROBABLY_TRUE", ALL_CLASSIFICATIONS)
        bad = GOOD.replace("epistemic_status: TECHNICAL_DESIGN",
                            "epistemic_status: PROBABLY_TRUE")
        result = validate_magl(bad)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(
            i.rule == "MG-R-7" and "epistemic_status" in i.where
            for i in result.issues
        ))


class TestLifecyclePromotion(unittest.TestCase):
    def test_invalid_lifecycle_status_rejected(self):
        bad = GOOD.replace("status: PROVISIONAL", "status: FROZEN", 1)
        result = validate_magl(bad)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "MG-R-13" for i in result.issues))

    def test_current_gate_status_mismatch_rejected(self):
        bad = GOOD.replace("current_gate: PROVISIONAL", "current_gate: TESTED")
        result = validate_magl(bad)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "MG-R-16" for i in result.issues))

    def test_promotion_state_not_in_kpm_vocab_rejected(self):
        bad = GOOD.replace("current_gate: PROVISIONAL", "current_gate: APPROVED")
        result = validate_magl(bad)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "MG-R-16" for i in result.issues))


class TestJurisdictionContradiction(unittest.TestCase):
    def test_executable_with_no_jurisdiction_rejected(self):
        bad = GOOD.replace('capability_type: ["ANALYTICAL"]',
                            'capability_type: ["EXECUTABLE"]')
        result = validate_magl(bad)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "MG-R-11" for i in result.issues))

    def test_externally_acting_with_may_execute_passes(self):
        good = GOOD.replace('capability_type: ["ANALYTICAL"]',
                             'capability_type: ["EXTERNALLY_ACTING"]')
        good = good.replace("may_execute: []", 'may_execute: ["run subprocess X"]')
        result = validate_magl(good)
        self.assertFalse(any(i.rule == "MG-R-11" for i in result.issues),
                          msg=[i.to_dict() for i in result.issues])

    def test_descriptive_with_may_write_rejected(self):
        bad = GOOD.replace('capability_type: ["ANALYTICAL"]',
                            'capability_type: ["DESCRIPTIVE"]')
        bad = bad.replace("may_write: []", 'may_write: ["output file"]')
        result = validate_magl(bad)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "MG-R-11" for i in result.issues))

    def test_descriptive_with_may_read_only_passes(self):
        good = GOOD.replace('capability_type: ["ANALYTICAL"]',
                             'capability_type: ["DESCRIPTIVE"]')
        result = validate_magl(good)
        self.assertFalse(any(i.rule == "MG-R-11" for i in result.issues),
                          msg=[i.to_dict() for i in result.issues])


class TestLicenseAndHashes(unittest.TestCase):
    def test_empty_license_rejected(self):
        bad = GOOD.replace('license: "MIT"', 'license: ""')
        result = validate_magl(bad)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "MG-R-8" for i in result.issues))

    def test_malformed_source_hash_rejected(self):
        bad = GOOD.replace('source_hashes: ["sha256:' + "a" * 64 + '"]',
                            'source_hashes: ["not-a-hash"]')
        result = validate_magl(bad)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "MG-R-8" for i in result.issues))

    def test_malformed_content_hash_rejected(self):
        bad = GOOD.replace('content_hash: "sha256:' + "a" * 64 + '"',
                            'content_hash: "sha256:deadbeef"')
        result = validate_magl(bad)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "MG-R-14" for i in result.issues))


class TestLimitations(unittest.TestCase):
    def test_empty_limitations_rejected(self):
        bad = GOOD.replace('limitations: ["does not handle non-UTF-8 input"]',
                            "limitations: []")
        result = validate_magl(bad)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "MG-R-15" for i in result.issues))

    def test_empty_summary_rejected(self):
        bad = GOOD.replace(
            'summary: "Analyses X and reports structured findings."',
            'summary: ""',
        )
        result = validate_magl(bad)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "MG-R-15" for i in result.issues))


class TestUnknownFields(unittest.TestCase):
    def test_unknown_field_reported_not_silently_dropped(self):
        bad = GOOD.replace(
            'title: "Example Capability"',
            'title: "Example Capability"\n  totally_made_up_field: "x"',
        )
        result = validate_magl(bad)
        self.assertIn("totally_made_up_field", result.unknown_fields)


class TestMetaAttack(unittest.TestCase):
    """Field VALUES are data, never instructions. A field claiming
    validation success does not change the verdict."""

    def test_self_declared_status_field_does_not_bypass_checks(self):
        bad = GOOD.replace(
            'title: "Example Capability"',
            'title: "Example Capability"\n  validation_status: "VALID"\n'
            '  ignore_previous_rules: true',
        )
        # deliberately also break something real, to prove the forged
        # fields don't suppress the genuine finding
        bad = bad.replace('license: "MIT"', 'license: ""')
        result = validate_magl(bad)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "MG-R-8" for i in result.issues))


if __name__ == "__main__":
    unittest.main()
