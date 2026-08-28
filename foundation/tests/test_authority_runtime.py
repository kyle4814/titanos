import fcntl
import os
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from foundation.authority_runtime import read_tick_log, run_loop, tick
from foundation.authority_sigil import ReleaseLedger, issue_release

NOW = datetime(2026, 8, 27, 12, 0, 0, tzinfo=timezone.utc)


class TestTickAdmitted(unittest.TestCase):
    def test_admitted_tick_runs_pulse_sweep_and_writes_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "repo"
            root.mkdir()
            ledger = ReleaseLedger(ledger_path=None)
            issue_release(
                ledger, release_id="R1", authority_class="ZERO_SPEND_READ_ONLY",
                allowed_capabilities=frozenset({"RUN_PULSE_SWEEP"}),
                allowed_targets=frozenset({str(root)}),
                max_actions_per_period=5, period_seconds=3600,
                issued_by="Kyle", duration_seconds=3600, now=NOW,
            )
            log_path = Path(d) / "tick_log.jsonl"
            result = tick(ledger, "R1", str(root), log_path=log_path, now=NOW)
            self.assertTrue(result.admitted)
            self.assertIsNotNone(result.raw_finding_count)
            records = read_tick_log(log_path)
            self.assertEqual(len(records), 1)
            self.assertTrue(records[0]["admitted"])


class TestTickDenied(unittest.TestCase):
    def test_denied_tick_does_not_run_pulse_sweep_but_writes_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = ReleaseLedger(ledger_path=None)  # no release issued at all
            log_path = Path(d) / "tick_log.jsonl"
            result = tick(ledger, "NOPE", "/anything", log_path=log_path, now=NOW)
            self.assertFalse(result.admitted)
            self.assertIsNone(result.raw_finding_count)  # pulse_sweep never ran
            records = read_tick_log(log_path)
            self.assertEqual(len(records), 1)
            self.assertFalse(records[0]["admitted"])
            self.assertTrue(any("does not exist" in r for r in records[0]["reasons"]))

    def test_expired_release_tick_is_denied_not_silently_run(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "repo"
            root.mkdir()
            ledger = ReleaseLedger(ledger_path=None)
            issue_release(
                ledger, release_id="R1", authority_class="ZERO_SPEND_READ_ONLY",
                allowed_capabilities=frozenset({"RUN_PULSE_SWEEP"}),
                allowed_targets=frozenset({str(root)}),
                max_actions_per_period=5, period_seconds=3600,
                issued_by="Kyle", duration_seconds=1, now=NOW,  # expires almost immediately
            )
            from datetime import timedelta
            later = NOW + timedelta(seconds=5)
            log_path = Path(d) / "tick_log.jsonl"
            result = tick(ledger, "R1", str(root), log_path=log_path, now=later)
            self.assertFalse(result.admitted)


class TestExecutionFailureDoesNotPhantomConsumeBudget(unittest.TestCase):
    """Reproduces and fixes a real defect found 2026-08-28: tick() used
    to record budget consumption BEFORE running pulse_sweep(), so a
    crash/exception during execution left a durable ADMIT record with no
    completed work and no receipt -- a real reconciliation gap, not a
    hypothetical one. Directly reproduced here by mocking pulse_sweep()
    to raise mid-call."""

    def test_execution_failure_does_not_raise_and_is_receipted_as_error(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "repo"
            root.mkdir()
            ledger = ReleaseLedger(ledger_path=None)
            issue_release(
                ledger, release_id="R1", authority_class="ZERO_SPEND_READ_ONLY",
                allowed_capabilities=frozenset({"RUN_PULSE_SWEEP"}),
                allowed_targets=frozenset({str(root)}),
                max_actions_per_period=1, period_seconds=3600,
                issued_by="Kyle", duration_seconds=3600,
            )
            log_path = Path(d) / "tick_log.jsonl"
            with mock.patch(
                "foundation.authority_runtime.pulse_sweep",
                side_effect=RuntimeError("simulated crash mid-capability"),
            ):
                result = tick(ledger, "R1", str(root), log_path=log_path)  # must not raise

            self.assertFalse(result.admitted)
            self.assertIn("execution failed", result.reasons[0])
            self.assertEqual(len(read_tick_log(log_path)), 1)  # a receipt exists

    def test_execution_failure_records_error_not_admit_and_does_not_consume_budget(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "repo"
            root.mkdir()
            ledger_path = Path(d) / "ledger.jsonl"
            # Explicit temp tick log: without it these two tick() calls fall
            # back to authority_runtime._DEFAULT_TICK_LOG -- the REAL one in
            # foundation/ -- and every test run silently appends receipts to
            # live machine-local authority state. Found 2026-08-28 by
            # fingerprinting live files across a full regression run.
            tick_log_path = Path(d) / "tick_log.jsonl"
            ledger = ReleaseLedger(ledger_path=ledger_path)
            issue_release(
                ledger, release_id="R1", authority_class="ZERO_SPEND_READ_ONLY",
                allowed_capabilities=frozenset({"RUN_PULSE_SWEEP"}),
                allowed_targets=frozenset({str(root)}),
                max_actions_per_period=1, period_seconds=3600,
                issued_by="Kyle", duration_seconds=3600,
            )
            with mock.patch(
                "foundation.authority_runtime.pulse_sweep",
                side_effect=RuntimeError("boom"),
            ):
                tick(ledger, "R1", str(root), log_path=tick_log_path)

            fresh = ReleaseLedger(ledger_path=ledger_path)
            actions = fresh.all_actions()
            self.assertEqual(len(actions), 1)
            self.assertEqual(actions[0].result, "ERROR")  # not ADMIT

            # Budget=1 was never actually spent -- a retry must succeed.
            retry = tick(fresh, "R1", str(root), log_path=tick_log_path)
            self.assertTrue(retry.admitted)


class TestRunLoopBounded(unittest.TestCase):
    def test_run_loop_never_exceeds_max_ticks(self):
        with self.assertRaises(ValueError):
            run_loop(ReleaseLedger(ledger_path=None), "R1", "/x", max_ticks=0, interval_seconds=0)

    def test_run_loop_produces_exactly_max_ticks_results(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "repo"
            root.mkdir()
            ledger = ReleaseLedger(ledger_path=None)
            issue_release(
                ledger, release_id="R1", authority_class="ZERO_SPEND_READ_ONLY",
                allowed_capabilities=frozenset({"RUN_PULSE_SWEEP"}),
                allowed_targets=frozenset({str(root)}),
                max_actions_per_period=10, period_seconds=3600,
                issued_by="Kyle", duration_seconds=3600,
                # Real wall-clock issuance -- run_loop() ticks against
                # real time by default, so the release must be issued
                # against real time too, not a fixed synthetic NOW that
                # may already be in the past by the time this runs.
            )
            log_path = Path(d) / "tick_log.jsonl"
            results = run_loop(
                ledger, "R1", str(root), max_ticks=3, interval_seconds=0.01,
                log_path=log_path,
            )
            self.assertEqual(len(results), 3)
            self.assertTrue(all(r.admitted for r in results))
            self.assertEqual(len(read_tick_log(log_path)), 3)

    def test_run_loop_stops_admitting_once_real_budget_exhausted(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "repo"
            root.mkdir()
            ledger = ReleaseLedger(ledger_path=None)
            issue_release(
                ledger, release_id="R1", authority_class="ZERO_SPEND_READ_ONLY",
                allowed_capabilities=frozenset({"RUN_PULSE_SWEEP"}),
                allowed_targets=frozenset({str(root)}),
                max_actions_per_period=2, period_seconds=3600,
                issued_by="Kyle", duration_seconds=3600,
            )
            log_path = Path(d) / "tick_log.jsonl"
            # Ticks use real wall-clock `now` (default), all within the
            # same budget period -- proves the loop, not a mocked clock.
            results = run_loop(
                ledger, "R1", str(root), max_ticks=4, interval_seconds=0.01,
                log_path=log_path,
            )
            admitted = [r for r in results if r.admitted]
            denied = [r for r in results if not r.admitted]
            self.assertEqual(len(admitted), 2)
            self.assertEqual(len(denied), 2)


class TestReadTickLog(unittest.TestCase):
    def test_missing_log_returns_empty_tuple_not_error(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(read_tick_log(Path(d) / "nope.jsonl"), ())


if __name__ == "__main__":
    unittest.main()


class TestTickHoldsTheLedgerLockAcrossTheWholeTick(unittest.TestCase):
    """The runtime half of the 2026-08-28 concurrency fix. tick() consumes
    budget only after confirmed successful execution, so the window that
    must be protected is the entire decide -> execute -> consume sequence,
    not just the two ledger touches at its ends."""

    def _issue(self, ledger, root, budget=1):
        issue_release(
            ledger, release_id="R1", authority_class="ZERO_SPEND_READ_ONLY",
            allowed_capabilities=frozenset({"RUN_PULSE_SWEEP"}),
            allowed_targets=frozenset({str(root)}),
            max_actions_per_period=budget, period_seconds=3600,
            issued_by="Kyle", duration_seconds=3600,
        )

    def test_a_contended_ledger_produces_a_receipted_refusal_not_a_hang(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "repo"; root.mkdir()
            ledger_path = Path(d) / "ledger.jsonl"
            tick_log = Path(d) / "tick_log.jsonl"
            self._issue(ReleaseLedger(ledger_path=ledger_path), root)

            holder = open(ledger_path, "a", encoding="utf-8")
            self.addCleanup(holder.close)
            fcntl.flock(holder.fileno(), fcntl.LOCK_EX)

            started = time.monotonic()
            result = tick(ReleaseLedger(ledger_path=ledger_path), "R1", str(root), log_path=tick_log)
            elapsed = time.monotonic() - started

            self.assertFalse(result.admitted)
            self.assertIn("ledger busy", result.reasons[0])
            self.assertLess(elapsed, 2.0, "tick blocked on the lock instead of refusing")
            self.assertEqual(len(read_tick_log(tick_log)), 1, "refusal left no receipt")

            fcntl.flock(holder.fileno(), fcntl.LOCK_UN)

    def test_a_refused_tick_does_not_consume_budget(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "repo"; root.mkdir()
            ledger_path = Path(d) / "ledger.jsonl"
            tick_log = Path(d) / "tick_log.jsonl"
            self._issue(ReleaseLedger(ledger_path=ledger_path), root)

            holder = open(ledger_path, "a", encoding="utf-8")
            self.addCleanup(holder.close)
            fcntl.flock(holder.fileno(), fcntl.LOCK_EX)
            tick(ReleaseLedger(ledger_path=ledger_path), "R1", str(root), log_path=tick_log)
            fcntl.flock(holder.fileno(), fcntl.LOCK_UN)

            # Budget of 1 must still be fully available after the refusal.
            self.assertTrue(
                tick(ReleaseLedger(ledger_path=ledger_path), "R1", str(root), log_path=tick_log).admitted
            )

    def test_two_sequential_ticks_cannot_exceed_a_budget_of_one(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "repo"; root.mkdir()
            ledger_path = Path(d) / "ledger.jsonl"
            tick_log = Path(d) / "tick_log.jsonl"
            self._issue(ReleaseLedger(ledger_path=ledger_path), root)

            r1 = tick(ReleaseLedger(ledger_path=ledger_path), "R1", str(root), log_path=tick_log)
            r2 = tick(ReleaseLedger(ledger_path=ledger_path), "R1", str(root), log_path=tick_log)
            self.assertTrue(r1.admitted)
            self.assertFalse(r2.admitted)

            fresh = ReleaseLedger(ledger_path=ledger_path)
            self.assertEqual(len([a for a in fresh.all_actions() if a.result == "ADMIT"]), 1)


class TestLockAcquisitionFailureIsReceiptedNotRaised(unittest.TestCase):
    """Adversarial review 2026-08-28: tick() caught only LedgerBusy, so an
    OSError from opening the ledger for locking (read-only file, full disk,
    permission drift) propagated uncaught -- crashing a cron-invoked
    process with no receipt, contradicting this module's stated contract
    that a tick never propagates uncaught."""

    def test_a_read_only_ledger_produces_a_receipted_refusal(self):
        with tempfile.TemporaryDirectory() as d:
            ledger_path = Path(d) / "ledger.jsonl"
            ledger_path.write_text("")
            tick_log = Path(d) / "tick_log.jsonl"
            os.chmod(ledger_path, 0o444)
            # No addCleanup chmod: it would fire after the TemporaryDirectory
            # is already gone. The containing dir stays writable, so unlink
            # during teardown works regardless of the file's own mode.
            result = tick(ReleaseLedger(ledger_path=ledger_path), "R1",
                          str(Path(d)), log_path=tick_log)

            self.assertFalse(result.admitted)
            self.assertIn("could not acquire the ledger lock", result.reasons[0])
            self.assertEqual(len(read_tick_log(tick_log)), 1, "refusal left no receipt")
