import unittest
from foundation.specialization import SpecializationBook

class SpecializationOutcomeTests(unittest.TestCase):
    def test_outcome_updates_domain_learning(self):
        s=SpecializationBook()
        s.record_outcome("w1","security",outcome="SUCCESS",evidence_count=3)
        s.record_outcome("w1","security",outcome="FAILURE")
        row=s.records[("w1","security")]
        self.assertEqual((row.completed,row.failed,row.evidence_count),(1,1,3))
        self.assertEqual(row.success_rate,0.5)
    def test_invalid_outcome_rejected(self):
        with self.assertRaises(ValueError):
            SpecializationBook().record_outcome("w1","security",outcome="UNKNOWN")
if __name__=="__main__": unittest.main()
