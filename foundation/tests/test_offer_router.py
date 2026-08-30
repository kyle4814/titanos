"""The router must never let inventory reopen a door the receipt closed.

O1-O8. The hardest case is O7: a generic call-to-action is still an offer
when its purpose is selling the remediation, so blocking a price panel
and waving through a booking link for the same work blocks nothing.
"""

import unittest

from foundation.receipt import Claim, Receipt
from foundation.business_receipt import derive_business_receipt
from foundation.offer_router import (
    TERMINAL_ROUTES,
    OfferCapability,
    route_offer,
)

MONITOR = OfferCapability(
    satisfies="REQUEST_CONTINUOUS_VERIFICATION",
    reference="POST /checkout/monitor", fulfilment="AUTOMATED",
    sells_remediation=True, human_action_required=False)

MANUAL_REMEDIATION = OfferCapability(
    satisfies="REQUEST_REMEDIATION",
    reference="POST /order/submit -> owner invoices", fulfilment="MANUAL_BY_OWNER",
    sells_remediation=True, human_action_required=True)

# The bypass candidate: a booking link whose purpose is selling the fix.
BOOKING_CTA = OfferCapability(
    satisfies="REQUEST_REMEDIATION",
    reference="cal.com booking - 'free' audit call", fulfilment="AUTOMATED",
    sells_remediation=True, human_action_required=False)


def _proven():
    return Claim("postgres is reachable", "PROVEN", "TCP connect succeeded")


def _receipt(verdict="DEFECT_ADMITTED", beneficiary="the on-call operator"):
    return Receipt(receipt_id="R-1", target="acme.example", question="q",
                   verdict=verdict, claims=(_proven(),), beneficiary=beneficiary)


class TestTheGateRunsFirst(unittest.TestCase):
    def test_O3_no_forced_offer_survives_a_full_catalogue(self):
        """Inventory must not reopen a closed door."""
        r = _receipt(verdict="NO_DEFECT")
        d = route_offer(r, derive_business_receipt(r), [MONITOR, MANUAL_REMEDIATION])
        self.assertEqual(d.route, "NO_FORCED_OFFER")
        self.assertIsNone(d.capability)

    def test_O4_no_beneficiary_yields_no_offer(self):
        r = Receipt(receipt_id="R-2", target="t", question="q",
                    verdict="COVERAGE_GAP_RECORDED", claims=(_proven(),))
        d = route_offer(r, derive_business_receipt(r), [MONITOR])
        self.assertEqual(d.route, "NO_FORCED_OFFER")

    def test_O5_no_defect_never_routes_to_remediation(self):
        r = _receipt(verdict="NO_DEFECT")
        d = route_offer(r, derive_business_receipt(r), [MANUAL_REMEDIATION])
        self.assertEqual(d.route, "NO_FORCED_OFFER")

    def test_a_missing_business_receipt_fails_closed(self):
        self.assertEqual(route_offer(_receipt(), None, [MONITOR]).route,
                         "NO_FORCED_OFFER")

    def test_the_two_gates_are_tested_against_DISAGREEMENT(self):
        """Mutation M5 -- removing the receipt-level gate -- survived the
        whole suite, because derive_business_receipt() already sets the
        withhold action whenever the receipt is not offer-eligible, so the
        second check always caught it and the first was never load-bearing.

        Duplicated enforcement is only real if the layers are tested while
        DISAGREEING. This builds that divergence directly: a receipt that
        is not offer-eligible, paired with a business receipt whose action
        says remediation is fine. Exactly the drift the duplication exists
        to survive.
        """
        r = _receipt(verdict="NO_DEFECT")          # not offer-eligible
        b = derive_business_receipt(r)
        object.__setattr__(b, "available_next_action", "REQUEST_REMEDIATION")
        self.assertFalse(r.offer_eligible())
        self.assertEqual(b.available_next_action, "REQUEST_REMEDIATION")

        d = route_offer(r, b, [MANUAL_REMEDIATION, BOOKING_CTA])
        self.assertEqual(d.route, "NO_FORCED_OFFER",
                         "the receipt-level gate must hold on its own")
        self.assertIsNone(d.capability)

    def test_O7_a_booking_cta_is_gated_exactly_like_a_price(self):
        """The bypass this prevents: block the price panel, wave through a
        'free call' that exists to sell the same remediation."""
        r = _receipt(verdict="NO_DEFECT")
        d = route_offer(r, derive_business_receipt(r), [BOOKING_CTA])
        self.assertEqual(d.route, "NO_FORCED_OFFER")
        self.assertIsNone(d.capability)


class TestEligibilityIsNotAvailability(unittest.TestCase):
    def test_O2_eligible_but_nothing_to_sell_is_its_own_route(self):
        """The gap gets a name instead of a fabricated product."""
        r = _receipt()
        d = route_offer(r, derive_business_receipt(r), [])
        self.assertEqual(d.route, "UNSUPPORTED_OFFER_PATH")
        self.assertIn("no existing capability", d.reason)

    def test_a_catalogue_that_misses_this_action_does_not_substitute(self):
        r = _receipt()   # DEFECT_ADMITTED -> REQUEST_REMEDIATION
        d = route_offer(r, derive_business_receipt(r), [MONITOR])
        self.assertEqual(d.route, "UNSUPPORTED_OFFER_PATH")

    def test_O1_eligible_plus_a_real_automated_capability_routes(self):
        """Positive control: the router must not refuse everything."""
        r = Receipt(receipt_id="R-3", target="t", question="q",
                    verdict="CONVENTION_NOT_CONTRACT", claims=(_proven(),),
                    beneficiary="the team relying on the convention")
        d = route_offer(r, derive_business_receipt(r), [MONITOR])
        self.assertEqual(d.route, "EXISTING_SUPPORTED_OFFER")
        self.assertEqual(d.capability, MONITOR)

    def test_a_manual_capability_requires_a_human_first(self):
        r = _receipt()
        d = route_offer(r, derive_business_receipt(r), [MANUAL_REMEDIATION])
        self.assertEqual(d.route, "HUMAN_REVIEW_REQUIRED")
        self.assertTrue(d.sells_nothing())

    def test_an_ambiguous_catalogue_escalates_rather_than_picking(self):
        r = _receipt()
        d = route_offer(r, derive_business_receipt(r),
                        [MANUAL_REMEDIATION, BOOKING_CTA])
        self.assertEqual(d.route, "HUMAN_REVIEW_REQUIRED")
        self.assertIn("commercial judgement", d.reason)


class TestTheRouterInventsNothing(unittest.TestCase):
    def test_O8_it_carries_no_price_or_product_data(self):
        import ast
        import re
        import foundation.offer_router as mod
        with open(mod.__file__) as fh:
            source = fh.read()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
                doc = ast.get_docstring(node, clean=False)
                if doc:
                    source = source.replace(doc, "")
        code = "\n".join(l.split("#", 1)[0] for l in source.splitlines())
        for pattern in (r"[$£€]\s*\d", r"\bprice\s*=", r"\bamount\s*=",
                        r"price_[A-Za-z0-9]{6,}", r"buy\.stripe\.com"):
            self.assertIsNone(re.search(pattern, code, re.I),
                              f"router must not carry {pattern!r}")

    def test_a_capability_must_say_how_it_is_fulfilled(self):
        with self.assertRaises(ValueError):
            OfferCapability(satisfies="REQUEST_REMEDIATION", reference="  ",
                            fulfilment="AUTOMATED", sells_remediation=True,
                            human_action_required=False)

    def test_an_unknown_action_in_a_capability_is_refused(self):
        with self.assertRaises(ValueError):
            OfferCapability(satisfies="SELL_THEM_SOMETHING", reference="x",
                            fulfilment="AUTOMATED", sells_remediation=True,
                            human_action_required=False)

    def test_every_decision_is_one_of_the_four_terminal_routes(self):
        r = _receipt()
        for registry in ([], [MONITOR], [MANUAL_REMEDIATION],
                         [MANUAL_REMEDIATION, BOOKING_CTA]):
            for verdict in ("DEFECT_ADMITTED", "NO_DEFECT"):
                rec = _receipt(verdict=verdict)
                d = route_offer(rec, derive_business_receipt(rec), registry)
                self.assertIn(d.route, TERMINAL_ROUTES)


if __name__ == "__main__":
    unittest.main()
