import unittest
from foundation.opportunity import *
class WorkerAssignmentTests(unittest.TestCase):
    def test_ready_opportunity_can_be_assigned_with_provenance(self):
        s=(SignalEvidence("DEMAND","maintainer requests work","PRIMARY","src"),SignalEvidence("CODE_PRESSURE","pressure","PRIMARY","src"))
        o=OpportunityReceipt("OPP-x","owner/repo","2026-09-24T00:00:00+00:00",s,activity_class="ACTIVE",locally_reproducible="YES")
        a=assign_worker(o,"worker-1","security",now=__import__("datetime").datetime.fromisoformat("2026-09-24T01:00:00+00:00"))
        self.assertEqual((a.opportunity_id,a.worker_id,a.domain),("OPP-x","worker-1","security"))
        self.assertTrue(a.evidence)
    def test_assignment_refuses_non_investigate(self):
        s=(SignalEvidence("DEMAND","request","THIRD_PARTY","src"),)
        o=OpportunityReceipt("OPP-y","owner/repo","2026-09-24T00:00:00+00:00",s)
        with self.assertRaises(HandoffRefused): assign_worker(o,"w","security")
if __name__=="__main__": unittest.main()
