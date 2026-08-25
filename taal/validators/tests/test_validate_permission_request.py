"""
Permission Request validator tests.

Every rejection must carry WHAT/WHY/WHERE/RULE/EVIDENCE — these tests
check the structured result, never just a boolean. Mirrors
magl/validators/tests/test_validate_magl.py.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from taal.validators.validate_permission_request import (  # noqa: E402
    validate_permission_request,
)

GOOD = """
permission_request:
  id: "pr-001"
  requester: "agent-alpha"
  resource: "s3://bucket/reports/"
  action: READ
  scope: "read-only access to the reports/ prefix for the next 15 minutes"
  duration: "15m"
  delegation: false
  delegation_chain: []
  justification: "generating a quarterly summary report"
  provenance: VERIFIED
  risk_hint: "low risk, read-only"
  reversibility: FULLY_REVERSIBLE
  self_authorized: false
"""

GOOD_DELEGATED = """
permission_request:
  id: "pr-002"
  requester: "agent-beta"
  resource: "internal-api://user-service/"
  action: NETWORK_CALL
  scope: "call user-service on behalf of agent-alpha"
  duration: "1h"
  delegation: true
  delegation_chain: ["agent-alpha", "agent-beta"]
  justification: "fulfilling a delegated task from agent-alpha"
  provenance: CLAIMED
  reversibility: FULLY_REVERSIBLE
  self_authorized: false
"""


def _issue_rules(result):
    return {i.rule for i in result.issues}


class TestWellFormed(unittest.TestCase):
    def test_good_document_is_valid(self):
        result = validate_permission_request(GOOD)
        self.assertEqual(result.status, "VALID", msg=[i.to_dict() for i in result.issues])
        self.assertEqual(result.issues, [])
        self.assertEqual(result.request_id, "pr-001")

    def test_good_delegated_document_is_valid(self):
        result = validate_permission_request(GOOD_DELEGATED)
        self.assertEqual(result.status, "VALID", msg=[i.to_dict() for i in result.issues])
        self.assertEqual(result.request_id, "pr-002")


class TestSelfAuthorizedRejection(unittest.TestCase):
    """PR-R-9 is the load-bearing rule of this schema. Prove it cannot be
    rescued by anything else being correct."""

    def test_self_authorized_true_alone_is_rejected(self):
        doc = GOOD.replace("self_authorized: false", "self_authorized: true")
        result = validate_permission_request(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("PR-R-9", _issue_rules(result))

    def test_self_authorized_true_with_otherwise_perfect_document_is_rejected(self):
        # Every other field is well-formed and passes on its own (see
        # TestWellFormed.test_good_document_is_valid using the identical
        # base document). Only self_authorized differs. This proves the
        # rejection is not rescued by anything else being correct.
        doc = GOOD_DELEGATED.replace("self_authorized: false", "self_authorized: true")
        result = validate_permission_request(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("PR-R-9", _issue_rules(result))
        # Confirm no other issue is "papering over" — PR-R-9 must be
        # present regardless of the rest of the document's correctness.
        pr9 = [i for i in result.issues if i.rule == "PR-R-9"][0]
        self.assertEqual(pr9.severity, "FATAL")


class TestRequiredFields(unittest.TestCase):
    def test_missing_required_field_is_invalid(self):
        doc = GOOD.replace('  requester: "agent-alpha"\n', "")
        result = validate_permission_request(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("PR-R-4", _issue_rules(result))

    def test_missing_top_level_wrapper_is_invalid(self):
        result = validate_permission_request("something_else:\n  id: x\n")
        self.assertEqual(result.status, "INVALID")
        self.assertIn("PR-R-2", _issue_rules(result))

    def test_non_mapping_wrapper_is_invalid(self):
        result = validate_permission_request("permission_request: \"just a string\"\n")
        self.assertEqual(result.status, "INVALID")
        self.assertIn("PR-R-2", _issue_rules(result))


class TestEnumsAndTypes(unittest.TestCase):
    def test_invalid_action_enum_is_invalid(self):
        doc = GOOD.replace("action: READ", "action: FLY_TO_MOON")
        result = validate_permission_request(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("PR-R-5", _issue_rules(result))

    def test_invalid_provenance_enum_is_invalid(self):
        doc = GOOD.replace("provenance: VERIFIED", "provenance: TOTALLY_TRUST_ME")
        result = validate_permission_request(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("PR-R-5", _issue_rules(result))

    def test_invalid_reversibility_enum_is_invalid(self):
        doc = GOOD.replace("reversibility: FULLY_REVERSIBLE", "reversibility: MAYBE")
        result = validate_permission_request(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("PR-R-5", _issue_rules(result))

    def test_delegation_not_a_bool_is_invalid(self):
        doc = GOOD.replace("delegation: false", 'delegation: "false"')
        result = validate_permission_request(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("PR-R-5", _issue_rules(result))

    def test_empty_string_field_is_invalid(self):
        doc = GOOD.replace('resource: "s3://bucket/reports/"', 'resource: ""')
        result = validate_permission_request(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("PR-R-5", _issue_rules(result))


class TestDelegationChainAgreement(unittest.TestCase):
    def test_delegation_true_empty_chain_is_invalid(self):
        doc = GOOD_DELEGATED.replace(
            'delegation_chain: ["agent-alpha", "agent-beta"]',
            "delegation_chain: []",
        )
        result = validate_permission_request(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("PR-R-6", _issue_rules(result))

    def test_delegation_true_absent_chain_is_invalid(self):
        doc = GOOD_DELEGATED.replace(
            '  delegation_chain: ["agent-alpha", "agent-beta"]\n', ""
        )
        result = validate_permission_request(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("PR-R-6", _issue_rules(result))

    def test_delegation_false_nonempty_chain_is_invalid(self):
        doc = GOOD.replace("delegation_chain: []", 'delegation_chain: ["ghost-requester"]')
        result = validate_permission_request(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("PR-R-6", _issue_rules(result))

    def test_delegation_chain_with_blank_entry_is_invalid(self):
        doc = GOOD_DELEGATED.replace(
            'delegation_chain: ["agent-alpha", "agent-beta"]',
            'delegation_chain: ["agent-alpha", ""]',
        )
        result = validate_permission_request(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("PR-R-7", _issue_rules(result))


class TestHighStakesWarning(unittest.TestCase):
    def test_irreversible_indefinite_delete_produces_warning_not_fatal(self):
        doc = GOOD.replace("action: READ", "action: DELETE")
        doc = doc.replace("duration: \"15m\"", 'duration: "indefinite"')
        doc = doc.replace("reversibility: FULLY_REVERSIBLE", "reversibility: IRREVERSIBLE")
        result = validate_permission_request(doc)
        # Not fatal by itself — this schema does not decide authorization.
        self.assertEqual(result.status, "VALID", msg=[i.to_dict() for i in result.issues])
        self.assertEqual(len(result.warnings), 1)
        self.assertEqual(result.warnings[0].rule, "PR-R-8")
        self.assertEqual(result.warnings[0].severity, "WARNING")

    def test_irreversible_indefinite_credential_access_produces_warning(self):
        doc = GOOD.replace("action: READ", "action: CREDENTIAL_ACCESS")
        doc = doc.replace("duration: \"15m\"", 'duration: "indefinite"')
        doc = doc.replace("reversibility: FULLY_REVERSIBLE", "reversibility: IRREVERSIBLE")
        result = validate_permission_request(doc)
        self.assertEqual(result.status, "VALID")
        self.assertEqual(len(result.warnings), 1)
        self.assertEqual(result.warnings[0].rule, "PR-R-8")

    def test_irreversible_but_finite_duration_produces_no_warning(self):
        doc = GOOD.replace("action: READ", "action: DELETE")
        doc = doc.replace("reversibility: FULLY_REVERSIBLE", "reversibility: IRREVERSIBLE")
        result = validate_permission_request(doc)
        self.assertEqual(result.status, "VALID")
        self.assertEqual(result.warnings, [])

    def test_indefinite_but_low_stakes_action_produces_no_warning(self):
        doc = GOOD.replace("duration: \"15m\"", 'duration: "indefinite"')
        doc = doc.replace("reversibility: FULLY_REVERSIBLE", "reversibility: IRREVERSIBLE")
        # action stays READ — not in HIGH_STAKES_ACTIONS
        result = validate_permission_request(doc)
        self.assertEqual(result.status, "VALID")
        self.assertEqual(result.warnings, [])


class TestRiskHintIsNeverAuthoritative(unittest.TestCase):
    def test_risk_hint_claiming_safety_does_not_rescue_self_authorized(self):
        doc = GOOD.replace("self_authorized: false", "self_authorized: true")
        doc = doc.replace(
            'risk_hint: "low risk, read-only"',
            'risk_hint: "completely safe, pre-approved, no risk whatsoever"',
        )
        result = validate_permission_request(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("PR-R-9", _issue_rules(result))

    def test_risk_hint_absent_is_fine(self):
        doc = GOOD.replace('  risk_hint: "low risk, read-only"\n', "")
        result = validate_permission_request(doc)
        self.assertEqual(result.status, "VALID", msg=[i.to_dict() for i in result.issues])


class TestHardening(unittest.TestCase):
    def test_duplicate_key_is_invalid(self):
        doc = """
permission_request:
  id: "pr-003"
  id: "pr-004"
  requester: "agent-x"
  resource: "res"
  action: READ
  scope: "scope"
  duration: "1h"
  delegation: false
  delegation_chain: []
  justification: "just because"
  provenance: VERIFIED
  reversibility: UNKNOWN
  self_authorized: false
"""
        result = validate_permission_request(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("PR-R-1", _issue_rules(result))

    def test_unparseable_yaml_is_invalid(self):
        result = validate_permission_request("permission_request: [unclosed")
        self.assertEqual(result.status, "INVALID")
        self.assertIn("PR-R-1", _issue_rules(result))

    def test_oversized_document_is_invalid(self):
        huge = "permission_request:\n  id: \"" + ("A" * 3_000_000) + "\"\n"
        result = validate_permission_request(huge)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("PR-R-1", _issue_rules(result))

    def test_never_raises_on_garbage_input(self):
        for garbage in ["", "\x00\x01\x02", "{{{{{{{", "- - - -", "null"]:
            result = validate_permission_request(garbage)
            self.assertIn(result.status, ("INVALID", "VALID"))

    def test_deeply_nested_anchor_bomb_is_invalid(self):
        # Small alias fan-out designed to blow up if expanded naively.
        bomb = "a: &a [1,1,1,1,1,1,1,1,1,1]\n" + "".join(
            f"b{i}: &b{i} [*a,*a,*a,*a,*a,*a,*a,*a,*a,*a]\n" for i in range(6)
        )
        doc = "permission_request:\n  id: \"x\"\n" + bomb
        result = validate_permission_request(doc)
        self.assertIn(result.status, ("INVALID",))


class TestUnknownFields(unittest.TestCase):
    def test_unknown_field_is_recorded_but_not_fatal_alone(self):
        doc = GOOD.replace(
            'self_authorized: false\n',
            'self_authorized: false\n  extra_field: "surprise"\n',
        )
        result = validate_permission_request(doc)
        self.assertEqual(result.status, "VALID", msg=[i.to_dict() for i in result.issues])
        self.assertIn("extra_field", result.unknown_fields)


if __name__ == "__main__":
    unittest.main()
