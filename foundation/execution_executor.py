"""Fail-safe execution boundary for canonical ExecutionIntent approvals.

No real external action is performed here.  The boundary requires an explicit
approval binding before returning a simulated execution result.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from foundation.execution_intent import ExecutionIntent, ExecutionIntentError

__all__ = ["ExecutionResult", "dry_run", "approved_dry_run"]


@dataclass(frozen=True)
class ExecutionResult:
    status: str
    intent_id: str
    fingerprint: str
    target: str
    action: str
    simulated_effect: str
    executed: bool = False

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "intent_id": self.intent_id,
            "fingerprint": self.fingerprint,
            "target": self.target,
            "action": self.action,
            "simulated_effect": self.simulated_effect,
            "executed": self.executed,
        }


def _validate(intent: ExecutionIntent) -> str:
    try:
        fingerprint = intent.fingerprint()
    except Exception as exc:
        raise ExecutionIntentError("intent could not be fingerprinted") from exc
    expires = datetime.fromisoformat(intent.expires_at.replace("Z", "+00:00"))
    if expires <= datetime.now(timezone.utc):
        raise ExecutionIntentError("execution intent is expired")
    return fingerprint


def dry_run(intent: ExecutionIntent) -> ExecutionResult:
    """Simulate an intent without requiring or performing an action."""
    return ExecutionResult(
        status="DRY_RUN",
        intent_id=intent.intent_id,
        fingerprint=_validate(intent),
        target=intent.target,
        action=intent.action,
        simulated_effect=intent.expected_effect,
    )


def approved_dry_run(intent: ExecutionIntent, approved_fingerprint: str) -> ExecutionResult:
    """Simulate execution only when approval binds to this exact intent."""
    fingerprint = _validate(intent)
    if approved_fingerprint != fingerprint:
        raise ExecutionIntentError(
            "approval fingerprint does not match the exact ExecutionIntent"
        )
    return ExecutionResult(
        status="APPROVED_DRY_RUN",
        intent_id=intent.intent_id,
        fingerprint=fingerprint,
        target=intent.target,
        action=intent.action,
        simulated_effect=intent.expected_effect,
    )
