"""Immutable execution receipt for the canonical ExecutionIntent boundary.

This is deliberately separate from the investigative Receipt: it records
what the executor did (or simulated), not whether an underlying claim is
true.  A receipt binds the execution result to the exact intent fingerprint.

PROVENANCE (2026-09-26). `receipt_id == f"exec:{fingerprint}"` is a
self-consistency check, not an authenticity check -- any caller can
construct a `ExecutionReceipt` that satisfies it. A receipt now carries an
optional HMAC-SHA256 `mac` (domain "receipt-v1", same key-and-MAC primitive
already used for `ApprovalEnvelope`/`ExecutionPermit`) over its own
canonical fields. `sign()`/`verify()` mirror `ApprovalEnvelope.signed()`/
`verify_mac()` exactly: whoever holds the Ring 0 key can produce a receipt
that verifies; nobody else can. A receipt with no `mac`, a wrong `mac`, or
a `mac` that doesn't match the expected fingerprint is not proof that the
underlying action ever happened -- `verify()` raises `ReceiptIntegrityError`
fail-closed rather than returning False, so a caller cannot forget to check
it. This module still constructs and returns *unsigned* receipts
(`receipt_from_result`, `mac=""`) for the legacy dry-run/dispatcher paths
that predate this fix and have no production caller today; only
`AdapterExecutionGateway.execute_permitted` (the one path this closes) signs
what it persists and verifies what it reads back.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import TYPE_CHECKING
import hmac

from foundation.approval_envelope import compute_mac
from foundation.execution_intent import ExecutionIntentError

if TYPE_CHECKING:
    # Type-only: execution_executor imports this module at load time to build
    # receipts, so a runtime import here is circular (introduced dc68e9e4).
    from foundation.execution_executor import ExecutionResult

__all__ = [
    "ExecutionReceipt", "ReceiptIntegrityError", "receipt_from_result",
]

RECEIPT_MAC_DOMAIN = "receipt-v1"


class ReceiptIntegrityError(ExecutionIntentError):
    """A stored receipt's provenance does not verify: missing/invalid MAC,
    or bound to a different fingerprint than the one being checked. Never
    raised for lack of information -- an absent receipt is simply `None`
    from the store; this is only raised for a receipt that exists but
    cannot be trusted."""


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
    mac: str = ""

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
            "mac": self.mac,
        }

    def signing_payload(self) -> dict[str, object]:
        """Every field except `mac` -- the exact bytes the MAC binds. Covers
        every field that matters (status, executed, evidence, target,
        action, fingerprint), so tampering any one of them breaks
        verification, not only the fingerprint."""
        payload = self.to_dict()
        payload.pop("mac")
        return payload

    def sign(self, key: bytes) -> "ExecutionReceipt":
        """Ring 0: only the legitimate execution path holds `key`."""
        return replace(self, mac=compute_mac(key, RECEIPT_MAC_DOMAIN, self.signing_payload()))

    def verify(self, key: bytes, expected_fingerprint: str) -> None:
        """Raises ReceiptIntegrityError unless this receipt was signed by
        `key` for exactly `expected_fingerprint`. Fail-closed: an empty,
        malformed, forged, or fingerprint-mismatched `mac` all raise the
        same way, and a valid MAC for a *different* fingerprint is refused
        even though the MAC itself verifies (the fingerprint is checked
        both inside the signed payload and again explicitly here)."""
        expected_mac = compute_mac(key, RECEIPT_MAC_DOMAIN, self.signing_payload())
        if not isinstance(self.mac, str) or not self.mac or not hmac.compare_digest(self.mac, expected_mac):
            raise ReceiptIntegrityError(
                f"execution receipt {self.receipt_id!r} has no valid provenance MAC; "
                "refusing to treat it as proof of execution"
            )
        if self.fingerprint != expected_fingerprint:
            raise ReceiptIntegrityError(
                f"execution receipt {self.receipt_id!r} is bound to a different fingerprint"
            )
        if self.receipt_id != f"exec:{self.fingerprint}":
            raise ReceiptIntegrityError(
                f"execution receipt {self.receipt_id!r} id/fingerprint binding is invalid"
            )


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
