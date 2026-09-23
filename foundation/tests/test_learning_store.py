import tempfile, unittest
from pathlib import Path
from foundation.opportunity_feedback import OutcomeFeedback, OpportunityFeedbackBook
from foundation.learning_store import OpportunityLearningStore
class TestLearningStore(unittest.TestCase):
    def test_round_trip_preserves_feedback(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"learning.json"; b=OpportunityFeedbackBook()
            b.record(OutcomeFeedback("o",10,15,True,.8,"2026-09-24T00:00:00+00:00"))
            OpportunityLearningStore(p).save(b)
            out=OpportunityLearningStore(p).load()
            self.assertEqual(out.records["o"][0],b.records["o"][0])
    def test_missing_store_is_empty(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(OpportunityLearningStore(Path(td)/"x").load().records,{})
if __name__=="__main__": unittest.main()
