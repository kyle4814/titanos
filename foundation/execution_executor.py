"""Fail-safe execution boundary for canonical ExecutionIntent approvals.

No real external action is performed here. The boundary requires explicit
approval binding and can optionally persist the resulting execution receipt.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from foundation.execution_intent import ExecutionIntent, ExecutionIntentError
from foundation.execution_receipt import ExecutionReceipt, receipt_from_result

if TYPE_CHECKING:
    from foundation.execution_receipt_store import ExecutionReceiptStore

__all__ = [
    "ExecutionResult",
    "dry_run",
    "approved_dry_run",
    "approved_dry_run_with_receipt",
]


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
    return ExecutionResult(
        status="DRY_RUN",
        intent_id=intent.intent_id,
        fingerprint=_validate(intent),
        target=intent.target,
        action=intent.action,
        simulated_effect=intent.expected_effect,
    )


def approved_dry_run(intent: ExecutionIntent, approved_fingerprint: str) -> ExecutionResult:
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


def approved_dry_run_with_receipt(
    intent: ExecutionIntent,
    approved_fingerprint: str,
    receipt_store: ExecutionReceiptStore,
) -> ExecutionReceipt:
    """Run the approved dry-run boundary and persist exactly one receipt."""
    result = approved_dry_run(intent, approved_fingerprint)
    receipt = receipt_from_result(result)
    receipt_store.record(receipt)
    return receipt
