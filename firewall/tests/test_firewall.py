"""
Adversarial tests for the Epistemic Firewall (§18, §19).

Every test asks one question: can narrative pressure reach runtime
authority? The answer must be no, by a predicate a reviewer can read.
"""

import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from firewall.gate import (  # noqa: E402
    Artifact, evaluate, collapse_ancestry, AUTHORIZED_RUNTIME_CLASSES,
)


def clean(**kw):
    """A fully-authorized artifact. Tests mutate one field at a time."""
    base = dict(
        artifact_id="a1", classification="GOVERNANCE_RULE",
        contamination_state="VERIFIED", schema_valid=True,
        provenance_valid=True, authorization_valid=True,
    )
    base.update(kw)
    return Artifact(**base)


class TestNarrativeCannotAuthorize(unittest.TestCase):
    def test_narrative_is_refused_however_valid_everything_else_is(self):
        for cls in ("NARRATIVE", "MYTH", "METAPHOR", "PHILOSOPHY", "VALUE_JUDGMENT",
                    "SPECULATION", "HYPOTHESIS", "UNKNOWN"):
            d = evaluate(clean(classification=cls))
            self.assertFalse(d.may_influence_runtime, f"{cls} must not govern")
            self.assertEqual(d.verdict, "REFUSED")

    def test_persuasiveness_adds_zero_authority(self):
        """The core inversion: compelling material gets MORE separation."""
        maximal = dict(emotional_intensity=100, persuasion_intensity=100,
                       authority_claim=100, inevitability_claim=100,
                       self_reference=100, identity_binding=100)
        d = evaluate(clean(classification="NARRATIVE", memetic_profile=maximal))
        self.assertEqual(d.verdict, "REFUSED")
        self.assertTrue(d.risk_flags, "high-risk rhetoric must be recorded")

    def test_persuasiveness_does_not_block_a_legitimate_rule_either(self):
        """Risk flags must not become an ideological filter (§8).

        A governance rule that happens to be forcefully written is still a
        governance rule. Flags are recorded; they do not vote.
        """
        d = evaluate(clean(memetic_profile=dict(emotional_intensity=95,
                                                persuasion_intensity=95)))
        self.assertEqual(d.verdict, "AUTHORIZED")
        self.assertTrue(d.risk_flags)


class TestSelfMythology(unittest.TestCase):
    """§6 — the system must not reason from existence to authority."""

    def test_self_authorizing_narrative_is_refused(self):
        d = evaluate(clean(
            artifact_id="eternal-guardian",
            classification="NARRATIVE",
            memetic_profile=dict(authority_claim=100, inevitability_claim=100,
                                 self_reference=100, identity_binding=90),
        ))
        self.assertEqual(d.verdict, "REFUSED")
        self.assertIn("asserts its own authority", d.risk_flags)
        self.assertIn("asserts inevitability or destiny", d.risk_flags)

    def test_agent_cannot_self_authorize(self):
        d = evaluate(clean(generated_by_agent=True))
        self.assertEqual(d.verdict, "REQUIRES_HUMAN_REVIEW")

    def test_agent_output_with_independent_confirmation_may_proceed(self):
        d = evaluate(clean(generated_by_agent=True,
                           independently_confirmed_by=("human-review-1",)))
        self.assertEqual(d.verdict, "AUTHORIZED")


class TestIndependence(unittest.TestCase):
    """§3, §12 — repetition and shared ancestry are not corroboration."""

    def test_common_ancestry_collapses_to_one_origin(self):
        derived = [Artifact(artifact_id=f"a{i}", classification="EVIDENCE",
                            root_origin="SPEC-A") for i in range(5)]
        self.assertEqual(collapse_ancestry(derived), 1,
                         "five artifacts from one spec are one origin")

    def test_five_agents_agreeing_is_not_five_sources(self):
        corro = [Artifact(artifact_id=f"agent{i}", classification="EVIDENCE",
                          root_origin="SPEC-A") for i in range(5)]
        d = evaluate(clean(), corroborating=corro)
        self.assertEqual(d.verdict, "REQUIRES_HUMAN_REVIEW")
        self.assertIn("Shared ancestry is not corroboration", " ".join(d.reasons))

    def test_genuinely_distinct_origins_pass(self):
        corro = [Artifact(artifact_id=f"s{i}", classification="EVIDENCE",
                          root_origin=f"ORIGIN-{i}") for i in range(3)]
        self.assertEqual(evaluate(clean(), corroborating=corro).verdict, "AUTHORIZED")

    def test_unknown_origin_counts_as_its_own(self):
        """Conservative: an undeclared origin might be shared, so never merge."""
        a = [Artifact(artifact_id="x", classification="EVIDENCE"),
             Artifact(artifact_id="y", classification="EVIDENCE")]
        self.assertEqual(collapse_ancestry(a), 2)


class TestPromptInjection(unittest.TestCase):
    """§14 — parsing an instruction is not authorization to execute it."""

    def test_unauthorized_instructions_require_review(self):
        d = evaluate(clean(contains_instructions=True, authorization_valid=False))
        self.assertEqual(d.verdict, "REQUIRES_HUMAN_REVIEW")
        self.assertIn("parsing is not permission", " ".join(d.reasons))

    def test_narrative_carrying_instructions_still_refused(self):
        d = evaluate(clean(classification="NARRATIVE", contains_instructions=True,
                           authorization_valid=False))
        self.assertNotEqual(d.verdict, "AUTHORIZED")


class TestContaminationStates(unittest.TestCase):
    """§15 — no automatic CONTAMINATED -> AUTHORIZED transition."""

    def test_contaminated_never_authorizes(self):
        for st in ("CONTAMINATED", "QUARANTINED", "REJECTED", "SUSPICIOUS"):
            d = evaluate(clean(contamination_state=st))
            self.assertEqual(d.verdict, "QUARANTINED")
            self.assertFalse(d.may_influence_runtime)

    def test_quarantine_preserves_rather_than_deletes(self):
        d = evaluate(clean(contamination_state="CONTAMINATED"))
        self.assertIn("preserved", " ".join(d.reasons))

    def test_invalid_provenance_quarantines_not_trusts(self):
        d = evaluate(clean(provenance_valid=False))
        self.assertEqual(d.verdict, "QUARANTINED")


class TestNotAnIdeologicalFilter(unittest.TestCase):
    """§8 — the filter guards process, not opinion."""

    def test_criticism_of_titanos_is_not_contamination(self):
        """A rule critical of the system passes on the same terms as any other."""
        d = evaluate(clean(artifact_id="titanos-is-wrong-about-scoring"))
        self.assertEqual(d.verdict, "AUTHORIZED",
                         "dissent must not be filtered as contamination")

    def test_dissenting_evidence_is_authorized_like_any_evidence(self):
        d = evaluate(clean(classification="EVIDENCE",
                           artifact_id="refutes-core-claim"))
        self.assertEqual(d.verdict, "AUTHORIZED")


class TestGateSurface(unittest.TestCase):
    def test_allowlist_excludes_all_interpretive_classes(self):
        for cls in ("NARRATIVE", "MYTH", "METAPHOR", "PHILOSOPHY",
                    "VALUE_JUDGMENT", "SPECULATION", "UNKNOWN", "CONTAMINATED"):
            self.assertNotIn(cls, AUTHORIZED_RUNTIME_CLASSES)

    def test_unrecognised_classification_is_refused_not_defaulted(self):
        d = evaluate(clean(classification="TOTALLY_NEW_CLASS"))
        self.assertEqual(d.verdict, "REFUSED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
