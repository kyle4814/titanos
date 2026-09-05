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


class TestFailedLookupNeverBecomesALead(unittest.TestCase):
    """Batch-level regression for a live-found defect: the shared discovery
    budget (5) exhausted mid-batch (DKIM alone probes 12 selectors), and the
    swallowed error made every domain after the cap read as 'no SPF/DMARC' —
    so `leads --from-csv` on a real list flagged nearly everything spoofable.
    A failed/incomplete lookup must be UNKNOWN and NEVER a hot lead."""

    def test_all_lookups_failing_yields_no_leads(self):
        def boom(url):
            raise RuntimeError("network down / budget exhausted")
        res = triage_domains(["a.com", "b.com", "c.com"], boom)
        self.assertTrue(all(r.grade.startswith("UNKNOWN") for r in res))
        self.assertTrue(all(not r.spoofable for r in res))
        self.assertTrue(all(r.heat == 0 for r in res))

    def test_one_failed_lookup_does_not_poison_a_real_open_domain(self):
        # open.com genuinely has no records (real spoofable); bad.com's fetch
        # fails. The real one still ranks hot; the failed one is UNKNOWN, cold.
        def fetch(url):
            if "name=bad.com" in url or "name=_dmarc.bad.com" in url \
               or "._domainkey.bad.com" in url:
                raise RuntimeError("lookup failed for bad.com")
            return _doh([])  # everything else absent -> open.com is wide open
        res = {r.domain: r for r in triage_domains(["open.com", "bad.com"], fetch)}
        self.assertEqual(res["open.com"].heat, 3)
        self.assertTrue(res["open.com"].spoofable)
        self.assertTrue(res["bad.com"].grade.startswith("UNKNOWN"))
        self.assertFalse(res["bad.com"].spoofable)


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
