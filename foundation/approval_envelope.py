"""Machine-readable human approval envelope for consequential execution.

An approval is bound to one exact ExecutionIntent fingerprint. It is not a
generic permission and cannot be reused for a materially different action.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from foundation.execution_intent import ExecutionIntent, ExecutionIntentError

__all__ = ["ApprovalDecision", "ApprovalEnvelope", "ApprovalError"]


ApprovalDecision = Literal["APPROVE", "DECLINE", "REVIEW"]


class ApprovalError(ExecutionIntentError):
    """Raised when an approval envelope is invalid or does not bind."""


@dataclass(frozen=True)
class ApprovalEnvelope:
    proposal_id: str
    intent_fingerprint: str
    decision: ApprovalDecision
    authority: str
    policy_version: str
    expires_at: str
    target: str
    action: str
    expected_effect: str
    decided_at: str
    reviewer: str

    @classmethod
    def decide(
        cls,
        *,
        proposal_id: str,
        intent: ExecutionIntent,
        decision: ApprovalDecision,
        authority: str,
        reviewer: str,
        decided_at: str | None = None,
    ) -> "ApprovalEnvelope":
        if decision not in ("APPROVE", "DECLINE", "REVIEW"):
            raise ApprovalError("decision must be APPROVE, DECLINE, or REVIEW")
        if not authority.strip() or not reviewer.strip():
            raise ApprovalError("authority and reviewer must be non-empty")
        return cls(
            proposal_id=proposal_id,
            intent_fingerprint=intent.fingerprint(),
            decision=decision,
            authority=authority,
            policy_version=intent.policy_version,
            expires_at=intent.expires_at,
            target=intent.target,
            action=intent.action,
            expected_effect=intent.expected_effect,
            decided_at=decided_at or datetime.now(timezone.utc).isoformat(),
            reviewer=reviewer,
        )

    def validate_for(self, intent: ExecutionIntent, now: datetime | None = None) -> None:
        if self.intent_fingerprint != intent.fingerprint():
            raise ApprovalError("approval does not bind to the exact intent fingerprint")
        if self.target != intent.target or self.action != intent.action:
            raise ApprovalError("approval target/action mismatch")
        if self.policy_version != intent.policy_version:
            raise ApprovalError("approval policy version mismatch")
        if self.expires_at != intent.expires_at:
            raise ApprovalError("approval expiry mismatch")
        if self.expected_effect != intent.expected_effect:
            raise ApprovalError("approval expected-effect mismatch")
        expiry = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
        current = now or datetime.now(timezone.utc)
        if expiry <= current:
            raise ApprovalError("approval is expired")

    def is_authorized_for(self, intent: ExecutionIntent, now: datetime | None = None) -> bool:
        self.validate_for(intent, now)
        return self.decision == "APPROVE"

    def to_dict(self) -> dict[str, object]:
        return {
            "proposal_id": self.proposal_id,
            "intent_fingerprint": self.intent_fingerprint,
            "decision": self.decision,
            "authority": self.authority,
            "policy_version": self.policy_version,
            "expires_at": self.expires_at,
            "target": self.target,
            "action": self.action,
            "expected_effect": self.expected_effect,
            "decided_at": self.decided_at,
            "reviewer": self.reviewer,
        }
