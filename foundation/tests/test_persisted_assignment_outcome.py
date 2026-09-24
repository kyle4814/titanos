import tempfile, unittest
from pathlib import Path
from foundation.institutional_memory import InstitutionalMemory, InstitutionalMemoryStore
from foundation.opportunity import InvestigationMission
from foundation.specialization import SpecializationBook
from foundation.worker_health import WorkerHealthBook
from foundation.worker_assignment import WorkerAssignment, persist_assignment_outcome

class PersistedAssignmentOutcomeTests(unittest.TestCase):
    def test_outcome_updates_feedback_and_survives_reload(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            store=InstitutionalMemoryStore(root/"memory.json")
            memory=InstitutionalMemory()
            mission=InvestigationMission("opp","target",("evidence",),(),5,0.8,
                                         "STRONG_EXECUTION_TARGET",(),(),"test","fail",())
            assignment=WorkerAssignment("opp","worker","security",mission)
            persist_assignment_outcome(
                store,memory,assignment,"SUCCESS",
                expected_value=10.0,realized_value=14.0,
                evidence_strength=1.0,evidence_count=3,
                actor="worker")
            restored=store.load()
            self.assertEqual(restored.worker_health.workers["worker"].completed,1)
            self.assertEqual(restored.specialization.records[("worker","security")].completed,1)
            self.assertEqual(len(restored.opportunity_learning.records["opp"]),1)
            self.assertEqual(restored.opportunity_learning.records["opp"][0].realized_value,14.0)
            self.assertTrue(store.ledger.verify())
            self.assertIsNone(store.journal.load())

if __name__=="__main__": unittest.main()
