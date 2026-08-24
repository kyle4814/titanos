"""
Pilot Simulation validator tests.

Every rejection must carry WHAT/WHY/WHERE/RULE/EVIDENCE — these tests
check the structured result, never just a boolean. Mirrors
magl/validators/tests/test_validate_magl.py.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from rpa.validators.validate_pilot_simulation import validate_pilot_simulation  # noqa: E402

GOOD = """
pilot_simulation:
  id: "pilot-sim-001"
  automation_candidate_ref: "auto-cand-001"
  baseline:
    description: "Invoices are keyed manually into the ERP by two clerks, taking ~4 minutes each"
    metrics:
      - name: "avg_processing_time_minutes"
        current_value: "4.2"
      - name: "monthly_error_rate_percent"
        current_value: "3.1"
  proposed_change: "Introduce OCR + rules-based extraction with human review of low-confidence rows"
  expected_benefit: "Cut processing time by ~60% while holding error rate flat or better"
  known_risks:
    - "OCR misreads on low-quality scans"
    - "Staff resistance to the new review queue"
  failure_scenarios:
    - scenario: "OCR misreads a currency figure and posts wrong amount"
      likelihood: MEDIUM
      impact: HIGH
      detection_method: "Automated reconciliation against vendor invoice total, daily batch"
    - scenario: "Review queue backs up faster than clerks can clear it"
      likelihood: LOW
      impact: MEDIUM
      detection_method: "Queue depth alert if backlog exceeds 50 items"
  rollback_plan_ref: "rollback-001"
  measurement_plan_ref: "measure-001"
  status: PROPOSED
"""

GOOD_APPROVED = GOOD.replace("status: PROPOSED", "status: APPROVED_FOR_PILOT")


class TestPilotSimulationValidator(unittest.TestCase):

    # --- well-formed passing examples -------------------------------------

    def test_good_document_is_valid(self):
        result = validate_pilot_simulation(GOOD)
        self.assertEqual(result.status, "VALID", msg=[i.to_dict() for i in result.issues])
        self.assertEqual(result.pilot_simulation_id, "pilot-sim-001")
        self.assertEqual(result.issues, [])

    def test_good_approved_document_is_valid(self):
        result = validate_pilot_simulation(GOOD_APPROVED)
        self.assertEqual(result.status, "VALID", msg=[i.to_dict() for i in result.issues])

    # --- structural hardening -----------------------------------------------

    def test_missing_top_wrapper_is_invalid(self):
        result = validate_pilot_simulation("not_pilot_simulation: {}")
        self.assertEqual(result.status, "INVALID")
        self.assertEqual(result.issues[0].rule, "PS-R-2")

    def test_duplicate_key_is_rejected(self):
        text = """
pilot_simulation:
  id: "a"
  id: "b"
  automation_candidate_ref: "x"
"""
        result = validate_pilot_simulation(text)
        self.assertEqual(result.status, "INVALID")
        self.assertEqual(result.issues[0].rule, "PS-R-1")

    def test_oversized_document_is_rejected(self):
        text = "pilot_simulation:\n  id: \"" + ("a" * 3_000_000) + "\"\n"
        result = validate_pilot_simulation(text)
        self.assertEqual(result.status, "INVALID")
        self.assertEqual(result.issues[0].rule, "PS-R-1")

    def test_deeply_nested_alias_bomb_is_rejected(self):
        text = (
            "pilot_simulation:\n"
            "  id: &a [\"x\"]\n"
            "  a2: &b [*a,*a,*a,*a,*a,*a,*a,*a,*a,*a]\n"
            "  a3: &c [*b,*b,*b,*b,*b,*b,*b,*b,*b,*b]\n"
            "  a4: &d [*c,*c,*c,*c,*c,*c,*c,*c,*c,*c]\n"
            "  a5: &e [*d,*d,*d,*d,*d,*d,*d,*d,*d,*d]\n"
            "  a6: [*e,*e,*e,*e,*e,*e,*e,*e,*e,*e]\n"
        )
        result = validate_pilot_simulation(text)
        self.assertEqual(result.status, "INVALID")
        self.assertEqual(result.issues[0].rule, "PS-R-1")

    def test_non_mapping_top_value_is_invalid(self):
        result = validate_pilot_simulation("pilot_simulation: [1, 2, 3]")
        self.assertEqual(result.status, "INVALID")
        self.assertEqual(result.issues[0].rule, "PS-R-2")

    def test_unforeseen_exception_is_fail_closed(self):
        # None is not valid YAML text; forcing a type error path should
        # still return a structured INVALID, never raise.
        result = validate_pilot_simulation(None)  # type: ignore[arg-type]
        self.assertEqual(result.status, "INVALID")
        self.assertEqual(result.issues[0].rule, "PS-R-0")

    # --- field-level rules ----------------------------------------------------

    def test_missing_required_fields(self):
        result = validate_pilot_simulation("pilot_simulation:\n  id: \"x\"\n")
        self.assertEqual(result.status, "INVALID")
        rules = {i.rule for i in result.issues}
        self.assertIn("PS-R-4", rules)

    def test_empty_known_risks_rejected(self):
        text = GOOD.replace(
            'known_risks:\n    - "OCR misreads on low-quality scans"\n    - "Staff resistance to the new review queue"',
            "known_risks: []",
        )
        result = validate_pilot_simulation(text)
        self.assertEqual(result.status, "INVALID")
        rules = {i.rule for i in result.issues}
        self.assertIn("PS-R-7", rules)

    def test_empty_failure_scenarios_rejected(self):
        text = """
pilot_simulation:
  id: "pilot-sim-002"
  automation_candidate_ref: "auto-cand-001"
  baseline:
    description: "desc"
  proposed_change: "change"
  expected_benefit: "benefit"
  known_risks: ["risk"]
  failure_scenarios: []
  rollback_plan_ref: "rollback-001"
  measurement_plan_ref: "measure-001"
  status: PROPOSED
"""
        result = validate_pilot_simulation(text)
        self.assertEqual(result.status, "INVALID")
        rules = {i.rule for i in result.issues}
        self.assertIn("PS-R-8", rules)

    def test_bad_likelihood_enum_rejected(self):
        text = GOOD.replace("likelihood: MEDIUM", "likelihood: SUPER_HIGH")
        result = validate_pilot_simulation(text)
        self.assertEqual(result.status, "INVALID")
        rules = {i.rule for i in result.issues}
        self.assertIn("PS-R-8", rules)

    def test_bad_impact_enum_rejected(self):
        text = GOOD.replace("impact: HIGH", "impact: CATASTROPHIC")
        result = validate_pilot_simulation(text)
        self.assertEqual(result.status, "INVALID")
        rules = {i.rule for i in result.issues}
        self.assertIn("PS-R-8", rules)

    def test_empty_detection_method_rejected(self):
        text = GOOD.replace(
            'detection_method: "Automated reconciliation against vendor invoice total, daily batch"',
            'detection_method: ""',
        )
        result = validate_pilot_simulation(text)
        self.assertEqual(result.status, "INVALID")
        rules = {i.rule for i in result.issues}
        self.assertIn("PS-R-8", rules)

    def test_bad_status_enum_rejected(self):
        text = GOOD.replace("status: PROPOSED", "status: MAYBE")
        result = validate_pilot_simulation(text)
        self.assertEqual(result.status, "INVALID")
        rules = {i.rule for i in result.issues}
        self.assertIn("PS-R-9", rules)

    # --- the "extra teeth" rule: APPROVED_FOR_PILOT completeness -------------

    def test_approved_for_pilot_without_rollback_ref_rejected(self):
        text = GOOD_APPROVED.replace('rollback_plan_ref: "rollback-001"', 'rollback_plan_ref: ""')
        result = validate_pilot_simulation(text)
        self.assertEqual(result.status, "INVALID")
        rules = {i.rule for i in result.issues}
        self.assertIn("PS-R-9", rules)
        approval_issue = [i for i in result.issues if i.rule == "PS-R-9"
                           and "APPROVED_FOR_PILOT" in i.what]
        self.assertTrue(approval_issue)
        self.assertIn("rollback_plan_ref", approval_issue[0].evidence)

    def test_approved_for_pilot_without_measurement_ref_rejected(self):
        text = GOOD_APPROVED.replace('measurement_plan_ref: "measure-001"', 'measurement_plan_ref: ""')
        result = validate_pilot_simulation(text)
        self.assertEqual(result.status, "INVALID")
        approval_issue = [i for i in result.issues if i.rule == "PS-R-9"
                           and "APPROVED_FOR_PILOT" in i.what]
        self.assertTrue(approval_issue)
        self.assertIn("measurement_plan_ref", approval_issue[0].evidence)

    def test_approved_for_pilot_with_missing_detection_method_rejected(self):
        text = GOOD_APPROVED.replace(
            'detection_method: "Queue depth alert if backlog exceeds 50 items"',
            'detection_method: ""',
        )
        result = validate_pilot_simulation(text)
        self.assertEqual(result.status, "INVALID")
        approval_issues = [i for i in result.issues if i.rule == "PS-R-9"
                            and "APPROVED_FOR_PILOT" in i.what]
        self.assertTrue(approval_issues)

    def test_proposed_status_does_not_require_completeness(self):
        # status PROPOSED does not trigger the APPROVED_FOR_PILOT
        # completeness check, even with an empty rollback_plan_ref —
        # that absence is still caught by the ordinary PS-R-5 field rule.
        text = GOOD.replace('rollback_plan_ref: "rollback-001"', 'rollback_plan_ref: ""')
        result = validate_pilot_simulation(text)
        self.assertEqual(result.status, "INVALID")
        rules = {i.rule for i in result.issues}
        self.assertIn("PS-R-5", rules)
        self.assertNotIn("PS-R-9", rules)

    def test_unknown_field_surfaced_not_silently_dropped(self):
        text = GOOD.replace(
            "status: PROPOSED",
            "status: PROPOSED\n  extra_field: \"surprise\"",
        )
        result = validate_pilot_simulation(text)
        self.assertIn("extra_field", result.unknown_fields)


if __name__ == "__main__":
    unittest.main()
