"""The approval-decision contract at the open/private boundary (2026-09-26).

`request_approval` is the open repository's authority gate for a human tap;
the transport (private) only supplies `sender` and `decision_source`.
Probed before this change: a decision was a bare string, unbound to the
card -- no nonce, no expiry, no one-time semantics (the same request_id
approved twice), no sender identity, and a constant default request_id, so
any decision source answering "approve" approved every card. The contract
now requires the decision to echo the card's single-use nonce, arrive before
the card expires, and carry a sender claim that equals the expected sender
the caller supplies (who that is remains a human policy input); anything
else is refused, fail closed. No transport is implemented here.
"""
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from foundation import telegram_approval as ta
from foundation.telegram_approval import ApprovalRequest, Decision, request_approval

REQ = ApprovalRequest(action="send invoice #1", why="paid work", cost="none", reversible="yes")
NOW = datetime(2026, 9, 26, 0, 0, tzinfo=timezone.utc)


def _run(decision_source, **kw):
    sent = []
    with mock.patch.object(ta, "authorize_communication", return_value=True):
        d = request_approval(REQ, sender=lambda rid, text: sent.append((rid, text)),
                             decision_source=decision_source, request_id="card-1", **kw)
    return d, sent


def _tap(decision="approve", sender="kyle", nonce=None):
    def source(request_id, card_nonce):
        return {"decision": decision, "nonce": nonce if nonce is not None else card_nonce, "sender": sender}
    return source


class DecisionContractTests(unittest.TestCase):
    def test_bound_approve_is_approved(self):
        d, sent = _run(_tap(), expected_sender="kyle", now=NOW)
        self.assertIs(d, Decision.APPROVED)
        self.assertEqual(sent[0][0], "card-1")

    def test_card_carries_request_id_nonce_and_expiry(self):
        seen = {}
        def source(request_id, nonce):
            seen["nonce"] = nonce
            return {"decision": "deny", "nonce": nonce, "sender": "kyle"}
        d, sent = _run(source, expected_sender="kyle", now=NOW)
        self.assertIs(d, Decision.DENIED)
        text = sent[0][1]
        self.assertIn("card-1", text)
        self.assertIn(seen["nonce"], text)
        self.assertIn("EXPIRES", text)

    def test_nonce_is_fresh_per_card_so_a_replayed_decision_cannot_approve_again(self):
        captured = {}
        def first(request_id, nonce):
            captured["nonce"] = nonce
            return {"decision": "approve", "nonce": nonce, "sender": "kyle"}
        d1, _ = _run(first, expected_sender="kyle", now=NOW)
        # A source replaying the first card's decision verbatim against a new card.
        d2, _ = _run(_tap(nonce=captured["nonce"]), expected_sender="kyle", now=NOW)
        self.assertIs(d1, Decision.APPROVED)
        self.assertIs(d2, Decision.MALFORMED)
        self.assertFalse(d2.is_approved)

    def test_wrong_or_missing_nonce_is_refused(self):
        d, _ = _run(_tap(nonce="0" * 32), expected_sender="kyle", now=NOW)
        self.assertIs(d, Decision.MALFORMED)
        d, _ = _run(lambda rid, n: {"decision": "approve", "sender": "kyle"}, expected_sender="kyle", now=NOW)
        self.assertIs(d, Decision.MALFORMED)

    def test_legacy_bare_string_decision_is_refused(self):
        d, _ = _run(lambda rid, n: "approve", expected_sender="kyle", now=NOW)
        self.assertIs(d, Decision.MALFORMED)
        self.assertFalse(d.is_approved)

    def test_approve_without_an_expected_sender_is_unbound_not_approved(self):
        d, _ = _run(_tap(), now=NOW)  # no expected_sender: identity policy not supplied
        self.assertIs(d, Decision.UNBOUND)
        self.assertFalse(d.is_approved)

    def test_sender_claim_mismatch_is_refused(self):
        d, _ = _run(_tap(sender="someone-else"), expected_sender="kyle", now=NOW)
        self.assertIs(d, Decision.MALFORMED)
        d, _ = _run(lambda rid, n: {"decision": "approve", "nonce": n}, expected_sender="kyle", now=NOW)
        self.assertIs(d, Decision.MALFORMED)

    def test_decision_after_expiry_is_refused(self):
        clock = {"t": NOW}
        def late(request_id, nonce):
            clock["t"] = NOW + timedelta(seconds=901)
            return {"decision": "approve", "nonce": nonce, "sender": "kyle"}
        d, _ = _run(late, expected_sender="kyle", now=lambda: clock["t"], ttl_seconds=900)
        self.assertIs(d, Decision.TIMEOUT)
        self.assertFalse(d.is_approved)

    def test_deny_and_no_tap_still_fail_closed(self):
        d, _ = _run(_tap(decision="deny"), expected_sender="kyle", now=NOW)
        self.assertIs(d, Decision.DENIED)
        d, _ = _run(lambda rid, n: None, expected_sender="kyle", now=NOW)
        self.assertIs(d, Decision.TIMEOUT)

    def test_malformed_decision_values_are_refused(self):
        for bad in ("yes", "approved", "", None, 1):
            d, _ = _run(lambda rid, n, b=bad: {"decision": b, "nonce": n, "sender": "kyle"},
                        expected_sender="kyle", now=NOW)
            self.assertFalse(d.is_approved, bad)

    def test_only_approved_is_approved(self):
        for d in Decision:
            self.assertEqual(d.is_approved, d is Decision.APPROVED)


if __name__ == "__main__":
    unittest.main()
