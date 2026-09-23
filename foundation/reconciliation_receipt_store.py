"""Durable atomic storage for reconciliation evidence."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import threading

from foundation.reconciliation_receipt import ReconciliationReceipt

__all__ = ["ReconciliationReceiptStore"]


class ReconciliationReceiptStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._mutation_lock = threading.RLock()

    def load(self) -> dict[str, ReconciliationReceipt]:
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid persisted reconciliation receipts") from exc
        if not isinstance(raw, dict):
            raise ValueError("persisted reconciliation receipts must be an object")
        items: dict[str, ReconciliationReceipt] = {}
        for key, value in raw.items():
            if not isinstance(key, str) or not isinstance(value, dict):
                raise ValueError("invalid persisted reconciliation receipt entry")
            receipt = ReconciliationReceipt(
                receipt_id=value["receipt_id"],
                execution_receipt_id=value["execution_receipt_id"],
                fingerprint=value["fingerprint"],
                status=value["status"],
                recorded_at=value["recorded_at"],
                evidence=tuple(value["evidence"]),
                external_reference=value["external_reference"],
            )
            if key != receipt.receipt_id:
                raise ValueError("reconciliation receipt key/id mismatch")
            if not receipt.receipt_id.startswith("reconcile:"):
                raise ValueError("reconciliation receipt identity mismatch")
            items[key] = receipt
        return items

    def save(self, items: dict[str, ReconciliationReceipt]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(
                {k: asdict(v) for k, v in sorted(items.items())},
                indent=2,
                sort_keys=True,
                default=lambda value: list(value) if isinstance(value, tuple) else value,
            ) + "\n",
            encoding="utf-8",
        )
        try:
            tmp.replace(self.path)
        finally:
            if tmp.exists():
                tmp.unlink()

    def record(self, receipt: ReconciliationReceipt) -> str:
        with self._mutation_lock:
            items = self.load()
            existing = items.get(receipt.receipt_id)
            if existing is not None:
                if existing != receipt:
                    raise ValueError("reconciliation receipt identity collision")
                return "DUPLICATE"
            items[receipt.receipt_id] = receipt
            self.save(items)
            return "RECORDED"

    def get(self, receipt_id: str) -> ReconciliationReceipt | None:
        return self.load().get(receipt_id)
