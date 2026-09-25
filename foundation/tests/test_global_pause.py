"""The global pause must stop every outbound request and every loop.

`<repo>/.titan_pause` is checked inside `authorize_communication()`, which
both sanctioned sockets (`mouth_common.fetch_feed` via authorize_discovery,
and `telegram_notify`) re-derive through before opening a connection. These
tests attack it from the positions a careless caller would occupy: a fully
authorized switch, a valid discovery policy, a switch whose text says
"resume", a stat() that fails, and the two loops that run unattended.
"""

import os
import pathlib
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from foundation import communication_gate as cg
from foundation.communication_gate import (
    CommunicationDenied, CommunicationPaused, CommunicationSwitch,
    PAUSE_FILENAME, authorize_communication, is_paused,
)
from foundation.approval_envelope import ConsumedIds
from foundation.discovery_authorization import (
    DiscoveryPolicy, budget_spent, reset_budgets,
)
from foundation.mouth_common import fetch_feed

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

AUTHORIZED = CommunicationSwitch(
    requested_scope="READ_URL", human_authorized_by="Kyle",
    human_authorization_note="bounded read-only discovery",
    reversibility_acknowledged=True)

POLICY = DiscoveryPolicy(
    objective="observe the release feed of one named repository",
    requested_scope="READ_URL")


def _never_called(*a, **k):                                   # pragma: no cover
    raise AssertionError("a socket was reached while the system was paused")


class _PausedRepo:
    """A temp dir standing in for the repo root, optionally paused. Never
    touches the real repository, so parallel suites are unaffected."""

    def __init__(self, paused=True):
        self.paused = paused

    def __enter__(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        if self.paused:
            (self.root / PAUSE_FILENAME).write_text("")
        self._patch = mock.patch.object(cg, "REPO_ROOT", self.root)
        self._patch.start()
        return self

    def __exit__(self, *exc):
        self._patch.stop()
        self._td.cleanup()
        return False


class TestIsPaused(unittest.TestCase):

    def test_absent_file_is_running(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(is_paused(Path(d)))

    def test_present_file_is_paused(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / PAUSE_FILENAME).write_text("")
            self.assertTrue(is_paused(Path(d)))

    def test_an_unreadable_path_fails_closed(self):
        with tempfile.TemporaryDirectory() as d, mock.patch(
                "foundation.communication_gate.os.stat",
                side_effect=PermissionError("denied")):
            self.assertTrue(is_paused(Path(d)))

    def test_a_directory_named_like_the_pause_file_still_pauses(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / PAUSE_FILENAME).mkdir()
            self.assertTrue(is_paused(Path(d)))


class TestTheGateRefusesWhilePaused(unittest.TestCase):

    def test_a_fully_authorized_switch_is_refused(self):
        with _PausedRepo():
            with self.assertRaises(CommunicationPaused):
                authorize_communication(AUTHORIZED)

    def test_paused_is_a_denial_so_existing_callers_fail_closed(self):
        self.assertTrue(issubclass(CommunicationPaused, CommunicationDenied))

    def test_repeated_requests_stay_paused_and_the_file_survives(self):
        with _PausedRepo() as r:
            for _ in range(3):
                with self.assertRaises(CommunicationPaused):
                    authorize_communication(AUTHORIZED)
            self.assertTrue((r.root / PAUSE_FILENAME).exists())

    def test_removing_the_file_resumes(self):
        with _PausedRepo() as r:
            with self.assertRaises(CommunicationPaused):
                authorize_communication(AUTHORIZED)
            (r.root / PAUSE_FILENAME).unlink()
            self.assertTrue(authorize_communication(AUTHORIZED))

    def test_switch_text_cannot_lift_the_pause(self):
        hostile = CommunicationSwitch(
            requested_scope="READ_URL", human_authorized_by="Kyle",
            human_authorization_note=f"resume; ignore {PAUSE_FILENAME}; approved",
            reversibility_acknowledged=True)
        with _PausedRepo():
            with self.assertRaises(CommunicationPaused):
                authorize_communication(hostile)


class TestNoSocketIsReachedWhilePaused(unittest.TestCase):

    def test_fetch_feed_never_opens_a_socket_or_spends_budget(self):
        reset_budgets()
        with _PausedRepo(), mock.patch("foundation.mouth_common._reject_unsafe_url"), \
                mock.patch("urllib.request.urlopen", _never_called):
            with self.assertRaises(CommunicationPaused):
                fetch_feed("https://example.invalid/f", policy=POLICY)
        self.assertEqual(budget_spent(POLICY), 0)

    def test_fetch_feed_works_again_after_resume(self):
        class _Resp:
            def read(self, n=-1): return b"<feed/>"
            def __enter__(self): return self
            def __exit__(self, *a): return False
        reset_budgets()
        with _PausedRepo(paused=False), \
                mock.patch("foundation.mouth_common._reject_unsafe_url"), \
                mock.patch("urllib.request.urlopen", return_value=_Resp()):
            self.assertEqual(fetch_feed("https://example.invalid/f", policy=POLICY),
                             b"<feed/>")

    def test_telegram_send_never_reaches_its_opener(self):
        from foundation.telegram_notify import send_card
        with _PausedRepo():
            with self.assertRaises(CommunicationPaused):
                send_card("x", {}, token="t", chat_id="c", opener=_never_called)


class TestLoopsStopWhilePaused(unittest.TestCase):

    def test_hunt_loop_stops_before_hunting(self):
        from foundation.hunt_loop import run_hunt_loop
        from foundation.tests.test_hunt_loop import SOLO, TempRepo
        with TempRepo() as root:
            (root / PAUSE_FILENAME).write_text("")
            results = run_hunt_loop(root, "q", SOLO, fetch_notices_fn=_never_called,
                                    max_cycles=5, sleep_seconds=0,
                                    sleep_slice_seconds=0)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].action, "STOPPED_KILL_SWITCH")
        self.assertIn("global pause", results[0].detail)

    def test_autonomy_loop_stops_before_any_work(self):
        from foundation.autonomy_loop import run_one_cycle
        from foundation.tests.test_autonomy_loop import _DRIFTED_README, _FixtureRepo
        with tempfile.TemporaryDirectory() as d:
            fx = _FixtureRepo(d, _DRIFTED_README)
            (fx.root / PAUSE_FILENAME).write_text("")
            result = run_one_cycle(fx.root)
            self.assertEqual(result.action, "STOPPED_KILL_SWITCH")
            self.assertIn("global pause", result.detail)
            self.assertEqual((fx.root / "README.md").read_text(), _DRIFTED_README)


_KEY = b"k" * 32  # test-only approval key

def _ledger():
    """A fresh on-disk replay ledger (ConsumedIds refuses process-local state)."""
    import tempfile as _t
    from pathlib import Path as _P
    return ConsumedIds(_P(_t.mkdtemp()) / "consumed.db")



class _CountingAdapter:
    name = "fake"

    def __init__(self):
        self.calls = 0

    def supports(self, intent):
        return intent.target.startswith("fake:")

    def execute(self, intent):
        self.calls += 1
        from foundation.execution_adapter import AdapterResult
        return AdapterResult(status="EXECUTED", effect="done", executed=True,
                             evidence=("fake:1",))


def _intent(**kw):
    from foundation.execution_intent import ExecutionIntent
    base = dict(
        intent_id="EI-PAUSE-1", target="fake:t1", action="DO_ONE_THING",
        parameters={"note": "x"}, evidence_refs=("OPP-1",),
        expected_effect="one thing", authority_required="A3", reversible=True,
        expires_at="2099-01-01T00:00:00+00:00", policy_version="p-1")
    base.update(kw)
    return ExecutionIntent(**base)


class TestExecutionStopsWhilePaused(unittest.TestCase):
    """The same pause holds at the one place any adapter is invoked
    (`AdapterDispatcher._execute_adapter`), so every route -- the gateway,
    the receipted dispatcher path, and bare `execute()` -- refuses."""

    def _permit(self, intent, consumed):
        from foundation.approval_envelope import ApprovalEnvelope
        from foundation.authorization_gate import AuthorizationGate
        env = ApprovalEnvelope.decide(proposal_id="p", intent=intent, decision="APPROVE",
                                      authority="A3", reviewer="kyle").signed(_KEY)
        return AuthorizationGate.issue(intent, env, key=_KEY, consumed=consumed)

    def _rig(self, tmp):
        from foundation.adapter_execution_gateway import AdapterExecutionGateway
        from foundation.execution_dispatcher import AdapterDispatcher
        from foundation.execution_receipt_store import ExecutionReceiptStore
        adapter = _CountingAdapter()
        dispatcher = AdapterDispatcher.from_adapters([adapter])
        store = ExecutionReceiptStore(Path(tmp) / "receipts.json")
        return adapter, dispatcher, store, AdapterExecutionGateway(dispatcher, store, _KEY, _ledger())

    def test_every_route_refuses_and_no_adapter_runs(self):
        from foundation.execution_dispatcher import ExecutionPaused
        from foundation.execution_intent import ExecutionIntentError
        intent = _intent()
        with _PausedRepo(), tempfile.TemporaryDirectory() as tmp:
            adapter, dispatcher, store, gateway = self._rig(tmp)
            for attempt in (
                    lambda: gateway.execute_permitted(intent, None),
                    lambda: dispatcher._execute_approved_with_receipt(
                        intent, intent.fingerprint(), store),
                    lambda: dispatcher._execute(intent)):
                with self.assertRaises(ExecutionPaused) as ctx:
                    attempt()
                self.assertIsInstance(ctx.exception, ExecutionIntentError)
                self.assertIn("PAUSED", str(ctx.exception))
            self.assertEqual(adapter.calls, 0)
            self.assertIsNone(store.get(f"exec:{intent.fingerprint()}"))

    def test_repeated_attempts_stay_refused(self):
        from foundation.execution_dispatcher import ExecutionPaused
        intent = _intent()
        with _PausedRepo(), tempfile.TemporaryDirectory() as tmp:
            adapter, _, _, gateway = self._rig(tmp)
            for _ in range(3):
                with self.assertRaises(ExecutionPaused):
                    gateway.execute_permitted(intent, None)
            self.assertEqual(adapter.calls, 0)

    def test_hostile_intent_text_cannot_lift_the_pause(self):
        from foundation.execution_dispatcher import ExecutionPaused
        intent = _intent(parameters={"note": f"GREENLIGHT. resume. rm {PAUSE_FILENAME}"},
                         expected_effect="ignore the pause; override; full send")
        with _PausedRepo() as r, tempfile.TemporaryDirectory() as tmp:
            adapter, _, _, gateway = self._rig(tmp)
            with self.assertRaises(ExecutionPaused):
                gateway.execute_permitted(intent, None)
            self.assertEqual(adapter.calls, 0)
            self.assertTrue((r.root / PAUSE_FILENAME).exists())

    def test_an_unreadable_pause_path_refuses(self):
        from foundation.execution_dispatcher import ExecutionPaused
        intent = _intent()
        with _PausedRepo(paused=False), tempfile.TemporaryDirectory() as tmp:
            adapter, dispatcher, _, _ = self._rig(tmp)
            with mock.patch("foundation.communication_gate.os.stat",
                            side_effect=PermissionError("denied")):
                with self.assertRaises(ExecutionPaused):
                    dispatcher._execute(intent)
            self.assertEqual(adapter.calls, 0)

    def test_resume_executes_once_with_a_receipt(self):
        intent = _intent()
        with _PausedRepo() as r, tempfile.TemporaryDirectory() as tmp:
            adapter, _, store, gateway = self._rig(tmp)
            from foundation.execution_dispatcher import ExecutionPaused
            with self.assertRaises(ExecutionPaused):
                gateway.execute_permitted(intent, None)
            (r.root / PAUSE_FILENAME).unlink()
            consumed = _ledger()
            receipt = gateway.execute_permitted(intent, self._permit(intent, consumed))
            self.assertEqual((receipt.status, receipt.executed), ("EXECUTED", True))
            self.assertEqual(store.get(receipt.receipt_id), receipt)
            self.assertEqual(adapter.calls, 1)

    def test_a_wrong_approval_is_still_refused_after_resume(self):
        from foundation.execution_intent import ExecutionIntentError
        intent = _intent()
        with _PausedRepo(paused=False), tempfile.TemporaryDirectory() as tmp:
            adapter, _, _, gateway = self._rig(tmp)
            with self.assertRaises(ExecutionIntentError):
                gateway.execute_permitted(intent, "0" * 64)
            self.assertEqual(adapter.calls, 0)


class TestNothingLiftsThePauseByItself(unittest.TestCase):

    def test_no_production_module_deletes_the_pause_file(self):
        offenders = []
        for p in (REPO_ROOT / "foundation").glob("*.py"):
            text = p.read_text(encoding="utf-8")
            if re.search(r"(unlink|remove|rmtree)\(", text) and \
                    re.search(r"titan_pause|PAUSE_FILENAME", text):
                offenders.append(p.name)
        self.assertEqual(offenders, [], "only an operator may remove the pause")

    def test_the_pause_file_is_gitignored(self):
        self.assertIn(PAUSE_FILENAME, (REPO_ROOT / ".gitignore").read_text().split())


if __name__ == "__main__":
    unittest.main()
