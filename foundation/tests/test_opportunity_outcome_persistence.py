import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from foundation.institutional_memory import InstitutionalMemoryStore
from foundation.worker_assignment import persist_opportunity_outcome

class OpportunityOutcomePersistenceTests(unittest.TestCase):
    def test_feedback_is_receipt_bound_and_reloaded(self):
        with TemporaryDirectory() as td:
            store=InstitutionalMemoryStore(Path(td)/"memory.json")
            fb=persist_opportunity_outcome(store,"opp-1",10,14,True,0.9,
                                           observed_at="2026-09-24T00:00:00+00:00")
            self.assertEqual(fb.value_error,4)
            restored=store.load()
            row=restored.opportunity_learning.records["opp-1"][0]
            self.assertEqual(row.realized_value,14)
            self.assertEqual(row.evidence_strength,0.9)
            self.assertAlmostEqual(
                restored.opportunity_learning.adjusted_value("opp-1",10,
                    now=__import__("datetime").datetime.fromisoformat("2026-09-24T00:00:00+00:00")),
                14)

if __name__=="__main__":
    unittest.main()
