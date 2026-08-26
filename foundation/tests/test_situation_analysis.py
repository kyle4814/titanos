"""Unit tests for foundation/situation_analysis.py — Monk pass, Demonblade
pass, and the structural block preventing a non-SURVIVED analysis from
becoming a MAGL candidate. See test_situation_analysis_end_to_end.py for
the full vertical slice through the real MAGL/RPA/Crystal gates."""

import inspect
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from kpm.schemas.epistemic_types import classify_claim  # noqa: E402
from foundation.situation_analysis import (  # noqa: E402
    AnalysisNotSurvived,
    CandidateAction,
    build_magl_candidate,
    demonblade_pass,
    monk_pass,
    record_situation_crystal,
)


def _claim(claim_id, text, classification, by="tester", confidence="MEDIUM"):
    return classify_claim(claim_id, text, classification, by, confidence=confidence)


class TestMonkPass(unittest.TestCase):
    def test_structures_a_minimal_situation(self):
        analysis = monk_pass(
            "sit-1", "a bounded automation is proposed",
            actors=("clerk", "backup-approver"), goals=("reduce delay",),
            constraints=("no write access",), known_information=(),
            unknowns=("roster staleness",), assumptions=(), candidate_actions=(),
            evidence_refs=(), analyzed_by="tester",
        )
        self.assertEqual(analysis.situation_id, "sit-1")
        self.assertEqual(analysis.actors, ("clerk", "backup-approver"))

    def test_never_invents_a_missing_field(self):
        analysis = monk_pass(
            "sit-2", "framing", actors=(), goals=(), constraints=(),
            known_information=(), unknowns=(), assumptions=(),
            candidate_actions=(), evidence_refs=(), analyzed_by="tester",
        )
        self.assertEqual(analysis.actors, ())
        self.assertEqual(analysis.unknowns, ())

    def test_rejects_unattributed_analysis(self):
        with self.assertRaises(ValueError):
            monk_pass(
                "sit-3", "framing", actors=(), goals=(), constraints=(),
                known_information=(), unknowns=(), assumptions=(),
                candidate_actions=(), evidence_refs=(), analyzed_by="",
            )

    def test_rejects_unrecognised_claim_classification(self):
        bad_claim = classify_claim("c-1", "text", "TECHNICAL_DESIGN", "tester")
        object.__setattr__(bad_claim, "classification", "NOT_A_REAL_CLASS")
        with self.assertRaises(ValueError):
            monk_pass(
                "sit-4", "framing", actors=(), goals=(), constraints=(),
                known_information=(bad_claim,), unknowns=(), assumptions=(),
                candidate_actions=(), evidence_refs=(), analyzed_by="tester",
            )


class TestDemonbladePass(unittest.TestCase):
    def test_survives_when_every_dependency_is_evidence_backed(self):
        claim = _claim("c-1", "bottleneck confirmed", "VERIFIED_FACT",
                        confidence="HIGH")
        analysis = monk_pass(
            "sit-5", "framing", actors=("clerk",), goals=("reduce delay",),
            constraints=(), known_information=(claim,),
            unknowns=("edge case",), assumptions=(),
            candidate_actions=(
                CandidateAction("act-1", "notify backup approver",
                                 depends_on_claim_ids=("c-1",)),
            ),
            evidence_refs=("evidence://c-1",), analyzed_by="tester",
        )
        verdict = demonblade_pass(analysis, attacked_by="red-team")
        self.assertEqual(verdict.verdict, "SURVIVED")
        self.assertEqual(verdict.contradiction_candidates, ())
        self.assertTrue(verdict.reason)

    def test_killed_when_action_depends_on_a_bare_assumption(self):
        analysis = monk_pass(
            "sit-6", "framing", actors=("clerk",), goals=(),
            constraints=(), known_information=(),
            unknowns=(), assumptions=("roster is always current",),
            candidate_actions=(
                CandidateAction("act-1", "auto-approve on backup's behalf",
                                 depends_on_claim_ids=("roster is always current",)),
            ),
            evidence_refs=(), analyzed_by="tester",
        )
        verdict = demonblade_pass(analysis, attacked_by="red-team")
        self.assertEqual(verdict.verdict, "KILLED")
        self.assertIn("unsupported premise", verdict.reason)

    def test_killed_when_action_depends_on_unevidenced_claim(self):
        claim = _claim("c-2", "probably fine", "SPECULATIVE_HYPOTHESIS")
        analysis = monk_pass(
            "sit-7", "framing", actors=(), goals=(), constraints=(),
            known_information=(claim,), unknowns=("x",), assumptions=(),
            candidate_actions=(
                CandidateAction("act-1", "proceed anyway",
                                 depends_on_claim_ids=("c-2",)),
            ),
            evidence_refs=(), analyzed_by="tester",
        )
        verdict = demonblade_pass(analysis, attacked_by="red-team")
        self.assertEqual(verdict.verdict, "KILLED")
        self.assertIn("equivalence-fraud risk", verdict.reason)

    def test_killed_when_action_cites_an_undeclared_reference(self):
        analysis = monk_pass(
            "sit-8", "framing", actors=(), goals=(), constraints=(),
            known_information=(), unknowns=("x",), assumptions=(),
            candidate_actions=(
                CandidateAction("act-1", "proceed",
                                 depends_on_claim_ids=("nothing-declared",)),
            ),
            evidence_refs=(), analyzed_by="tester",
        )
        verdict = demonblade_pass(analysis, attacked_by="red-team")
        self.assertEqual(verdict.verdict, "KILLED")

    def test_is_pure_same_input_same_output(self):
        claim = _claim("c-1", "x", "VERIFIED_FACT", confidence="HIGH")
        analysis = monk_pass(
            "sit-9", "framing", actors=(), goals=(), constraints=(),
            known_information=(claim,), unknowns=("x",), assumptions=(),
            candidate_actions=(
                CandidateAction("act-1", "y", depends_on_claim_ids=("c-1",)),
            ),
            evidence_refs=("e",), analyzed_by="tester",
        )
        v1 = demonblade_pass(analysis, attacked_by="red-team")
        v2 = demonblade_pass(analysis, attacked_by="red-team")
        self.assertEqual(v1, v2)

    def test_rejects_unattributed_attack(self):
        analysis = monk_pass(
            "sit-10", "framing", actors=(), goals=(), constraints=(),
            known_information=(), unknowns=(), assumptions=(),
            candidate_actions=(), evidence_refs=(), analyzed_by="tester",
        )
        with self.assertRaises(ValueError):
            demonblade_pass(analysis, attacked_by="")


class TestNeitherPassCanAuthorizeOrExecute(unittest.TestCase):
    """Mirrors foundation/tests/test_sentinel.py::TestSentinelCannotExecute."""

    _FORBIDDEN_VERBS = {
        "execute", "apply", "commit", "write", "delete", "run",
        "authorize", "approve", "promote", "grant", "admit", "register",
    }

    def test_no_public_callable_uses_a_forbidden_execution_verb(self):
        import foundation.situation_analysis as mod
        for name, obj in inspect.getmembers(mod):
            if name.startswith("_") or not (inspect.isfunction(obj) or inspect.isclass(obj)):
                continue
            first_word = name.split("_")[0].lower()
            self.assertNotIn(
                first_word, self._FORBIDDEN_VERBS,
                f"public callable '{name}' starts with a forbidden execution "
                f"verb — Monk/Demonblade must only analyse/propose.",
            )

    def test_module_source_has_no_direct_store_writes(self):
        import foundation.situation_analysis as mod
        source = inspect.getsource(mod)
        # monk_pass/demonblade_pass themselves must never instantiate or
        # write to ContradictionRegistry/CrystalStore/PromotionStore/
        # MAGLCatalogue directly — build_magl_candidate/
        # record_situation_crystal only ever construct plain data or
        # delegate to a caller-supplied store's own .record(), never
        # instantiate a store themselves.
        for forbidden in ("ContradictionRegistry(", "PromotionStore(",
                          "MAGLCatalogue(", ".resolve(", "subprocess.",
                          "os.remove(", "unlink("):
            self.assertNotIn(forbidden, source)


class TestBuildMaglCandidateCannotBypassSurvival(unittest.TestCase):
    """The one structural control this module adds: a killed analysis
    cannot become a MAGL candidate at all."""

    def test_killed_verdict_is_refused(self):
        analysis = monk_pass(
            "sit-11", "framing", actors=(), goals=(), constraints=(),
            known_information=(), unknowns=(), assumptions=(),
            candidate_actions=(
                CandidateAction("act-1", "proceed",
                                 depends_on_claim_ids=("nothing-declared",)),
            ),
            evidence_refs=(), analyzed_by="tester",
        )
        verdict = demonblade_pass(analysis, attacked_by="red-team")
        self.assertEqual(verdict.verdict, "KILLED")
        with self.assertRaises(AnalysisNotSurvived):
            build_magl_candidate(
                analysis, verdict, version="1.0.0", name="x", domain=("test",),
                capability_type=("ANALYTICAL",), maturity="EXPERIMENTAL",
                license="MIT", content_hash="sha256:deadbeef",
            )

    def test_survived_verdict_produces_a_candidate(self):
        claim = _claim("c-1", "x", "VERIFIED_FACT", confidence="HIGH")
        analysis = monk_pass(
            "sit-12", "framing", actors=(), goals=(), constraints=(),
            known_information=(claim,), unknowns=("x",), assumptions=(),
            candidate_actions=(
                CandidateAction("act-1", "y", depends_on_claim_ids=("c-1",)),
            ),
            evidence_refs=("e",), analyzed_by="tester",
        )
        verdict = demonblade_pass(analysis, attacked_by="red-team")
        entry, summary = build_magl_candidate(
            analysis, verdict, version="1.0.0", name="x", domain=("test",),
            capability_type=("ANALYTICAL",), maturity="EXPERIMENTAL",
            license="MIT", content_hash="sha256:deadbeef",
        )
        self.assertEqual(entry.magl_id, "sit-12")
        self.assertEqual(entry.epistemic_status, "TECHNICAL_DESIGN")
        self.assertEqual(summary.magl_id, "sit-12")


class TestRecordSituationCrystal(unittest.TestCase):
    def test_records_a_readable_crystal(self):
        from foundation.crystal import CrystalStore

        claim = _claim("c-1", "x", "VERIFIED_FACT", confidence="HIGH")
        analysis = monk_pass(
            "sit-13", "framing", actors=(), goals=(), constraints=(),
            known_information=(claim,), unknowns=("x",), assumptions=(),
            candidate_actions=(
                CandidateAction("act-1", "y", depends_on_claim_ids=("c-1",)),
            ),
            evidence_refs=("e",), analyzed_by="tester",
        )
        verdict = demonblade_pass(analysis, attacked_by="red-team")
        store = CrystalStore()
        crystal = record_situation_crystal(
            store, analysis, verdict, crystal_id="crys-1",
            hypothesis="action y is bounded and safe to pilot",
            provenance="sha256:deadbeef", epistemic_status="TECHNICAL_DESIGN",
            recorded_by="tester",
        )
        self.assertEqual(crystal.result, "SURVIVED")
        reread = store.get("crys-1")
        self.assertIsNotNone(reread)
        self.assertTrue(reread.reusable_abstraction)


if __name__ == "__main__":
    unittest.main(verbosity=2)
