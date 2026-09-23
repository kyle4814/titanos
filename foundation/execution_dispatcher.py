"""Deterministic dispatcher for already-authorized external execution.

The dispatcher selects exactly one compatible adapter. Ambiguous routing,
unsupported intents, and adapter execution failures are surfaced rather than
silently selecting a fallback.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from foundation.execution_adapter import AdapterResult, ExecutionAdapter
from foundation.execution_intent import ExecutionIntent, ExecutionIntentError

__all__ = ["AdapterDispatcher", "AdapterDispatchError"]


class AdapterDispatchError(ExecutionIntentError):
    """Raised when an intent cannot be routed unambiguously."""


@dataclass(frozen=True)
class AdapterDispatcher:
    adapters: tuple[ExecutionAdapter, ...]

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
