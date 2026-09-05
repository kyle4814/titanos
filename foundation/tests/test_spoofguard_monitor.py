"""Tests for `foundation/spoofguard_monitor.py` — posture change detection.

No network: the DoH fetch is injected. Load-bearing: a first-ever check reports
no change (never fabricated), and only a real regression against a stored
snapshot raises an alert."""

import json
import tempfile
import unittest
from pathlib import Path

from foundation.spoofguard_monitor import (
    monitor, diff_snapshots, regressions, render_alert, snapshot_from_report,
    last_snapshot, PostureChange,
)


def _doh(answers):
    return json.dumps({"Status": 0,
                       "Answer": [{"data": a} for a in answers]}).encode()


def make_fetch(records):
    def fetch(url: str) -> bytes:
        q = url.split("?", 1)[1]
        parts = dict(kv.split("=", 1) for kv in q.split("&"))
        return _doh(records.get(f"{parts['name']}|{parts['type']}", []))
    return fetch


STRONG = {
    "d.com|TXT": ["v=spf1 -all"],
    "_dmarc.d.com|TXT": ["v=DMARC1; p=reject"],
    "default._domainkey.d.com|TXT": ["v=DKIM1; p=MIG"],
    "d.com|DS": ["1 8 2 AB"], "d.com|MX": ["10 mx.d.com."],
}
WEAKENED = {  # DMARC dropped to none, SPF removed
    "_dmarc.d.com|TXT": ["v=DMARC1; p=none"],
    "default._domainkey.d.com|TXT": ["v=DKIM1; p=MIG"],
    "d.com|DS": ["1 8 2 AB"], "d.com|MX": ["10 mx.d.com."],
}


class TestDiff(unittest.TestCase):
    def test_regression_is_flagged_worse(self):
        old = {"checks": {"DMARC": "PASS"}}
        new = {"checks": {"DMARC": "FAIL"}}
        ch = diff_snapshots(old, new)
        self.assertEqual(len(ch), 1)
        self.assertTrue(ch[0].worse)
        self.assertEqual(regressions(ch), ch)

    def test_improvement_is_not_worse(self):
        ch = diff_snapshots({"checks": {"SPF": "FAIL"}},
                            {"checks": {"SPF": "PASS"}})
        self.assertFalse(ch[0].worse)
        self.assertEqual(regressions(ch), [])

    def test_no_change_is_empty(self):
        self.assertEqual(diff_snapshots({"checks": {"SPF": "PASS"}},
                                        {"checks": {"SPF": "PASS"}}), [])


class TestMonitor(unittest.TestCase):
    def test_first_check_has_no_change(self):
        with tempfile.TemporaryDirectory() as d:
            store = Path(d) / "snaps.jsonl"
            snap, changes = monitor("d.com", store, fetch_fn=make_fetch(STRONG))
            self.assertEqual(changes, [])          # nothing to compare to
            self.assertEqual(snap["domain"], "d.com")
            self.assertTrue(store.is_file())

    def test_second_check_detects_the_regression(self):
        with tempfile.TemporaryDirectory() as d:
            store = Path(d) / "snaps.jsonl"
            monitor("d.com", store, fetch_fn=make_fetch(STRONG))       # baseline
            _, changes = monitor("d.com", store, fetch_fn=make_fetch(WEAKENED))
            regs = regressions(changes)
            self.assertTrue(regs)
            checks = {c.check for c in regs}
            self.assertIn("DMARC", checks)   # reject -> none is worse
            self.assertIn("SPF", checks)     # -all present -> absent is worse

    def test_alert_names_the_regressed_controls(self):
        changes = [PostureChange("DMARC", "PASS", "WARN", True),
                   PostureChange("SPF", "PASS", "FAIL", True)]
        msg = render_alert("d.com", changes)
        self.assertIn("REGRESSED", msg)
        self.assertIn("DMARC", msg)
        self.assertIn("SPF", msg)

    def test_alert_when_no_regression_is_calm(self):
        self.assertIn("no change", render_alert("d.com", []).lower())

    def test_store_keeps_latest_per_domain(self):
        with tempfile.TemporaryDirectory() as d:
            store = Path(d) / "snaps.jsonl"
            monitor("d.com", store, fetch_fn=make_fetch(STRONG))
            monitor("d.com", store, fetch_fn=make_fetch(WEAKENED))
            latest = last_snapshot(store, "d.com")
            self.assertEqual(latest["checks"]["DMARC"], "WARN")  # weakened state


if __name__ == "__main__":
    unittest.main()
