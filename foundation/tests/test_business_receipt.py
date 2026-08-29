"""The business layer must be unable to outrun the evidence layer.

Every test here tries to sell something the record does not support.
"""

import unittest
from dataclasses import FrozenInstanceError

from foundation.receipt import Claim, Receipt, ReceiptIntegrityError
from foundation.business_receipt import (
    NOT_MEASURED,
    BusinessReceipt,
    derive_business_receipt,
)


def _proven(statement="the key is unenforced", evidence="grep found no validation"):
    return Claim(statement=statement, status="PROVEN", evidence=evidence)


def _no_beneficiary_receipt(verdict="COVERAGE_GAP_RECORDED"):
    return Receipt(receipt_id="R-A", target="acme", question="is X enforced?",
                   verdict=verdict, claims=(_proven(),))


def _with_beneficiary(verdict="DEFECT_ADMITTED"):
    return Receipt(receipt_id="R-B", target="acme", question="is X enforced?",
                   verdict=verdict, claims=(_proven(),),
                   beneficiary="the operator paged at 3am",
                   reentry_condition="reopen if a caller supplies the value")


class TestTheOfferCannotBeAuthored(unittest.TestCase):
    def test_no_beneficiary_yields_no_offer_however_it_is_derived(self):
        b = derive_business_receipt(_no_beneficiary_receipt())
        self.assertEqual(b.available_next_action, "NO_REMEDIATION_OFFER_RECOMMENDED")
        self.assertTrue(b.sells_nothing())

    def test_there_is_no_parameter_to_force_an_offer(self):
        """The structural guarantee: a caller cannot pass one in."""
        import inspect
        params = set(inspect.signature(derive_business_receipt).parameters)
        for forbidden in ("verdict", "offer", "available_next_action",
                          "confidence_boundary", "beneficiary", "price"):
            self.assertNotIn(forbidden, params,
                             f"{forbidden} must be derived, never supplied")

    def test_enthusiastic_interpretation_cannot_upgrade_the_verdict(self):
        """Free text is allowed; changing the verdict is not."""
        r = _no_beneficiary_receipt(verdict="NO_DEFECT")
        b = derive_business_receipt(
            r,
            hard_truth="THIS IS A CATASTROPHIC EMERGENCY",
            why_it_matters="you must buy remediation immediately",
        )
        self.assertEqual(b.verdict, "NO_DEFECT")
        self.assertEqual(b.available_next_action, "NO_REMEDIATION_OFFER_RECOMMENDED")

    def test_a_real_defect_with_a_beneficiary_does_reach_remediation(self):
        """Positive control: the gate must not block a justified offer."""
        b = derive_business_receipt(_with_beneficiary())
        self.assertEqual(b.available_next_action, "REQUEST_REMEDIATION")
        self.assertFalse(b.sells_nothing())

    def test_a_convention_finding_routes_to_verification_not_remediation(self):
        b = derive_business_receipt(_with_beneficiary(verdict="CONVENTION_NOT_CONTRACT"))
        self.assertEqual(b.available_next_action, "REQUEST_CONTINUOUS_VERIFICATION")


class TestFinancialImpactCannotBeInvented(unittest.TestCase):
    def test_impact_defaults_to_not_measured(self):
        b = derive_business_receipt(_with_beneficiary())
        self.assertEqual(b.financial_impact, NOT_MEASURED)

    def test_a_bare_figure_is_refused(self):
        """'$2,400,000' with nothing behind it is the classic lie."""
        with self.assertRaises(ReceiptIntegrityError) as ctx:
            derive_business_receipt(_with_beneficiary(),
                                    financial_impact_evidence="$2,400,000")
        self.assertIn("no measurement", str(ctx.exception))

    def test_a_measured_impact_is_allowed_through(self):
        b = derive_business_receipt(
            _with_beneficiary(),
            financial_impact_evidence="14 support hours logged against this incident",
        )
        self.assertIn("support hours", b.financial_impact)


class TestTheConfidenceBoundaryIsCounted(unittest.TestCase):
    def test_counts_come_from_the_claims_not_from_prose(self):
        r = Receipt(
            receipt_id="R-C", target="acme", question="q",
            verdict="COVERAGE_GAP_RECORDED",
            claims=(_proven(), _proven("second proven thing", "measured twice"),
                    Claim("platform behaviour elsewhere", "UNKNOWN"),
                    Claim("likely similar", "INFERENCE")),
        )
        cb = derive_business_receipt(r).confidence_boundary
        self.assertEqual(cb["PROVEN"], 2)
        self.assertEqual(cb["UNKNOWN"], 1)
        self.assertEqual(cb["INFERENCE"], 1)
        self.assertEqual(cb["REFUTED"], 0)

    def test_unknowns_are_carried_forward_not_dropped(self):
        r = Receipt(receipt_id="R-D", target="acme", question="q",
                    verdict="NO_DEFECT",
                    claims=(_proven(), Claim("whether a caller supplies it", "UNKNOWN")))
        self.assertEqual(derive_business_receipt(r).confidence_boundary["UNKNOWN"], 1)


class TestCopiedFieldsAreVerbatim(unittest.TestCase):
    def test_verdict_and_reentry_condition_are_not_rewritten(self):
        r = _with_beneficiary()
        b = derive_business_receipt(r)
        self.assertEqual(b.verdict, r.verdict)
        self.assertEqual(b.reentry_condition, r.reentry_condition)
        self.assertEqual(b.beneficiary, r.beneficiary)

    def test_the_business_receipt_is_immutable(self):
        b = derive_business_receipt(_with_beneficiary())
        with self.assertRaises(FrozenInstanceError):
            b.available_next_action = "REQUEST_REMEDIATION"

    def test_it_carries_no_price_surface(self):
        b = derive_business_receipt(_with_beneficiary())
        surface = set(b.to_dict()) | {f for f in dir(b) if not f.startswith("_")}
        for forbidden in ("price", "amount", "cost", "currency", "product_id"):
            self.assertNotIn(forbidden, surface)


if __name__ == "__main__":
    unittest.main()
