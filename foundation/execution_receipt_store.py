"""Durable, atomic execution-receipt storage.

Execution receipts are historical records, not authority.  The store is
idempotent for the same receipt ID and rejects conflicting rewrites.

CROSS-PROCESS (2026-09-26). record() is load -> merge -> atomic save. The
threading lock covers one process; two processes recording different
fingerprints could interleave between load and save, and the later save
replaced the earlier one -- an executed action's receipt vanished while
its caller held a copy and its `exec:<fingerprint>` claim stood
(reproduced: 8 processes -> 8 executions, 2 receipts on disk; the shared
`.tmp` name also raced). record() now also holds an exclusive flock on
`<path>.lock`, the same pattern InstitutionalMemoryStore uses, for the
whole sequence. load() stays lock-free: save() replaces atomically, so a
reader sees a whole old or whole new file.
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
        self.lock_path = self.path.with_suffix(".lock")

    def _lock(self):
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        f = self.lock_path.open("a+")
        try:
            import fcntl
        except ImportError as exc:
            # Fail closed: without flock the cross-process guarantee this
            # lock exists for (no lost receipts) cannot be given, and a
            # silent thread-lock-only fallback would hide exactly that.
            f.close()
            raise RuntimeError(
                "execution receipt store needs flock (fcntl) for cross-process "
                "safety and refuses to record without it") from exc
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        return f

    @staticmethod
    def _unlock(f) -> None:
        import fcntl
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        f.close()

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
            lock = self._lock()
            try:
                items = self.load()
                existing = items.get(receipt.receipt_id)
                if existing is not None:
                    if existing != receipt:
                        raise ValueError("execution receipt identity collision")
                    return "DUPLICATE"
                items[receipt.receipt_id] = receipt
                self.save(items)
                return "RECORDED"
            finally:
                self._unlock(lock)

    def get(self, receipt_id: str) -> ExecutionReceipt | None:
        return self.load().get(receipt_id)
