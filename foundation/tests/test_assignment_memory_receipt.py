import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from foundation.institutional_memory import InstitutionalMemory, InstitutionalMemoryStore
from foundation.learning_receipt import LearningReceipt
from foundation.worker_assignment import WorkerAssignment, record_assignment_outcome
from foundation.specialization import SpecializationBook
from foundation.worker_health import WorkerHealthBook

class AssignmentMemoryReceiptTests(unittest.TestCase):
    def test_assignment_outcome_binds_and_persists_to_memory(self):
        with TemporaryDirectory() as td:
            store=InstitutionalMemoryStore(Path(td)/"memory.json")
            memory=InstitutionalMemory()
            assignment=WorkerAssignment("opp-1","worker-1","security",None)
            before=store._payload(memory)
            outcome=record_assignment_outcome(assignment,"SUCCESS",memory.worker_health,memory.specialization,evidence_count=3)
            after=store._payload(memory)
            receipt=LearningReceipt.create("worker-1","assignment_outcome",("opp-1",),before,after,observed_at="2026-09-24T00:00:00+00:00")
            store.save(memory,receipt)
            restored=store.load()
            self.assertEqual(restored.worker_health.workers["worker-1"].completed,1)
            self.assertEqual(restored.specialization.records[("worker-1","security")].evidence_count,3)

if __name__=="__main__": unittest.main()
