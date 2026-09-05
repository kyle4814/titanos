"""Tests for `foundation/remediation.py` — safe DNS-record generation.

The load-bearing properties are all about NOT breaking a live mail service:
SPF starts at softfail never hardfail, DMARC is staged and never jumps to
reject, an unknown provider is never given a fabricated SPF include, and DKIM
keys are never invented."""

import unittest

from foundation.email_security_report import EmailSecurityReport, Finding
from foundation.remediation import (
    build_remediation, detect_provider, render_remediation_md, Provider,
)


def report(domain="acme.com", *, spf, dmarc, dkim="WARN", mx_detail=None):
    """Build a report from explicit statuses. mx_detail sets the MX PASS detail
    (so provider detection has hosts to read); default = no MX."""
    findings = [
        Finding("SPF", spf, "spf detail", "fix"),
        Finding("DMARC", dmarc, "dmarc detail", "fix"),
        Finding("DKIM", dkim, "dkim detail", "fix"),
        Finding("DNSSEC", "WARN", "d", "f"),
        Finding("MX", "PASS" if mx_detail else "WARN",
                mx_detail or "No MX records", "f"),
        Finding("MTA-STS", "WARN", "m", "f"),
    ]
    return EmailSecurityReport(domain=domain, findings=tuple(findings))


class TestProviderDetection(unittest.TestCase):
    def test_google_detected(self):
        p = detect_provider(["aspmx.l.google.com", "alt1.aspmx.l.google.com"])
        self.assertIsNotNone(p)
        self.assertIn("_spf.google.com", p.spf_include)

    def test_m365_detected(self):
        p = detect_provider(["acme-com.mail.protection.outlook.com"])
        self.assertIn("spf.protection.outlook.com", p.spf_include)

    def test_unknown_provider_is_none(self):
        self.assertIsNone(detect_provider(["mail.some-random-host.example"]))

    def test_no_mx_is_none(self):
        self.assertIsNone(detect_provider([]))


class TestSpfSafety(unittest.TestCase):
    def test_spf_is_never_hardfail(self):
        # A generated SPF record must never end in -all (would bounce a missed sender)
        r = report(spf="FAIL", dmarc="FAIL",
                   mx_detail="Mail servers configured: aspmx.l.google.com")
        plan = build_remediation(r)
        spf_recs = [x for x in plan.records if x.value.startswith("v=spf1")]
        self.assertEqual(len(spf_recs), 1)
        self.assertTrue(spf_recs[0].value.endswith("~all"))
        self.assertNotIn("-all", spf_recs[0].value)

    def test_known_provider_include_is_used(self):
        r = report(spf="FAIL", dmarc="PASS",
                   mx_detail="Mail servers configured: aspmx.l.google.com")
        plan = build_remediation(r)
        spf = next(x for x in plan.records if x.value.startswith("v=spf1"))
        self.assertIn("include:_spf.google.com", spf.value)

    def test_unknown_provider_never_fabricates_an_include(self):
        # No recognised MX -> SPF must be a bare template with NO include: mech,
        # and a loud warning. Never invent a sender.
        r = report(spf="FAIL", dmarc="PASS")  # no MX -> provider unknown
        plan = build_remediation(r)
        spf = next(x for x in plan.records if x.value.startswith("v=spf1"))
        self.assertNotIn("include:", spf.value)
        self.assertEqual(spf.value, "v=spf1 ~all")
        self.assertTrue(any("UNKNOWN" in w or "add" in w.lower() for w in plan.warnings))


class TestDmarcStaging(unittest.TestCase):
    def test_from_nothing_starts_at_p_none_never_reject(self):
        r = report(spf="PASS", dmarc="FAIL")
        plan = build_remediation(r)
        dmarc = next(x for x in plan.records if x.host.startswith("_dmarc"))
        self.assertIn("p=none", dmarc.value)
        self.assertNotIn("p=reject", dmarc.value)
        self.assertNotIn("p=quarantine", dmarc.value)

    def test_from_quarantine_advances_to_reject(self):
        r = report(spf="PASS",
                   dmarc="WARN")
        # simulate the "already quarantining" detail
        findings = list(r.findings)
        findings[1] = Finding("DMARC", "WARN",
                              "DMARC quarantining, not rejecting (p=quarantine): v=DMARC1; p=quarantine",
                              "fix")
        r = EmailSecurityReport(domain=r.domain, findings=tuple(findings))
        plan = build_remediation(r)
        dmarc = next(x for x in plan.records if x.host.startswith("_dmarc"))
        self.assertIn("p=reject", dmarc.value)

    def test_rollout_path_is_always_stated(self):
        r = report(spf="PASS", dmarc="FAIL")
        plan = build_remediation(r)
        self.assertTrue(any("reject" in s.lower() and "never skip" in s.lower()
                            for s in plan.rollout))


class TestDkimNeverFabricated(unittest.TestCase):
    def test_dkim_is_an_instruction_not_a_record(self):
        r = report(spf="PASS", dmarc="PASS", dkim="WARN")
        plan = build_remediation(r)
        # no DNS record is emitted for DKIM (we cannot generate the key)
        self.assertFalse(any("_domainkey" in x.host for x in plan.records))
        self.assertTrue(any("DKIM" in i for i in plan.instructions))
        # and nothing that looks like a fabricated key
        self.assertFalse(any("v=DKIM1" in x.value for x in plan.records))


class TestNoOverReach(unittest.TestCase):
    def test_passing_controls_get_no_records(self):
        r = report(spf="PASS", dmarc="PASS", dkim="PASS",
                   mx_detail="Mail servers configured: aspmx.l.google.com")
        plan = build_remediation(r)
        self.assertTrue(plan.nothing_to_fix)

    def test_unknown_report_generates_no_changes(self):
        findings = tuple(Finding(c, "UNKNOWN", "lookup failed", "")
                         for c in ("SPF", "DMARC", "DKIM", "DNSSEC", "MX", "MTA-STS"))
        r = EmailSecurityReport(domain="x.com", findings=findings)
        plan = build_remediation(r)
        self.assertEqual(plan.records, [])
        self.assertTrue(any("did not complete" in w for w in plan.warnings))

    def test_render_is_stable_and_mentions_domain(self):
        r = report(spf="FAIL", dmarc="FAIL",
                   mx_detail="Mail servers configured: aspmx.l.google.com")
        md = render_remediation_md(build_remediation(r))
        self.assertIn("acme.com", md)
        self.assertIn("Records to publish", md)


if __name__ == "__main__":
    unittest.main()
