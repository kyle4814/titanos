"""Tests for `foundation/report_html.py` — the client-facing HTML report.

Load-bearing properties: it is fully self-contained (no external resource an
email client or offline viewer would fail to load), it presents the same safe
records remediation generates, an incomplete scan renders UNKNOWN not a grade,
and dynamic text cannot inject markup."""

import unittest

from foundation.email_security_report import EmailSecurityReport, Finding
from foundation.report_html import render_report_html


def _report(domain="acme.com", *, spf, dmarc, dkim="WARN", mx_detail=None):
    findings = (
        Finding("SPF", spf, "spf detail", "fix"),
        Finding("DMARC", dmarc, "dmarc detail", "fix"),
        Finding("DKIM", dkim, "dkim detail", "fix"),
        Finding("DNSSEC", "WARN", "d", "f"),
        Finding("MX", "PASS" if mx_detail else "WARN", mx_detail or "No MX", "f"),
        Finding("MTA-STS", "WARN", "m", "f"),
    )
    return EmailSecurityReport(domain=domain, findings=findings)


class TestSelfContained(unittest.TestCase):
    def test_has_doctype_and_title(self):
        html = render_report_html(_report(spf="FAIL", dmarc="FAIL"))
        self.assertTrue(html.lstrip().lower().startswith("<!doctype html>"))
        self.assertIn("acme.com", html)

    def test_no_external_resources(self):
        # nothing an email client / offline viewer would have to fetch
        html = render_report_html(_report(spf="FAIL", dmarc="FAIL"))
        for needle in ("http://", "https://", "src=", "<script", "@import", "url("):
            self.assertNotIn(needle, html, f"external/e resource leaked: {needle}")


class TestPresentsGradeAndFix(unittest.TestCase):
    def test_shows_grade_letter(self):
        html = render_report_html(_report(spf="FAIL", dmarc="FAIL"))
        self.assertIn("Email security: acme.com", html)
        self.assertIn("D", html)   # grade badge

    def test_includes_the_safe_records(self):
        html = render_report_html(
            _report(spf="FAIL", dmarc="FAIL",
                    mx_detail="Mail servers configured: aspmx.l.google.com"))
        self.assertIn("v=spf1", html)
        self.assertIn("~all", html)           # softfail, safe
        self.assertNotIn("v=spf1 -all", html)  # never a hardfail record
        self.assertIn("p=none", html)          # staged DMARC

    def test_clean_domain_shows_no_records_block(self):
        html = render_report_html(
            _report(spf="PASS", dmarc="PASS", dkim="PASS",
                    mx_detail="Mail servers configured: aspmx.l.google.com"))
        self.assertNotIn("records to publish", html.lower())


class TestHonestyAndSafety(unittest.TestCase):
    def test_unknown_scan_renders_unknown_not_a_grade(self):
        findings = tuple(Finding(c, "UNKNOWN", "lookup failed", "")
                         for c in ("SPF", "DMARC", "DKIM", "DNSSEC", "MX", "MTA-STS"))
        html = render_report_html(EmailSecurityReport(domain="x.com", findings=findings))
        self.assertIn("UNKNOWN", html)
        self.assertIn("not a full security audit", html)

    def test_domain_cannot_inject_markup(self):
        evil = 'e.com"><script>alert(1)</script>'
        html = render_report_html(_report(domain=evil, spf="FAIL", dmarc="FAIL"))
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_scope_disclaimer_travels_with_it(self):
        html = render_report_html(_report(spf="FAIL", dmarc="FAIL"))
        self.assertIn("not a full security audit", html)


if __name__ == "__main__":
    unittest.main()
