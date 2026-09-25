"""ExecutionReceiptStore.record() must not lose receipts across processes.

record() is load -> merge -> atomic save, guarded by a threading lock, which
covers one process only. Two processes recording DIFFERENT fingerprints
could interleave between load and save; the last writer's file replaced the
first writer's, and an executed action's receipt vanished while its caller
held a copy and its execution claim stood (reproduced 2026-09-26: 8
processes, 200 ms between load and save -> 8 executions, 2 receipts on
disk). The store now takes a cross-process file lock (flock on
`<path>.lock`, the pattern InstitutionalMemoryStore already uses) around
that sequence.
"""
import multiprocessing as mp
import tempfile
import time
import unittest
from pathlib import Path

from foundation.execution_receipt import ExecutionReceipt
from foundation.execution_receipt_store import ExecutionReceiptStore

KEY = b"k" * 32


class SlowSaveStore(ExecutionReceiptStore):
    """Same code path with a scheduling gap between load() and save()."""

    def save(self, items):
        time.sleep(0.15)
        super().save(items)


def _receipt(i):
    return ExecutionReceipt(
        receipt_id=f"exec:fp{i}", intent_id=f"EI-{i}", fingerprint=f"fp{i}",
        target=f"stripe:c{i}", action="CREATE_PAYMENT_LINK", status="EXECUTED",
        executed=True, recorded_at="2026-09-26T00:00:00+00:00", evidence="stripe:1",
    ).sign(KEY)


def _record_worker(path, i, barrier, q):
    barrier.wait()
    try:
        q.put((i, SlowSaveStore(path).record(_receipt(i))))
    except Exception as exc:  # noqa: BLE001
        q.put((i, type(exc).__name__ + ": " + str(exc)[:60]))


class CrossProcessReceiptStoreTests(unittest.TestCase):
    def test_eight_processes_eight_fingerprints_keep_eight_receipts(self):
        n = 8
        with tempfile.TemporaryDirectory() as td:
            path = str(Path(td) / "receipts.json")
            ctx = mp.get_context("spawn")
            q, barrier = ctx.Queue(), ctx.Barrier(n)
            procs = [ctx.Process(target=_record_worker, args=(path, i, barrier, q)) for i in range(n)]
            for p in procs:
                p.start()
            for p in procs:
                p.join()
            results = dict(q.get() for _ in procs)
            self.assertEqual(sorted(results.values()), ["RECORDED"] * n, results)
            persisted = ExecutionReceiptStore(path).load()
            self.assertEqual(sorted(persisted), sorted(f"exec:fp{i}" for i in range(n)))
            for i in range(n):
                persisted[f"exec:fp{i}"].verify(KEY, f"fp{i}")

    def test_same_receipt_from_two_processes_is_duplicate_not_collision(self):
        with tempfile.TemporaryDirectory() as td:
            path = str(Path(td) / "receipts.json")
            ctx = mp.get_context("spawn")
            q, barrier = ctx.Queue(), ctx.Barrier(2)
            procs = [ctx.Process(target=_record_worker, args=(path, 7, barrier, q)) for _ in range(2)]
            for p in procs:
                p.start()
            for p in procs:
                p.join()
            results = [q.get()[1] for _ in procs]
            self.assertEqual(sorted(results), ["DUPLICATE", "RECORDED"], results)
            self.assertEqual(len(ExecutionReceiptStore(path).load()), 1)

    def test_lock_file_is_beside_the_store_and_not_a_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            store = ExecutionReceiptStore(Path(td) / "receipts.json")
            store.record(_receipt(1))
            self.assertTrue(Path(td, "receipts.lock").exists())
            self.assertEqual(list(store.load()), ["exec:fp1"])


if __name__ == "__main__":
    unittest.main()
