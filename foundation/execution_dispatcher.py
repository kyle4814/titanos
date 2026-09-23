"""Deterministic dispatcher for already-authorized external execution.

The dispatcher selects exactly one compatible adapter. Ambiguous routing,
unsupported intents, and adapter execution failures are surfaced rather than
silently selecting a fallback.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from typing import TYPE_CHECKING, Iterable
import threading

from foundation.execution_adapter import AdapterResult, ExecutionAdapter
from foundation.execution_executor import (
    ExecutionResult,
    _validate,
)
from foundation.execution_intent import ExecutionIntent, ExecutionIntentError
from foundation.execution_receipt import ExecutionReceipt, receipt_from_result

if TYPE_CHECKING:
    from foundation.execution_receipt_store import ExecutionReceiptStore

__all__ = ["AdapterDispatcher", "AdapterDispatchError"]


class AdapterDispatchError(ExecutionIntentError):
    """Raised when an intent cannot be routed unambiguously."""


@dataclass(frozen=True)
class AdapterDispatcher:
    adapters: tuple[ExecutionAdapter, ...]
    _execution_lock: threading.RLock = dataclass_field(default_factory=threading.RLock, init=False, repr=False, compare=False)

    @classmethod
    def from_adapters(cls, adapters: Iterable[ExecutionAdapter]) -> "AdapterDispatcher":
        return cls(tuple(adapters))

    def select(self, intent: ExecutionIntent) -> ExecutionAdapter:
        matches = tuple(adapter for adapter in self.adapters if adapter.supports(intent))
        if not matches:
            raise AdapterDispatchError("no execution adapter supports this intent")
        if len(matches) > 1:
            names = ", ".join(getattr(adapter, "name", "<unnamed>") for adapter in matches)
            raise AdapterDispatchError(f"ambiguous execution adapters: {names}")
        return matches[0]

    def execute(self, intent: ExecutionIntent) -> AdapterResult:
        return self.select(intent).execute(intent)

    def execute_approved_with_receipt(
        self,
        intent: ExecutionIntent,
        approved_fingerprint: str,
        receipt_store: "ExecutionReceiptStore",
    ) -> ExecutionReceipt:
        """Execute one approved intent and durably record its normalized result.

        An existing receipt for the exact fingerprint is returned without
        invoking the adapter again, making retries safe at the kernel boundary.
        """
        with self._execution_lock:
            return self._execute_approved_with_receipt_locked(intent, approved_fingerprint, receipt_store)

    def _execute_approved_with_receipt_locked(
        self,
        intent: ExecutionIntent,
        approved_fingerprint: str,
        receipt_store: "ExecutionReceiptStore",
    ) -> ExecutionReceipt:
        fingerprint = _validate(intent)
        if approved_fingerprint != fingerprint:
            raise ExecutionIntentError(
                "approval fingerprint does not match the exact ExecutionIntent"
            )

        receipt_id = f"exec:{fingerprint}"
        existing = receipt_store.get(receipt_id)
        if existing is not None:
            return existing

        adapter = self.select(intent)
        result = adapter.execute(intent)
        execution = ExecutionResult(
            status=result.status,
            intent_id=intent.intent_id,
            fingerprint=fingerprint,
            target=intent.target,
            action=intent.action,
            simulated_effect=result.effect,
            executed=result.executed,
            evidence=result.evidence,
        )
        receipt = receipt_from_result(execution)
        receipt_store.record(receipt)
        return receipt
