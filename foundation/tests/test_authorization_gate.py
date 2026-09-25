from __future__ import annotations

from datetime import datetime, timezone
import unittest

from foundation.approval_envelope import ApprovalEnvelope, ApprovalError, ConsumedIds
from foundation.authorization_gate import AuthorizationError, AuthorizationGate
from foundation.execution_intent import ExecutionIntent

KEY = b"k" * 32  # test-only approval key

def _ledger():
    """A fresh on-disk replay ledger (ConsumedIds refuses process-local state)."""
    import tempfile as _t
    from pathlib import Path as _P
    return ConsumedIds(_P(_t.mkdtemp()) / "consumed.db")



class TestAuthorizationGate(unittest.TestCase):
    def setUp(self):
        self.intent = ExecutionIntent(
            intent_id="EI-GATE-1",
            target="stripe:customer",
            action="CREATE_PAYMENT_LINK",
            parameters={"amount": 1000, "currency": "AUD"},
            evidence_refs=("OPP-1",),
            expected_effect="create one payment link",
            authority_required="A3",
            reversible=True,
            expires_at="2099-01-01T00:00:00+00:00",
            policy_version="mothership-1",
        )

    def approval(self, decision="APPROVE", authority="A3"):
        return ApprovalEnvelope.decide(
            proposal_id="p1",
            intent=self.intent,
            decision=decision,
            authority=authority,
            reviewer="kyle",
            decided_at="2026-09-23T12:00:00+00:00",
        ).signed(KEY)

    def test_approve_issues_bound_permit(self):
        permit = AuthorizationGate.issue(
            self.intent,
            self.approval(),
            key=KEY, consumed=_ledger(),
            now=datetime(2026, 9, 23, 13, tzinfo=timezone.utc),
        )
        self.assertEqual(permit.intent_fingerprint, self.intent.fingerprint())
        self.assertEqual(permit.target, self.intent.target)
        self.assertEqual(permit.action, self.intent.action)
        self.assertEqual(permit.approved_by, "kyle")

    def test_decline_cannot_issue_permit(self):
        with self.assertRaisesRegex(AuthorizationError, "does not authorize"):
            AuthorizationGate.issue(
                self.intent,
                self.approval("DECLINE"),
                key=KEY, consumed=_ledger(),
            now=datetime(2026, 9, 23, 13, tzinfo=timezone.utc),
            )

    def test_review_cannot_issue_permit(self):
        with self.assertRaisesRegex(AuthorizationError, "does not authorize"):
            AuthorizationGate.issue(
                self.intent,
                self.approval("REVIEW"),
                key=KEY, consumed=_ledger(),
            now=datetime(2026, 9, 23, 13, tzinfo=timezone.utc),
            )

    def test_changed_intent_cannot_reuse_permit(self):
        approval = self.approval()
        changed = ExecutionIntent(
            intent_id=self.intent.intent_id,
            target=self.intent.target,
            action=self.intent.action,
            parameters={"amount": 1001, "currency": "AUD"},
            evidence_refs=self.intent.evidence_refs,
            expected_effect=self.intent.expected_effect,
            authority_required=self.intent.authority_required,
            reversible=self.intent.reversible,
            expires_at=self.intent.expires_at,
            policy_version=self.intent.policy_version,
        )
        with self.assertRaisesRegex(AuthorizationError, "fingerprint"):
            AuthorizationGate.issue(
                changed,
                approval,
                key=KEY, consumed=_ledger(),
            now=datetime(2026, 9, 23, 13, tzinfo=timezone.utc),
            )

    def test_insufficient_authority_cannot_issue_permit(self):
        with self.assertRaisesRegex(AuthorizationError, "authority"):
            AuthorizationGate.issue(
                self.intent,
                self.approval(authority="A2"),
                key=KEY, consumed=_ledger(),
            now=datetime(2026, 9, 23, 13, tzinfo=timezone.utc),
            )


if __name__ == "__main__":
    unittest.main()
