"""Canonical bridge from approved intents to adapter execution and receipts.

The gateway is the ONLY public route to an adapter. It accepts only an
`ExecutionPermit` minted by `AuthorizationGate` (verified by its MAC, bound to
the exact intent fingerprint, unexpired, and consumed exactly once in the
SQLite ledger). It previously accepted a bare `approved_fingerprint` string,
which any caller could compute from the intent itself -- approval was a
claim, not a proof. That entry point was removed on 2026-09-25, and the
dispatcher's execution methods became private the same day.

A gateway cannot exist without a valid Ring 0 key: the constructor refuses an
invalid one, and `boot_gateway()` reads it from TITANOS_RING0_SECRET with no
fallback, before the dispatcher or any adapter is built.

RECEIPT PROVENANCE (2026-09-26). The idempotency check below used to be
`receipt_store.get(f"exec:{fingerprint}")` -- if anything under that key
existed at all, it was returned as proof the intent had already executed.
Nothing bound that record to the legitimate execution path: a planted,
corrupted, or legacy-unsigned receipt file entry would silently short-circuit
execution and hand back fabricated "evidence". Every receipt this gateway
persists is now signed with the same Ring 0 key (`ExecutionReceipt.sign`,
domain "receipt-v1", distinct from "permit-v1" and "approval-v1" so one MAC
can never be replayed as another), and every existing receipt is verified
(`ExecutionReceipt.verify`) before being trusted. A receipt that fails
verification is not silently accepted (that was the hole) and not silently
re-executed either (an adapter side effect may not be safely repeatable, and
this gateway cannot know whether the untrusted record reflects a real prior
execution) -- it raises `ReceiptIntegrityError` and refuses to proceed,
fail-closed, the same posture this repository already takes for execution,
publication and credential actions. The check-existing/execute/persist
sequence is now serialized under the dispatcher's own `_execution_lock`
(already used by `AdapterDispatcher._execute_approved_with_receipt` for the
same reason) so two concurrent permitted calls for the same fingerprint
cannot both observe "no receipt yet" and both execute the adapter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Mapping, Optional

from foundation import communication_gate
from foundation.approval_envelope import (
    AlreadyConsumedError, ConsumedIds, _check_key, load_ring0_key,
)
# ConsumptionUnavailable (ledger locked/unreachable) is deliberately NOT
# caught anywhere below: an infrastructure failure must surface as one,
# never be mistaken for a domain-level "already executed".
from foundation.authorization_gate import (
    ApprovalReplayed, AuthorizationError, ExecutionPermit,
)
from foundation.execution_adapter import AdapterResult, ExecutionAdapter
from foundation.execution_dispatcher import AdapterDispatcher, ExecutionPaused
from foundation.execution_executor import _validate
from foundation.execution_intent import ExecutionIntent
from foundation.execution_receipt import ExecutionReceipt, ReceiptIntegrityError

if TYPE_CHECKING:
    from foundation.execution_receipt_store import ExecutionReceiptStore

__all__ = ["AdapterExecutionGateway", "ExecutionClaimed", "ReceiptIntegrityError", "boot_gateway"]


class ExecutionClaimed(AuthorizationError):
    """Another process holds the `exec:<fingerprint>` claim and no authentic
    receipt is persisted yet (it is mid-execution, or it crashed after
    claiming). The adapter may already have acted, so this caller must not
    run it again: fail closed and let a human or a later call that finds
    the receipt resolve it."""


@dataclass(frozen=True)
class AdapterExecutionGateway:
    dispatcher: AdapterDispatcher
    receipt_store: ExecutionReceiptStore
    key: bytes = field(repr=False)
    consumed: ConsumedIds = field(repr=False)

    def __post_init__(self) -> None:
        _check_key(self.key)
        if not isinstance(self.consumed, ConsumedIds):
            raise AuthorizationError("a ConsumedIds ledger is required for replay protection")

    def execute_permitted(self, intent: ExecutionIntent,
                          permit: ExecutionPermit) -> ExecutionReceipt:
        """Execute exactly the permitted intent and persist its adapter receipt."""
        # Checked before the permit is consumed, so a pause never burns it.
        if communication_gate.is_paused():
            raise ExecutionPaused(
                f"execution of {intent.action} on {intent.target} is PAUSED: "
                f"{communication_gate.PAUSE_FILENAME} is present")
        if not isinstance(permit, ExecutionPermit):
            raise AuthorizationError(
                f"an ExecutionPermit is required, not {type(permit).__name__}")
        fingerprint = _validate(intent)
        permit.verify(self.key, fingerprint)
        try:
            self.consumed.consume(f"permit:{permit.permit_id}")
        except AlreadyConsumedError as exc:
            raise ApprovalReplayed(str(exc)) from exc
        # Serialize check-existing/execute/persist so two concurrent permitted
        # calls for the same fingerprint (e.g. two independently issued,
        # individually valid permits) cannot both see "no receipt yet" and
        # both run the adapter. Same lock AdapterDispatcher already uses for
        # the equivalent legacy sequence.
        with self.dispatcher._execution_lock:
            # Same idempotency contract as ExecutionDispatcher: never
            # re-execute an intent that already has a receipt -- but only a
            # receipt this gateway can prove it minted. An existing record
            # that fails provenance verification is neither trusted nor
            # silently re-executed; see the module docstring.
            existing = self._authentic_receipt(fingerprint)
            if existing is not None:
                return existing
            # The thread lock above covers one process. Across processes the
            # single-use ledger decides: exactly one caller claims
            # `exec:<fingerprint>` (SQLite PRIMARY KEY, BEGIN IMMEDIATE) and
            # executes. A loser either finds the winner's authentic receipt
            # or refuses -- it never runs the adapter a second time. Claimed
            # after the permit is consumed, so a loser has spent its permit on
            # an intent that is being executed exactly once, and before the
            # adapter, so nothing external happens without the claim.
            try:
                self.consumed.consume(f"exec:{fingerprint}")
            except AlreadyConsumedError as exc:
                existing = self._authentic_receipt(fingerprint)
                if existing is not None:
                    return existing
                raise ExecutionClaimed(
                    f"execution of {intent.action} on {intent.target} is claimed by "
                    "another process and no authentic receipt exists yet; refusing "
                    "to execute again") from exc
            result: AdapterResult = self.dispatcher._execute(intent)
            receipt = ExecutionReceipt(
                receipt_id=f"exec:{fingerprint}",
                intent_id=intent.intent_id,
                fingerprint=fingerprint,
                target=intent.target,
                action=intent.action,
                status=result.status,
                executed=result.executed,
                recorded_at=datetime.now(timezone.utc).isoformat(),
                evidence="; ".join(result.evidence) or result.effect,
            ).sign(self.key)
            self.receipt_store.record(receipt)
            return receipt

    def _authentic_receipt(self, fingerprint: str) -> Optional[ExecutionReceipt]:
        """The persisted receipt for `fingerprint`, or None if absent. A
        persisted record that fails provenance verification raises: it is
        neither trusted nor a licence to re-execute."""
        existing = self.receipt_store.get(f"exec:{fingerprint}")
        if existing is None:
            return None
        try:
            existing.verify(self.key, fingerprint)
        except ReceiptIntegrityError as exc:
            raise ReceiptIntegrityError(
                f"stored receipt {existing.receipt_id!r} failed provenance "
                "verification; refusing to trust it as proof of execution "
                "and refusing to blindly re-execute a possibly-already-"
                f"executed intent: {exc}"
            ) from exc
        return existing


def boot_gateway(adapters: Iterable[ExecutionAdapter], receipt_store: ExecutionReceiptStore,
                 ledger_path: Path, *,
                 environ: Optional[Mapping[str, str]] = None) -> AdapterExecutionGateway:
    """Production construction. The Ring 0 secret is loaded and validated
    FIRST; if it is missing or unusable this raises Ring0SecretError before
    the ledger, the dispatcher or any adapter is touched."""
    key = load_ring0_key(environ)
    consumed = ConsumedIds(ledger_path)
    return AdapterExecutionGateway(
        AdapterDispatcher.from_adapters(tuple(adapters)), receipt_store, key, consumed)
