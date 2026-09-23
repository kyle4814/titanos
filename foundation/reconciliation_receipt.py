"""Immutable evidence record for a reconciliation check."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from foundation.execution_reconciliation import ReconciliationResult

__all__ = ["ReconciliationReceipt", "reconciliation_receipt_from_result"]


@dataclass(frozen=True)
class ReconciliationReceipt:
    receipt_id: str
    execution_receipt_id: str
    fingerprint: str
    status: str
    recorded_at: str
    evidence: tuple[str, ...]
    external_reference: str

    def to_dict(self) -> dict[str, object]:
        return {
            "receipt_id": self.receipt_id,
            "execution_receipt_id": self.execution_receipt_id,
            "fingerprint": self.fingerprint,
            "status": self.status,
            "recorded_at": self.recorded_at,
            "evidence": list(self.evidence),
            "external_reference": self.external_reference,
        }


def reconciliation_receipt_from_result(
    execution_receipt_id: str,
    fingerprint: str,
    result: ReconciliationResult,
) -> ReconciliationReceipt:
    return ReconciliationReceipt(
        receipt_id=f"reconcile:{execution_receipt_id}:{result.status}",
        execution_receipt_id=execution_receipt_id,
        fingerprint=fingerprint,
        status=result.status,
        recorded_at=datetime.now(timezone.utc).isoformat(),
        evidence=result.evidence,
        external_reference=result.external_reference,
    )
