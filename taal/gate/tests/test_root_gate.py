"""
Root gate tests.

Mirrors firewall/gate.py's test discipline (not present as a separate
file there, but implied by its module docstring): every non-AUTHORIZED
verdict must carry a legible reason naming which of the 12 questions
produced it. These tests check the structured GateDecision, never just a
verdict string in isolation, except where the verdict itself IS the
entire point of the test (the core invariant tests).
"""

import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from taal.gate.root_gate import GateInput, evaluate_request  # noqa: E402


def _clean_input(**overrides) -> GateInput:
    """A fully clean, high-confidence, low-impact, verified-everything
    request. Individual tests override only the field(s) under test."""
    base = GateInput(
        request_id="req-001",
        requester="svc-account-42",
        action="read",
        resource="logs/app.log",
        scope="read:logs",
        duration="1h",
        delegation=False,
        identity_verified=True,
        authority_asserted=True,
        authority_evidence=("role-grant-9981",),
        scope_declared_necessary=True,
        reducible_scope=(),
        reversible=True,
        provenance_status="VERIFIED",
        supporting_evidence=("audit-log-entry-1",),
        contradictory_evidence=(),
        high_impact=False,
    )
    return replace(base, **overrides)


def _maximally_uncertain_input(**overrides) -> GateInput:
    base = GateInput(
        request_id="req-unknown",
        requester="unknown",
        action="unknown",
        resource="unknown",
        scope="unknown",
        duration="",
        delegation=False,
        identity_verified=False,
        authority_asserted=False,
        authority_evidence=(),
        scope_declared_necessary=False,
        reducible_scope=(),
        reversible=False,
        provenance_status="UNKNOWN",
        supporting_evidence=(),
        contradictory_evidence=(),
        high_impact=False,
    )
    return replace(base, **overrides)


class TestCleanRequestIsAuthorized(unittest.TestCase):
    """Rule 10: prove the gate CAN say yes — an always-refuse gate is a
    wall, not a working gate."""

    def test_fully_clean_request_is_authorized(self):
        d = evaluate_request(_clean_input())
        self.assertEqual(d.verdict, "AUTHORIZED")
        self.assertEqual(d.constraints, [])
        self.assertTrue(d.reasons)

    def test_authorized_reasons_reference_q12(self):
        d = evaluate_request(_clean_input())
        self.assertTrue(any("Q12" in r for r in d.reasons))


class TestCoreInvariantUnknownNeverSilentlyAuthorized(unittest.TestCase):
    """Rule 8: the core invariant. A maximally-uncertain GateInput must
    never resolve to AUTHORIZED or AUTHORIZED_WITH_CONSTRAINTS."""

    def test_maximally_uncertain_input_is_not_authorized(self):
        d = evaluate_request(_maximally_uncertain_input())
        self.assertNotIn(d.verdict, ("AUTHORIZED", "AUTHORIZED_WITH_CONSTRAINTS"))
        self.assertIn(d.verdict, ("REFUSED", "REQUIRES_HUMAN_REVIEW", "QUARANTINED"))

    def test_maximally_uncertain_input_reasons_are_present(self):
        d = evaluate_request(_maximally_uncertain_input())
        self.assertTrue(d.reasons)


class TestSelfAuthorizationCannotBypassIdentity(unittest.TestCase):
    """Rule 9: an otherwise-maximally-convincing request cannot talk its
    way past unverified identity by being perfect everywhere else."""

    def test_perfect_except_identity_is_not_authorized(self):
        d = evaluate_request(_clean_input(identity_verified=False))
        self.assertNotEqual(d.verdict, "AUTHORIZED")
        self.assertNotEqual(d.verdict, "AUTHORIZED_WITH_CONSTRAINTS")
        self.assertEqual(d.verdict, "REQUIRES_HUMAN_REVIEW")

    def test_perfect_except_identity_names_q1_in_reasons(self):
        d = evaluate_request(_clean_input(identity_verified=False))
        self.assertTrue(any("Q1" in r for r in d.reasons))


class TestUnverifiedIdentityRule1(unittest.TestCase):
    def test_unverified_identity_never_authorized_even_with_high_impact_false(self):
        d = evaluate_request(_clean_input(identity_verified=False, high_impact=False))
        self.assertNotEqual(d.verdict, "AUTHORIZED")

    def test_unverified_identity_caps_at_requires_human_review_not_worse(self):
        # identity_verified=False alone (everything else clean) should
        # cap at REQUIRES_HUMAN_REVIEW, not escalate to REFUSED/QUARANTINED.
        d = evaluate_request(_clean_input(identity_verified=False))
        self.assertEqual(d.verdict, "REQUIRES_HUMAN_REVIEW")


class TestAuthorityRule2(unittest.TestCase):
    def test_no_authority_asserted_is_refused(self):
        d = evaluate_request(_clean_input(authority_asserted=False, authority_evidence=()))
        self.assertEqual(d.verdict, "REFUSED")
        self.assertTrue(any("Q2" in r for r in d.reasons))

    def test_authority_asserted_without_evidence_is_human_review(self):
        d = evaluate_request(_clean_input(authority_asserted=True, authority_evidence=()))
        self.assertEqual(d.verdict, "REQUIRES_HUMAN_REVIEW")
        self.assertTrue(any("Q2" in r for r in d.reasons))

    def test_authority_asserted_with_evidence_does_not_trigger_q2_cap(self):
        d = evaluate_request(_clean_input())
        self.assertFalse(any("authority_evidence is empty" in r for r in d.reasons))


class TestScopeReductionRule3(unittest.TestCase):
    def test_unnecessary_scope_with_reducible_offer_is_constrained(self):
        d = evaluate_request(_clean_input(
            scope_declared_necessary=False,
            reducible_scope=("read:logs",),
        ))
        self.assertEqual(d.verdict, "AUTHORIZED_WITH_CONSTRAINTS")
        self.assertNotEqual(d.verdict, "AUTHORIZED")
        self.assertTrue(any("read:logs" in c for c in d.constraints))

    def test_unnecessary_scope_without_reducible_offer_is_human_review(self):
        d = evaluate_request(_clean_input(
            scope_declared_necessary=False,
            reducible_scope=(),
        ))
        self.assertEqual(d.verdict, "REQUIRES_HUMAN_REVIEW")

    def test_unnecessary_scope_never_plain_authorized(self):
        d = evaluate_request(_clean_input(
            scope_declared_necessary=False,
            reducible_scope=("narrower",),
        ))
        self.assertNotEqual(d.verdict, "AUTHORIZED")


class TestProvenanceRule4(unittest.TestCase):
    def test_provenance_unknown_caps_at_human_review(self):
        d = evaluate_request(_clean_input(provenance_status="UNKNOWN"))
        self.assertEqual(d.verdict, "REQUIRES_HUMAN_REVIEW")

    def test_provenance_unverifiable_caps_at_human_review(self):
        d = evaluate_request(_clean_input(provenance_status="UNVERIFIABLE"))
        self.assertEqual(d.verdict, "REQUIRES_HUMAN_REVIEW")

    def test_provenance_verified_does_not_cap(self):
        d = evaluate_request(_clean_input(provenance_status="VERIFIED"))
        self.assertEqual(d.verdict, "AUTHORIZED")

    def test_provenance_claimed_does_not_cap(self):
        d = evaluate_request(_clean_input(provenance_status="CLAIMED"))
        self.assertEqual(d.verdict, "AUTHORIZED")

    def test_unrecognised_provenance_status_is_refused(self):
        d = evaluate_request(_clean_input(provenance_status="TOTALLY_MADE_UP"))
        self.assertEqual(d.verdict, "REFUSED")


class TestContradictoryEvidenceRule5(unittest.TestCase):
    def test_contradictory_evidence_never_authorized(self):
        d = evaluate_request(_clean_input(contradictory_evidence=("conflicting log entry",)))
        self.assertNotEqual(d.verdict, "AUTHORIZED")

    def test_contradictory_evidence_is_human_review(self):
        d = evaluate_request(_clean_input(contradictory_evidence=("conflicting log entry",)))
        self.assertEqual(d.verdict, "REQUIRES_HUMAN_REVIEW")
        self.assertTrue(any("Q5" in r and "conflicting log entry" in r for r in d.reasons))


class TestSupportingEvidenceRule6(unittest.TestCase):
    def test_missing_supporting_evidence_never_authorized(self):
        d = evaluate_request(_clean_input(supporting_evidence=()))
        self.assertNotIn(d.verdict, ("AUTHORIZED", "AUTHORIZED_WITH_CONSTRAINTS"))

    def test_missing_supporting_evidence_is_human_review(self):
        d = evaluate_request(_clean_input(supporting_evidence=()))
        self.assertEqual(d.verdict, "REQUIRES_HUMAN_REVIEW")


class TestHighImpactRule7(unittest.TestCase):
    def test_high_impact_with_identity_uncertainty_capped_at_human_review(self):
        d = evaluate_request(_clean_input(high_impact=True, identity_verified=False))
        self.assertEqual(d.verdict, "REQUIRES_HUMAN_REVIEW")

    def test_high_impact_with_authority_uncertainty_capped_at_human_review(self):
        d = evaluate_request(_clean_input(
            high_impact=True, authority_asserted=True, authority_evidence=(),
        ))
        self.assertEqual(d.verdict, "REQUIRES_HUMAN_REVIEW")

    def test_high_impact_with_provenance_uncertainty_capped_at_human_review(self):
        d = evaluate_request(_clean_input(high_impact=True, provenance_status="UNKNOWN"))
        self.assertEqual(d.verdict, "REQUIRES_HUMAN_REVIEW")

    def test_high_impact_fully_certain_and_reversible_is_authorized(self):
        d = evaluate_request(_clean_input(high_impact=True, reversible=True))
        self.assertEqual(d.verdict, "AUTHORIZED")

    def test_high_impact_fully_certain_but_irreversible_is_constrained_not_plain_authorized(self):
        d = evaluate_request(_clean_input(high_impact=True, reversible=False))
        self.assertEqual(d.verdict, "AUTHORIZED_WITH_CONSTRAINTS")
        self.assertTrue(d.constraints)

    def test_high_impact_never_jumps_straight_to_quarantined(self):
        # High-impact + uncertainty must cap at REQUIRES_HUMAN_REVIEW,
        # never escalate past it to QUARANTINED on its own.
        d = evaluate_request(_clean_input(high_impact=True, identity_verified=False))
        self.assertNotEqual(d.verdict, "QUARANTINED")


class TestEdgeCases(unittest.TestCase):
    def test_empty_duration_results_in_constrained_not_refused(self):
        d = evaluate_request(_clean_input(duration=""))
        self.assertEqual(d.verdict, "AUTHORIZED_WITH_CONSTRAINTS")
        self.assertTrue(any("duration" in c for c in d.constraints))

    def test_whitespace_only_duration_treated_as_empty(self):
        d = evaluate_request(_clean_input(duration="   "))
        self.assertEqual(d.verdict, "AUTHORIZED_WITH_CONSTRAINTS")

    def test_delegation_without_identity_verification_still_capped_by_q1(self):
        d = evaluate_request(_clean_input(delegation=True, identity_verified=False))
        self.assertEqual(d.verdict, "REQUIRES_HUMAN_REVIEW")
        self.assertTrue(any("Q8" in r for r in d.reasons))
        self.assertTrue(any("Q1" in r for r in d.reasons))

    def test_delegation_with_verified_identity_does_not_itself_downgrade(self):
        d = evaluate_request(_clean_input(delegation=True))
        self.assertEqual(d.verdict, "AUTHORIZED")

    def test_reversible_high_impact_vs_irreversible_high_impact_differ(self):
        rev = evaluate_request(_clean_input(high_impact=True, reversible=True))
        irrev = evaluate_request(_clean_input(high_impact=True, reversible=False))
        self.assertEqual(rev.verdict, "AUTHORIZED")
        self.assertEqual(irrev.verdict, "AUTHORIZED_WITH_CONSTRAINTS")
        self.assertNotEqual(rev.verdict, irrev.verdict)

    def test_multiple_simultaneous_defects_take_the_least_permissive(self):
        # authority not asserted at all (-> REFUSED) combined with
        # unverified identity (-> REQUIRES_HUMAN_REVIEW): REFUSED is
        # strictly less permissive and must win.
        d = evaluate_request(_clean_input(
            identity_verified=False, authority_asserted=False, authority_evidence=(),
        ))
        self.assertEqual(d.verdict, "REFUSED")

    def test_request_id_is_carried_through(self):
        d = evaluate_request(_clean_input(request_id="req-xyz-123"))
        self.assertEqual(d.request_id, "req-xyz-123")

    def test_to_dict_shape(self):
        d = evaluate_request(_clean_input())
        as_dict = d.to_dict()
        self.assertEqual(as_dict["verdict"], "AUTHORIZED")
        self.assertIn("reasons", as_dict)
        self.assertIn("constraints", as_dict)
        self.assertIn("request_id", as_dict)


if __name__ == "__main__":
    unittest.main()
