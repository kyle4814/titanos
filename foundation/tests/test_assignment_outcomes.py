import unittest
from foundation.worker_assignment import WorkerAssignment, AssignmentOutcome, AssignmentRefused, record_assignment_outcome
from foundation.opportunity import InvestigationMission
from foundation.worker_health import WorkerHealthBook
from foundation.specialization import SpecializationBook

class AssignmentOutcomeTests(unittest.TestCase):
    def _assignment(self):
        mission=InvestigationMission("opp","target",("reason",),(),5,0.8,"STRONG_EXECUTION_TARGET",(),(), "test","fail",())
        return WorkerAssignment("opp","worker","security",mission)
    def test_success_updates_health_and_specialization(self):
        h=WorkerHealthBook(); s=SpecializationBook()
        out=record_assignment_outcome(self._assignment(),"SUCCESS",h,s,evidence_count=4)
        self.assertIsInstance(out,AssignmentOutcome)
        self.assertEqual(h.workers["worker"].completed,1)
        self.assertEqual(s.records[("worker","security")].completed,1)
        self.assertEqual(out.opportunity_id,"opp")
    def test_failure_updates_both(self):
        h=WorkerHealthBook(); s=SpecializationBook()
        record_assignment_outcome(self._assignment(),"FAILURE",h,s)
        self.assertEqual(h.workers["worker"].failed,1)
        self.assertEqual(s.records[("worker","security")].failed,1)
    def test_invalid_outcome_rejected(self):
        with self.assertRaises(AssignmentRefused):
            record_assignment_outcome(self._assignment(),"UNKNOWN",WorkerHealthBook(),SpecializationBook())
if __name__=="__main__": unittest.main()
