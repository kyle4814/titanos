"""
Before/After Measurement validator tests.

Every rejection must carry WHAT/WHY/WHERE/RULE/EVIDENCE — these tests
check the structured result, never just a boolean. Mirrors
rpa/validators/tests/test_validate_pilot_simulation.py.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from rpa.validators.validate_before_after_measurement import validate_before_after_measurement  # noqa: E402

GOOD_NOT_YET_MEASURED = """
before_after_measurement:
  id: "measure-001"
  pilot_simulation_ref: "pilot-sim-001"
  metrics:
    - name: "avg_processing_time_minutes"
      before_value: "4.2"
      measurement_method: "Timestamp diff between invoice receipt and ERP posting, sampled weekly"
    - name: "monthly_error_rate_percent"
      before_value: "3.1"
      measurement_method: "Count of corrected postings / total postings per month"
  measurement_window: "4 weeks post-deployment"
  confounding_factors:
    - "Holiday season staffing changes overlap with pilot window"
"""

GOOD_MEASURED_WITH_CONCLUSION = """
before_after_measurement:
  id: "measure-002"
  pilot_simulation_ref: "pilot-sim-001"
  metrics:
    - name: "avg_processing_time_minutes"
      before_value: "4.2"
      after_value: "1.6"
      measurement_method: "Timestamp diff between invoice receipt and ERP posting, sampled weekly"
    - name: "monthly_error_rate_percent"
      before_value: "3.1"
      after_value: "2.4"
      measurement_method: "Count of corrected postings / total postings per month"
  measurement_window: "4 weeks post-deployment"
  confounding_factors: []
  conclusion: "Processing time dropped ~62% with error rate holding roughly flat"
"""


class TestBeforeAfterMeasurementValidator(unittest.TestCase):

    # --- well-formed passing examples -------------------------------------

    def test_good_not_yet_measured_document_is_valid(self):
        result = validate_before_after_measurement(GOOD_NOT_YET_MEASURED)
        self.assertEqual(result.status, "VALID", msg=[i.to_dict() for i in result.issues])
        self.assertEqual(result.before_after_measurement_id, "measure-001")
        self.assertEqual(result.issues, [])

    def test_good_measured_with_conclusion_document_is_valid(self):
        result = validate_before_after_measurement(GOOD_MEASURED_WITH_CONCLUSION)
        self.assertEqual(result.status, "VALID", msg=[i.to_dict() for i in result.issues])

    # --- structural hardening -----------------------------------------------

    def test_missing_top_wrapper_is_invalid(self):
        result = validate_before_after_measurement("not_before_after_measurement: {}")
        self.assertEqual(result.status, "INVALID")
        self.assertEqual(result.issues[0].rule, "BA-R-2")

    def test_duplicate_key_is_rejected(self):
        text = """
before_after_measurement:
  id: "a"
  id: "b"
  pilot_simulation_ref: "x"
"""
        result = validate_before_after_measurement(text)
        self.assertEqual(result.status, "INVALID")
        self.assertEqual(result.issues[0].rule, "BA-R-1")

    def test_oversized_document_is_rejected(self):
        text = "before_after_measurement:\n  id: \"" + ("a" * 3_000_000) + "\"\n"
        result = validate_before_after_measurement(text)
        self.assertEqual(result.status, "INVALID")
        self.assertEqual(result.issues[0].rule, "BA-R-1")

    def test_non_mapping_top_value_is_invalid(self):
        result = validate_before_after_measurement("before_after_measurement: [1, 2, 3]")
        self.assertEqual(result.status, "INVALID")
        self.assertEqual(result.issues[0].rule, "BA-R-2")

    def test_unforeseen_exception_is_fail_closed(self):
        result = validate_before_after_measurement(None)  # type: ignore[arg-type]
        self.assertEqual(result.status, "INVALID")
        self.assertEqual(result.issues[0].rule, "BA-R-0")

    # --- field-level rules ----------------------------------------------------

    def test_missing_required_fields(self):
        result = validate_before_after_measurement("before_after_measurement:\n  id: \"x\"\n")
        self.assertEqual(result.status, "INVALID")
        rules = {i.rule for i in result.issues}
        self.assertIn("BA-R-4", rules)

    def test_empty_metrics_rejected(self):
        text = """
before_after_measurement:
  id: "measure-003"
  pilot_simulation_ref: "pilot-sim-001"
  metrics: []
  measurement_window: "4 weeks"
  confounding_factors: []
"""
        result = validate_before_after_measurement(text)
        self.assertEqual(result.status, "INVALID")
        rules = {i.rule for i in result.issues}
        self.assertIn("BA-R-5", rules)

    def test_missing_measurement_method_rejected(self):
        text = GOOD_NOT_YET_MEASURED.replace(
            'measurement_method: "Count of corrected postings / total postings per month"',
            'measurement_method: ""',
        )
        result = validate_before_after_measurement(text)
        self.assertEqual(result.status, "INVALID")
        rules = {i.rule for i in result.issues}
        self.assertIn("BA-R-5", rules)

    def test_confounding_factors_must_be_present_even_if_empty(self):
        # Present as an empty list is fine (mirrors legacy_system_map's
        # "unknowns must be preserved" pattern) — this is the positive
        # case already covered by GOOD_MEASURED_WITH_CONCLUSION
        # (confounding_factors: []); here we check it is REQUIRED, not
        # merely permitted to be empty.
        text = GOOD_NOT_YET_MEASURED.replace(
            'confounding_factors:\n    - "Holiday season staffing changes overlap with pilot window"\n',
            "",
        )
        result = validate_before_after_measurement(text)
        self.assertEqual(result.status, "INVALID")
        rules = {i.rule for i in result.issues}
        self.assertIn("BA-R-4", rules)

    # --- the "extra teeth" rule: conclusion requires full measurement --------

    def test_conclusion_with_missing_after_value_rejected(self):
        text = GOOD_NOT_YET_MEASURED + "\n"
        text = text.rstrip("\n") + '\n  conclusion: "It worked great"\n'
        # rebuild properly: append conclusion to the not-yet-measured doc
        text = GOOD_NOT_YET_MEASURED.rstrip("\n") + '\n  conclusion: "It worked great"\n'
        result = validate_before_after_measurement(text)
        self.assertEqual(result.status, "INVALID")
        rules = {i.rule for i in result.issues}
        self.assertIn("BA-R-6", rules)
        conclusion_issue = [i for i in result.issues if i.rule == "BA-R-6"][0]
        self.assertIn("conclusion", conclusion_issue.what)

    def test_conclusion_with_one_metric_unmeasured_rejected(self):
        text = GOOD_MEASURED_WITH_CONCLUSION.replace('after_value: "2.4"', "")
        result = validate_before_after_measurement(text)
        self.assertEqual(result.status, "INVALID")
        rules = {i.rule for i in result.issues}
        self.assertIn("BA-R-6", rules)

    def test_empty_conclusion_string_rejected(self):
        text = GOOD_MEASURED_WITH_CONCLUSION.replace(
            'conclusion: "Processing time dropped ~62% with error rate holding roughly flat"',
            'conclusion: ""',
        )
        result = validate_before_after_measurement(text)
        # empty string is treated as "not present" (None-equivalent) per
        # the schema's optional-field convention — should remain VALID.
        self.assertEqual(result.status, "VALID", msg=[i.to_dict() for i in result.issues])

    def test_unknown_field_surfaced_not_silently_dropped(self):
        text = GOOD_NOT_YET_MEASURED.replace(
            'measurement_window: "4 weeks post-deployment"',
            'measurement_window: "4 weeks post-deployment"\n  extra_field: "surprise"',
        )
        result = validate_before_after_measurement(text)
        self.assertIn("extra_field", result.unknown_fields)


if __name__ == "__main__":
    unittest.main()
