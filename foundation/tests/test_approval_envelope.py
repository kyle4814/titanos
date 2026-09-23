from __future__ import annotations

from datetime import datetime, timezone
import unittest

from foundation.approval_envelope import ApprovalEnvelope, ApprovalError
from foundation.execution_intent import ExecutionIntent


class TestApprovalEnvelope(unittest.TestCase):
    def setUp(self):
        self.intent = ExecutionIntent(
            intent_id="EI-APPROVAL-1",
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

    def test_approval_binds_to_exact_intent(self):
        approval = ApprovalEnvelope.decide(
            proposal_id="retry-proposal:1",
            intent=self.intent,
            decision="APPROVE",
            authority="A3",
            reviewer="kyle",
            decided_at="2026-09-23T12:00:00+00:00",
        )
        self.assertTrue(approval.is_authorized_for(
            self.intent,
            datetime(2026, 9, 23, tzinfo=timezone.utc),
        ))

    def test_changed_parameters_break_binding(self):
        approval = ApprovalEnvelope.decide(
            proposal_id="p1",
            intent=self.intent,
            decision="APPROVE",
            authority="A3",
            reviewer="kyle",
        )
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
        with self.assertRaisesRegex(ApprovalError, "fingerprint"):
            approval.validate_for(changed)

    def test_insufficient_authority_is_rejected(self):
        approval = ApprovalEnvelope.decide(
            proposal_id="p1",
            intent=self.intent,
            decision="APPROVE",
            authority="A2",
            reviewer="kyle",
        )
        with self.assertRaisesRegex(ApprovalError, "authority"):
            approval.validate_for(self.intent, datetime(2026, 9, 23, tzinfo=timezone.utc))

    def test_decline_is_not_authorization(self):
        approval = ApprovalEnvelope.decide(
            proposal_id="p1",
            intent=self.intent,
            decision="DECLINE",
            authority="A3",
            reviewer="kyle",
        )
        self.assertFalse(approval.is_authorized_for(
            self.intent,
            datetime(2026, 9, 23, tzinfo=timezone.utc),
        ))

    def test_expired_approval_is_rejected(self):
        expired = ExecutionIntent(
            intent_id=self.intent.intent_id,
            target=self.intent.target,
            action=self.intent.action,
            parameters=dict(self.intent.parameters),
            evidence_refs=self.intent.evidence_refs,
            expected_effect=self.intent.expected_effect,
            authority_required=self.intent.authority_required,
            reversible=self.intent.reversible,
            expires_at="2020-01-01T00:00:00+00:00",
            policy_version=self.intent.policy_version,
        )
        approval = ApprovalEnvelope.decide(
            proposal_id="p1",
            intent=expired,
            decision="APPROVE",
            authority="A3",
            reviewer="kyle",
        )
        with self.assertRaisesRegex(ApprovalError, "expired"):
            approval.is_authorized_for(expired, datetime.now(timezone.utc))

    def test_review_is_not_authorization(self):
        approval = ApprovalEnvelope.decide(
            proposal_id="p1",
            intent=self.intent,
            decision="REVIEW",
            authority="A3",
            reviewer="kyle",
        )
        self.assertFalse(approval.is_authorized_for(
            self.intent,
            datetime(2026, 9, 23, tzinfo=timezone.utc),
        ))


if __name__ == "__main__":
    unittest.main()
