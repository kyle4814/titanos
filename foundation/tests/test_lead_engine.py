"""Tests for `foundation/lead_engine.py` — prospect triage.

No network: the DoH fetch is injected. Load-bearing properties: the weakest
(most spoofable) domains rank first, a secure domain is NOT inflated into a
lead, and the sheet is honest about being a posture signal, not an audit."""

import json
import unittest

from foundation.lead_engine import triage_domains, render_lead_sheet_md


def _doh(answers):
    return json.dumps({"Status": 0,
                       "Answer": [{"data": a} for a in answers]}).encode()


def make_fetch(records):
    def fetch(url: str) -> bytes:
        q = url.split("?", 1)[1]
        parts = dict(kv.split("=", 1) for kv in q.split("&"))
        return _doh(records.get(f"{parts['name']}|{parts['type']}", []))
    return fetch


# a wide-open domain (no SPF, no DMARC) and a locked one (strong SPF+DMARC+DKIM)
OPEN = {}  # nothing configured -> SPF FAIL, DMARC FAIL
LOCKED = {
    "safe.com|TXT": ["v=spf1 -all"],
    "_dmarc.safe.com|TXT": ["v=DMARC1; p=reject"],
    "default._domainkey.safe.com|TXT": ["v=DKIM1; p=MIGf"],
    "safe.com|DS": ["1 8 2 ABC"],
    "safe.com|MX": ["10 mx.safe.com."],
}
SOFT = {"weak.com|TXT": ["v=spf1 ~all"],
        "_dmarc.weak.com|TXT": ["v=DMARC1; p=none"]}


def _fetch_multi():
    merged = {}
    merged.update(LOCKED)
    merged.update(SOFT)
    # OPEN (open.com) has no records -> everything absent
    return make_fetch(merged)


class TestTriage(unittest.TestCase):
    def test_wide_open_domain_is_on_fire_and_spoofable(self):
        res = triage_domains(["open.com"], make_fetch(OPEN))[0]
        self.assertEqual(res.heat, 3)
        self.assertTrue(res.spoofable)
        self.assertIn("SPOOFED", res.angle)

    def test_locked_domain_is_not_a_lead(self):
        res = triage_domains(["safe.com"], _fetch_multi())[0]
        self.assertEqual(res.heat, 0)
        self.assertFalse(res.spoofable)
        self.assertEqual(res.angle, "")

    def test_soft_domain_is_warm_not_on_fire(self):
        res = triage_domains(["weak.com"], _fetch_multi())[0]
        self.assertEqual(res.heat, 1)
        self.assertTrue(res.spoofable)  # present-but-weak is still forgeable

    def test_ranking_puts_hottest_first(self):
        res = triage_domains(["safe.com", "weak.com", "open.com"], _fetch_multi())
        heats = [r.heat for r in res]
        self.assertEqual(heats, sorted(heats, reverse=True))
        self.assertEqual(res[0].domain, "open.com")   # on fire
        self.assertEqual(res[-1].domain, "safe.com")  # secure, last

    def test_blank_domains_are_skipped(self):
        res = triage_domains(["open.com", "  ", ""], make_fetch(OPEN))
        self.assertEqual(len(res), 1)


class TestSheet(unittest.TestCase):
    def test_sheet_counts_hot_leads_and_stays_honest(self):
        res = triage_domains(["safe.com", "weak.com", "open.com"], _fetch_multi())
        md = render_lead_sheet_md(res)
        self.assertIn("hot leads", md)
        self.assertIn("open.com", md)
        # secure domain is explicitly not-a-lead, not dressed up
        self.assertIn("not a lead", md.lower())
        # honesty: posture signal, not an audit; you make the contact
        self.assertIn("not a full audit", md)
        self.assertIn("lawfully", md.lower())


if __name__ == "__main__":
    unittest.main()
