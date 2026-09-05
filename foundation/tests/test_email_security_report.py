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
