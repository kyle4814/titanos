"""Final pre-execution authorization gate.

This module does not perform external side effects. It converts a valid,
unexpired APPROVE envelope into a short-lived execution permit bound to the
same immutable intent. DECLINE, REVIEW, mismatches, insufficient authority,
and expired approvals are rejected.

AUTHENTICITY (2026-09-25). The envelope's HMAC is verified with the approval
key before anything else is trusted, its nonce is consumed exactly once, and
the permit minted here carries its own MAC and single-use `permit_id`. An
`ExecutionPermit(...)` built by hand has no valid MAC, so the gateway refuses
it: approval authorizes permit issuance, the permit authorizes execution, and
neither can be asserted by a caller. Nothing is issued while globally paused.
"""

from __future__ import annotations

import hmac
import secrets
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone

from foundation import communication_gate
from foundation.approval_envelope import (
    AlreadyConsumedError, ApprovalEnvelope, ApprovalError, ConsumedIds,
    compute_mac, parameter_hash,
)
from foundation.execution_intent import ExecutionIntent

__all__ = ["ExecutionPermit", "AuthorizationGate", "AuthorizationError", "ApprovalReplayed"]

# An envelope stamped further in the future than this was not issued by a
# clock we trust.
MAX_CLOCK_SKEW = timedelta(seconds=60)


class AuthorizationError(ApprovalError):
    """Raised when an execution permit cannot be issued."""


class ApprovalReplayed(AuthorizationError, AlreadyConsumedError):
    """An approval nonce or permit id that was already consumed. Both an
    authorization refusal and the ledger's domain-level replay result."""


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
    permit_id: str = ""
    mac: str = ""

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
            "permit_id": self.permit_id,
            "mac": self.mac,
        }

    def _payload(self) -> dict[str, object]:
        payload = self.to_dict()
        payload.pop("mac")
        return payload

    def verify(self, key: bytes, intent_fingerprint: str,
               now: datetime | None = None) -> None:
        """Raises AuthorizationError unless this permit was minted by the
        gate under `key`, for exactly this intent, and has not expired."""
        expected = compute_mac(key, "permit-v1", self._payload())
        if not isinstance(self.mac, str) or not hmac.compare_digest(self.mac, expected):
            raise AuthorizationError("execution permit MAC is missing or invalid")
        if self.intent_fingerprint != intent_fingerprint:
            raise AuthorizationError("execution permit is for a different intent")
        expiry = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
        if expiry <= (now or datetime.now(timezone.utc)):
            raise AuthorizationError("execution permit is expired")


class AuthorizationGate:
    """The final deterministic boundary immediately before an executor."""

    @staticmethod
    def issue(
        intent: ExecutionIntent,
        approval: ApprovalEnvelope,
        *,
        key: bytes,
        consumed: ConsumedIds,
        now: datetime | None = None,
    ) -> ExecutionPermit:
        current = now or datetime.now(timezone.utc)
        if communication_gate.is_paused():
            raise AuthorizationError(
                f"permit issuance is PAUSED: {communication_gate.PAUSE_FILENAME} is present")
        if not isinstance(approval, ApprovalEnvelope):
            raise AuthorizationError(
                f"approval must be a signed ApprovalEnvelope, not {type(approval).__name__}")
        if not isinstance(consumed, ConsumedIds):
            raise AuthorizationError("a ConsumedIds ledger is required for replay protection")
        try:
            approval.verify_mac(key)
        except ApprovalError as exc:
            raise AuthorizationError(str(exc)) from exc
        if approval.decision != "APPROVE":
            raise AuthorizationError(
                f"decision {approval.decision!r} does not authorize execution"
            )
        try:
            approval.validate_for(intent, current)
        except ApprovalError as exc:
            raise AuthorizationError(str(exc)) from exc
        if approval.intent_id != intent.intent_id:
            raise AuthorizationError("approval is for a different intent id")
        if approval.parameter_hash != parameter_hash(intent):
            raise AuthorizationError("approval parameter hash does not match the intent")
        try:
            issued = datetime.fromisoformat(approval.decided_at.replace("Z", "+00:00"))
        except (AttributeError, ValueError) as exc:
            raise AuthorizationError("approval decided_at is not ISO-8601") from exc
        if issued.tzinfo is None or issued > current + MAX_CLOCK_SKEW:
            raise AuthorizationError("approval decided_at is in the future")
        # Consumed last, so an envelope that fails any check above is not
        # burned; one that passes can never mint a second permit.
        try:
            consumed.consume(f"approval:{approval.nonce}")
        except AlreadyConsumedError as exc:
            raise ApprovalReplayed(str(exc)) from exc
        permit = ExecutionPermit(
            intent_fingerprint=intent.fingerprint(),
            target=intent.target,
            action=intent.action,
            authority=approval.authority,
            policy_version=intent.policy_version,
            expires_at=intent.expires_at,
            approved_by=approval.reviewer,
            permit_id=secrets.token_hex(16),
        )
        return replace(permit, mac=compute_mac(key, "permit-v1", permit._payload()))
