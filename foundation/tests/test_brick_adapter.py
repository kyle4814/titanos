"""The adapter's job is to stop the renderer saying more than the receipt.

Every test here tries to get a customer-facing artifact to overclaim: to
show a price it did not earn, to print a figure without its source state,
or to let a guess wear the colours of a proven fact.
"""

import unittest

from foundation.receipt import Claim, Receipt
from foundation.business_receipt import derive_business_receipt
from foundation.value_model import ValueInput, ValueModel
from foundation.brick_adapter import (
    BrickIntegrityError,
    build_brick_input,
    offer_permitted,
)

SCAN = {
    "domain": "acme.example",
    "timestamp": "2026-08-30T00:00:00Z",
    "summary": {"total_findings": 2, "critical": 1, "high": 0,
                "medium": 1, "low": 0, "info": 0},
    "findings": [
        {"type": "port", "severity": "CRITICAL", "title": "Postgres exposed",
         "detail": "5432 reachable", "remediation": "firewall it"},
        {"type": "header", "severity": "MEDIUM", "title": "No HSTS",
         "detail": "missing header", "remediation": "add HSTS"},
    ],
}

OFFER = {"headline": "Continuous Monitoring", "body": "Monthly scans.",
         "price_label": "$1,500/month"}


def _proven(statement="postgres is reachable from the internet",
            evidence="TCP connect to 5432 succeeded"):
    return Claim(statement=statement, status="PROVEN", evidence=evidence)


def _receipt(verdict="DEFECT_ADMITTED", beneficiary="the operator paged at 3am",
             claims=None):
    return Receipt(receipt_id="R-1", target="acme.example",
                   question="is the database exposed?", verdict=verdict,
                   claims=claims or (_proven(),), beneficiary=beneficiary)


class TestTheOfferGate(unittest.TestCase):
    def test_no_business_receipt_means_no_offer(self):
        """Fail closed: the honest default for a gift report is silence."""
        out = build_brick_input(SCAN, _receipt(), None, offer_content=OFFER)
        self.assertFalse(out["offer_permitted"])
        self.assertIsNone(out["offer"])

    def test_no_beneficiary_means_no_offer_even_with_a_proven_defect(self):
        r = Receipt(receipt_id="R-2", target="t", question="q",
                    verdict="COVERAGE_GAP_RECORDED", claims=(_proven(),))
        out = build_brick_input(SCAN, r, derive_business_receipt(r),
                                offer_content=OFFER)
        self.assertFalse(out["offer_permitted"])
        self.assertIsNone(out["offer"])

    def test_no_defect_means_no_offer(self):
        r = _receipt(verdict="NO_DEFECT")
        out = build_brick_input(SCAN, r, derive_business_receipt(r),
                                offer_content=OFFER)
        self.assertFalse(out["offer_permitted"])

    def test_an_earned_offer_is_allowed_through(self):
        """Positive control: the gate must not block a justified offer."""
        r = _receipt()
        out = build_brick_input(SCAN, r, derive_business_receipt(r),
                                offer_content=OFFER)
        self.assertTrue(out["offer_permitted"])
        self.assertEqual(out["offer"], OFFER)

    def test_supplying_offer_content_does_not_make_it_appear(self):
        """The content is passed in precisely so the gate, not the template,
        decides. This is the whole design."""
        r = _receipt(verdict="NO_DEFECT")
        out = build_brick_input(SCAN, r, derive_business_receipt(r),
                                offer_content=OFFER)
        self.assertIsNone(out["offer"])

    def test_both_layers_must_agree(self):
        """Duplicated enforcement: a future loosening of one still meets
        the other."""
        r = _receipt()
        self.assertTrue(offer_permitted(r, derive_business_receipt(r)))
        self.assertFalse(offer_permitted(r, None))

    def test_the_offer_status_string_travels_with_the_artifact(self):
        r = _receipt(verdict="NO_DEFECT")
        out = build_brick_input(SCAN, r, derive_business_receipt(r))
        self.assertEqual(out["offer_status"], "NO_FORCED_OFFER")


class TestTheTwoAxesDoNotCollapse(unittest.TestCase):
    def test_a_claim_status_smuggled_in_as_a_severity_is_refused(self):
        """PROVEN is not a severity. Rendering it as one would let evidential
        strength wear a red badge it never earned."""
        scan = dict(SCAN, findings=[dict(SCAN["findings"][0], severity="PROVEN")])
        with self.assertRaises(BrickIntegrityError) as ctx:
            build_brick_input(scan, _receipt(), None)
        self.assertIn("different axis", str(ctx.exception))

    def test_real_scanner_severities_pass_through_untouched(self):
        out = build_brick_input(SCAN, _receipt(), None)
        self.assertEqual([f["severity"] for f in out["findings"]],
                         ["CRITICAL", "MEDIUM"])

    def test_the_adapter_invents_no_severity_for_claims(self):
        out = build_brick_input(SCAN, _receipt(), None)
        for claim in out["claims"]:
            self.assertNotIn("severity", claim)

    def test_scanner_facts_pass_through_verbatim(self):
        out = build_brick_input(SCAN, _receipt(), None)
        self.assertEqual(out["domain"], SCAN["domain"])
        self.assertEqual(out["summary"], SCAN["summary"])

    def test_the_input_scan_is_not_mutated(self):
        before = str(SCAN)
        build_brick_input(SCAN, _receipt(), None)
        self.assertEqual(str(SCAN), before)


class TestClaimsCarryTheirStrength(unittest.TestCase):
    def test_every_claim_keeps_its_status(self):
        r = _receipt(claims=(_proven(),
                             Claim("other hosts are likely similar", "INFERENCE"),
                             Claim("behaviour behind the WAF", "UNKNOWN")))
        statuses = [c["status"] for c in build_brick_input(SCAN, r, None)["claims"]]
        self.assertEqual(statuses, ["PROVEN", "INFERENCE", "UNKNOWN"])

    def test_status_travels_on_the_claim_not_in_a_parallel_list(self):
        """A parallel list can be dropped by a template; a field cannot be
        rendered without being seen."""
        out = build_brick_input(SCAN, _receipt(), None)
        self.assertIn("status", out["claims"][0])
        self.assertIn("label", out["claims"][0])

    def test_unknown_claims_are_carried_not_filtered_out(self):
        r = _receipt(claims=(_proven(), Claim("whether X is reachable", "UNKNOWN")))
        self.assertEqual(len(build_brick_input(SCAN, r, None)["claims"]), 2)


class TestValueCannotLoseItsState(unittest.TestCase):
    def test_a_bare_figure_is_refused(self):
        """A number with no state attached must never reach a customer."""
        r = _receipt()
        b = derive_business_receipt(r)
        object.__setattr__(b, "financial_impact", "24800")
        with self.assertRaises(BrickIntegrityError) as ctx:
            build_brick_input(SCAN, r, b)
        self.assertIn("bare figure", str(ctx.exception))

    def test_not_measured_travels_through_as_words(self):
        r = _receipt()
        out = build_brick_input(SCAN, r, derive_business_receipt(r))
        self.assertEqual(out["value_line"], "NOT MEASURED")
        self.assertEqual(out["value_state"], "NOT_MEASURED")

    def test_a_measured_figure_keeps_its_state_label(self):
        model = ValueModel(
            inputs=(ValueInput(name="events", unit="events", status="MEASURED",
                               amount=62.0, source="62 rows counted"),
                    ValueInput(name="cost_each", unit="AUD", status="ESTIMATED",
                               amount=400.0, assumption="mean order value")),
            factors=("events", "cost_each"), result_unit="AUD")
        r = _receipt()
        out = build_brick_input(SCAN, r, derive_business_receipt(r, value_model=model))
        self.assertIn("ESTIMATED", out["value_line"])
        self.assertEqual(out["value_state"], "ESTIMATED")

    def test_no_business_receipt_yields_no_value_line(self):
        out = build_brick_input(SCAN, _receipt(), None)
        self.assertIsNone(out["value_line"])
        self.assertEqual(out["value_state"], "NOT_MEASURED")


class TestTheAdapterHoldsNoPricing(unittest.TestCase):
    def test_it_stores_no_price_of_its_own(self):
        """Commercial policy stays at the routing boundary. The adapter
        decides only whether an offer is permitted, never what it costs.

        Checks executable lines only. An earlier version scanned the whole
        file and failed on the docstring sentence that NAMES the
        prohibition -- a test that forbids describing a rule is not
        enforcing the rule, so it was narrowed to what actually matters:
        a stored price value or a currency-bearing literal in code.
        """
        import ast
        import inspect
        import re

        import foundation.brick_adapter as mod

        with open(mod.__file__) as fh:
            source = fh.read()

        # Strip docstrings so prose describing the rule cannot trip it.
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
                doc = ast.get_docstring(node, clean=False)
                if doc:
                    source = source.replace(doc, "")

        code = "\n".join(
            line.split("#", 1)[0] for line in source.splitlines()
        )
        for pattern in (r"[$£€]\s*\d", r"\bprice\s*=", r"\bamount\s*=",
                        r"\bcurrency\s*=", r"\bprice_id\s*="):
            self.assertIsNone(
                re.search(pattern, code, re.I),
                f"the gate must not carry pricing logic matching {pattern!r}",
            )

        # And the public surface must expose no pricing field.
        for name in ("price", "amount", "currency", "product_id"):
            self.assertNotIn(name, [n for n in dir(mod) if not n.startswith("_")])

    def test_a_non_dict_scan_is_refused(self):
        with self.assertRaises(BrickIntegrityError):
            build_brick_input("not a scan", _receipt(), None)


if __name__ == "__main__":
    unittest.main()
