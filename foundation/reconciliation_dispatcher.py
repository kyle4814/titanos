"""Deterministic routing for read-only execution reconciliation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from foundation.execution_intent import ExecutionIntent, ExecutionIntentError
from foundation.execution_receipt import ExecutionReceipt
from foundation.execution_reconciliation import (
    ReconciliationAdapter,
    ReconciliationResult,
)

__all__ = ["ReconciliationDispatcher", "ReconciliationDispatchError"]


class ReconciliationDispatchError(ExecutionIntentError):
    """Raised when reconciliation cannot be routed unambiguously."""


@dataclass(frozen=True)
class ReconciliationDispatcher:
    adapters: tuple[ReconciliationAdapter, ...]

    @classmethod
    def from_adapters(
        cls, adapters: Iterable[ReconciliationAdapter]
    ) -> "ReconciliationDispatcher":
        return cls(tuple(adapters))

    def select(
        self, intent: ExecutionIntent, receipt: ExecutionReceipt
    ) -> ReconciliationAdapter:
        matches = tuple(
            adapter
            for adapter in self.adapters
            if adapter.supports(intent)
        )
        if not matches:
            raise ReconciliationDispatchError(
                "no reconciliation adapter supports this intent"
            )
        if len(matches) > 1:
            names = ", ".join(
                getattr(adapter, "name", "<unnamed>") for adapter in matches
            )
            raise ReconciliationDispatchError(
                f"ambiguous reconciliation adapters: {names}"
            )
        return matches[0]

    def reconcile(
        self, intent: ExecutionIntent, receipt: ExecutionReceipt
    ) -> ReconciliationResult:
        if receipt.fingerprint != intent.fingerprint():
            raise ReconciliationDispatchError(
                "receipt fingerprint does not match the exact ExecutionIntent"
            )
        if receipt.status == "EXECUTED" and receipt.executed:
            raise ReconciliationDispatchError(
                "confirmed execution does not require reconciliation"
            )
        return self.select(intent, receipt).reconcile(intent, receipt)
