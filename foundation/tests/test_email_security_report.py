"""Tests for `foundation/email_security_report.py` — the first sellable product.

No test touches the network: every check is driven by an injected fetch_fn that
returns canned DoH JSON. The load-bearing properties: an absent control is
reported FAIL/absent (never hand-waved), a present-but-weak control is WARN not
PASS, and the grade reflects the spoofing-critical controls."""

import json
import unittest

from foundation.email_security_report import (
    assess_email_security,
    render_report_md,
    Finding,
)


def _doh(answers):
    """Build a DoH JSON body from a list of TXT/record data strings."""
    return json.dumps({"Status": 0,
                       "Answer": [{"data": a} for a in answers]}).encode()


def make_fetch(records):
    """records: dict mapping 'name|TYPE' -> list of data strings."""
    def fetch(url: str) -> bytes:
        # url like https://dns.google/resolve?name=X&type=TXT
        q = url.split("?", 1)[1]
        parts = dict(kv.split("=", 1) for kv in q.split("&"))
        key = f"{parts['name']}|{parts['type']}"
        return _doh(records.get(key, []))
    return fetch


class TestStrongDomain(unittest.TestCase):
    def setUp(self):
        self.records = {
            "good.com|TXT": ["v=spf1 include:_spf.google.com -all"],
            "_dmarc.good.com|TXT": ["v=DMARC1; p=reject; rua=mailto:a@good.com"],
            "default._domainkey.good.com|TXT": ["v=DKIM1; k=rsa; p=MIGf..."],
            "good.com|DS": ["12345 8 2 ABCDEF"],
            "good.com|MX": ["10 aspmx.l.google.com."],
        }

    def test_strong_domain_grades_A(self):
        r = assess_email_security("good.com", make_fetch(self.records))
        self.assertEqual(r.grade, "A — strong")
        self.assertEqual(r.fails, ())

    def test_spf_hardfail_is_pass(self):
        r = assess_email_security("good.com", make_fetch(self.records))
        spf = next(f for f in r.findings if f.check == "SPF")
        self.assertEqual(spf.status, "PASS")


class TestSpoofableDomain(unittest.TestCase):
    def test_no_spf_no_dmarc_is_fail_and_low_grade(self):
        # empty records = nothing configured
        r = assess_email_security("bad.com", make_fetch({}))
        spf = next(f for f in r.findings if f.check == "SPF")
        dmarc = next(f for f in r.findings if f.check == "DMARC")
        self.assertEqual(spf.status, "FAIL")
        self.assertEqual(dmarc.status, "FAIL")
        self.assertIn("forge", spf.detail.lower())
        self.assertIn(r.grade[0], ("C", "D"))
        # absent controls surface with a concrete fix, never hand-waved
        self.assertTrue(spf.fix and dmarc.fix)

    def test_soft_spf_is_warn_not_pass(self):
        recs = {"weak.com|TXT": ["v=spf1 include:x ~all"]}
        r = assess_email_security("weak.com", make_fetch(recs))
        spf = next(f for f in r.findings if f.check == "SPF")
        self.assertEqual(spf.status, "WARN")

    def test_dmarc_p_quarantine_with_sp_reject_is_not_misread_as_reject(self):
        # Live-found bug: p=quarantine; sp=reject must grade WARN (quarantine),
        # not PASS — a substring match on "p=reject" wrongly caught "sp=reject".
        recs = {"gh.com|TXT": ["v=spf1 -all"],
                "_dmarc.gh.com|TXT": ["v=DMARC1; p=quarantine; sp=reject; pct=100"]}
        r = assess_email_security("gh.com", make_fetch(recs))
        dmarc = next(f for f in r.findings if f.check == "DMARC")
        self.assertEqual(dmarc.status, "WARN")
        self.assertIn("quarantine", dmarc.detail.lower())

    def test_dmarc_monitor_only_is_warn_not_pass(self):
        recs = {"m.com|TXT": ["v=spf1 -all"],
                "_dmarc.m.com|TXT": ["v=DMARC1; p=none"]}
        r = assess_email_security("m.com", make_fetch(recs))
        dmarc = next(f for f in r.findings if f.check == "DMARC")
        self.assertEqual(dmarc.status, "WARN")
        self.assertIn("p=none", dmarc.detail.lower())


class TestLookupFailureIsUnknownNotAbsent(unittest.TestCase):
    """A failed DNS read must never be scored as 'record absent'. Regression
    for a live-found defect: the discovery budget (default 5) exhausted after
    DKIM's 12 selector probes, and the swallowed DiscoveryBudgetExhausted made
    MX/MTA-STS read as 'No record' — manufacturing false 'spoofable' grades on
    domains (paypal.com, google.com) that are in fact well configured."""

    def test_every_check_unknown_when_fetch_raises(self):
        def boom(url):
            raise RuntimeError("network down / budget exhausted")
        r = assess_email_security("x.com", boom)
        self.assertTrue(all(f.status == "UNKNOWN" for f in r.findings))

    def test_lookup_failure_never_counts_as_a_fail(self):
        def boom(url):
            raise RuntimeError("network down")
        r = assess_email_security("x.com", boom)
        self.assertEqual(r.fails, ())

    def test_incomplete_report_grades_unknown_not_a_letter(self):
        def boom(url):
            raise RuntimeError("network down")
        r = assess_email_security("x.com", boom)
        self.assertTrue(r.grade.startswith("UNKNOWN"))
        self.assertNotIn(r.grade[0], ("A", "B", "C", "D"))

    def test_one_failed_check_does_not_poison_the_others(self):
        # SPF reads fine (absent → FAIL), but MX lookup fails → MX UNKNOWN.
        # The whole report is then UNKNOWN (not fully assessed), but the SPF
        # FAIL is a real absent-record finding, not a fabricated one.
        def fetch(url):
            if "type=MX" in url:
                raise RuntimeError("MX lookup failed")
            return json.dumps({"Status": 0, "Answer": []}).encode()
        r = assess_email_security("x.com", fetch)
        mx = next(f for f in r.findings if f.check == "MX")
        spf = next(f for f in r.findings if f.check == "SPF")
        self.assertEqual(mx.status, "UNKNOWN")
        self.assertEqual(spf.status, "FAIL")   # genuine absent, fetch succeeded
        self.assertTrue(r.grade.startswith("UNKNOWN"))


class TestReportRendering(unittest.TestCase):
    def test_report_has_grade_actions_and_scope_disclaimer(self):
        r = assess_email_security("bad.com", make_fetch({}))
        md = render_report_md(r)
        self.assertIn("Email Security Report — bad.com", md)
        self.assertIn("Overall grade", md)
        self.assertIn("What to fix", md)
        # honest scope statement present — not sold as a full audit
        self.assertIn("not a full security audit", md)

    def test_domain_is_normalised(self):
        r = assess_email_security("  Good.COM.  ", make_fetch(
            {"good.com|TXT": ["v=spf1 -all"]}))
        self.assertEqual(r.domain, "good.com")


if __name__ == "__main__":
    unittest.main()
