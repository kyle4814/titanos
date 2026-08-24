"""Tests for rpa/validators/validate_value_flow.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from rpa.validators.validate_value_flow import validate_value_flow  # noqa: E402

VALID_DOC = """
value_flow:
  id: "vf-001"
  system_map_ref: "map-legacy-2026"
  period: "2026-Q3"
  value_created:
    - source: "widget sales"
      amount_description: "approx $500k in gross revenue"
  necessary_consumption:
    - category: "STAFF"
      amount_description: "approx $150k payroll"
      basis: "core operating team required to deliver the product"
    - category: "INFRASTRUCTURE"
      amount_description: "approx $20k cloud hosting"
      basis: "production systems must run somewhere"
  extractions:
    - id: "ext-001"
      recipient: "Founder A"
      reason: "quarterly distribution per shareholder agreement"
      authority: "shareholder agreement clause 4.2"
      contribution: "product strategy and technical leadership this quarter"
      limit: "capped at 10% of net margin per agreement"
      audit_mechanism: "reviewed by external accountant each quarter"
      reviewable: true
  reinvestment:
    - target: "R&D — next-gen widget"
      amount_description: "approx $80k"
      rationale: "maintain product competitiveness"
  reserved:
    - purpose: "emergency operating buffer"
      amount_description: "approx $30k"
  returned:
    - recipient: "early customer rebate pool"
      amount_description: "approx $5k"
      basis: "loyalty program terms"
  undeclared_leakage_flag: false
"""


def _get(res, rule, warnings=False):
    pool = res.warnings if warnings else res.issues
    return [i for i in pool if i.rule == rule]


class TestValidValueFlow(unittest.TestCase):
    def test_well_formed_document_is_valid(self):
        res = validate_value_flow(VALID_DOC)
        self.assertEqual(res.status, "VALID", msg=res.issues)
        self.assertEqual(res.value_flow_id, "vf-001")
        self.assertEqual(res.issues, [])
        self.assertEqual(res.warnings, [])


class TestMalformedYaml(unittest.TestCase):
    def test_unparseable_yaml_is_invalid(self):
        res = validate_value_flow("value_flow: [unterminated")
        self.assertEqual(res.status, "INVALID")
        self.assertTrue(_get(res, "VF-R-1"))

    def test_duplicate_keys_rejected(self):
        doc = """
value_flow:
  id: "vf-dup"
  id: "vf-dup-2"
  system_map_ref: "m"
  period: "2026-Q3"
  value_created: []
  necessary_consumption:
    - category: "STAFF"
      amount_description: "x"
      basis: "y"
  extractions: []
  reinvestment: []
  reserved: []
  returned: []
  undeclared_leakage_flag: false
"""
        res = validate_value_flow(doc)
        self.assertEqual(res.status, "INVALID")
        self.assertTrue(_get(res, "VF-R-1"))

    def test_deep_alias_recursion_does_not_crash(self):
        lines = ["value_flow:", "  id: &a0 x"]
        prev = "a0"
        for i in range(1, 60):
            lines.append(f"  n{i}: &a{i} [*{prev}, *{prev}]")
            prev = f"a{i}"
        doc = "\n".join(lines)
        try:
            res = validate_value_flow(doc)
        except Exception as e:  # noqa: BLE001
            self.fail(f"validate_value_flow raised instead of failing closed: {e}")
        self.assertEqual(res.status, "INVALID")

    def test_non_string_keys_rejected(self):
        doc = """
value_flow:
  id: "vf-003"
  true: "weird key"
  system_map_ref: "m"
  period: "2026-Q3"
  value_created: []
  necessary_consumption:
    - category: "STAFF"
      amount_description: "x"
      basis: "y"
  extractions: []
  reinvestment: []
  reserved: []
  returned: []
  undeclared_leakage_flag: false
"""
        res = validate_value_flow(doc)
        self.assertTrue(_get(res, "VF-R-3"))


class TestStructuralRules(unittest.TestCase):
    def test_missing_top_level_wrapper(self):
        res = validate_value_flow("foo: bar")
        self.assertEqual(res.status, "INVALID")
        self.assertTrue(_get(res, "VF-R-2"))

    def test_missing_required_fields(self):
        res = validate_value_flow("value_flow:\n  id: \"vf-004\"\n")
        self.assertEqual(res.status, "INVALID")
        missing_fields = {i.where for i in _get(res, "VF-R-4")}
        self.assertIn("value_flow.system_map_ref", missing_fields)
        self.assertIn("value_flow.necessary_consumption", missing_fields)

    def test_empty_necessary_consumption_rejected(self):
        doc = VALID_DOC.replace(
            '  necessary_consumption:\n'
            '    - category: "STAFF"\n'
            '      amount_description: "approx $150k payroll"\n'
            '      basis: "core operating team required to deliver the product"\n'
            '    - category: "INFRASTRUCTURE"\n'
            '      amount_description: "approx $20k cloud hosting"\n'
            '      basis: "production systems must run somewhere"\n',
            "  necessary_consumption: []\n",
        )
        res = validate_value_flow(doc)
        self.assertEqual(res.status, "INVALID")
        self.assertTrue(_get(res, "VF-R-6"))

    def test_invalid_necessary_consumption_category_rejected(self):
        doc = VALID_DOC.replace('category: "STAFF"', 'category: "MADE_UP_CATEGORY"')
        res = validate_value_flow(doc)
        self.assertEqual(res.status, "INVALID")
        self.assertTrue(_get(res, "VF-R-7"))


class TestExtractionSixQuestions(unittest.TestCase):
    """VF-R-9 — the core rule. Independently prove several different
    missing fields are each caught, not just one happy-path case."""

    def _remove_extraction_field(self, field_name: str) -> str:
        lines = VALID_DOC.splitlines()
        out = []
        skip_line_prefix = f"      {field_name}:"
        for line in lines:
            if line.strip().startswith(f"{field_name}:"):
                continue
            out.append(line)
        return "\n".join(out)

    def test_missing_recipient_rejected(self):
        doc = self._remove_extraction_field("recipient")
        res = validate_value_flow(doc)
        self.assertEqual(res.status, "INVALID")
        rule9 = _get(res, "VF-R-9")
        self.assertTrue(any("recipient" in i.what for i in rule9))

    def test_missing_authority_rejected(self):
        doc = self._remove_extraction_field("authority")
        res = validate_value_flow(doc)
        self.assertEqual(res.status, "INVALID")
        rule9 = _get(res, "VF-R-9")
        self.assertTrue(any("authority" in i.what for i in rule9))

    def test_missing_audit_mechanism_rejected(self):
        doc = self._remove_extraction_field("audit_mechanism")
        res = validate_value_flow(doc)
        self.assertEqual(res.status, "INVALID")
        rule9 = _get(res, "VF-R-9")
        self.assertTrue(any("audit_mechanism" in i.what for i in rule9))

    def test_missing_limit_rejected(self):
        doc = self._remove_extraction_field("limit")
        res = validate_value_flow(doc)
        self.assertEqual(res.status, "INVALID")
        rule9 = _get(res, "VF-R-9")
        self.assertTrue(any("limit" in i.what for i in rule9))

    def test_blank_reason_rejected(self):
        doc = VALID_DOC.replace(
            'reason: "quarterly distribution per shareholder agreement"',
            'reason: "   "',
        )
        res = validate_value_flow(doc)
        self.assertEqual(res.status, "INVALID")
        self.assertTrue(_get(res, "VF-R-9"))

    def test_all_six_fields_present_and_reviewable_passes(self):
        res = validate_value_flow(VALID_DOC)
        self.assertEqual(res.status, "VALID", msg=res.issues)


class TestReviewableWarning(unittest.TestCase):
    def test_reviewable_false_is_warning_not_fatal(self):
        doc = VALID_DOC.replace("reviewable: true", "reviewable: false")
        res = validate_value_flow(doc)
        self.assertEqual(res.status, "VALID", msg=res.issues)
        self.assertTrue(_get(res, "VF-R-10", warnings=True))

    def test_reviewable_non_bool_is_error(self):
        doc = VALID_DOC.replace("reviewable: true", 'reviewable: "yes"')
        res = validate_value_flow(doc)
        self.assertEqual(res.status, "INVALID")
        self.assertTrue(_get(res, "VF-R-9"))


class TestLeakageConsistency(unittest.TestCase):
    def test_true_flag_without_description_rejected(self):
        doc = VALID_DOC.replace(
            "undeclared_leakage_flag: false", "undeclared_leakage_flag: true"
        )
        res = validate_value_flow(doc)
        self.assertEqual(res.status, "INVALID")
        self.assertTrue(_get(res, "VF-R-12"))

    def test_true_flag_with_description_accepted(self):
        doc = VALID_DOC.replace(
            "undeclared_leakage_flag: false",
            'undeclared_leakage_flag: true\n  leakage_description: "unaccounted vendor rebate discovered in audit"',
        )
        res = validate_value_flow(doc)
        self.assertEqual(res.status, "VALID", msg=res.issues)

    def test_false_flag_with_description_rejected(self):
        doc = VALID_DOC.replace(
            "undeclared_leakage_flag: false",
            'undeclared_leakage_flag: false\n  leakage_description: "should not be here"',
        )
        res = validate_value_flow(doc)
        self.assertEqual(res.status, "INVALID")
        self.assertTrue(_get(res, "VF-R-12"))


class TestFailClosed(unittest.TestCase):
    def test_non_string_input_type_does_not_crash(self):
        try:
            res = validate_value_flow(None)  # type: ignore[arg-type]
        except Exception as e:  # noqa: BLE001
            self.fail(f"validate_value_flow raised instead of failing closed: {e}")
        self.assertEqual(res.status, "INVALID")
        self.assertTrue(_get(res, "VF-R-0"))


if __name__ == "__main__":
    unittest.main()
