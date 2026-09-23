from __future__ import annotations

import unittest

from foundation.execution_intent import ExecutionIntent
from foundation.execution_reconciliation import ReconciliationStatus
from foundation.reconciliation_receipt import ReconciliationReceipt
from foundation.retry_proposal import build_retry_proposal


class TestRetryProposal(unittest.TestCase):
    def setUp(self):
        self.intent = ExecutionIntent(
            intent_id="EI-RETRY-1",
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

    def receipt(self, status=ReconciliationStatus.RESOLVED_NOT_EXECUTED):
        return ReconciliationReceipt(
            receipt_id="reconcile:exec-1:RESOLVED_NOT_EXECUTED",
            execution_receipt_id="exec-1",
            fingerprint=self.intent.fingerprint(),
            status=status,
            recorded_at="2026-09-23T00:00:00+00:00",
            evidence=("provider:absent",),
            external_reference="",
        )

    def test_builds_new_candidate_bound_to_reconciliation(self):
        proposal = build_retry_proposal(self.intent, self.receipt())
        self.assertEqual(proposal.status, "PROPOSED")
        self.assertNotEqual(
            proposal.candidate_intent.intent_id, self.intent.intent_id
        )
        self.assertIn(
            proposal.reconciliation_receipt_id,
            proposal.candidate_intent.evidence_refs,
        )
        self.assertIn("provider:absent", proposal.candidate_intent.evidence_refs)

    def test_never_builds_from_confirmed_execution(self):
        with self.assertRaisesRegex(ValueError, "RESOLVED_NOT_EXECUTED"):
            build_retry_proposal(
                self.intent,
                self.receipt(ReconciliationStatus.RESOLVED_EXECUTED),
            )

    def test_fingerprint_mismatch_is_rejected(self):
        other = ExecutionIntent(
            **{**self.intent.__dict__, "intent_id": "EI-OTHER"}
        )
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            build_retry_proposal(other, self.receipt())


if __name__ == "__main__":
    unittest.main()
