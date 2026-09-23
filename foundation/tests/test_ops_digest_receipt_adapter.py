"""Regression tests for the receipt -> phone-card adapter."""

import unittest

from foundation.opportunity import OpportunityReceipt, SignalEvidence
from foundation.ops_digest import (
    live_opportunities_from_receipts,
    opportunities_from_receipts,
)


class TestReceiptAdapter(unittest.TestCase):
    def test_receipt_becomes_one_conservative_card(self):
        receipt = OpportunityReceipt(
            opportunity_id="OPP-1",
            target="target-a",
            discovered_at="2026-09-23T00:00:00+00:00",
            signals=(
                SignalEvidence(
                    kind="DEMAND",
                    detail="Official request observed",
                    source_type="OFFICIAL",
                    source_ref="https://example.test/source",
                ),
            ),
            reward_advertised="",
            reward_eligibility="UNKNOWN",
            unknowns=("eligibility unknown",),
        )

        cards = opportunities_from_receipts((receipt,))

        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0].opp_id, "OPP-1")
        self.assertEqual(cards[0].value, "UNKNOWN — reward not observed")
        self.assertEqual(cards[0].deadline.startswith("None (standing)"), True)
        self.assertIn("eligibility unknown", cards[0].note)
        self.assertEqual(cards[0].link, "https://example.test/source")


    def test_live_entrypoint_preserves_receipt_boundary(self):
        receipt = OpportunityReceipt(
            opportunity_id="OPP-LIVE",
            target="target-live",
            discovered_at="2026-09-23T00:00:00+00:00",
            signals=(
                SignalEvidence(
                    kind="DEMAND",
                    detail="Qualified demand observed",
                    source_type="OFFICIAL",
                    source_ref="https://example.test/live",
                ),
            ),
            reward_eligibility="UNKNOWN",
        )

        cards = live_opportunities_from_receipts((receipt,))

        self.assertEqual([card.opp_id for card in cards], ["OPP-LIVE"])
        self.assertEqual(cards[0].link, "https://example.test/live")
        self.assertEqual(cards[0].value, "UNKNOWN — reward not observed")

    def test_non_receipt_is_rejected(self):
        with self.assertRaises(Exception):
            opportunities_from_receipts(({"not": "a receipt"},))


if __name__ == "__main__":
    unittest.main()
