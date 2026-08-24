"""
Rollback Contract validator tests.

Every rejection must carry WHAT/WHY/WHERE/RULE/EVIDENCE — these tests
check the structured result, never just a boolean. Mirrors
rpa/validators/tests/test_validate_pilot_simulation.py.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from rpa.validators.validate_rollback_contract import validate_rollback_contract  # noqa: E402

GOOD_UNVERIFIED = """
rollback_contract:
  id: "rollback-001"
  applies_to_ref: "pilot-sim-001"
  trigger_conditions:
    - "Error rate exceeds 5% for two consecutive days"
    - "Any single misposting over $10,000"
  rollback_steps:
    - "Disable OCR pipeline feature flag"
    - "Route all new invoices back to manual clerk queue"
    - "Notify finance lead of rollback and reason"
  rollback_owner: "Finance Systems Lead (Priya N.)"
  estimated_rollback_time: "Under 15 minutes"
  data_loss_risk: LOW
  verified: false
"""

GOOD_VERIFIED = """
rollback_contract:
  id: "rollback-002"
  applies_to_ref: "pilot-sim-001"
  trigger_conditions:
    - "Error rate exceeds 5% for two consecutive days"
  rollback_steps:
    - "Disable OCR pipeline feature flag"
    - "Route all new invoices back to manual clerk queue"
  rollback_owner: "Finance Systems Lead (Priya N.)"
  estimated_rollback_time: "Under 15 minutes"
  data_loss_risk: NONE
  verified: true
  verification_evidence: "Dry-run performed in staging 2026-08-10, feature flag toggled and queue rerouted successfully within 9 minutes"
"""


class TestRollbackContractValidator(unittest.TestCase):

    # --- well-formed passing examples -------------------------------------

    def test_good_unverified_document_is_valid(self):
        result = validate_rollback_contract(GOOD_UNVERIFIED)
        self.assertEqual(result.status, "VALID", msg=[i.to_dict() for i in result.issues])
        self.assertEqual(result.rollback_contract_id, "rollback-001")
        self.assertEqual(result.issues, [])

    def test_good_verified_document_is_valid(self):
        result = validate_rollback_contract(GOOD_VERIFIED)
        self.assertEqual(result.status, "VALID", msg=[i.to_dict() for i in result.issues])

    # --- structural hardening -----------------------------------------------

    def test_missing_top_wrapper_is_invalid(self):
        result = validate_rollback_contract("not_rollback_contract: {}")
        self.assertEqual(result.status, "INVALID")
        self.assertEqual(result.issues[0].rule, "RB-R-2")

    def test_duplicate_key_is_rejected(self):
        text = """
rollback_contract:
  id: "a"
  id: "b"
  applies_to_ref: "x"
"""
        result = validate_rollback_contract(text)
        self.assertEqual(result.status, "INVALID")
        self.assertEqual(result.issues[0].rule, "RB-R-1")

    def test_oversized_document_is_rejected(self):
        text = "rollback_contract:\n  id: \"" + ("a" * 3_000_000) + "\"\n"
        result = validate_rollback_contract(text)
        self.assertEqual(result.status, "INVALID")
        self.assertEqual(result.issues[0].rule, "RB-R-1")

    def test_non_mapping_top_value_is_invalid(self):
        result = validate_rollback_contract("rollback_contract: [1, 2, 3]")
        self.assertEqual(result.status, "INVALID")
        self.assertEqual(result.issues[0].rule, "RB-R-2")

    def test_unforeseen_exception_is_fail_closed(self):
        result = validate_rollback_contract(None)  # type: ignore[arg-type]
        self.assertEqual(result.status, "INVALID")
        self.assertEqual(result.issues[0].rule, "RB-R-0")

    # --- field-level rules ----------------------------------------------------

    def test_missing_required_fields(self):
        result = validate_rollback_contract("rollback_contract:\n  id: \"x\"\n")
        self.assertEqual(result.status, "INVALID")
        rules = {i.rule for i in result.issues}
        self.assertIn("RB-R-4", rules)

    def test_empty_trigger_conditions_rejected(self):
        text = GOOD_UNVERIFIED.replace(
            'trigger_conditions:\n    - "Error rate exceeds 5% for two consecutive days"\n    - "Any single misposting over $10,000"',
            "trigger_conditions: []",
        )
        result = validate_rollback_contract(text)
        self.assertEqual(result.status, "INVALID")
        rules = {i.rule for i in result.issues}
        self.assertIn("RB-R-6", rules)

    def test_empty_rollback_steps_rejected(self):
        text = """
rollback_contract:
  id: "rollback-003"
  applies_to_ref: "pilot-sim-001"
  trigger_conditions:
    - "Error rate exceeds 5%"
  rollback_steps: []
  rollback_owner: "Priya N."
  estimated_rollback_time: "15 minutes"
  data_loss_risk: LOW
  verified: false
"""
        result = validate_rollback_contract(text)
        self.assertEqual(result.status, "INVALID")
        rules = {i.rule for i in result.issues}
        self.assertIn("RB-R-6", rules)

    def test_bad_data_loss_risk_enum_rejected(self):
        text = GOOD_UNVERIFIED.replace("data_loss_risk: LOW", "data_loss_risk: CATASTROPHIC")
        result = validate_rollback_contract(text)
        self.assertEqual(result.status, "INVALID")
        rules = {i.rule for i in result.issues}
        self.assertIn("RB-R-7", rules)

    def test_verified_non_boolean_rejected(self):
        text = GOOD_UNVERIFIED.replace("verified: false", 'verified: "no"')
        result = validate_rollback_contract(text)
        self.assertEqual(result.status, "INVALID")
        rules = {i.rule for i in result.issues}
        self.assertIn("RB-R-7", rules)

    # --- the "extra teeth" rule: verified/verification_evidence pairing ------

    def test_verified_true_without_evidence_rejected(self):
        text = GOOD_VERIFIED.replace(
            'verification_evidence: "Dry-run performed in staging 2026-08-10, feature flag toggled and queue rerouted successfully within 9 minutes"',
            "",
        ).replace("\n\n", "\n")
        result = validate_rollback_contract(text)
        self.assertEqual(result.status, "INVALID")
        rules = {i.rule for i in result.issues}
        self.assertIn("RB-R-8", rules)

    def test_verified_false_with_evidence_rejected(self):
        text = GOOD_UNVERIFIED.rstrip("\n") + '\n  verification_evidence: "Tested it once, trust me"\n'
        result = validate_rollback_contract(text)
        self.assertEqual(result.status, "INVALID")
        rules = {i.rule for i in result.issues}
        self.assertIn("RB-R-8", rules)
        contradiction_issue = [i for i in result.issues if i.rule == "RB-R-8"][0]
        self.assertIn("contradiction", contradiction_issue.why)

    def test_verified_false_without_evidence_is_valid(self):
        # GOOD_UNVERIFIED already covers this as the primary passing case;
        # explicit assertion here documents the intent directly.
        result = validate_rollback_contract(GOOD_UNVERIFIED)
        self.assertEqual(result.status, "VALID")

    def test_unknown_field_surfaced_not_silently_dropped(self):
        text = GOOD_UNVERIFIED.rstrip("\n") + '\n  extra_field: "surprise"\n'
        result = validate_rollback_contract(text)
        self.assertIn("extra_field", result.unknown_fields)


if __name__ == "__main__":
    unittest.main()
