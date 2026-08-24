"""Tests for rpa/validators/validate_bottleneck.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from rpa.validators.validate_bottleneck import validate_bottleneck  # noqa: E402

VALID_DOC = """
institutional_bottleneck:
  id: "bn-001"
  system_map_ref: "map-legacy-2026"
  involved_node_ids:
    - "node-finance-approvals"
    - "node-cfo-signoff"
  bottleneck_type: "KEY_PERSON_DEPENDENCY"
  epistemic_status: "EVIDENCE_SUPPORTED_MODEL"
  evidence:
    - "72-hour median delay observed across 40 approval tickets, Q2 2026"
  estimated_impact:
    value_at_risk: "approx $2M/quarter in delayed vendor payments"
    delay_contribution: "adds 3-5 business days to every approval over $50k"
    failure_propagation_scope:
      - "vendor payment SLA breach"
      - "downstream procurement backlog"
  assumptions:
    - "approval volume remains at current levels"
  unknowns:
    - "whether a delegated-authority policy already exists but is unused"
  recommended_next_step: "interview the CFO's office to measure actual queue time and identify delegation options"
"""


def _get(res, rule):
    return [i for i in res.issues if i.rule == rule]


class TestValidBottleneck(unittest.TestCase):
    def test_well_formed_document_is_valid(self):
        res = validate_bottleneck(VALID_DOC)
        self.assertEqual(res.status, "VALID", msg=res.issues)
        self.assertEqual(res.bottleneck_id, "bn-001")
        self.assertEqual(res.issues, [])


class TestMalformedYaml(unittest.TestCase):
    def test_unparseable_yaml_is_invalid(self):
        res = validate_bottleneck("institutional_bottleneck: [unterminated")
        self.assertEqual(res.status, "INVALID")
        self.assertTrue(_get(res, "BN-R-1"))

    def test_duplicate_keys_rejected(self):
        doc = """
institutional_bottleneck:
  id: "bn-002"
  id: "bn-002-dup"
  system_map_ref: "m"
  involved_node_ids: ["n1"]
  bottleneck_type: "SINGLE_POINT_OF_FAILURE"
  epistemic_status: "UNKNOWN"
  estimated_impact:
    value_at_risk: "x"
    delay_contribution: "y"
    failure_propagation_scope: []
  assumptions: []
  unknowns: []
  recommended_next_step: "investigate further"
"""
        res = validate_bottleneck(doc)
        self.assertEqual(res.status, "INVALID")
        self.assertTrue(_get(res, "BN-R-1"))

    def test_deep_alias_recursion_does_not_crash(self):
        # F-009-style adversarial alias fan-out — must be rejected, never raise.
        lines = ["institutional_bottleneck:", "  id: &a0 x"]
        prev = "a0"
        for i in range(1, 60):
            lines.append(f"  n{i}: &a{i} [*{prev}, *{prev}]")
            prev = f"a{i}"
        doc = "\n".join(lines)
        try:
            res = validate_bottleneck(doc)
        except Exception as e:  # noqa: BLE001
            self.fail(f"validate_bottleneck raised instead of failing closed: {e}")
        self.assertEqual(res.status, "INVALID")

    def test_non_string_keys_rejected(self):
        doc = """
institutional_bottleneck:
  id: "bn-003"
  true: "weird key"
  system_map_ref: "m"
  involved_node_ids: ["n1"]
  bottleneck_type: "SINGLE_POINT_OF_FAILURE"
  epistemic_status: "UNKNOWN"
  estimated_impact:
    value_at_risk: "x"
    delay_contribution: "y"
    failure_propagation_scope: []
  assumptions: []
  unknowns: []
  recommended_next_step: "investigate further"
"""
        res = validate_bottleneck(doc)
        self.assertTrue(_get(res, "BN-R-3"))


class TestStructuralRules(unittest.TestCase):
    def test_missing_top_level_wrapper(self):
        res = validate_bottleneck("foo: bar")
        self.assertEqual(res.status, "INVALID")
        self.assertTrue(_get(res, "BN-R-2"))

    def test_missing_required_fields(self):
        res = validate_bottleneck("institutional_bottleneck:\n  id: \"bn-004\"\n")
        self.assertEqual(res.status, "INVALID")
        missing_rules = _get(res, "BN-R-4")
        missing_fields = {i.where for i in missing_rules}
        self.assertIn("institutional_bottleneck.system_map_ref", missing_fields)
        self.assertIn("institutional_bottleneck.bottleneck_type", missing_fields)

    def test_empty_involved_node_ids_rejected(self):
        doc = VALID_DOC.replace(
            '  involved_node_ids:\n    - "node-finance-approvals"\n    - "node-cfo-signoff"\n',
            "  involved_node_ids: []\n",
        )
        res = validate_bottleneck(doc)
        self.assertEqual(res.status, "INVALID")
        self.assertTrue(_get(res, "BN-R-6"))

    def test_blank_node_id_entry_rejected(self):
        doc = VALID_DOC.replace(
            '    - "node-cfo-signoff"', '    - "   "'
        )
        res = validate_bottleneck(doc)
        self.assertEqual(res.status, "INVALID")
        self.assertTrue(_get(res, "BN-R-6"))

    def test_invalid_bottleneck_type_rejected(self):
        doc = VALID_DOC.replace(
            'bottleneck_type: "KEY_PERSON_DEPENDENCY"', 'bottleneck_type: "MADE_UP_TYPE"'
        )
        res = validate_bottleneck(doc)
        self.assertEqual(res.status, "INVALID")
        self.assertTrue(_get(res, "BN-R-7"))

    def test_invalid_epistemic_status_rejected(self):
        doc = VALID_DOC.replace(
            'epistemic_status: "EVIDENCE_SUPPORTED_MODEL"',
            'epistemic_status: "TOTALLY_SURE"',
        )
        res = validate_bottleneck(doc)
        self.assertEqual(res.status, "INVALID")
        self.assertTrue(_get(res, "BN-R-8"))

    def test_valid_epistemic_status_from_shared_vocabulary(self):
        doc = VALID_DOC.replace(
            'epistemic_status: "EVIDENCE_SUPPORTED_MODEL"',
            'epistemic_status: "ARCHITECTURAL_METAPHOR"',
        ).replace(
            "  evidence:\n    - \"72-hour median delay observed across 40 approval tickets, Q2 2026\"\n",
            "  evidence: []\n",
        )
        res = validate_bottleneck(doc)
        # ARCHITECTURAL_METAPHOR is not in EVIDENCE_REQUIRED_CLASSIFICATIONS,
        # so an empty evidence list must not trip BN-R-10.
        self.assertFalse(_get(res, "BN-R-10"))


class TestNextStepActionVerbBlocklist(unittest.TestCase):
    def test_automate_verb_rejected(self):
        doc = VALID_DOC.replace(
            'recommended_next_step: "interview the CFO\'s office to measure actual queue time and identify delegation options"',
            'recommended_next_step: "automate the approval step immediately"',
        )
        res = validate_bottleneck(doc)
        self.assertEqual(res.status, "INVALID")
        self.assertTrue(_get(res, "BN-R-9"))

    def test_deploy_verb_rejected(self):
        doc = VALID_DOC.replace(
            'recommended_next_step: "interview the CFO\'s office to measure actual queue time and identify delegation options"',
            'recommended_next_step: "deploy a bot to replace the approver"',
        )
        res = validate_bottleneck(doc)
        self.assertEqual(res.status, "INVALID")
        self.assertTrue(_get(res, "BN-R-9"))

    def test_investigation_phrasing_accepted(self):
        doc = VALID_DOC.replace(
            'recommended_next_step: "interview the CFO\'s office to measure actual queue time and identify delegation options"',
            'recommended_next_step: "measure queue times over the next 30 days and interview stakeholders"',
        )
        res = validate_bottleneck(doc)
        self.assertEqual(res.status, "VALID", msg=res.issues)

    def test_word_boundary_not_falsely_triggered(self):
        # "deployment" contains "deploy" as a substring but not as a whole
        # word match against the blocklist entry "deploy" — must NOT trip.
        doc = VALID_DOC.replace(
            'recommended_next_step: "interview the CFO\'s office to measure actual queue time and identify delegation options"',
            'recommended_next_step: "review historical deployment records from the archive team"',
        )
        res = validate_bottleneck(doc)
        self.assertFalse(_get(res, "BN-R-9"))


class TestEvidenceRequirement(unittest.TestCase):
    def test_verified_fact_without_evidence_rejected(self):
        doc = VALID_DOC.replace(
            'epistemic_status: "EVIDENCE_SUPPORTED_MODEL"', 'epistemic_status: "VERIFIED_FACT"'
        ).replace(
            "  evidence:\n    - \"72-hour median delay observed across 40 approval tickets, Q2 2026\"\n",
            "  evidence: []\n",
        )
        res = validate_bottleneck(doc)
        self.assertEqual(res.status, "INVALID")
        self.assertTrue(_get(res, "BN-R-10"))

    def test_speculative_hypothesis_without_evidence_ok(self):
        doc = VALID_DOC.replace(
            'epistemic_status: "EVIDENCE_SUPPORTED_MODEL"',
            'epistemic_status: "SPECULATIVE_HYPOTHESIS"',
        ).replace(
            "  evidence:\n    - \"72-hour median delay observed across 40 approval tickets, Q2 2026\"\n",
            "  evidence: []\n",
        )
        res = validate_bottleneck(doc)
        self.assertEqual(res.status, "VALID", msg=res.issues)


class TestFailClosed(unittest.TestCase):
    def test_non_string_input_type_does_not_crash(self):
        # Bypass type hints deliberately to exercise fail-closed wrapper.
        try:
            res = validate_bottleneck(None)  # type: ignore[arg-type]
        except Exception as e:  # noqa: BLE001
            self.fail(f"validate_bottleneck raised instead of failing closed: {e}")
        self.assertEqual(res.status, "INVALID")
        self.assertTrue(_get(res, "BN-R-0"))


if __name__ == "__main__":
    unittest.main()
