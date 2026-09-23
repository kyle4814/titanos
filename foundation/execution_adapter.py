"""Adapter contract for externally meaningful execution.

The contract is deliberately credential-free and side-effect-neutral. Concrete
adapters (Stripe, GitHub, email, tenders, Web3, private business systems, etc.)
live outside the core kernel and receive an already-authorized ExecutionIntent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, runtime_checkable

from foundation.execution_intent import ExecutionIntent
from foundation.execution_executor import ExecutionResult

__all__ = ["ExecutionAdapter", "AdapterResult"]


@dataclass(frozen=True)
class AdapterResult:
    """Normalized adapter outcome; it does not itself grant authority."""

    status: str
    effect: str
    executed: bool
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "effect": self.effect,
            "executed": self.executed,
            "evidence": list(self.evidence),
        }


@runtime_checkable
class ExecutionAdapter(Protocol):
    """Minimal contract for one external action family."""

    name: str

    def supports(self, intent: ExecutionIntent) -> bool:
        """Return whether this adapter can handle the exact intent family."""

    def execute(self, intent: ExecutionIntent) -> AdapterResult:
        """Execute an already-authorized intent and return an auditable result."""
