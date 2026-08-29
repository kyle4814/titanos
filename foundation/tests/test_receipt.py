"""The Receipt's value is entirely in what it REFUSES to let you say.

Every test below tries to make the object tell a specific commercially
convenient lie, and asserts that it cannot. A test that only proved the
happy path would prove nothing: anyone can build a dataclass that holds
a verdict.
"""

import unittest
from dataclasses import FrozenInstanceError

from foundation.receipt import (
    CLAIM_STATUSES,
    VERDICTS,
    Claim,
    Receipt,
    ReceiptIntegrityError,
    format_executive_summary,
)


def _claim(status="PROVEN", statement="the log carries offset 0:00:00",
           evidence="parsed 227 timestamps from 6 live logs"):
    return Claim(statement=statement, status=status, evidence=evidence)


class TestAClaimCannotAssertProofItDoesNotHave(unittest.TestCase):
    def test_a_proven_claim_without_evidence_is_refused(self):
        """The cheapest possible lie: assert PROVEN, cite nothing."""
        with self.assertRaises(ReceiptIntegrityError) as ctx:
            Claim(statement="the system is secure", status="PROVEN", evidence="")
        self.assertIn("no evidence", str(ctx.exception))

    def test_whitespace_is_not_evidence(self):
        with self.assertRaises(ReceiptIntegrityError):
            Claim(statement="the system is secure", status="PROVEN", evidence="   ")

    def test_an_inference_may_stand_without_evidence(self):
        """INFERENCE is an honest label, so it carries no evidence debt.
        Only PROVEN does."""
        c = Claim(statement="other sites likely behave the same", status="INFERENCE")
        self.assertEqual(c.status, "INFERENCE")

    def test_an_invented_status_is_refused(self):
        with self.assertRaises(ReceiptIntegrityError):
            Claim(statement="x", status="DEFINITELY_TRUE", evidence="trust me")

    def test_an_empty_statement_is_refused(self):
        with self.assertRaises(ReceiptIntegrityError):
            Claim(statement="   ", status="UNKNOWN")


class TestAReceiptCannotManufactureFear(unittest.TestCase):
    """RULE 1 and RULE 2 -- the anti-bullshit firewall."""

    def test_a_defect_cannot_be_admitted_on_inference_alone(self):
        with self.assertRaises(ReceiptIntegrityError) as ctx:
            Receipt(
                receipt_id="R-1", target="acme.example", question="is X safe?",
                verdict="DEFECT_ADMITTED",
                claims=(_claim(status="INFERENCE", evidence=""),),
                beneficiary="the on-call operator",
            )
        self.assertIn("PROVEN", str(ctx.exception))

    def test_a_defect_cannot_be_admitted_with_no_beneficiary(self):
        """The finding that ended five of this project's own cycles: a real
        measured wrongness that nobody suffers from is a coverage gap, and
        selling a fix for it would be manufactured urgency."""
        with self.assertRaises(ReceiptIntegrityError) as ctx:
            Receipt(
                receipt_id="R-2", target="acme.example", question="is X safe?",
                verdict="DEFECT_ADMITTED", claims=(_claim(),), beneficiary=None,
            )
        self.assertIn("beneficiary", str(ctx.exception))

    def test_the_same_evidence_is_admissible_as_a_coverage_gap(self):
        """The honest downgrade must remain available, or the rule above
        would just push people to fake a beneficiary."""
        r = Receipt(
            receipt_id="R-3", target="acme.example", question="is X safe?",
            verdict="COVERAGE_GAP_RECORDED", claims=(_claim(),), beneficiary=None,
        )
        self.assertEqual(r.verdict, "COVERAGE_GAP_RECORDED")

    def test_a_defect_with_both_proof_and_a_beneficiary_is_allowed(self):
        """Positive control: the rules must not forbid a real finding."""
        r = Receipt(
            receipt_id="R-4", target="acme.example", question="is X safe?",
            verdict="DEFECT_ADMITTED", claims=(_claim(),),
            beneficiary="the customer whose payment webhook is replayed",
        )
        self.assertTrue(r.offer_eligible())

    def test_an_invented_verdict_is_refused(self):
        with self.assertRaises(ReceiptIntegrityError):
            Receipt(receipt_id="R-5", target="t", question="q",
                    verdict="CATASTROPHIC_URGENT_ACT_NOW", claims=(_claim(),))

    def test_a_receipt_asserting_nothing_is_refused(self):
        with self.assertRaises(ReceiptIntegrityError):
            Receipt(receipt_id="R-6", target="t", question="q",
                    verdict="NO_DEFECT", claims=())


class TestTheOfferGate(unittest.TestCase):
    """RULE 3 -- no beneficiary, no offer. NO_FORCED_OFFER is the default."""

    def test_no_defect_produces_no_offer_even_with_a_beneficiary(self):
        r = Receipt(receipt_id="R-7", target="t", question="q",
                    verdict="NO_DEFECT", claims=(_claim(),),
                    beneficiary="the operator")
        self.assertFalse(r.offer_eligible())
        self.assertEqual(r.offer_status(), "NO_FORCED_OFFER")

    def test_a_coverage_gap_with_no_beneficiary_produces_no_offer(self):
        r = Receipt(receipt_id="R-8", target="t", question="q",
                    verdict="COVERAGE_GAP_RECORDED", claims=(_claim(),))
        self.assertEqual(r.offer_status(), "NO_FORCED_OFFER")

    def test_a_coverage_gap_with_a_real_beneficiary_may_carry_an_offer(self):
        r = Receipt(receipt_id="R-9", target="t", question="q",
                    verdict="COVERAGE_GAP_RECORDED", claims=(_claim(),),
                    beneficiary="the team whose deploy gate this silently skips")
        self.assertEqual(r.offer_status(), "OFFER_ELIGIBLE")

    def test_a_blank_beneficiary_does_not_unlock_an_offer(self):
        """Whitespace must not be a loophole around the beneficiary test."""
        r = Receipt(receipt_id="R-10", target="t", question="q",
                    verdict="COVERAGE_GAP_RECORDED", claims=(_claim(),),
                    beneficiary="   ")
        self.assertFalse(r.offer_eligible())

    def test_the_receipt_has_no_price_surface_at_all(self):
        """Structural, not conventional: a receipt that could carry a price
        could be tuned to justify one. Enforced by absence."""
        r = Receipt(receipt_id="R-11", target="t", question="q",
                    verdict="NO_DEFECT", claims=(_claim(),))
        surface = set(r.to_dict()) | {f for f in dir(r) if not f.startswith("_")}
        for forbidden in ("price", "amount", "cost", "currency", "discount",
                          "product_id", "price_id", "invoice"):
            self.assertNotIn(forbidden, surface,
                             f"the sensor must not carry a {forbidden} field")


class TestTheExecutiveLayerCannotOutrunTheRecord(unittest.TestCase):
    def test_the_summary_reports_the_real_proven_count(self):
        r = Receipt(
            receipt_id="R-12", target="acme.example", question="is X enforced?",
            verdict="CONVENTION_NOT_CONTRACT",
            claims=(_claim(), _claim(status="UNKNOWN", statement="behaviour on other platforms",
                                     evidence=""),),
        )
        text = format_executive_summary(r)
        self.assertIn("PROVEN (1)", text)
        self.assertIn("STILL UNKNOWN (1)", text)

    def test_the_summary_surfaces_unknowns_rather_than_hiding_them(self):
        r = Receipt(receipt_id="R-13", target="t", question="q", verdict="NO_DEFECT",
                    claims=(_claim(), Claim("whether a future caller supplies it",
                                            "UNKNOWN"),))
        self.assertIn("whether a future caller supplies it",
                      format_executive_summary(r))

    def test_the_summary_states_no_beneficiary_plainly(self):
        r = Receipt(receipt_id="R-14", target="t", question="q", verdict="NO_DEFECT",
                    claims=(_claim(),))
        text = format_executive_summary(r)
        self.assertIn("NONE IDENTIFIED", text)
        self.assertIn("NO_FORCED_OFFER", text)


class TestImmutabilityAndSupersession(unittest.TestCase):
    def test_a_finalized_receipt_cannot_be_edited(self):
        r = Receipt(receipt_id="R-15", target="t", question="q",
                    verdict="NO_DEFECT", claims=(_claim(),))
        with self.assertRaises(FrozenInstanceError):
            r.verdict = "DEFECT_ADMITTED"

    def test_a_correction_supersedes_rather_than_rewrites(self):
        """This project convicted its own prior receipt twice. The object
        must make that correction expressible without erasing the original."""
        first = Receipt(receipt_id="R-16", target="t", question="q",
                        verdict="NO_DEFECT", claims=(_claim(),))
        second = Receipt(receipt_id="R-17", target="t", question="q",
                         verdict="COVERAGE_GAP_RECORDED", claims=(_claim(),),
                         supersedes=first.receipt_id)
        self.assertEqual(second.supersedes, first.receipt_id)
        self.assertEqual(first.verdict, "NO_DEFECT")

    def test_the_serialised_form_is_deterministic(self):
        """Required for any downstream content hash to mean anything."""
        kwargs = dict(receipt_id="R-18", target="t", question="q",
                      verdict="NO_DEFECT", claims=(_claim(),),
                      recorded_at="2026-08-30T00:00:00+00:00")
        self.assertEqual(Receipt(**kwargs).to_dict(), Receipt(**kwargs).to_dict())

    def test_the_serialised_form_carries_the_offer_status(self):
        r = Receipt(receipt_id="R-19", target="t", question="q",
                    verdict="NO_DEFECT", claims=(_claim(),))
        self.assertEqual(r.to_dict()["offer_status"], "NO_FORCED_OFFER")


class TestVocabulariesAreClosed(unittest.TestCase):
    def test_claim_statuses_cover_the_partition_this_project_uses(self):
        for expected in ("PROVEN", "REFUTED", "INFERENCE", "UNKNOWN", "NOT_CLAIMABLE"):
            self.assertIn(expected, CLAIM_STATUSES)

    def test_no_defect_and_convention_are_first_class_verdicts(self):
        """A verdict vocabulary that only described problems would quietly
        make 'found nothing' feel like failure."""
        self.assertIn("NO_DEFECT", VERDICTS)
        self.assertIn("CONVENTION_NOT_CONTRACT", VERDICTS)


if __name__ == "__main__":
    unittest.main()
