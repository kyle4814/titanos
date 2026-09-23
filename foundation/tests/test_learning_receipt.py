import unittest
from foundation.learning_receipt import LearningReceipt
class TestLearningReceipt(unittest.TestCase):
    def test_receipt_binds_transition(self):
        r=LearningReceipt.create("worker:a","record_outcome",("evidence:1",),{"v":1},{"v":2},"2026-09-24T00:00:00+00:00")
        self.assertTrue(r.verify_transition({"v":1},{"v":2}))
        self.assertFalse(r.verify_transition({"v":0},{"v":2}))
    def test_receipt_has_provenance(self):
        r=LearningReceipt.create("human:kyle","record_outcome",("evidence:1",),{}, {})
        self.assertEqual(r.actor,"human:kyle"); self.assertEqual(r.input_evidence,("evidence:1",))
if __name__=="__main__": unittest.main()
