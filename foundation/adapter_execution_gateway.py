"""Canonical bridge from approved intents to adapter execution and receipts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from foundation.execution_adapter import AdapterResult
from foundation.execution_dispatcher import AdapterDispatcher
from foundation.execution_executor import _validate
from foundation.execution_intent import ExecutionIntent, ExecutionIntentError
from foundation.execution_receipt import ExecutionReceipt

if TYPE_CHECKING:
    from foundation.execution_receipt_store import ExecutionReceiptStore

__all__ = ["AdapterExecutionGateway"]


@dataclass(frozen=True)
class AdapterExecutionGateway:
    dispatcher: AdapterDispatcher
    receipt_store: ExecutionReceiptStore

    def execute_approved(
        self,
        intent: ExecutionIntent,
        approved_fingerprint: str,
    ) -> ExecutionReceipt:
        """Execute exactly the approved intent and persist its adapter receipt."""
        fingerprint = _validate(intent)
        if approved_fingerprint != fingerprint:
            raise ExecutionIntentError(
                "approval fingerprint does not match the exact ExecutionIntent"
            )

        # Same idempotency contract as ExecutionDispatcher: never re-execute an
        # intent that already has a receipt; return the recorded one.
        existing = self.receipt_store.get(f"exec:{fingerprint}")
        if existing is not None:
            return existing

        result: AdapterResult = self.dispatcher.execute(intent)
        receipt = ExecutionReceipt(
            receipt_id=f"exec:{fingerprint}",
            intent_id=intent.intent_id,
            fingerprint=fingerprint,
            target=intent.target,
            action=intent.action,
            status=result.status,
            executed=result.executed,
            recorded_at=__import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
            evidence="; ".join(result.evidence) or result.effect,
        )
        self.receipt_store.record(receipt)
        return receipt
