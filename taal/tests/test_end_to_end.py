"""
§16 demonstration — the four required examples, wired through the real
integrator, root gate, and quarantine mapping (not narrated).

  1. BENIGN example -> AUTHORIZED
  2. SUSPICIOUS example -> QUARANTINED (via taal_quarantine, the real
     firewall.quarantine.QuarantineStore underneath)
  3. AMBIGUOUS example -> REQUIRES_HUMAN_REVIEW (UNKNOWN != malicious)
  4. FALSE-POSITIVE RECOVERY -> quarantined, then reviewed, then recovered,
     preserving the original evidence throughout (nothing deleted)
"""

import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from taal.integrator.integrator import RawSignal, normalize, propose_archetype_candidates  # noqa: E402
from taal.gate.root_gate import GateInput, evaluate_request  # noqa: E402
from taal.gate.quarantine_mapping import (  # noqa: E402
    taal_quarantine, taal_mark_reviewed, taal_mark_recovered,
)
from firewall.quarantine import QuarantineStore  # noqa: E402


class TestBenignRequestAuthorized(unittest.TestCase):
    """A fully verified, low-impact, evidenced, non-contradicted request
    with a mundane signal behind it -> AUTHORIZED. Proves the gate can say
    yes, not just refuse everything."""

    def test_benign_read_request_authorized(self):
        signal = RawSignal(
            signal_id="sig-benign-001", source_type="ACCESS_REQUEST",
            entity="reporting-service", observed_action="requested read access",
            affected_resource="quarterly_sales_summary",
            raw_facts=("scheduled monthly report generation job",
                      "identical request pattern for 8 consecutive months"),
        )
        event = normalize(signal)
        candidates = propose_archetype_candidates(event)
        self.assertEqual(candidates, (), "a routine scheduled read should propose no threat candidates")

        decision = evaluate_request(GateInput(
            request_id="req-benign-001", requester="reporting-service",
            action="READ", resource="quarterly_sales_summary",
            scope="declared_dataset", duration="15m",
            identity_verified=True, authority_asserted=True,
            authority_evidence=("service account role: reporting-readonly",),
            scope_declared_necessary=True, reversible=True,
            provenance_status="VERIFIED",
            supporting_evidence=("monthly job schedule record",),
        ))
        self.assertEqual(decision.verdict, "AUTHORIZED", decision.reasons)


class TestSuspiciousRequestQuarantined(unittest.TestCase):
    """Unverified identity + contradictory evidence + high impact ->
    the gate refuses/escalates, and the event is actually quarantined in
    the real store (not a simulated one)."""

    def test_suspicious_request_quarantined_via_real_store(self):
        signal = RawSignal(
            signal_id="sig-suspicious-001", source_type="ACCESS_REQUEST",
            entity="unknown-service-account-77",
            observed_action="requested credential access",
            affected_resource="production_database_credentials",
            raw_facts=("first request ever seen from this account",
                      "requested at 03:14 local time outside normal hours",
                      "access log shows unauthorized access attempt recorded prior to this request"),
        )
        event = normalize(signal)
        candidates = propose_archetype_candidates(event)
        # credential access + no prior authority is exactly what
        # AUTHORIZATION_ABUSE / PRIVILEGE_ESCALATION_ATTEMPTS candidates exist for
        self.assertTrue(len(candidates) >= 1, candidates)

        decision = evaluate_request(GateInput(
            request_id="req-suspicious-001", requester="unknown-service-account-77",
            action="CREDENTIAL_ACCESS", resource="production_database_credentials",
            scope="all_credentials", duration="indefinite",
            identity_verified=False, authority_asserted=True,
            authority_evidence=(), provenance_status="UNVERIFIABLE",
            contradictory_evidence=("no prior authority grant on file",),
            high_impact=True, reversible=False,
        ))
        self.assertIn(decision.verdict, ("REFUSED", "QUARANTINED", "REQUIRES_HUMAN_REVIEW"))
        self.assertNotIn(decision.verdict, ("AUTHORIZED", "AUTHORIZED_WITH_CONSTRAINTS"))

        store = QuarantineStore()
        record = taal_quarantine(
            store, artifact_id="req-suspicious-001",
            content=f"signal={signal.signal_id} candidates={candidates} "
                    f"gate_verdict={decision.verdict}",
            reason=f"root gate returned {decision.verdict}: {'; '.join(decision.reasons)}",
            provenance={"signal_id": signal.signal_id, "entity": signal.entity},
        )
        self.assertEqual(record.state, "QUARANTINED")
        self.assertIn(signal.signal_id, record.preserved_content)


class TestAmbiguousRequestRequiresHumanReview(unittest.TestCase):
    """Genuinely unknown provenance, no contradictory evidence, not
    obviously hostile -> REQUIRES_HUMAN_REVIEW, never REFUSED outright and
    never AUTHORIZED. UNKNOWN != malicious, proven structurally."""

    def test_ambiguous_request_is_human_review_not_refused_or_authorized(self):
        signal = RawSignal(
            signal_id="sig-ambiguous-001", source_type="AI_TOOL_REQUEST",
            entity="agent-worker-14", observed_action="requested tool call",
            affected_resource="external_notification_api",
            raw_facts=("new agent, no prior request history",
                      "declared justification present but not independently verified"),
        )
        event = normalize(signal)
        candidates = propose_archetype_candidates(event)

        decision = evaluate_request(GateInput(
            request_id="req-ambiguous-001", requester="agent-worker-14",
            action="NETWORK_CALL", resource="external_notification_api",
            scope="single_notification", duration="1m",
            identity_verified=True,  # the agent's identity IS verified
            authority_asserted=True, authority_evidence=("declared workflow config",),
            scope_declared_necessary=True, reversible=True,
            provenance_status="UNKNOWN",  # but provenance of the REQUEST is unknown
            supporting_evidence=("declared workflow config",),
        ))
        self.assertEqual(decision.verdict, "REQUIRES_HUMAN_REVIEW", decision.reasons)
        self.assertNotEqual(decision.verdict, "REFUSED",
                            "unknown must not collapse to refused, that would treat "
                            "uncertainty as guilt")
        self.assertNotIn(decision.verdict, ("AUTHORIZED", "AUTHORIZED_WITH_CONSTRAINTS"),
                         "unknown must never be silently promoted to authorized")


class TestFalsePositiveRecovery(unittest.TestCase):
    """A quarantined event that turns out to be legitimate is reviewed and
    recovered — and the original evidence survives the whole cycle,
    because false positives are training data, not embarrassments to
    delete (§11 of the governing directive)."""

    def test_quarantine_review_recover_preserves_evidence(self):
        store = QuarantineStore()
        original_content = "entity=new-vendor-integration action=READ resource=shared_calendar"
        record = taal_quarantine(
            store, artifact_id="req-fp-001", content=original_content,
            reason="new, unrecognised integration requesting calendar read access",
            provenance={"entity": "new-vendor-integration"},
        )
        self.assertEqual(record.state, "QUARANTINED")

        reviewed = taal_mark_reviewed(
            store, artifact_id="req-fp-001",
            reason="confirmed with vendor management: this integration was approved "
                   "last week, onboarding record found",
            reviewed_by="security-operator-jane",
        )
        self.assertEqual(reviewed.state, "VERIFIED")
        self.assertEqual(reviewed.preserved_content, original_content,
                         "evidence must survive review unchanged")

        recovered = taal_mark_recovered(
            store, artifact_id="req-fp-001",
            reason="false positive confirmed, releasing to normal operation",
        )
        self.assertEqual(recovered.state, "AUTHORIZED")
        self.assertEqual(recovered.preserved_content, original_content,
                         "evidence must survive recovery unchanged — false positives "
                         "are preserved as training data, never deleted")
        # The full cycle is visible in history — nothing was silently skipped.
        transitions = [h["to"] for h in recovered.history]
        self.assertEqual(transitions, ["QUARANTINED", "VERIFIED", "AUTHORIZED"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
