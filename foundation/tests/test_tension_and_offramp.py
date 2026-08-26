"""Unit tests for find_tension_hypotheses() / evaluate_off_ramp_candidates()
— the tectonic-conflict extension to foundation/situation_analysis.py.
See test_situation_analysis_external_system.py for the full real-fixture
end-to-end wiring into the existing gate chain."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from kpm.schemas.epistemic_types import classify_claim  # noqa: E402
from foundation.situation_analysis import (  # noqa: E402
    CandidateAction,
    OffRampCandidate,
    evaluate_off_ramp_candidates,
    find_tension_hypotheses,
    monk_pass,
)


def _claim(claim_id, text, classification="VERIFIED_FACT", confidence="HIGH"):
    return classify_claim(claim_id, text, classification, "recon-agent",
                           confidence=confidence)


class TestFindTensionHypotheses(unittest.TestCase):
    def test_insufficient_evidence(self):
        analysis = monk_pass(
            "sit-t1", "framing", actors=("a", "b"), goals=(), constraints=(),
            known_information=(), unknowns=(), assumptions=(),
            candidate_actions=(), evidence_refs=(), analyzed_by="tester",
        )
        report = find_tension_hypotheses(analysis, evaluated_by="red-team")
        self.assertEqual(report.decision, "INSUFFICIENT_EVIDENCE")

    def test_no_tension_when_no_shared_constraint(self):
        claim_a = _claim("c-a", "clerk delay confirmed")
        claim_b = _claim("c-b", "vendor delay confirmed")
        analysis = monk_pass(
            "sit-t2", "framing", actors=("clerk", "vendor"), goals=(),
            constraints=("unrelated constraint",),
            known_information=(claim_a, claim_b), unknowns=(), assumptions=(),
            candidate_actions=(), evidence_refs=(), analyzed_by="tester",
        )
        report = find_tension_hypotheses(analysis, evaluated_by="red-team")
        self.assertEqual(report.decision, "NO_TENSION_IDENTIFIED")

    def test_structural_tension_when_shared_constraint_and_no_relaxer(self):
        claim_a = _claim("c-a", "clerk holds informal approval authority")
        claim_b = _claim("c-b", "workflow requires formal escalation authority")
        analysis = monk_pass(
            "sit-t3", "framing", actors=("clerk", "workflow"), goals=(),
            constraints=("clerk and workflow both claim approval authority",),
            known_information=(claim_a, claim_b), unknowns=("x",), assumptions=(),
            candidate_actions=(), evidence_refs=(), analyzed_by="tester",
        )
        report = find_tension_hypotheses(analysis, evaluated_by="red-team")
        self.assertEqual(report.decision, "STRUCTURAL_TENSION")
        self.assertEqual(len(report.candidates), 1)
        self.assertEqual(
            report.candidates[0].tension_claim.classification,
            "SPECULATIVE_HYPOTHESIS",
        )

    def test_contingent_tension_when_relaxing_action_declared(self):
        claim_a = _claim("c-a", "clerk holds informal approval authority")
        claim_b = _claim("c-b", "workflow requires formal escalation authority")
        analysis = monk_pass(
            "sit-t4", "framing", actors=("clerk", "workflow"), goals=(),
            constraints=("clerk and workflow both claim approval authority",),
            known_information=(claim_a, claim_b), unknowns=("x",), assumptions=(),
            candidate_actions=(
                CandidateAction("act-1", "clarify clerk and workflow authority boundaries",
                                 depends_on_claim_ids=("c-a", "c-b")),
            ),
            evidence_refs=(), analyzed_by="tester",
        )
        report = find_tension_hypotheses(analysis, evaluated_by="red-team")
        self.assertEqual(report.decision, "CONTINGENT_TENSION")

    def test_ambiguous_multiple_preserves_both_pairs(self):
        claim_a = _claim("c-a", "clerk holds authority")
        claim_b = _claim("c-b", "workflow holds authority")
        claim_c = _claim("c-c", "vendor holds authority")
        analysis = monk_pass(
            "sit-t5", "framing", actors=("clerk", "workflow", "vendor"), goals=(),
            constraints=(
                "clerk and workflow both claim authority",
                "workflow and vendor both claim authority",
            ),
            known_information=(claim_a, claim_b, claim_c), unknowns=("x",),
            assumptions=(), candidate_actions=(), evidence_refs=(),
            analyzed_by="tester",
        )
        report = find_tension_hypotheses(analysis, evaluated_by="red-team")
        self.assertEqual(report.decision, "AMBIGUOUS_MULTIPLE")
        self.assertEqual(len(report.candidates), 2)

    def test_tension_claim_never_exceeds_speculative_hypothesis(self):
        claim_a = _claim("c-a", "clerk holds authority")
        claim_b = _claim("c-b", "workflow holds authority")
        analysis = monk_pass(
            "sit-t6", "framing", actors=("clerk", "workflow"), goals=(),
            constraints=("clerk and workflow both claim authority",),
            known_information=(claim_a, claim_b), unknowns=("x",), assumptions=(),
            candidate_actions=(), evidence_refs=(), analyzed_by="tester",
        )
        report = find_tension_hypotheses(analysis, evaluated_by="red-team")
        claim = report.candidates[0].tension_claim
        self.assertEqual(claim.classification, "SPECULATIVE_HYPOTHESIS")
        with self.assertRaises(Exception):
            from kpm.schemas.epistemic_types import reclassify
            reclassify(claim, "VERIFIED_FACT", "just trust me", "tester",
                       evidence_refs=())


def _offramp(**overrides):
    base = dict(
        offramp_id="or-1", tension_ref="clerk-workflow-authority",
        category="BOUNDARY", description="clarify jurisdiction boundary",
        preconditions=("process owner is available to clarify boundary",),
        mechanism_claim=classify_claim(
            "mech-1", "a clarified boundary reduces authority overlap",
            "SPECULATIVE_HYPOTHESIS", "red-team",
        ),
        supporting_evidence_refs=(), limitations=("boundary may be re-contested later",),
        reversibility="REVERSIBLE", interim_cost_if_reversible="brief process pause",
        affected_relationships=("clerk-manager reporting line",),
        transition_cost="LOW", proposed_by="red-team",
    )
    base.update(overrides)
    return OffRampCandidate(**base)


class TestOffRampCandidateConstruction(unittest.TestCase):
    def test_rejects_empty_affected_relationships(self):
        with self.assertRaises(ValueError):
            _offramp(affected_relationships=())

    def test_rejects_reversible_without_interim_cost(self):
        with self.assertRaises(ValueError):
            _offramp(interim_cost_if_reversible="")

    def test_allows_irreversible_without_interim_cost(self):
        candidate = _offramp(reversibility="IRREVERSIBLE", interim_cost_if_reversible="")
        self.assertEqual(candidate.reversibility, "IRREVERSIBLE")

    def test_rejects_unknown_category(self):
        with self.assertRaises(ValueError):
            _offramp(category="NOT_A_REAL_CATEGORY")

    def test_rejects_mechanism_claim_above_speculative(self):
        strong_claim = classify_claim("mech-2", "x", "VERIFIED_FACT", "red-team",
                                        confidence="HIGH")
        with self.assertRaises(ValueError):
            _offramp(mechanism_claim=strong_claim)


class TestEvaluateOffRampCandidates(unittest.TestCase):
    def _analysis_with_evidence(self, evidence_text):
        claim = _claim("c-support", evidence_text)
        return monk_pass(
            "sit-or1", "framing", actors=("clerk", "workflow"), goals=(),
            constraints=(), known_information=(claim,), unknowns=("x",),
            assumptions=(), candidate_actions=(), evidence_refs=(),
            analyzed_by="tester",
        )

    def test_no_candidates_proposed_returns_no_credible(self):
        analysis = self._analysis_with_evidence("some evidence")
        report = evaluate_off_ramp_candidates(analysis, (), evaluated_by="red-team")
        self.assertEqual(report.decision, "NO_CREDIBLE_OFF_RAMP_IDENTIFIED")

    def test_precondition_supported_by_evidence_is_single_candidate(self):
        analysis = self._analysis_with_evidence(
            "process owner is available to clarify boundary"
        )
        candidate = _offramp()
        report = evaluate_off_ramp_candidates(analysis, (candidate,), evaluated_by="red-team")
        self.assertEqual(report.decision, "SINGLE_CANDIDATE")
        self.assertEqual(len(report.candidates), 1)

    def test_precondition_unsupported_by_evidence_is_unmet(self):
        analysis = self._analysis_with_evidence("completely unrelated fact")
        candidate = _offramp()
        report = evaluate_off_ramp_candidates(analysis, (candidate,), evaluated_by="red-team")
        self.assertEqual(report.decision, "PRECONDITIONS_UNMET")
        self.assertEqual(len(report.unmet_precondition_candidates), 1)
        self.assertEqual(report.candidates, ())

    def test_two_credible_candidates_are_multiple_not_collapsed(self):
        analysis = self._analysis_with_evidence(
            "process owner is available to clarify boundary"
        )
        c1 = _offramp(offramp_id="or-1")
        c2 = _offramp(offramp_id="or-2", category="SEQUENCING")
        report = evaluate_off_ramp_candidates(analysis, (c1, c2), evaluated_by="red-team")
        self.assertEqual(report.decision, "MULTIPLE_CANDIDATES")
        self.assertEqual(len(report.candidates), 2)

    def test_rejects_unattributed_evaluation(self):
        analysis = self._analysis_with_evidence("x")
        with self.assertRaises(ValueError):
            evaluate_off_ramp_candidates(analysis, (), evaluated_by="")


class TestNoStructuralPathToAuthorization(unittest.TestCase):
    """K4/K11: an OffRampCandidate/TensionReport has no shape that fits
    build_magl_candidate's signature -- the absence of a bridge is the
    guard, proven here by asserting the dataclasses share no field
    names with what that function requires."""

    def test_offramp_report_has_no_verdict_shaped_field(self):
        import foundation.situation_analysis as mod
        forbidden = {"verdict", "authorized", "approved", "execute"}
        for field_name in mod.OffRampReport.__dataclass_fields__:
            self.assertNotIn(field_name.lower(), forbidden)
        for field_name in mod.TensionReport.__dataclass_fields__:
            self.assertNotIn(field_name.lower(), forbidden)


if __name__ == "__main__":
    unittest.main(verbosity=2)
