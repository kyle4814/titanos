"""
Proof that "criticism != attack" (directive §13) holds for the
integrator built this session.

firewall/dissent.py already enforces this property for the epistemic
firewall's own disagreement handling (see
firewall/tests/test_firewall.py::TestNotAnIdeologicalFilter). This file
proves the SAME property for taal/integrator/integrator.py, the one
component this session actually owns and can test directly — not for the
root-gate/integrator being built by another agent this session, which we
do not import.

We DO write a small local stub representing the general SHAPE of the
claim ("a signal that criticizes policy, with no accompanying evidence of
harmful behaviour, must not itself be classified as a security threat")
purely to state the property in prose/type form. The actual assertion
that matters is made against REAL code we own:
`propose_archetype_candidates` from taal/integrator/integrator.py.
"""

from __future__ import annotations

import unittest
from dataclasses import dataclass

from taal.integrator.integrator import (
    RawSignal, normalize, propose_archetype_candidates,
)


@dataclass(frozen=True)
class _StubGateDecision:
    """Minimal local stand-in for "a root-gate decision", NOT the real
    gate (owned by another agent, may not exist yet). Only used to state
    the shape of the property being tested in this file; the real
    assertions below run against the real integrator, not this stub.
    """
    is_flagged_as_threat: bool
    reason: str


def _stub_gate_would_flag(has_criticism: bool, has_harmful_evidence: bool) -> _StubGateDecision:
    """Illustrative stub only: a gate must require evidence of actual
    harmful behaviour (privilege escalation, unauthorized action, boundary
    crossing) before flagging — criticism alone is never sufficient. This
    function is NOT the system under test; it exists only to make the
    property statement executable in the same file as the real test.
    """
    if has_harmful_evidence:
        return _StubGateDecision(True, "harmful behaviour evidenced")
    return _StubGateDecision(False, "criticism alone is not evidence of harm")


class TestStubShapeOfTheProperty(unittest.TestCase):
    """States the property in stub form, for readability only."""

    def test_criticism_without_harm_evidence_is_not_flagged_by_stub(self):
        decision = _stub_gate_would_flag(has_criticism=True, has_harmful_evidence=False)
        self.assertFalse(decision.is_flagged_as_threat)

    def test_criticism_with_harm_evidence_is_flagged_by_stub(self):
        decision = _stub_gate_would_flag(has_criticism=True, has_harmful_evidence=True)
        self.assertTrue(decision.is_flagged_as_threat)


class TestIntegratorDoesNotTreatDissentAsThreat(unittest.TestCase):
    """The real test: feed the REAL propose_archetype_candidates (owned by
    this session, Part A) a signal that is pure policy disagreement with
    explicit evidence of NO harmful action, and assert zero candidates.
    """

    def test_written_objection_to_policy_produces_no_candidates(self):
        signal = RawSignal(
            signal_id="dissent-1",
            source_type="HUMAN_REPORT",
            entity="user:jordan",
            observed_action="disagrees with TitanOS security policy",
            affected_resource="policy-review-board",
            raw_facts=(
                "filed a written objection to the classification policy",
                "no system access attempted",
            ),
        )
        event = normalize(signal)
        candidates = propose_archetype_candidates(event)
        self.assertEqual(
            candidates, (),
            msg=(
                f"disagreement alone must never produce a threat_class "
                f"candidate, got {candidates!r}"
            ),
        )

    def test_criticism_of_a_classification_result_alone_is_not_flagged(self):
        signal = RawSignal(
            signal_id="dissent-2",
            source_type="HUMAN_REPORT",
            entity="user:morgan",
            observed_action="publicly criticized the root-gate's verdict as overreach",
            affected_resource="gate-verdict-log",
            raw_facts=(
                "wrote a blog post arguing the classification was wrong",
                "account activity remained entirely within normal permitted bounds",
                "no new system action of any kind was taken",
            ),
        )
        event = normalize(signal)
        candidates = propose_archetype_candidates(event)
        self.assertEqual(candidates, ())

    def test_same_entity_with_actual_harmful_action_still_gets_candidates(self):
        """Contrast case: this test does NOT assert dissent is punished —
        it proves the emptiness above is because of the absent evidence,
        not because the function always returns empty. Same entity,
        genuinely different facts (privilege escalation attempted).
        """
        signal = RawSignal(
            signal_id="dissent-3",
            source_type="SECURITY_TELEMETRY",
            entity="user:jordan",
            observed_action="attempted privilege escalation via sudo after policy objection was denied",
            affected_resource="prod-db",
            raw_facts=("sudo requested outside allowed window",),
        )
        event = normalize(signal)
        candidates = propose_archetype_candidates(event)
        self.assertIn("PRIVILEGE_ESCALATION_ATTEMPTS", candidates)


if __name__ == "__main__":
    unittest.main()
