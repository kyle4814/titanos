"""Tests for `foundation/telegram_approval.py` — the async approval + alert loop.

No network: sender/decision_source/opener are injected. The load-bearing
property is FAIL-CLOSED — anything that isn't an explicit Approve tap has
`is_approved == False`, so a gated action never proceeds by default."""

import os
import unittest
from unittest import mock

from foundation.telegram_approval import (
    ApprovalRequest, Decision, request_approval, alert_operator, format_card,
)


def _req():
    return ApprovalRequest(
        action="Send document-request email to buyer X",
        why="Unlocks the HSA SOC tender pack",
        cost="0 EUR, 2 minutes",
        reversible="Yes — no commitment, just a request",
    )


class TestApprovalRequest(unittest.TestCase):
    def test_empty_field_is_refused(self):
        with self.assertRaises(ValueError):
            ApprovalRequest(action="", why="x", cost="x", reversible="x")

    def test_card_has_every_field_and_is_html_safe(self):
        req = ApprovalRequest(action="do <thing> & more", why="w", cost="c",
                              reversible="r")
        card = format_card(req)
        for label in ("WHAT", "WHY", "COST", "REVERSIBLE"):
            self.assertIn(label, card)
        # the < > & in the action are escaped, not raw
        self.assertIn("&lt;thing&gt;", card)
        self.assertIn("&amp;", card)


class TestDecisions(unittest.TestCase):
    def test_approve_tap_is_approved(self):
        d = request_approval(_req(), sender=lambda rid, t: None,
                             decision_source=lambda rid: "approve")
        self.assertEqual(d, Decision.APPROVED)
        self.assertTrue(d.is_approved)

    def test_deny_is_not_approved(self):
        d = request_approval(_req(), sender=lambda rid, t: None,
                             decision_source=lambda rid: "deny")
        self.assertEqual(d, Decision.DENIED)
        self.assertFalse(d.is_approved)

    def test_no_tap_times_out_and_is_not_approved(self):
        d = request_approval(_req(), sender=lambda rid, t: None,
                             decision_source=lambda rid: None)
        self.assertEqual(d, Decision.TIMEOUT)
        self.assertFalse(d.is_approved)

    def test_unrecognised_response_is_not_approved(self):
        d = request_approval(_req(), sender=lambda rid, t: None,
                             decision_source=lambda rid: "maybe")
        self.assertFalse(d.is_approved)

    def test_the_card_actually_gets_sent(self):
        sent = {}
        request_approval(_req(), sender=lambda rid, t: sent.update({"t": t}),
                         decision_source=lambda rid: "approve")
        self.assertIn("WHAT", sent["t"])

    def test_no_credentials_is_unavailable_and_not_approved(self):
        # No sender/source injected + no bot env -> cannot obtain approval ->
        # UNAVAILABLE, which is NOT approved (fail-closed).
        with mock.patch.dict(os.environ, {}, clear=True):
            d = request_approval(_req())
        self.assertEqual(d, Decision.UNAVAILABLE)
        self.assertFalse(d.is_approved)

    def test_only_approved_is_approved(self):
        for d in Decision:
            self.assertEqual(d.is_approved, d is Decision.APPROVED)


class TestAlert(unittest.TestCase):
    def test_alert_sends_when_creds_present(self):
        calls = []

        class _Resp:
            def read(self_inner):
                return b'{"ok": true}'
        with mock.patch.dict(os.environ,
                             {"TELEGRAM_BOT_TOKEN": "t", "TELEGRAM_CHAT_ID": "c"},
                             clear=False):
            ok = alert_operator("I hit a fork on the HSA bid",
                                "Two valid strategies — need your call",
                                opener=lambda req: (calls.append(req) or _Resp()))
        self.assertTrue(ok)
        self.assertEqual(len(calls), 1)

    def test_alert_fails_soft_without_creds(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(alert_operator("x", "y"))


if __name__ == "__main__":
    unittest.main()
