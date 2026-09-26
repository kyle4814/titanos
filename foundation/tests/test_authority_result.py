from __future__ import annotations
import tempfile, unittest
from dataclasses import replace
from pathlib import Path
from foundation.next_kernel import Opportunity, OpportunityStore
from foundation.authority_result import apply_worker_result
from foundation.worker_result import WorkerResult


def qualified_opportunity(opportunity_id: str = "o", authority: str = "O1") -> Opportunity:
    """A QUALIFIED record with a real persisted qualification result -- the
    only status from which PREPARED is a legal transition (next_kernel
    FORWARD), and it needs O1 (MIN_AUTHORITY). Same construction as
    foundation/test_next_kernel.py's `qualified_item`."""
    from foundation.eligibility import assess_eligibility
    from foundation.qualification import assess
    from foundation.tests.test_qualification import _notice_with_empty_criteria, _real_operator_profile
    result = replace(assess(assess_eligibility(_notice_with_empty_criteria()), _real_operator_profile()),
                     publication_number=opportunity_id)
    return Opportunity(opportunity_id, "x", "x", "QUALIFIED", evidence_refs=(result.evidence_ref(),),
                       authority=authority, qualification_result=result)


class TestAuthorityResult(unittest.TestCase):
    def test_completed_can_prepare_but_not_commit(self):
        # PREPARED requires O1 on the record (next_kernel.MIN_AUTHORITY,
        # 2e5aa1ae) and is reachable only from QUALIFIED (FORWARD); a worker
        # result never confers authority. The former DISCOVERED/O0 fixture
        # predates both rules. Authority issuance itself stays deferred
        # (HUMAN_DECISIONS.md item 20, delegated decision 2026-09-26).
        with tempfile.TemporaryDirectory() as td:
            s=OpportunityStore(Path(td)/"next.json")
            s.upsert(qualified_opportunity())
            r=WorkerResult("w","o","COMPLETED","prepared",("ev:1",))
            item=apply_worker_result(s,r)
            self.assertEqual(item.status,"PREPARED")
            self.assertEqual(item.authority,"O1")
    def test_completed_result_cannot_lift_an_o0_record(self):
        with tempfile.TemporaryDirectory() as td:
            s=OpportunityStore(Path(td)/"next.json")
            s.upsert(Opportunity("o","x","x","DISCOVERED",authority="O0"))
            r=WorkerResult("w","o","COMPLETED","prepared",("ev:1",))
            with self.assertRaisesRegex(PermissionError,"O1"): apply_worker_result(s,r)
            self.assertEqual((s.load()["o"].status,s.load()["o"].authority),("DISCOVERED","O0"))
    def test_completed_result_cannot_skip_qualification(self):
        with tempfile.TemporaryDirectory() as td:
            s=OpportunityStore(Path(td)/"next.json")
            s.upsert(Opportunity("o","x","x","DISCOVERED",authority="O1"))
            r=WorkerResult("w","o","COMPLETED","prepared",("ev:1",))
            with self.assertRaisesRegex(ValueError,"invalid transition"): apply_worker_result(s,r)
            self.assertEqual(s.load()["o"].status,"DISCOVERED")
    def test_escalation_enters_human_gate(self):
        with tempfile.TemporaryDirectory() as td:
            s=OpportunityStore(Path(td)/"next.json")
            s.upsert(Opportunity("o","x","x","PREPARED",authority="O1"))
            r=WorkerResult("w","o","ESCALATED","needs approval",("ev:1",),escalation="commit")
            item=apply_worker_result(s,r)
            self.assertEqual(item.status,"HUMAN-GATED")

if __name__=="__main__": unittest.main()
