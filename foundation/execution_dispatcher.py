"""Deterministic dispatcher for already-authorized external execution.

The dispatcher selects exactly one compatible adapter. Ambiguous routing,
unsupported intents, and adapter execution failures are surfaced rather than
silently selecting a fallback.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from typing import TYPE_CHECKING, Iterable
import threading

from foundation import communication_gate
from foundation.execution_adapter import AdapterResult, ExecutionAdapter
from foundation.execution_executor import (
    ExecutionResult,
    _validate,
)
from foundation.execution_intent import ExecutionIntent, ExecutionIntentError
from foundation.execution_receipt import ExecutionReceipt, receipt_from_result

if TYPE_CHECKING:
    from foundation.execution_receipt_store import ExecutionReceiptStore

__all__ = ["AdapterDispatcher", "AdapterDispatchError", "ExecutionPaused"]


class AdapterDispatchError(ExecutionIntentError):
    """Raised when an intent cannot be routed unambiguously."""


class ExecutionPaused(AdapterDispatchError):
    """The global pause (`communication_gate.PAUSE_FILENAME`) is present.
    Raised before any adapter runs and before any receipt is recorded, so a
    paused attempt leaves nothing behind that would block it after resume."""


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

    # The gateway (AdapterExecutionGateway.execute_permitted) is the only
    # public route to an adapter. These two names used to run an adapter with
    # no permit at all (execute) or with a caller-computable fingerprint
    # (execute_approved_with_receipt). They are kept only so a stale caller
    # fails closed with a pointer, instead of silently executing.
    def execute(self, *_args, **_kwargs):
        raise AdapterDispatchError(
            "AdapterDispatcher.execute is not a public execution route; "
            "use AdapterExecutionGateway.execute_permitted with an ExecutionPermit")

    def execute_approved_with_receipt(self, *_args, **_kwargs):
        raise AdapterDispatchError(
            "AdapterDispatcher.execute_approved_with_receipt is not a public "
            "execution route; use AdapterExecutionGateway.execute_permitted")

    def _execute(self, intent: ExecutionIntent) -> AdapterResult:
        return self._execute_adapter(self.select(intent), intent)

    @staticmethod
    def _execute_adapter(adapter: ExecutionAdapter, intent: ExecutionIntent) -> AdapterResult:
        # Every adapter invocation in this repository passes through here, so
        # the global pause is enforced once, ahead of any approval, however
        # valid.
        if communication_gate.is_paused():
            raise ExecutionPaused(
                f"execution of {intent.action} on {intent.target} is PAUSED: "
                f"{communication_gate.PAUSE_FILENAME} is present")
        try:
            result = adapter.execute(intent)
        except Exception as exc:
            # An adapter exception cannot prove that the external side effect
            # did not happen. Preserve that uncertainty explicitly.
            return AdapterResult(
                status="UNKNOWN",
                effect="adapter execution raised an exception",
                executed=False,
                evidence=(f"{type(exc).__name__}: {exc}",),
            )

        allowed = {"EXECUTED", "FAILED", "TIMEOUT", "UNKNOWN", "PARTIAL"}
        if result.status not in allowed:
            raise AdapterDispatchError(
                f"unsupported adapter result status: {result.status}"
            )
        if result.status == "UNKNOWN" and result.executed:
            raise AdapterDispatchError(
                "adapter cannot report UNKNOWN with executed=True"
            )
        if result.status == "TIMEOUT" and result.executed:
            raise AdapterDispatchError(
                "adapter cannot report TIMEOUT with executed=True"
            )
        return result

    def _execute_approved_with_receipt(
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
        result = self._execute_adapter(adapter, intent)
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
