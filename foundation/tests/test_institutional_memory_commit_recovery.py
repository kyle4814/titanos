"""Recovery from a crash after the memory write, before the ledger commit.

Durable state at that instant: journal PREPARED (with the staged ledger
entry hash), memory file at the new payload with the receipt persisted
verbatim, ledger head unchanged. The previous payload is retained nowhere,
so rollback is impossible; but the staged entry can be rebuilt from the
persisted receipt and the current head, and it is trusted only if its hash
reproduces the journal's. Pinned 2026-09-26 (frontier 3(b)).
"""
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from foundation.institutional_memory import InstitutionalMemory, InstitutionalMemoryStore
from foundation.learning_receipt import LearningReceipt
from foundation.opportunity_feedback import OutcomeFeedback


def _crash_at_commit(td):
    store = InstitutionalMemoryStore(Path(td) / "memory.json")
    memory = InstitutionalMemory()
    before = store._payload(memory)
    memory.opportunity_learning.record(
        OutcomeFeedback("x", 10, 15, True, 1.0, "2026-09-24T00:00:00+00:00"))
    after = store._payload(memory)
    receipt = LearningReceipt.create("recovery", "commit-crash", ("x",), before, after,
                                     observed_at="2026-09-24T00:00:00+00:00")
    store.ledger.commit = lambda *_: (_ for _ in ()).throw(RuntimeError("crash"))
    try:
        store.save(memory, receipt)
    except RuntimeError:
        pass
    return receipt


class CommitPhaseRecoveryTests(unittest.TestCase):
    def test_commit_crash_is_finalized_from_durable_evidence(self):
        with TemporaryDirectory() as td:
            receipt = _crash_at_commit(td)
            recovered = InstitutionalMemoryStore(Path(td) / "memory.json")  # fresh process
            tx = recovered.journal.load()
            self.assertEqual(tx["status"], "PREPARED")
            self.assertEqual(recovered.ledger.read(), [])

            self.assertEqual(recovered.reconcile(), "FINALIZED")

            rows = recovered.ledger.read()
            self.assertEqual([r["receipt"]["receipt_id"] for r in rows], [receipt.receipt_id])
            self.assertEqual(rows[0]["entry_hash"], tx["ledger_entry_hash"])
            self.assertTrue(recovered.ledger.verify())
            self.assertIsNone(recovered.journal.load())
            self.assertEqual(
                recovered.load().opportunity_learning.records["x"][0].realized_value, 15)
            # Idempotent: nothing left to do.
            self.assertEqual(recovered.reconcile(), "CLEAN")

    def test_commit_crash_with_a_receipt_that_does_not_reproduce_the_journal_stays_unresolved(self):
        with TemporaryDirectory() as td:
            _crash_at_commit(td)
            path = Path(td) / "memory.json"
            raw = json.loads(path.read_text())
            raw["receipt"]["actor"] = "someone-else"  # receipt no longer matches the staged entry
            path.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n")

            recovered = InstitutionalMemoryStore(path)
            with self.assertRaisesRegex(ValueError, "unresolved"):
                recovered.reconcile()
            # Fail closed: no ledger entry was fabricated, journal still open.
            self.assertEqual(recovered.ledger.read(), [])
            self.assertIsNotNone(recovered.journal.load())


if __name__ == "__main__":
    unittest.main()
