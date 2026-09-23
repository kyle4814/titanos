import tempfile,unittest
from pathlib import Path
from foundation.transaction_journal import MemoryTransactionJournal
class TestTransactionJournal(unittest.TestCase):
    def test_prepare_commit_recover(self):
        with tempfile.TemporaryDirectory() as td:
            j=MemoryTransactionJournal(Path(td)/"tx.json")
            j.begin("t","r","a","b","c")
            self.assertEqual(j.load()["status"],"PREPARED")
            j.mark_committed()
            self.assertEqual(j.load()["status"],"COMMITTED")
    def test_clear(self):
        with tempfile.TemporaryDirectory() as td:
            j=MemoryTransactionJournal(Path(td)/"tx.json"); j.begin("t","r","a","b","c"); j.clear()
            self.assertIsNone(j.load())
if __name__=="__main__": unittest.main()
