"""Fail-safe executor boundary for canonical ExecutionIntent proposals.

The dry-run executor deliberately performs no external I/O and grants no
authority. It validates that the supplied intent remains the exact immutable
proposal, then returns a machine-readable simulation result. Real adapters
must sit behind the same boundary and be separately authorized.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from foundation.execution_intent import ExecutionIntent, ExecutionIntentError

__all__ = ["ExecutionResult", "dry_run"]


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


def dry_run(intent: ExecutionIntent) -> ExecutionResult:
    """Validate and simulate an intent without performing external action."""
    try:
        fingerprint = intent.fingerprint()
    except Exception as exc:
        raise ExecutionIntentError("intent could not be fingerprinted") from exc

    expires = datetime.fromisoformat(intent.expires_at.replace("Z", "+00:00"))
    if expires <= datetime.now(timezone.utc):
        raise ExecutionIntentError("execution intent is expired")

    return ExecutionResult(
        status="DRY_RUN",
        intent_id=intent.intent_id,
        fingerprint=fingerprint,
        target=intent.target,
        action=intent.action,
        simulated_effect=intent.expected_effect,
    )
