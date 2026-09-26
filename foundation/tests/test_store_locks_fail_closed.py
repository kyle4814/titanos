"""Cross-process store locks must fail closed when flock is unavailable.

Both durable stores took an exclusive flock in `_lock()` and, on a platform
without `fcntl`, silently continued with the thread lock alone -- the
exact cross-process guarantee the lock exists for (receipt loss,
receipts.json rewrite race; institutional-memory serialization) would
have degraded without any signal. A missing integrity primitive is a
refusal, not a fallback (fail closed where data integrity is involved).
"""
import builtins
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from foundation.execution_receipt import ExecutionReceipt
from foundation.execution_receipt_store import ExecutionReceiptStore
from foundation.institutional_memory import InstitutionalMemory, InstitutionalMemoryStore
from foundation.learning_receipt import LearningReceipt

KEY = b"k" * 32


def _no_fcntl():
    real_import = builtins.__import__

    def fake(name, *a, **k):
        if name == "fcntl":
            raise ImportError("no fcntl on this platform")
        return real_import(name, *a, **k)

    return mock.patch.object(builtins, "__import__", side_effect=fake)


class StoreLocksFailClosedTests(unittest.TestCase):
    def test_receipt_store_refuses_to_record_without_flock(self):
        with tempfile.TemporaryDirectory() as td:
            store = ExecutionReceiptStore(Path(td) / "receipts.json")
            receipt = ExecutionReceipt(
                receipt_id="exec:fp1", intent_id="EI-1", fingerprint="fp1", target="t",
                action="A", status="EXECUTED", executed=True,
                recorded_at="2026-09-26T00:00:00+00:00", evidence="e").sign(KEY)
            with _no_fcntl():
                with self.assertRaisesRegex(RuntimeError, "flock"):
                    store.record(receipt)
            self.assertFalse((Path(td) / "receipts.json").exists())

    def test_institutional_memory_refuses_to_save_or_load_without_flock(self):
        with tempfile.TemporaryDirectory() as td:
            store = InstitutionalMemoryStore(Path(td) / "memory.json")
            memory = InstitutionalMemory()
            receipt = LearningReceipt.create("t", "seed", (), store._raw_payload(), store._payload(memory))
            with _no_fcntl():
                with self.assertRaisesRegex(RuntimeError, "flock"):
                    store.save(memory, receipt)
                with self.assertRaisesRegex(RuntimeError, "flock"):
                    store.load()
            self.assertFalse((Path(td) / "memory.json").exists())

    def test_with_flock_present_both_stores_work(self):
        with tempfile.TemporaryDirectory() as td:
            store = InstitutionalMemoryStore(Path(td) / "memory.json")
            memory = InstitutionalMemory()
            store.save(memory, LearningReceipt.create("t", "seed", (), store._raw_payload(), store._payload(memory)))
            self.assertIsNotNone(store.load())
            rs = ExecutionReceiptStore(Path(td) / "receipts.json")
            self.assertEqual(rs.record(ExecutionReceipt(
                receipt_id="exec:fp1", intent_id="EI-1", fingerprint="fp1", target="t",
                action="A", status="EXECUTED", executed=True,
                recorded_at="2026-09-26T00:00:00+00:00", evidence="e").sign(KEY)), "RECORDED")


if __name__ == "__main__":
    unittest.main()
