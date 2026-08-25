"""
Verdict validator tests.

Every rejection must carry WHAT/WHY/WHERE/RULE/EVIDENCE — these tests
check the structured result, never just a boolean. Mirrors
magl/validators/tests/test_validate_magl.py.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from taal.validators.validate_verdict import validate_verdict  # noqa: E402


GOOD_AUTHORIZED = """
verdict:
  id: "verdict-001"
  subject_ref: "permission_request-001"
  decision: AUTHORIZED
  why:
    - "identity verified via mTLS certificate"
    - "authority evidence matches declared role"
  evidence:
    - "cert chain valid, issued by internal CA"
  unknown_factors: []
  alternative_explanations: []
  recommended_action: "grant access as requested"
  reversal_path: "revoke the issued token via token-revocation-001"
  review_path: "escalate to on-call security reviewer within 24h"
  explanation_tiers:
    public: "Access was granted based on verified identity and role."
    operator: "mTLS cert chain verified against internal CA; role claim matched RBAC table entry rbac-4471."
"""

GOOD_AUTHORIZED_WITH_CONSTRAINTS = """
verdict:
  id: "verdict-002"
  subject_ref: "permission_request-002"
  decision: AUTHORIZED_WITH_CONSTRAINTS
  why:
    - "requested scope exceeded declared necessity; reduced to minimum viable scope"
  evidence:
    - "reducible_scope offered by requester: ['read:logs']"
  unknown_factors:
    - "whether requester will need broader scope later"
  alternative_explanations: []
  recommended_action: "grant reduced scope only"
  reversal_path: "revoke scoped token via token-revocation-002"
  review_path: "reviewable by security-ops queue item so-002"
  constraints:
    - "scope limited to read:logs"
    - "duration limited to 1h"
  explanation_tiers:
    public: "Access was granted with a reduced scope."
    operator: "Requested scope was broader than justified; reduced to read:logs per reducible_scope offer."
"""

GOOD_UNKNOWN = """
verdict:
  id: "verdict-003"
  subject_ref: "normalized_security_event-777"
  decision: UNKNOWN
  why:
    - "insufficient corroborating evidence to resolve either way"
  evidence:
    - "single unverified log line"
  unknown_factors:
    - "whether the log line's source system is compromised"
  alternative_explanations:
    - "benign misconfiguration"
    - "active compromise"
  recommended_action: "hold for additional telemetry before any action"
  reversal_path: "n/a — no action was taken to reverse"
  review_path: "reviewable by threat-intel triage queue"
  explanation_tiers:
    public: "This event could not be conclusively classified."
    operator: "Single-source log evidence, no corroboration; classification withheld pending more telemetry."
"""

GOOD_REFUSED = """
verdict:
  id: "verdict-004"
  subject_ref: "permission_request-004"
  decision: REFUSED
  why:
    - "no authority evidence was supplied for the asserted role"
  evidence:
    - "authority_evidence field was empty on the request"
  unknown_factors: []
  alternative_explanations: []
  recommended_action: "resubmit with valid authority evidence"
  reversal_path: "n/a — nothing was granted to reverse"
  review_path: "reviewable by security-ops queue"
  explanation_tiers:
    public: "The request could not be authorized."
    operator: "No authority evidence supplied; refused per root-gate question 2."
"""


class TestGoodDocuments(unittest.TestCase):
    def test_authorized_is_valid(self):
        r = validate_verdict(GOOD_AUTHORIZED)
        self.assertEqual(r.status, "VALID", r.issues)
        self.assertEqual(r.verdict_id, "verdict-001")

    def test_authorized_with_constraints_is_valid(self):
        r = validate_verdict(GOOD_AUTHORIZED_WITH_CONSTRAINTS)
        self.assertEqual(r.status, "VALID", r.issues)

    def test_unknown_decision_is_valid(self):
        r = validate_verdict(GOOD_UNKNOWN)
        self.assertEqual(r.status, "VALID", r.issues)

    def test_refused_is_valid(self):
        r = validate_verdict(GOOD_REFUSED)
        self.assertEqual(r.status, "VALID", r.issues)


class TestUnknownIsNeverAuthorized(unittest.TestCase):
    """UNKNOWN is a legitimate terminal state, not a defect — but nothing
    in this schema or validator may ever treat it as equivalent to
    AUTHORIZED."""

    def test_unknown_validates_cleanly_on_its_own_terms(self):
        r = validate_verdict(GOOD_UNKNOWN)
        self.assertEqual(r.status, "VALID", r.issues)

    def test_unknown_is_not_in_authorization_decisions(self):
        from taal.schema.verdict import AUTHORIZATION_DECISIONS
        self.assertNotIn("UNKNOWN", AUTHORIZATION_DECISIONS)

    def test_unknown_with_empty_evidence_is_invalid_via_generic_rule_not_authorization_rule(self):
        # evidence is unconditionally required non-empty (VD-R-8) for
        # every decision including UNKNOWN. What must NOT happen is
        # VD-R-11 (the authorization-specific escalation) firing for a
        # decision that was never an authorization in the first place.
        text = GOOD_UNKNOWN.replace(
            'evidence:\n    - "single unverified log line"',
            "evidence: []",
        )
        r = validate_verdict(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "VD-R-8" for i in r.issues))
        self.assertFalse(any(i.rule == "VD-R-11" for i in r.issues))


class TestMissingRequiredFields(unittest.TestCase):
    def test_missing_id(self):
        text = GOOD_AUTHORIZED.replace('id: "verdict-001"\n  ', "")
        r = validate_verdict(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "VD-R-4" and "id" in i.where for i in r.issues))

    def test_missing_subject_ref(self):
        text = GOOD_AUTHORIZED.replace('subject_ref: "permission_request-001"\n  ', "")
        r = validate_verdict(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "VD-R-4" for i in r.issues))

    def test_missing_why(self):
        text = """
verdict:
  id: "v1"
  subject_ref: "pr-1"
  decision: REFUSED
  evidence:
    - "e"
  unknown_factors: []
  alternative_explanations: []
  recommended_action: "x"
  reversal_path: "x"
  review_path: "x"
  explanation_tiers:
    public: "p"
    operator: "o"
"""
        r = validate_verdict(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "VD-R-4" and "why" in i.where for i in r.issues))

    def test_empty_why_list_rejected(self):
        text = GOOD_REFUSED.replace(
            'why:\n    - "no authority evidence was supplied for the asserted role"',
            "why: []",
        )
        r = validate_verdict(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "VD-R-7" for i in r.issues))

    def test_missing_explanation_tiers(self):
        text = """
verdict:
  id: "v1"
  subject_ref: "pr-1"
  decision: REFUSED
  why:
    - "w"
  evidence:
    - "e"
  unknown_factors: []
  alternative_explanations: []
  recommended_action: "x"
  reversal_path: "x"
  review_path: "x"
"""
        r = validate_verdict(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "VD-R-4" and "explanation_tiers" in i.where for i in r.issues))


class TestDecisionEnum(unittest.TestCase):
    def test_invalid_decision_rejected(self):
        text = GOOD_REFUSED.replace("decision: REFUSED", "decision: MAYBE_LATER")
        r = validate_verdict(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "VD-R-6" for i in r.issues))


class TestEvidenceRequiredRule(unittest.TestCase):
    """VD-R-11: the load-bearing rule. Authorization decisions must never
    carry empty evidence, regardless of how well-formed everything else
    is."""

    def test_authorized_with_empty_evidence_is_invalid(self):
        text = GOOD_AUTHORIZED.replace(
            'evidence:\n    - "cert chain valid, issued by internal CA"',
            "evidence: []",
        )
        r = validate_verdict(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "VD-R-11" for i in r.issues))

    def test_authorized_with_constraints_and_empty_evidence_is_invalid(self):
        text = GOOD_AUTHORIZED_WITH_CONSTRAINTS.replace(
            "evidence:\n    - \"reducible_scope offered by requester: ['read:logs']\"",
            "evidence: []",
        )
        r = validate_verdict(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "VD-R-11" for i in r.issues))

    def test_refused_with_empty_evidence_is_also_invalid(self):
        # evidence is unconditionally required non-empty by the schema
        # (VD-R-8) — REFUSED does not get a pass on this either. VD-R-11
        # is the AUTHORIZATION-specific escalation of the same defect.
        text = GOOD_REFUSED.replace(
            'evidence:\n    - "authority_evidence field was empty on the request"',
            "evidence: []",
        )
        r = validate_verdict(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "VD-R-8" for i in r.issues))
        self.assertFalse(any(i.rule == "VD-R-11" for i in r.issues))

    def test_authorized_missing_evidence_field_entirely_is_invalid(self):
        text = """
verdict:
  id: "v1"
  subject_ref: "pr-1"
  decision: AUTHORIZED
  why:
    - "w"
  unknown_factors: []
  alternative_explanations: []
  recommended_action: "x"
  reversal_path: "x"
  review_path: "x"
  explanation_tiers:
    public: "p"
    operator: "o"
"""
        r = validate_verdict(text)
        self.assertEqual(r.status, "INVALID")
        # Both the required-field rule and the evidence-required rule fire.
        self.assertTrue(any(i.rule == "VD-R-4" for i in r.issues))
        self.assertTrue(any(i.rule == "VD-R-11" for i in r.issues))


class TestConstraintsConditionalRule(unittest.TestCase):
    """VD-R-12."""

    def test_authorized_with_constraints_missing_constraints_is_invalid(self):
        text = GOOD_AUTHORIZED_WITH_CONSTRAINTS.replace(
            '  constraints:\n    - "scope limited to read:logs"\n    - "duration limited to 1h"\n',
            "",
        )
        r = validate_verdict(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "VD-R-12" for i in r.issues))

    def test_plain_authorized_with_constraints_field_is_invalid(self):
        text = GOOD_AUTHORIZED + '  constraints:\n    - "should not be here"\n'
        r = validate_verdict(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "VD-R-12" for i in r.issues))

    def test_refused_with_constraints_field_is_invalid(self):
        text = GOOD_REFUSED + '  constraints:\n    - "should not be here"\n'
        r = validate_verdict(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "VD-R-12" for i in r.issues))

    def test_authorized_with_constraints_and_empty_constraints_list_is_invalid(self):
        text = GOOD_AUTHORIZED_WITH_CONSTRAINTS.replace(
            '  constraints:\n    - "scope limited to read:logs"\n    - "duration limited to 1h"\n',
            "  constraints: []\n",
        )
        r = validate_verdict(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "VD-R-12" for i in r.issues))


class TestPublicRestrictedLeak(unittest.TestCase):
    """VD-R-13."""

    def test_leak_of_restricted_into_public_rejected(self):
        text = GOOD_REFUSED.replace(
            'operator: "No authority evidence supplied; refused per root-gate question 2."',
            'operator: "No authority evidence supplied; refused per root-gate question 2."\n'
            '    restricted_detection_details: "signature XK-99 matched on the requester token"',
        ).replace(
            'public: "The request could not be authorized."',
            'public: "The request could not be authorized. signature XK-99 matched on the requester token"',
        )
        r = validate_verdict(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "VD-R-13" for i in r.issues))

    def test_restricted_details_absent_from_public_is_fine(self):
        text = GOOD_REFUSED.replace(
            'operator: "No authority evidence supplied; refused per root-gate question 2."',
            'operator: "No authority evidence supplied; refused per root-gate question 2."\n'
            '    restricted_detection_details: "signature XK-99 matched on the requester token"',
        )
        r = validate_verdict(text)
        self.assertEqual(r.status, "VALID", r.issues)


class TestUnknownFieldsRecorded(unittest.TestCase):
    def test_unknown_top_level_field_is_recorded_not_fatal(self):
        text = GOOD_REFUSED.replace(
            'decision: REFUSED', 'decision: REFUSED\n  totally_unrecognised_field: "x"'
        )
        r = validate_verdict(text)
        self.assertEqual(r.status, "VALID", r.issues)
        self.assertIn("totally_unrecognised_field", r.unknown_fields)


class TestMalformedInput(unittest.TestCase):
    def test_not_a_mapping_at_top_level(self):
        r = validate_verdict("- just\n- a\n- list\n")
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "VD-R-1" for i in r.issues))

    def test_missing_verdict_wrapper(self):
        r = validate_verdict("not_verdict:\n  id: v1\n")
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "VD-R-2" for i in r.issues))

    def test_verdict_not_a_mapping(self):
        r = validate_verdict("verdict: just a string\n")
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "VD-R-2" for i in r.issues))

    def test_duplicate_keys_rejected(self):
        text = "verdict:\n  id: v1\n  id: v2\n"
        r = validate_verdict(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "VD-R-1" for i in r.issues))

    def test_oversized_document_rejected(self):
        huge = "verdict:\n  id: " + "a" * 3_000_000 + "\n"
        r = validate_verdict(huge)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "VD-R-1" for i in r.issues))

    def test_never_raises_on_garbage(self):
        # Should never propagate an exception — always a structured result.
        try:
            r = validate_verdict("verdict: [1, 2, {3: [4, [5, [6]]]}]\n")
        except Exception as e:  # noqa: BLE001
            self.fail(f"validate_verdict raised {e!r} instead of returning INVALID")
        self.assertIn(r.status, ("VALID", "INVALID"))


class TestNeverMutatesInput(unittest.TestCase):
    def test_original_text_preserved(self):
        r = validate_verdict(GOOD_AUTHORIZED)
        self.assertEqual(r.original_text, GOOD_AUTHORIZED)


if __name__ == "__main__":
    unittest.main()
