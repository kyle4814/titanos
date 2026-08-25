"""Tests for foundation/hells_gate.py."""

import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from foundation.hells_gate import (  # noqa: E402
    HellsGateArtifact, evaluate, quarantine_artifact, DeltaVeto,
    STATE_ADMIT, STATE_QUARANTINE, STATE_REJECT, STATE_HUMAN_REVIEW,
    TRUSTED_FORBIDDEN_STRING,
)
from firewall.quarantine import QuarantineStore  # noqa: E402


def _fully_admissible(**overrides) -> HellsGateArtifact:
    fields = dict(
        artifact_id="a1", artifact_type="code",
        stated_purpose="adds a regression test", concealed_objective_signals=(),
        harm_confirmed=(), harm_suspected=(),
        reversible=True, independently_verified=False,
        source="git commit abc123", provenance_chain=("commit:abc123",),
        claimed_capabilities=("adds a test",), verified_capabilities=("adds a test",),
        information_velocity=1.0, verification_velocity=2.0,
        requested_privileges=("write:tests",), minimum_required_privileges=("write:tests",),
        counterarguments_considered=("could be redundant with an existing test",),
        criticism_prohibited=False,
        proposes_action=True, verification_method_stated=True,
        beneficiary="future contributors", measurable_benefit="catches a real regression",
    )
    fields.update(overrides)
    return HellsGateArtifact(**fields)


class TestDefaultIsQuarantineNotAdmit(unittest.TestCase):
    def test_bare_default_artifact_is_not_admitted(self):
        d = evaluate(HellsGateArtifact(artifact_id="bare"))
        self.assertNotEqual(d.state, STATE_ADMIT)

    def test_bare_default_artifact_never_lands_on_reject(self):
        """Nothing malicious was declared, just nothing was established —
        the outcome must never be REJECT (that's reserved for confirmed
        harm or criticism-prohibited), only QUARANTINE or the stricter
        HUMAN_REVIEW_REQUIRED. Which of those two depends on which gate's
        default state is most severe (here, Gate 3's 'unverified AND
        irreversible = no admission' fires on the defaults and is more
        severe than Gate 1/4/10's QUARANTINE-level findings) — confirmed
        by actually running it rather than assumed."""
        d = evaluate(HellsGateArtifact(artifact_id="bare"))
        self.assertIn(d.state, (STATE_QUARANTINE, STATE_HUMAN_REVIEW))


class TestFullyAdmissiblePasses(unittest.TestCase):
    def test_admits_when_every_gate_genuinely_satisfied(self):
        d = evaluate(_fully_admissible())
        self.assertEqual(d.state, STATE_ADMIT)
        self.assertTrue(all(f.passed for f in d.findings))


class TestGate1Intent(unittest.TestCase):
    def test_concealed_objective_rejects(self):
        d = evaluate(_fully_admissible(concealed_objective_signals=("hidden network call",)))
        self.assertEqual(d.state, STATE_REJECT)

    def test_no_stated_purpose_quarantines(self):
        d = evaluate(_fully_admissible(stated_purpose=""))
        self.assertEqual(d.state, STATE_QUARANTINE)


class TestGate2HarmScreen(unittest.TestCase):
    def test_confirmed_harm_rejects(self):
        d = evaluate(_fully_admissible(harm_confirmed=("credential_theft",)))
        self.assertEqual(d.state, STATE_REJECT)

    def test_suspected_harm_routes_to_human_review(self):
        d = evaluate(_fully_admissible(harm_suspected=("possible privilege abuse",)))
        self.assertEqual(d.state, STATE_HUMAN_REVIEW)


class TestGate3Reversibility(unittest.TestCase):
    def test_unverified_and_irreversible_is_no_admission(self):
        d = evaluate(_fully_admissible(reversible=False, independently_verified=False))
        self.assertNotEqual(d.state, STATE_ADMIT)
        self.assertEqual(d.state, STATE_HUMAN_REVIEW)

    def test_irreversible_but_independently_verified_can_still_admit(self):
        d = evaluate(_fully_admissible(reversible=False, independently_verified=True))
        self.assertEqual(d.state, STATE_ADMIT)


class TestGate4Provenance(unittest.TestCase):
    def test_no_provenance_quarantines_not_rejects(self):
        """No provenance does not mean false — it means unverified. Must
        route to QUARANTINE, never REJECT, on this gate alone."""
        d = evaluate(_fully_admissible(source="", provenance_chain=()))
        self.assertEqual(d.state, STATE_QUARANTINE)


class TestGate5CapabilityVsClaim(unittest.TestCase):
    def test_overclaimed_capability_quarantines(self):
        d = evaluate(_fully_admissible(
            claimed_capabilities=("adds a test", "generates revenue"),
            verified_capabilities=("adds a test",),
        ))
        self.assertEqual(d.state, STATE_QUARANTINE)


class TestGate6CT141(unittest.TestCase):
    def test_panic_condition_quarantines(self):
        d = evaluate(_fully_admissible(information_velocity=10.0, verification_velocity=1.0))
        self.assertEqual(d.state, STATE_QUARANTINE)

    def test_zero_zero_is_not_panic_and_can_still_admit(self):
        d = evaluate(_fully_admissible(information_velocity=0.0, verification_velocity=0.0))
        self.assertEqual(d.state, STATE_ADMIT)


class TestGate7Privilege(unittest.TestCase):
    def test_excess_privilege_request_routes_to_human_review(self):
        d = evaluate(_fully_admissible(
            requested_privileges=("write:tests", "delete:production_db"),
            minimum_required_privileges=("write:tests",),
        ))
        self.assertEqual(d.state, STATE_HUMAN_REVIEW)


class TestGate8BlackIceReflection(unittest.TestCase):
    def test_criticism_prohibited_rejects(self):
        d = evaluate(_fully_admissible(criticism_prohibited=True))
        self.assertEqual(d.state, STATE_REJECT)

    def test_no_counterarguments_considered_quarantines(self):
        d = evaluate(_fully_admissible(counterarguments_considered=()))
        self.assertEqual(d.state, STATE_QUARANTINE)


class TestGate9ThreeRail(unittest.TestCase):
    def test_action_without_verification_method_routes_to_human_review(self):
        d = evaluate(_fully_admissible(proposes_action=True, verification_method_stated=False))
        self.assertEqual(d.state, STATE_HUMAN_REVIEW)

    def test_non_action_artifact_unaffected_by_missing_verification_method(self):
        d = evaluate(_fully_admissible(proposes_action=False, verification_method_stated=False))
        self.assertEqual(d.state, STATE_ADMIT)


class TestGate10HumanBeneficiary(unittest.TestCase):
    def test_no_beneficiary_quarantines(self):
        d = evaluate(_fully_admissible(beneficiary=""))
        self.assertEqual(d.state, STATE_QUARANTINE)

    def test_no_measurable_benefit_quarantines(self):
        d = evaluate(_fully_admissible(measurable_benefit=""))
        self.assertEqual(d.state, STATE_QUARANTINE)


class TestMostSevereFindingWins(unittest.TestCase):
    def test_reject_beats_quarantine_and_human_review_together(self):
        """A single REJECT-worthy gate must dominate even when other gates
        would independently suggest a milder outcome."""
        d = evaluate(_fully_admissible(
            harm_confirmed=("fraud",),           # REJECT
            beneficiary="",                        # QUARANTINE
            requested_privileges=("root",), minimum_required_privileges=(),  # HUMAN_REVIEW
        ))
        self.assertEqual(d.state, STATE_REJECT)

    def test_all_failing_findings_are_preserved_not_just_the_worst(self):
        d = evaluate(_fully_admissible(harm_confirmed=("fraud",), beneficiary=""))
        failed_gates = {f.gate for f in d.findings if not f.passed}
        self.assertIn("HARM_SCREEN", failed_gates)
        self.assertIn("HUMAN_BENEFICIARY", failed_gates)


class TestNeverOutputsTrusted(unittest.TestCase):
    def test_admit_state_string_is_not_bare_trusted(self):
        d = evaluate(_fully_admissible())
        self.assertNotEqual(d.state, TRUSTED_FORBIDDEN_STRING)
        self.assertEqual(d.state, "ADMITTED_UNDER_CURRENT_EVIDENCE")

    def test_no_decision_state_across_any_outcome_is_the_word_trusted(self):
        scenarios = [
            _fully_admissible(),
            HellsGateArtifact(artifact_id="bare"),
            _fully_admissible(harm_confirmed=("x",)),
            _fully_admissible(harm_suspected=("x",)),
        ]
        for artifact in scenarios:
            d = evaluate(artifact)
            self.assertNotEqual(d.state.strip(), TRUSTED_FORBIDDEN_STRING)


class TestDeltaVetoStructure(unittest.TestCase):
    def test_veto_requires_all_four_fields(self):
        with self.assertRaises(ValueError):
            DeltaVeto(rejection_reason="bad", evidence="", counterexample="x", remediation_path="y")

    def test_complete_veto_constructs(self):
        v = DeltaVeto(rejection_reason="requests excess privilege",
                     evidence="requested_privileges includes delete:production_db",
                     counterexample="a read-only variant would satisfy the stated purpose",
                     remediation_path="narrow requested_privileges to write:tests only")
        self.assertTrue(v.rejection_reason)


class TestQuarantineIntegration(unittest.TestCase):
    """Proves QUARANTINE decisions actually route through the real
    firewall.quarantine.QuarantineStore, not a parallel mechanism."""

    def test_quarantine_decision_is_actually_contained(self):
        artifact = _fully_admissible(beneficiary="")  # -> QUARANTINE
        decision = evaluate(artifact)
        self.assertEqual(decision.state, STATE_QUARANTINE)

        store = QuarantineStore()
        record = quarantine_artifact(store, decision, content="artifact body here")
        self.assertEqual(record.state, "QUARANTINED")
        self.assertIn("Hell's Gate", record.reason)
        self.assertEqual(record.preserved_content, "artifact body here")

    def test_non_quarantine_decision_refused_by_quarantine_artifact(self):
        decision = evaluate(_fully_admissible())  # -> ADMIT
        store = QuarantineStore()
        with self.assertRaises(ValueError):
            quarantine_artifact(store, decision, content="x")


class TestSerialization(unittest.TestCase):
    def test_to_dict_shape(self):
        d = evaluate(_fully_admissible()).to_dict()
        self.assertIn("state", d)
        self.assertIn("findings", d)
        self.assertEqual(len(d["findings"]), 10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
