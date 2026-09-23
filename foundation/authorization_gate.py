"""Final pre-execution authorization gate.

This module does not perform external side effects. It converts a valid,
unexpired APPROVE envelope into a short-lived execution permit bound to the
same immutable intent. DECLINE, REVIEW, mismatches, insufficient authority,
and expired approvals are rejected.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from foundation.approval_envelope import ApprovalEnvelope, ApprovalError
from foundation.execution_intent import ExecutionIntent

__all__ = ["ExecutionPermit", "AuthorizationGate", "AuthorizationError"]


class AuthorizationError(ApprovalError):
    """Raised when an execution permit cannot be issued."""


@dataclass(frozen=True)
class ExecutionPermit:
    intent_fingerprint: str
    target: str
    action: str
    authority: str
    policy_version: str
    expires_at: str
    approved_by: str
    approval_decision: str = "APPROVE"

    def to_dict(self) -> dict[str, object]:
        return {
            "intent_fingerprint": self.intent_fingerprint,
            "target": self.target,
            "action": self.action,
            "authority": self.authority,
            "policy_version": self.policy_version,
            "expires_at": self.expires_at,
            "approved_by": self.approved_by,
            "approval_decision": self.approval_decision,
        }


class AuthorizationGate:
    """The final deterministic boundary immediately before an executor."""

    @staticmethod
    def issue(
        intent: ExecutionIntent,
        approval: ApprovalEnvelope,
        *,
        now: datetime | None = None,
    ) -> ExecutionPermit:
        current = now or datetime.now(timezone.utc)
        if approval.decision != "APPROVE":
            raise AuthorizationError(
                f"decision {approval.decision!r} does not authorize execution"
            )
        try:
            approval.validate_for(intent, current)
        except ApprovalError as exc:
            raise AuthorizationError(str(exc)) from exc
        return ExecutionPermit(
            intent_fingerprint=intent.fingerprint(),
            target=intent.target,
            action=intent.action,
            authority=approval.authority,
            policy_version=intent.policy_version,
            expires_at=intent.expires_at,
            approved_by=approval.reviewer,
        )
