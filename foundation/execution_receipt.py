"""Immutable execution receipt for the canonical ExecutionIntent boundary.

This is deliberately separate from the investigative Receipt: it records
what the executor did (or simulated), not whether an underlying claim is
true.  A receipt binds the execution result to the exact intent fingerprint.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from foundation.execution_executor import ExecutionResult

__all__ = ["ExecutionReceipt", "receipt_from_result"]


@dataclass(frozen=True)
class ExecutionReceipt:
    receipt_id: str
    intent_id: str
    fingerprint: str
    target: str
    action: str
    status: str
    executed: bool
    recorded_at: str
    evidence: str

    def to_dict(self) -> dict:
        return {
            "receipt_id": self.receipt_id,
            "intent_id": self.intent_id,
            "fingerprint": self.fingerprint,
            "target": self.target,
            "action": self.action,
            "status": self.status,
            "executed": self.executed,
            "recorded_at": self.recorded_at,
            "evidence": self.evidence,
        }


def receipt_from_result(result: ExecutionResult) -> ExecutionReceipt:
    """Create an immutable receipt directly from an executor result."""
    return ExecutionReceipt(
        receipt_id=f"exec:{result.fingerprint}",
        intent_id=result.intent_id,
        fingerprint=result.fingerprint,
        target=result.target,
        action=result.action,
        status=result.status,
        executed=result.executed,
        recorded_at=datetime.now(timezone.utc).isoformat(),
        evidence="\n".join(result.evidence) if result.evidence else result.simulated_effect,
    )
