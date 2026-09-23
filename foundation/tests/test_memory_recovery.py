import tempfile,unittest
from pathlib import Path
from foundation.institutional_memory import InstitutionalMemory,InstitutionalMemoryStore
from foundation.learning_receipt import LearningReceipt

class TestMemoryRecovery(unittest.TestCase):
    def test_clean_reconcile(self):
        with tempfile.TemporaryDirectory() as td:
            s=InstitutionalMemoryStore(Path(td)/"memory.json")
            self.assertEqual(s.reconcile(),"CLEAN")
    def test_completed_transaction_is_cleared(self):
        with tempfile.TemporaryDirectory() as td:
            s=InstitutionalMemoryStore(Path(td)/"memory.json")
            s.journal.begin("t","r","old","new","head")
            s.journal.mark_committed()
            self.assertEqual(s.reconcile(),"COMMITTED_CLEARED")
            self.assertIsNone(s.journal.load())
    def test_guarded_abort_clears_matching_prepared_transaction(self):
        with tempfile.TemporaryDirectory() as td:
            s=InstitutionalMemoryStore(Path(td)/"memory.json")
            s.journal.begin("tx-1","r","old","new","head")
            s.journal.abort("tx-1")
            self.assertIsNone(s.journal.load())

    def test_guarded_abort_rejects_wrong_transaction(self):
        with tempfile.TemporaryDirectory() as td:
            s=InstitutionalMemoryStore(Path(td)/"memory.json")
            s.journal.begin("tx-1","r","old","new","head")
            with self.assertRaises(ValueError): s.journal.abort("tx-2")
            self.assertIsNotNone(s.journal.load())


    def test_unresolved_transaction_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            s=InstitutionalMemoryStore(Path(td)/"memory.json")
            s.journal.begin("t","r","old","new","head")
            with self.assertRaises(ValueError): s.reconcile()

    def test_concurrent_writers_serialize_transaction(self):
        import multiprocessing

        def worker(path, result_queue):
            store=InstitutionalMemoryStore(path)
            memory=InstitutionalMemory()
            before={}
            payload=store._payload(memory)
            receipt=LearningReceipt.create("worker","concurrent-save",(),before,payload)
            try:
                store.save(memory,receipt)
                result_queue.put("saved")
            except ValueError:
                result_queue.put("rejected")

        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"memory.json"
            queue=multiprocessing.Queue()
            processes=[multiprocessing.Process(target=worker,args=(path,queue)) for _ in range(2)]
            for process in processes: process.start()
            for process in processes: process.join()

            results=[queue.get() for _ in processes]
            self.assertEqual(results.count("saved"),1)
            self.assertEqual(results.count("rejected"),1)

            store=InstitutionalMemoryStore(path)
            self.assertTrue(store.ledger.verify())
            self.assertEqual(len(store.ledger.read()),1)
            self.assertIsNone(store.journal.load())
            store.load()


    def test_crash_after_memory_write_rolls_back(self):
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"memory.json"
            store=InstitutionalMemoryStore(path)
            memory=InstitutionalMemory()
            before=store._raw_payload()
            payload=store._payload(memory)
            receipt=LearningReceipt.create("worker","crash-after-memory",(),before,payload)
            with patch.object(store.ledger,"commit",side_effect=RuntimeError("simulated crash")):
                with self.assertRaises(RuntimeError):
                    store.save(memory,receipt)

            recovered=InstitutionalMemoryStore(path)
            self.assertEqual(recovered.reconcile(),"ROLLED_BACK")
            self.assertIsNone(recovered.journal.load())
            self.assertEqual(recovered._raw_payload(),payload)
            self.assertEqual(len(recovered.ledger.read()),0)
            self.assertTrue(recovered.ledger.verify())


    def test_crash_after_ledger_commit_finalizes(self):
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"memory.json"
            store=InstitutionalMemoryStore(path)
            memory=InstitutionalMemory()
            before=store._raw_payload()
            payload=store._payload(memory)
            receipt=LearningReceipt.create("worker","crash-after-ledger",(),before,payload)
            original_mark=store.journal.mark_committed
            with patch.object(store.journal,"mark_committed",side_effect=RuntimeError("simulated crash")):
                with self.assertRaises(RuntimeError):
                    store.save(memory,receipt)

            recovered=InstitutionalMemoryStore(path)
            self.assertEqual(recovered.reconcile(),"FINALIZED")
            self.assertIsNone(recovered.journal.load())
            self.assertEqual(len(recovered.ledger.read()),1)
            self.assertTrue(recovered.ledger.verify())
            self.assertEqual(recovered._raw_payload(),payload)


    def test_duplicate_receipt_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            store=InstitutionalMemoryStore(Path(td)/"memory.json")
            memory=InstitutionalMemory()
            before={}
            payload=store._payload(memory)
            receipt=LearningReceipt.create("worker","duplicate",(),before,payload)
            store.save(memory,receipt)
            with self.assertRaises(ValueError):
                store.save(memory,receipt)
            self.assertEqual(len(store.ledger.read()),1)
            self.assertTrue(store.ledger.verify())


if __name__=="__main__": unittest.main()
