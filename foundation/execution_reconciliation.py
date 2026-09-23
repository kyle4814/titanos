"""Reconciliation contract for uncertain external execution outcomes.

A reconciliation check observes external reality; it never authorizes a new
side effect. Concrete adapters implement the check in the private/external
integration layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from foundation.execution_intent import ExecutionIntent
from foundation.execution_receipt import ExecutionReceipt

__all__ = ["ReconciliationStatus", "ReconciliationResult", "ReconciliationAdapter"]


class ReconciliationStatus(StrEnum):
    RESOLVED_EXECUTED = "RESOLVED_EXECUTED"
    RESOLVED_NOT_EXECUTED = "RESOLVED_NOT_EXECUTED"
    STILL_UNKNOWN = "STILL_UNKNOWN"


@dataclass(frozen=True)
class ReconciliationResult:
    status: ReconciliationStatus
    evidence: tuple[str, ...] = ()
    external_reference: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "evidence": list(self.evidence),
            "external_reference": self.external_reference,
        }


@runtime_checkable
class ReconciliationAdapter(Protocol):
    name: str

    def supports(self, intent: ExecutionIntent) -> bool:
        """Return whether this adapter can inspect the exact intent family."""

    def reconcile(
        self, intent: ExecutionIntent, receipt: ExecutionReceipt
    ) -> ReconciliationResult:
        """Observe external state without creating a new side effect."""
