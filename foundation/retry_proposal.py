"""Explicit re-authorization proposals derived from reconciliation evidence.

A RetryProposal is a new execution candidate, never an authorization and never
an implicit retry. The caller must route it through the normal authority gate.
"""

from __future__ import annotations

from dataclasses import dataclass

from foundation.execution_intent import ExecutionIntent
from foundation.execution_reconciliation import ReconciliationResult, ReconciliationStatus
from foundation.reconciliation_receipt import ReconciliationReceipt

__all__ = ["RetryProposal", "build_retry_proposal"]


@dataclass(frozen=True)
class RetryProposal:
    proposal_id: str
    original_intent_fingerprint: str
    reconciliation_receipt_id: str
    candidate_intent: ExecutionIntent
    reason: str
    status: str = "PROPOSED"

    def to_dict(self) -> dict[str, object]:
        return {
            "proposal_id": self.proposal_id,
            "original_intent_fingerprint": self.original_intent_fingerprint,
            "reconciliation_receipt_id": self.reconciliation_receipt_id,
            "candidate_intent": self.candidate_intent.to_dict(),
            "reason": self.reason,
            "status": self.status,
        }


def build_retry_proposal(
    original: ExecutionIntent,
    reconciliation: ReconciliationReceipt,
) -> RetryProposal:
    """Build a new candidate only from a resolved-not-executed result."""
    if reconciliation.status != ReconciliationStatus.RESOLVED_NOT_EXECUTED:
        raise ValueError("only RESOLVED_NOT_EXECUTED can produce a retry proposal")
    if reconciliation.fingerprint != original.fingerprint():
        raise ValueError("reconciliation fingerprint does not match original intent")
    if not reconciliation.evidence:
        raise ValueError("retry proposal requires reconciliation evidence")

    candidate = ExecutionIntent(
        intent_id=f"{original.intent_id}:retry:{reconciliation.receipt_id}",
        target=original.target,
        action=original.action,
        parameters=dict(original.parameters),
        evidence_refs=tuple(
            dict.fromkeys(
                (*original.evidence_refs, reconciliation.receipt_id, *reconciliation.evidence)
            )
        ),
        expected_effect=original.expected_effect,
        authority_required=original.authority_required,
        reversible=original.reversible,
        expires_at=original.expires_at,
        policy_version=original.policy_version,
    )
    return RetryProposal(
        proposal_id=f"retry-proposal:{reconciliation.receipt_id}",
        original_intent_fingerprint=original.fingerprint(),
        reconciliation_receipt_id=reconciliation.receipt_id,
        candidate_intent=candidate,
        reason="external evidence resolved the original attempt as not executed",
    )
