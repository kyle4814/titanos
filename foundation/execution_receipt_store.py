"""Durable, atomic execution-receipt storage.

Execution receipts are historical records, not authority.  The store is
idempotent for the same receipt ID and rejects conflicting rewrites.
"""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import threading

from foundation.execution_receipt import ExecutionReceipt

__all__ = ["ExecutionReceiptStore"]


class ExecutionReceiptStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._mutation_lock = threading.RLock()

    def load(self) -> dict[str, ExecutionReceipt]:
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid persisted execution receipts") from exc
        if not isinstance(raw, dict):
            raise ValueError("persisted execution receipts must be an object")
        items: dict[str, ExecutionReceipt] = {}
        for key, value in raw.items():
            if not isinstance(key, str) or not isinstance(value, dict):
                raise ValueError("invalid persisted execution receipt entry")
            receipt = ExecutionReceipt(**value)
            if key != receipt.receipt_id:
                raise ValueError("execution receipt key/id mismatch")
            if receipt.receipt_id != f"exec:{receipt.fingerprint}":
                raise ValueError("execution receipt identity mismatch")
            items[key] = receipt
        return items

    def save(self, items: dict[str, ExecutionReceipt]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        payload = {k: asdict(v) for k, v in sorted(items.items())}
        tmp.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        try:
            tmp.replace(self.path)
        finally:
            if tmp.exists():
                tmp.unlink()

    def record(self, receipt: ExecutionReceipt) -> str:
        if not isinstance(receipt.receipt_id, str) or receipt.receipt_id != f"exec:{receipt.fingerprint}":
            raise ValueError("execution receipt identity mismatch")
        if not isinstance(receipt.fingerprint, str) or not receipt.fingerprint:
            raise ValueError("execution receipt fingerprint is required")
        with self._mutation_lock:
            items = self.load()
            existing = items.get(receipt.receipt_id)
            if existing is not None:
                if existing != receipt:
                    raise ValueError("execution receipt identity collision")
                return "DUPLICATE"
            items[receipt.receipt_id] = receipt
            self.save(items)
            return "RECORDED"

    def get(self, receipt_id: str) -> ExecutionReceipt | None:
        return self.load().get(receipt_id)
