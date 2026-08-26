"""Unit tests for find_bottleneck_hypotheses() — the external-world-ping
extension to foundation/situation_analysis.py. See
test_situation_analysis_external_system.py for the full real-fixture
vertical slice."""

import inspect
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from kpm.schemas.epistemic_types import classify_claim  # noqa: E402
from foundation.situation_analysis import (  # noqa: E402
    CandidateAction,
    find_bottleneck_hypotheses,
    monk_pass,
)


def _claim(claim_id, text, classification, confidence="MEDIUM"):
    return classify_claim(claim_id, text, classification, "recon-agent",
                           confidence=confidence)


class TestInsufficientEvidence(unittest.TestCase):
    def test_zero_evidenced_claims_holds_insufficient(self):
        analysis = monk_pass(
            "sit-b1", "framing", actors=(), goals=(), constraints=("x",),
            known_information=(), unknowns=(), assumptions=(),
            candidate_actions=(), evidence_refs=(), analyzed_by="tester",
        )
        report = find_bottleneck_hypotheses(analysis, evaluated_by="red-team")
        self.assertEqual(report.decision, "INSUFFICIENT_EVIDENCE")
        self.assertEqual(report.candidates, ())

    def test_below_min_observation_count_holds_insufficient(self):
        claim = _claim("c-1", "system delay", "VERIFIED_FACT", confidence="HIGH")
        analysis = monk_pass(
            "sit-b2", "framing", actors=(), goals=(), constraints=("delay",),
            known_information=(claim,), unknowns=(), assumptions=(),
            candidate_actions=(), evidence_refs=(), analyzed_by="tester",
        )
        report = find_bottleneck_hypotheses(
            analysis, evaluated_by="red-team", min_observation_count=2,
        )
        self.assertEqual(report.decision, "INSUFFICIENT_EVIDENCE")


class TestHold(unittest.TestCase):
    def test_evidence_present_but_no_constraint_matches_holds(self):
        claim1 = _claim("c-1", "unrelated fact one", "VERIFIED_FACT", confidence="HIGH")
        claim2 = _claim("c-2", "unrelated fact two", "VERIFIED_FACT", confidence="HIGH")
        analysis = monk_pass(
            "sit-b3", "framing", actors=(), goals=(),
            constraints=("something entirely different",),
            known_information=(claim1, claim2), unknowns=(), assumptions=(),
            candidate_actions=(), evidence_refs=(), analyzed_by="tester",
        )
        report = find_bottleneck_hypotheses(analysis, evaluated_by="red-team")
        self.assertEqual(report.decision, "HOLD")
        self.assertEqual(report.candidates, ())

    def test_matching_evidence_with_no_dependent_action_holds(self):
        claim1 = _claim("c-1", "invoice clerk delay confirmed", "VERIFIED_FACT",
                         confidence="HIGH")
        claim2 = _claim("c-2", "second supporting observation", "EVIDENCE_SUPPORTED_MODEL")
        analysis = monk_pass(
            "sit-b4", "framing", actors=(), goals=(),
            constraints=("invoice clerk delay",),
            known_information=(claim1, claim2), unknowns=(), assumptions=(),
            candidate_actions=(), evidence_refs=(), analyzed_by="tester",
        )
        report = find_bottleneck_hypotheses(analysis, evaluated_by="red-team")
        self.assertEqual(report.decision, "HOLD")


class TestSingleCandidate(unittest.TestCase):
    def test_one_dominant_constraint_is_single_candidate(self):
        claim1 = _claim("c-1", "invoice clerk delay confirmed by scan", "VERIFIED_FACT",
                         confidence="HIGH")
        claim2 = _claim("c-2", "clerk delay also seen in second audit",
                         "EVIDENCE_SUPPORTED_MODEL")
        analysis = monk_pass(
            "sit-b5", "framing", actors=("clerk",), goals=(),
            constraints=("invoice clerk delay",),
            known_information=(claim1, claim2), unknowns=("x",), assumptions=(),
            candidate_actions=(
                CandidateAction("act-1", "notify backup", depends_on_claim_ids=("c-1",)),
                CandidateAction("act-2", "escalate to manager", depends_on_claim_ids=("c-2",)),
            ),
            evidence_refs=("e",), analyzed_by="tester",
        )
        report = find_bottleneck_hypotheses(analysis, evaluated_by="red-team")
        self.assertEqual(report.decision, "SINGLE_CANDIDATE")
        self.assertEqual(len(report.candidates), 1)
        self.assertEqual(report.candidates[0].leverage_estimate, "HIGH")
        self.assertEqual(
            report.candidates[0].hypothesis_claim.classification,
            "SPECULATIVE_HYPOTHESIS",
        )


class TestAmbiguousMultiple(unittest.TestCase):
    def test_two_tied_constraints_are_preserved_not_collapsed(self):
        claim1 = _claim("c-1", "clerk delay confirmed", "VERIFIED_FACT", confidence="HIGH")
        claim2 = _claim("c-2", "vendor delay confirmed", "VERIFIED_FACT", confidence="HIGH")
        analysis = monk_pass(
            "sit-b6", "framing", actors=(), goals=(),
            constraints=("clerk delay", "vendor delay"),
            known_information=(claim1, claim2), unknowns=("x",), assumptions=(),
            candidate_actions=(
                CandidateAction("act-1", "notify clerk backup", depends_on_claim_ids=("c-1",)),
                CandidateAction("act-2", "notify vendor backup", depends_on_claim_ids=("c-2",)),
            ),
            evidence_refs=("e",), analyzed_by="tester",
        )
        report = find_bottleneck_hypotheses(analysis, evaluated_by="red-team")
        self.assertEqual(report.decision, "AMBIGUOUS_MULTIPLE")
        self.assertEqual(len(report.candidates), 2)


class TestNoFloatScoreAnywhere(unittest.TestCase):
    """Kill test for K2/K6 (score laundering): leverage must be an
    ordinal label, never a bare number, anywhere on the returned
    dataclasses."""

    def test_leverage_estimate_is_always_a_string_label(self):
        claim1 = _claim("c-1", "clerk delay confirmed", "VERIFIED_FACT", confidence="HIGH")
        claim2 = _claim("c-2", "second observation", "EVIDENCE_SUPPORTED_MODEL")
        analysis = monk_pass(
            "sit-b7", "framing", actors=(), goals=(), constraints=("clerk delay",),
            known_information=(claim1, claim2), unknowns=("x",), assumptions=(),
            candidate_actions=(
                CandidateAction("act-1", "notify", depends_on_claim_ids=("c-1",)),
            ),
            evidence_refs=("e",), analyzed_by="tester",
        )
        report = find_bottleneck_hypotheses(analysis, evaluated_by="red-team")
        for candidate in report.candidates:
            self.assertIsInstance(candidate.leverage_estimate, str)
            self.assertIn(candidate.leverage_estimate, ("LOW", "MEDIUM", "HIGH"))
            for _, level in candidate.dimensions_scored:
                self.assertIn(level, ("LOW", "MEDIUM", "HIGH"))

    def test_no_public_dataclass_field_is_a_bare_authorization_flag(self):
        import foundation.situation_analysis as mod
        forbidden_exact = {"score", "authorized", "approved", "is_authorized",
                           "authorization", "permitted", "granted"}
        for name in ("BottleneckCandidate", "BottleneckReport"):
            cls = getattr(mod, name)
            for field_name in cls.__dataclass_fields__:
                self.assertNotIn(field_name.lower(), forbidden_exact)


if __name__ == "__main__":
    unittest.main(verbosity=2)
