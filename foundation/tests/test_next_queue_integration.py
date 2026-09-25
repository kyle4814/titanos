import json
import tempfile
import unittest
from pathlib import Path

from foundation import opportunity_cycle
from foundation.mouth_ted import MOUTH_ID as TED_MOUTH_ID
from foundation.next_kernel import OpportunityStore
from foundation.outcome_ledger import OutcomeLedger
from foundation.tender_radar import MOUTH_ID as UK_MOUTH_ID


def _uk_feed():
    return json.dumps({
        "releases": [{
            "ocid": "ocds-next-001",
            "tag": ["tender"],
            "date": "2026-09-23T00:00:00Z",
            "buyer": {"name": "Next Queue Buyer"},
            "tender": {
                "id": "ocds-next-001",
                "title": "Security testing",
                "description": "Cyber security testing service",
                "status": "active",
                "value": {"amount": 50000, "currency": "GBP"},
                "tenderPeriod": {"endDate": "2026-12-01T00:00:00Z"},
            },
        }]
    }).encode()


def _ted_feed():
    return json.dumps({
        "notices": [{
            "publication-number": "NEXT-002-2026",
            "notice-title": {"eng": "Security testing"},
            "description-proc": {"eng": "Cyber security testing service"},
            "buyer-name": {"eng": "Second Queue Buyer"},
            "deadline-receipt-request": ["2026-12-02T00:00:00Z"],
        }]
    }).encode()


class NextQueueIntegrationTests(unittest.TestCase):
    def test_cycle_persists_observed_opportunities_into_next_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / "state"
            ledger = OutcomeLedger(ledger_path=Path(tmp) / "ledger.jsonl")
            report = opportunity_cycle.run_cycle(
                state_dir,
                ledger,
                fetch_fns={
                    UK_MOUTH_ID: _uk_feed,
                    TED_MOUTH_ID: _ted_feed,
                },
            )

            self.assertEqual(report.signal_count, 2)
            self.assertEqual(report.queue_new, 2)
            self.assertEqual(report.queue_updated, 0)

            queue_path = state_dir / "next_opportunities.json"
            self.assertTrue(queue_path.exists())

            store = OpportunityStore(queue_path)
            items = store.load()
            self.assertEqual(len(items), 2)
            self.assertTrue(all(item.status == "DISCOVERED" for item in items.values()))
            self.assertTrue(all(item.authority == "O0" for item in items.values()))
            self.assertTrue(all(item.source == "opportunity_pipeline" for item in items.values()))
            self.assertTrue(all(item.evidence_refs for item in items.values()))
            self.assertTrue(all("QUALIFY:" in item.next_action for item in items.values()))

    def test_repeated_evidence_compounds_without_inventing_qualification(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = OpportunityStore(Path(tmp) / "next.json")
            from foundation.next_kernel import Opportunity

            first = Opportunity(
                id="opp-1",
                source="opportunity_pipeline",
                title="Observed demand: Example Buyer",
                evidence_refs=("signal:a",),
                authority="O0",
                next_action="QUALIFY: verify primary evidence",
            )
            second = Opportunity(
                id="opp-1",
                source="opportunity_pipeline",
                title="Observed demand: Example Buyer",
                evidence_refs=("signal:b",),
                authority="O0",
                next_action="QUALIFY: verify primary evidence",
            )

            self.assertEqual(store.upsert(first), "NEW")
            self.assertEqual(store.upsert(second), "UPDATED")

            current = store.load()["opp-1"]
            self.assertEqual(current.status, "DISCOVERED")
            self.assertEqual(current.evidence_refs, ("signal:a", "signal:b"))


if __name__ == "__main__":
    unittest.main()
