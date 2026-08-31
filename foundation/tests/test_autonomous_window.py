"""The autonomy ramp, phases 3 through 7, proven rather than claimed.

The governing order refuses to let "the loop could run" substitute for
"the loop ran". Phases 1 and 2 (offline sweep; mouth -> tentacle ->
signal) were already proven by `test_radar_rail.py`. These tests cover
what was missing: persistence, restart, recovery, multiple cycles, and
a bounded window.

Every test runs offline. `urlopen` is patched to raise so that a socket
opened anywhere in this path fails the suite loudly.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from foundation.autonomous_window import (
    STOP_REASONS, CycleRecord, WindowResult, resume_or_start, run_window,
)
from foundation.checkpoint import CheckpointStore


def _feed(n, label="help wanted", login="dev", assignees=()):
    return json.dumps({"items": [
        {"html_url": f"https://github.com/acme/r{i}/issues/{i}",
         "repository_url": f"https://api.github.com/repos/acme/r{i}",
         "number": i, "title": f"Real problem {i}",
         "labels": [{"name": label}], "comments": 5,
         "assignees": [{"login": a} for a in assignees],
         "user": {"login": login},
         "created_at": "2026-08-01T00:00:00Z",
         "updated_at": f"2026-08-3{i % 10}T00:00:00Z",
         "state": "open"} for i in range(n)]}).encode()


def _never_opens_a_socket(*a, **k):                       # pragma: no cover
    raise AssertionError("a socket was opened during an offline window test")


class _Window(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        patch = mock.patch("urllib.request.urlopen", _never_opens_a_socket)
        patch.start(); self.addCleanup(patch.stop)

    def _growing_feed(self, start=0):
        c = {"n": start}
        def f():
            c["n"] += 1
            return _feed(c["n"] + 1)
        return f


class TestPhase3Persistence(_Window):

    def test_a_checkpoint_is_written_for_every_cycle(self):
        cp = self.root / "cp.jsonl"
        r = run_window(self.root / "s", fetch_fn=self._growing_feed(),
                       budget_seconds=10, max_cycles=3, checkpoint_path=cp)
        self.assertEqual(r.cycles_run, 3)
        self.assertIsNotNone(r.checkpoint_id)
        self.assertEqual(len(CheckpointStore(cp).history("AUTONOMOUS_WINDOW")), 3)

    def test_the_checkpoint_survives_the_object(self):
        cp = self.root / "cp.jsonl"
        run_window(self.root / "s", fetch_fn=self._growing_feed(),
                   budget_seconds=10, max_cycles=2, checkpoint_path=cp)
        self.assertEqual(resume_or_start(CheckpointStore(cp)), 2)


class TestPhase4And5RestartAndRecover(_Window):
    """A restart that starts over has not recovered. It has merely run
    again. That distinction is the entire point of these two phases."""

    def test_a_second_window_resumes_instead_of_repeating(self):
        cp = self.root / "cp.jsonl"
        first = run_window(self.root / "s", fetch_fn=self._growing_feed(),
                           budget_seconds=10, max_cycles=2, checkpoint_path=cp)
        second = run_window(self.root / "s", fetch_fn=self._growing_feed(9),
                            budget_seconds=10, max_cycles=4, checkpoint_path=cp)
        self.assertEqual(second.cycles_resumed_from, first.cycles_run)
        self.assertEqual(second.records[0].cycle, first.cycles_run + 1)

    def test_the_resume_is_reported_not_silent(self):
        cp = self.root / "cp.jsonl"
        run_window(self.root / "s", fetch_fn=self._growing_feed(),
                   budget_seconds=10, max_cycles=2, checkpoint_path=cp)
        second = run_window(self.root / "s", fetch_fn=self._growing_feed(9),
                            budget_seconds=10, max_cycles=4, checkpoint_path=cp)
        self.assertTrue(any("resumed" in n for n in second.notes))

    def test_a_first_run_with_no_checkpoint_is_not_an_error(self):
        self.assertEqual(resume_or_start(CheckpointStore(None)), 0)

    def test_a_tampered_checkpoint_is_not_resumed_from(self):
        """Continuing from state whose integrity failed would silently
        build on a lie."""
        cp = self.root / "cp.jsonl"
        run_window(self.root / "s", fetch_fn=self._growing_feed(),
                   budget_seconds=10, max_cycles=2, checkpoint_path=cp)
        lines = [json.loads(x) for x in cp.read_text().splitlines() if x.strip()]
        lines[-1]["payload"]["cycle"] = 99          # forge progress
        cp.write_text("\n".join(json.dumps(x, sort_keys=True) for x in lines) + "\n")
        self.assertEqual(resume_or_start(CheckpointStore(cp)), 0)


class TestPhase6And7BoundedWindow(_Window):

    def test_the_cycle_cap_is_honoured(self):
        r = run_window(self.root / "s", fetch_fn=self._growing_feed(),
                       budget_seconds=60, max_cycles=2,
                       checkpoint_path=self.root / "cp.jsonl")
        self.assertEqual(r.cycles_run, 2)
        self.assertEqual(r.stop_reason, "CYCLE_CAP_REACHED")

    def test_the_time_budget_is_honoured(self):
        r = run_window(self.root / "s", fetch_fn=self._growing_feed(),
                       budget_seconds=0.0, max_cycles=99,
                       checkpoint_path=self.root / "cp.jsonl")
        self.assertEqual(r.stop_reason, "BUDGET_EXHAUSTED")
        self.assertEqual(r.cycles_run, 0)

    def test_an_empty_source_stops_rather_than_spinning(self):
        r = run_window(self.root / "s", fetch_fn=lambda: b'{"items":[]}',
                       budget_seconds=10, max_cycles=99,
                       checkpoint_path=self.root / "cp.jsonl")
        self.assertEqual(r.stop_reason, "NO_WORK")

    def test_a_caller_stop_condition_interrupts(self):
        r = run_window(self.root / "s", fetch_fn=self._growing_feed(),
                       budget_seconds=10, max_cycles=9,
                       checkpoint_path=self.root / "cp.jsonl",
                       should_stop=lambda: True)
        self.assertEqual(r.stop_reason, "INTERRUPTED")

    def test_every_stop_reason_is_declared(self):
        for reason in ("BUDGET_EXHAUSTED", "CYCLE_CAP_REACHED", "NO_WORK",
                       "INTERRUPTED"):
            self.assertIn(reason, STOP_REASONS)

    def test_a_raising_source_stops_the_window(self):
        """A loop that retries a broken source until its budget expires has
        converted a clear failure into an expensive silence."""
        def boom():
            raise RuntimeError("source down")
        r = run_window(self.root / "s", fetch_fn=boom, budget_seconds=10,
                       max_cycles=9, checkpoint_path=self.root / "cp.jsonl")
        self.assertEqual(r.stop_reason, "SOURCE_FAILED")
        self.assertTrue(any("RuntimeError" in n for n in r.notes))


class TestItObservesAndNothingMore(_Window):

    def test_it_starts_cold_with_no_state_directory(self):
        """A window that cannot start cold is not autonomous. Found on the
        very first real run, where sweep() raised FileNotFoundError."""
        r = run_window(self.root / "never" / "existed",
                       fetch_fn=self._growing_feed(), budget_seconds=10,
                       max_cycles=1, checkpoint_path=self.root / "cp.jsonl")
        self.assertEqual(r.cycles_run, 1)

    def test_it_writes_nothing_to_the_outcome_ledger(self):
        from foundation.outcome_ledger import OutcomeLedger
        before = len(OutcomeLedger()._records)
        run_window(self.root / "s", fetch_fn=self._growing_feed(),
                   budget_seconds=10, max_cycles=2,
                   checkpoint_path=self.root / "cp.jsonl")
        self.assertEqual(len(OutcomeLedger()._records), before)

    def test_the_report_states_it_only_observes(self):
        r = run_window(self.root / "s", fetch_fn=self._growing_feed(),
                       budget_seconds=10, max_cycles=1,
                       checkpoint_path=self.root / "cp.jsonl")
        self.assertIn("observes and checkpoints only", r.show_the_math())

    def test_rejections_are_carried_through_the_window(self):
        r = run_window(self.root / "s",
                       fetch_fn=lambda: _feed(2, login="somebot[bot]"),
                       budget_seconds=10, max_cycles=1,
                       checkpoint_path=self.root / "cp.jsonl")
        self.assertEqual(r.records[0].explicit_demand, 0)
        self.assertGreater(r.records[0].rejected, 0)


if __name__ == "__main__":
    unittest.main()
