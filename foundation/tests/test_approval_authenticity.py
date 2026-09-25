"""Approval must be proven, never asserted.

Before 2026-09-25 the gateway accepted a bare fingerprint string that any
caller could compute from the intent, and AuthorizationGate accepted any
ApprovalEnvelope a caller constructed. These tests attack the boundary from
the positions an untrusted caller occupies: a dict claiming approval, a
random MAC, a signed envelope mutated after signing, a replayed nonce, a
hand-built permit, a replayed permit, and a global pause.
"""

import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from foundation import communication_gate as cg
from foundation.adapter_execution_gateway import AdapterExecutionGateway
from foundation.approval_envelope import ApprovalEnvelope, ConsumedIds
from foundation.authorization_gate import (
    AuthorizationError, AuthorizationGate, ExecutionPermit,
)
from foundation.execution_adapter import AdapterResult
from foundation.execution_dispatcher import AdapterDispatcher, ExecutionPaused
from foundation.execution_intent import ExecutionIntent
from foundation.execution_receipt_store import ExecutionReceiptStore

KEY = b"k" * 32          # test-only key; production keys are never in source
OTHER_KEY = b"x" * 32

def _ledger():
    """A fresh on-disk replay ledger (ConsumedIds refuses process-local state)."""
    import tempfile as _t
    from pathlib import Path as _P
    return ConsumedIds(_P(_t.mkdtemp()) / "consumed.db")

NOW = datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc)


def _intent(**kw):
    base = dict(
        intent_id="EI-AUTH-1", target="fake:acct-1", action="CREATE_LINK",
        parameters={"amount": 1000, "currency": "AUD"}, evidence_refs=("OPP-1",),
        expected_effect="create one link", authority_required="A3",
        reversible=True, expires_at="2099-01-01T00:00:00+00:00",
        policy_version="p-1")
    base.update(kw)
    return ExecutionIntent(**base)


def _envelope(intent, *, key=KEY, nonce="n-1", **kw):
    env = ApprovalEnvelope.decide(
        proposal_id="p1", intent=intent, decision="APPROVE", authority="A3",
        reviewer="kyle", decided_at="2026-09-25T11:59:00+00:00", nonce=nonce)
    return replace(env, **kw).signed(key) if kw else env.signed(key)


class _Adapter:
    name = "fake"

    def __init__(self):
        self.calls = 0

    def supports(self, intent):
        return intent.target.startswith("fake:")

    def execute(self, intent):
        self.calls += 1
        return AdapterResult(status="EXECUTED", effect="done", executed=True,
                             evidence=("fake:r1",))


class _Unpaused:
    """Point the pause check at an empty temp dir, so a stray real
    `.titan_pause` cannot change these results."""

    def __enter__(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        self._p = mock.patch.object(cg, "REPO_ROOT", self.root)
        self._p.start()
        return self

    def __exit__(self, *exc):
        self._p.stop()
        self._td.cleanup()
        return False


class TestPermitIssuance(unittest.TestCase):

    def setUp(self):
        self._u = _Unpaused().__enter__()
        self.addCleanup(self._u.__exit__)
        self.intent = _intent()
        self.consumed = _ledger()

    def issue(self, approval, intent=None, key=KEY, now=NOW):
        return AuthorizationGate.issue(intent or self.intent, approval, key=key,
                                       consumed=self.consumed, now=now)

    def test_01_a_dict_claiming_approval_is_rejected(self):
        with self.assertRaisesRegex(AuthorizationError, "signed ApprovalEnvelope"):
            self.issue({"approved": True})

    def test_01b_an_unsigned_envelope_is_rejected(self):
        env = ApprovalEnvelope.decide(proposal_id="p1", intent=self.intent,
                                      decision="APPROVE", authority="A3", reviewer="kyle",
                                      decided_at="2026-09-25T11:59:00+00:00")
        with self.assertRaisesRegex(AuthorizationError, "MAC"):
            self.issue(env)

    def test_02_a_random_mac_is_rejected(self):
        with self.assertRaisesRegex(AuthorizationError, "MAC"):
            self.issue(replace(_envelope(self.intent), mac="0" * 64))

    def test_02b_a_mac_under_another_key_is_rejected(self):
        with self.assertRaisesRegex(AuthorizationError, "MAC"):
            self.issue(_envelope(self.intent, key=OTHER_KEY))

    def test_02c_a_short_or_missing_key_refuses_everything(self):
        for bad in (b"short", None, "k" * 32):
            with self.assertRaises(AuthorizationError):
                self.issue(_envelope(self.intent), key=bad)

    def test_03_a_valid_envelope_issues_a_bound_permit(self):
        permit = self.issue(_envelope(self.intent))
        self.assertEqual(permit.intent_fingerprint, self.intent.fingerprint())
        self.assertTrue(permit.permit_id and permit.mac)
        permit.verify(KEY, self.intent.fingerprint(), NOW)

    def test_04_action_mutated_after_signing_is_rejected(self):
        with self.assertRaisesRegex(AuthorizationError, "MAC"):
            self.issue(replace(_envelope(self.intent), action="DELETE_ACCOUNT"))

    def test_04b_approval_for_a_different_action_is_rejected(self):
        with self.assertRaises(AuthorizationError):
            self.issue(_envelope(self.intent), intent=_intent(action="DELETE_ACCOUNT"))

    def test_05_parameters_mutated_after_signing_are_rejected(self):
        with self.assertRaisesRegex(AuthorizationError, "MAC"):
            self.issue(replace(_envelope(self.intent), parameter_hash="0" * 64))
        with self.assertRaises(AuthorizationError):
            self.issue(_envelope(self.intent),
                       intent=_intent(parameters={"amount": 999999, "currency": "AUD"}))

    def test_06_a_different_intent_id_is_rejected(self):
        with self.assertRaisesRegex(AuthorizationError, "MAC"):
            self.issue(replace(_envelope(self.intent), intent_id="EI-OTHER"))
        with self.assertRaises(AuthorizationError):
            self.issue(_envelope(self.intent), intent=_intent(intent_id="EI-OTHER"))

    def test_07_a_mutated_authority_is_rejected(self):
        with self.assertRaisesRegex(AuthorizationError, "MAC"):
            self.issue(replace(_envelope(self.intent), authority="A4"))
        with self.assertRaisesRegex(AuthorizationError, "authority"):
            self.issue(_envelope(self.intent, authority="A1"))

    def test_07b_approval_for_a_different_target_is_rejected(self):
        with self.assertRaises(AuthorizationError):
            self.issue(_envelope(self.intent), intent=_intent(target="fake:acct-2"))

    def test_08_an_expired_envelope_is_rejected(self):
        with self.assertRaisesRegex(AuthorizationError, "expired"):
            self.issue(_envelope(self.intent), now=datetime(2099, 1, 2, tzinfo=timezone.utc))

    def test_08b_a_future_dated_envelope_is_rejected(self):
        future = (NOW + timedelta(hours=1)).isoformat()
        with self.assertRaisesRegex(AuthorizationError, "future"):
            self.issue(_envelope(self.intent, decided_at=future))

    def test_09_a_replayed_envelope_is_rejected(self):
        env = _envelope(self.intent)
        self.issue(env)
        with self.assertRaisesRegex(AuthorizationError, "replay"):
            self.issue(env)

    def test_09b_a_rejected_attempt_does_not_burn_the_nonce(self):
        env = _envelope(self.intent)
        with self.assertRaises(AuthorizationError):
            self.issue(env, intent=_intent(action="OTHER"))
        self.issue(env)  # the genuine use still works

    def test_09c_replay_is_refused_across_a_restart(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "consumed.db"
            env = _envelope(self.intent)
            AuthorizationGate.issue(self.intent, env, key=KEY,
                                    consumed=ConsumedIds(path), now=NOW)
            with self.assertRaisesRegex(AuthorizationError, "replay"):
                AuthorizationGate.issue(self.intent, env, key=KEY,
                                        consumed=ConsumedIds(path), now=NOW)

    def test_decline_and_review_still_issue_nothing(self):
        for i, decision in enumerate(("DECLINE", "REVIEW")):
            with self.assertRaisesRegex(AuthorizationError, "does not authorize"):
                self.issue(_envelope(self.intent, nonce=f"d{i}", decision=decision))


class TestPermitToExecution(unittest.TestCase):

    def setUp(self):
        self._u = _Unpaused().__enter__()
        self.addCleanup(self._u.__exit__)
        self.intent = _intent()
        self.consumed = _ledger()
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.adapter = _Adapter()
        self.store = ExecutionReceiptStore(Path(self._td.name) / "receipts.json")
        self.gateway = AdapterExecutionGateway(
            AdapterDispatcher.from_adapters([self.adapter]), self.store, KEY, self.consumed)

    def permit(self, nonce="n-1"):
        return AuthorizationGate.issue(self.intent, _envelope(self.intent, nonce=nonce),
                                       key=KEY, consumed=self.consumed, now=NOW)

    def run_(self, permit, key=KEY):
        return self.gateway.execute_permitted(self.intent, permit)

    def test_10_valid_approval_to_permit_to_adapter_executes_once(self):
        receipt = self.run_(self.permit())
        self.assertEqual((receipt.status, receipt.executed), ("EXECUTED", True))
        self.assertEqual(self.store.get(receipt.receipt_id), receipt)
        self.assertEqual(self.adapter.calls, 1)

    def test_11_a_consumed_permit_cannot_be_replayed(self):
        permit = self.permit()
        self.run_(permit)
        with self.assertRaisesRegex(AuthorizationError, "replay"):
            self.run_(permit)
        self.assertEqual(self.adapter.calls, 1)

    def test_11b_a_hand_built_permit_is_rejected(self):
        forged = ExecutionPermit(
            intent_fingerprint=self.intent.fingerprint(), target=self.intent.target,
            action=self.intent.action, authority="A3", policy_version="p-1",
            expires_at=self.intent.expires_at, approved_by="kyle",
            permit_id="forged", mac="0" * 64)
        with self.assertRaisesRegex(AuthorizationError, "MAC"):
            self.run_(forged)
        self.assertEqual(self.adapter.calls, 0)

    def test_11c_a_permit_for_another_intent_is_rejected(self):
        permit = self.permit()
        other = _intent(intent_id="EI-AUTH-2")
        with self.assertRaises(AuthorizationError):
            self.gateway.execute_permitted(other, permit)
        self.assertEqual(self.adapter.calls, 0)

    def test_11d_a_bare_fingerprint_is_no_longer_accepted(self):
        with self.assertRaisesRegex(AuthorizationError, "ExecutionPermit is required"):
            self.run_(self.intent.fingerprint())
        self.assertFalse(hasattr(self.gateway, "execute_approved"))

    def test_11e_an_approval_mac_cannot_pass_as_a_permit_mac(self):
        env = _envelope(self.intent)
        permit = self.permit(nonce="n-2")
        with self.assertRaisesRegex(AuthorizationError, "MAC"):
            self.run_(replace(permit, mac=env.mac))

    def test_12_global_pause_blocks_issuance_and_execution(self):
        permit = self.permit()
        (self._u.root / cg.PAUSE_FILENAME).write_text("")
        with self.assertRaisesRegex(AuthorizationError, "PAUSED"):
            self.permit(nonce="n-3")
        with self.assertRaises(ExecutionPaused):
            self.run_(permit)
        self.assertEqual(self.adapter.calls, 0)
        (self._u.root / cg.PAUSE_FILENAME).unlink()
        self.assertTrue(self.run_(permit).executed)  # pause did not burn the permit


if __name__ == "__main__":
    unittest.main()
