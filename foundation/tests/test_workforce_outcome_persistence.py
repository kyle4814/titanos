import tempfile, unittest
from pathlib import Path
from foundation.worker_health import WorkerHealthBook
from foundation.specialization import SpecializationBook
from foundation.workforce_memory import WorkforceMemoryStore

class WorkforceOutcomePersistenceTests(unittest.TestCase):
    def test_record_outcome_persists_learning(self):
        with tempfile.TemporaryDirectory() as td:
            store=WorkforceMemoryStore(Path(td)/"workforce.json")
            h=WorkerHealthBook(); s=SpecializationBook()
            store.record_outcome(h,s,"w","security",outcome="SUCCESS",evidence_count=5)
            _,restored=store.load()
            self.assertEqual(restored.records[("w","security")].completed,1)
            self.assertEqual(restored.records[("w","security")].evidence_count,5)

if __name__=="__main__": unittest.main()
