"""Adversarial verification of the ten safety properties a governing
directive names as requiring PROOF rather than assumption.

    1. process death mid-run
    2. restart
    3. resume from checkpoint
    4. forged checkpoint refusal
    5. budget exhaustion
    6. empty work
    7. source failure
    8. kill switch
    9. dirty-tree refusal
   10. replay safety (running the same operation twice must not
       duplicate state)

WHAT WAS ALREADY PROVEN ELSEWHERE, AND WHERE (checked by reading the
suites before writing a single new test here, per this repository's
own reuse-before-build discipline)

Properties 1-7 are already fully proven by
`foundation/tests/test_autonomous_window.py`:
  1. process death mid-run  -> TestPhase3Persistence (a checkpoint is
     written every cycle, so a killed process loses at most one cycle)
  2. restart                -> TestPhase4And5RestartAndRecover::
     test_a_second_window_resumes_instead_of_repeating
  3. resume from checkpoint -> TestPhase3Persistence::
     test_the_checkpoint_survives_the_object, and the same restart test
  4. forged checkpoint refusal -> TestPhase4And5RestartAndRecover::
     test_a_tampered_checkpoint_is_not_resumed_from
  5. budget exhaustion      -> TestPhase6And7BoundedWindow::
     test_the_time_budget_is_honoured
  6. empty work             -> TestPhase6And7BoundedWindow::
     test_an_empty_source_stops_rather_than_spinning
  7. source failure         -> TestPhase6And7BoundedWindow::
     test_a_raising_source_stops_the_window

Property 8 (kill switch) is already proven at BOTH required points by
`foundation/tests/test_autonomy_loop.py`:
  - cycle boundary, no mutation ->
    TestRunOneCycleKillSwitch::test_kill_switch_present_stops_before_any_git_or_sensing_work
  - mid-sleep -> TestRunLoop::test_kill_switch_dropped_mid_sleep_stops_the_loop
  - exactly-once receipt for the mid-sleep path ->
    TestEveryCycleIsReceipted::test_mid_sleep_kill_switch_is_still_receipted_exactly_once

Property 9 (dirty-tree refusal) is PARTIALLY proven there
(TestRunOneCycleDirtyTree asserts only the returned action, not that the
tree is left byte-identical and uncommitted) -- the missing half is
proven below.

None of properties 1-8 are duplicated here. This file adds only:
  - the missing half of property 9 (byte-identical tree + no commit,
    not just the returned action)
  - property 10 (replay safety) end to end, genuinely unproven anywhere
    in this repository before this file
  - one additional angle on the loop's finding-handling that the
    existing suite does not exercise: a SINGLE finding that is not the
    authorized README-drift class (the existing test only covers TWO
    findings, one of which is the drift)
"""

import json
import tempfile
import unittest
from pathlib import Path

from foundation.autonomy_loop import run_one_cycle
from foundation.checkpoint import Checkpoint, CheckpointStore
from foundation.outcome_ledger import OutcomeLedger, Witness, freeze_pre_action
from foundation.tests.test_autonomy_loop import (
    _CLEAN_README,
    _DRIFTED_README,
    _FixtureRepo,
    _git,
)


# ---------------------------------------------------------------------
# Property 9 (the missing half): dirty tree leaves the repository
# byte-identical, not merely "stopped".
# ---------------------------------------------------------------------

class TestDirtyTreeLeavesTheRepositoryExactlyAsFound(unittest.TestCase):
    """PROVEN. `TestRunOneCycleDirtyTree` (test_autonomy_loop.py) already
    proves the returned action is STOPPED_DIRTY_TREE. It does not prove
    the repository was left untouched -- a STOPPED_* result that reads
    as "nothing happened" while quietly mutating something would be
    exactly the trajectory gap `TestStoppedResultLeavesNoMutation`
    (same file) closed for the fix-and-rollback path. This closes the
    analogous gap for the dirty-tree path, which that class does not
    cover (it only exercises the post-write-failure path)."""

    def test_readme_is_byte_identical_after_a_dirty_tree_stop(self):
        with tempfile.TemporaryDirectory() as d:
            fx = _FixtureRepo(d, _DRIFTED_README)   # real drift present
            (fx.root / "untracked.txt").write_text("uncommitted")
            before = (fx.root / "README.md").read_text()
            result = run_one_cycle(fx.root)
            self.assertEqual(result.action, "STOPPED_DIRTY_TREE")
            # The real drift was never touched despite being present.
            self.assertEqual((fx.root / "README.md").read_text(), before)

    def test_the_untracked_file_that_caused_the_stop_is_still_there(self):
        with tempfile.TemporaryDirectory() as d:
            fx = _FixtureRepo(d, _CLEAN_README)
            (fx.root / "untracked.txt").write_text("uncommitted")
            run_one_cycle(fx.root)
            self.assertEqual(
                (fx.root / "untracked.txt").read_text(), "uncommitted")

    def test_no_commit_is_made_on_a_dirty_tree_stop(self):
        with tempfile.TemporaryDirectory() as d:
            fx = _FixtureRepo(d, _CLEAN_README)
            (fx.root / "untracked.txt").write_text("uncommitted")
            before = _git(fx.root, "rev-list", "--count", "HEAD").stdout.strip()
            run_one_cycle(fx.root)
            after = _git(fx.root, "rev-list", "--count", "HEAD").stdout.strip()
            self.assertEqual(before, after)

    def test_porcelain_status_is_unchanged_by_the_stop(self):
        # The dirty status itself must be exactly what caused the stop --
        # not widened or narrowed by anything the cycle did on its way
        # to STOPPED_DIRTY_TREE.
        with tempfile.TemporaryDirectory() as d:
            fx = _FixtureRepo(d, _CLEAN_README)
            (fx.root / "untracked.txt").write_text("uncommitted")
            before = _git(fx.root, "status", "--porcelain").stdout
            run_one_cycle(fx.root)
            after = _git(fx.root, "status", "--porcelain").stdout
            self.assertEqual(before, after)


class TestSingleUnauthorizedFindingRefusal(unittest.TestCase):
    """UNSUPPORTED-FINDING REFUSAL, the angle the existing suite does not
    cover. `test_readme_drift_plus_another_finding_stops_for_human_review`
    (test_autonomy_loop.py) proves the TWO-findings case (drift + one
    other). It never exercises a SINGLE finding that simply is not the
    one authorized class -- a genuinely different branch of
    `_run_one_cycle_uncounted`'s `if len(findings) == 1 and
    findings[0].observation == README_DRIFT_OBSERVATION` check: this
    proves the `len(findings) == 1` branch can still be false when the
    one finding present is the wrong kind, not only when there is more
    than one."""

    def test_one_finding_that_is_not_readme_drift_still_halts_for_review(self):
        with tempfile.TemporaryDirectory() as d:
            fx = _FixtureRepo(d, _CLEAN_README)   # no drift finding at all
            (fx.root / "broken.py").write_text("def f(:\n    pass\n")
            _git(fx.root, "add", ".")
            _git(fx.root, "commit", "-q", "-m", "add broken file")
            before = (fx.root / "README.md").read_text()
            before_commits = _git(fx.root, "rev-list", "--count", "HEAD").stdout.strip()

            result = run_one_cycle(fx.root)

            self.assertEqual(result.action, "STOPPED_UNEXPECTED_FINDINGS")
            self.assertEqual((fx.root / "README.md").read_text(), before)
            self.assertEqual(
                _git(fx.root, "rev-list", "--count", "HEAD").stdout.strip(),
                before_commits)


# ---------------------------------------------------------------------
# Property 10: replay safety. For each store below, run the same
# operation twice and state whether duplication is PREVENTED, HARMLESS,
# or a REAL DEFECT -- with a concrete test as the evidence either way.
# ---------------------------------------------------------------------

def _cp(task_id="T-replay", phase="P", **kw):
    return Checkpoint(task_id=task_id, phase=phase, payload=kw.pop("payload", {}),
                       created_at="2026-01-01T00:00:00+00:00", **kw)


class TestReplaySafety_CheckpointStoreSave(unittest.TestCase):
    """CheckpointStore.save() called twice with the IDENTICAL checkpoint.

    VERDICT: duplication is NOT PREVENTED but is HARMLESS for the
    purpose this store actually serves (resuming). `save()` (see
    checkpoint.py) unconditionally appends to `self._checkpoints` --
    there is no id-based dedup anywhere in it. Saving the same
    `Checkpoint` object twice therefore leaves TWO entries in
    `history()` with the SAME `checkpoint_id` and identical content.
    This is a genuine, demonstrable gap -- "idempotent" is asserted
    nowhere in the module's own docstring, and this test is the reason
    that omission is honest rather than an oversight: `latest()`/
    `resume()` still return the correct (and, since the content is
    identical, indistinguishable) state, so a caller that retries a
    save after an ambiguous failure (e.g. it does not know whether the
    prior save's `os.replace` completed) is not corrupted -- but the
    on-disk file grows by one full duplicate line per retry, forever,
    with nothing here to cap or collapse it. A caller that retries
    saves under uncertainty (the exact situation this module exists
    for) will silently accumulate duplicate history rows."""

    def test_saving_the_identical_checkpoint_twice_duplicates_history(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "cp.jsonl"
            store = CheckpointStore(path=path)
            cp = _cp(payload={"cycle": 1})
            store.save(cp)
            store.save(cp)   # exact same object, replayed verbatim

            history = store.history("T-replay")
            self.assertEqual(
                len(history), 2,
                "KNOWN GAP: CheckpointStore.save() has no id-based dedup -- "
                "saving the identical checkpoint twice produces two rows "
                "with the same checkpoint_id. Duplication is NOT PREVENTED "
                "at this layer.")
            self.assertEqual(history[0].checkpoint_id, history[1].checkpoint_id)

    def test_the_duplication_is_harmless_to_resume_correctness(self):
        # The half that keeps the gap above from being a REAL DEFECT:
        # resume() still returns the right (identical) state, so a
        # retrying caller is not corrupted, only wasteful on disk.
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "cp.jsonl"
            store = CheckpointStore(path=path)
            cp = _cp(payload={"cycle": 7})
            store.save(cp)
            store.save(cp)
            store.save(cp)

            reloaded = CheckpointStore(path=path)
            self.assertEqual(len(reloaded.history("T-replay")), 3)
            self.assertEqual(reloaded.resume("T-replay").payload["cycle"], 7)


class TestReplaySafety_OutcomeLedgerRecord(unittest.TestCase):
    """OutcomeLedger.record() called twice with the SAME context, brick,
    and state.

    VERDICT: REAL DEFECT. `record()` (outcome_ledger.py) mints a fresh
    `outcome_id` from a hash that includes `_now()` and
    `len(self._records)` -- both of which differ on every call by
    construction -- so calling it twice with identical logical inputs
    (same brick, same sealed context, same state, same witness) never
    collapses to one record. Both records are appended, both are
    CHAIN_VERIFIED, and (because neither `supersedes` the other)
    `current_for_brick()` returns only the second, but
    `outcomes_for_brick()` and `all_records()` still return BOTH -- an
    operation retried after an ambiguous failure (the exact situation
    `seal()`'s own docstring calls out for `PreActionContext` -- "a
    re-sealing an identical context is idempotent" -- has NO matching
    protection here for the outcome itself. This is the single
    calibration dataset `pairs()` feeds; a caller that retries
    `record()` under uncertainty silently doubles a real-world event in
    the data this module exists to keep honest."""

    def _seal(self, ledger):
        ctx = freeze_pre_action(
            target="acme/repo#1", target_established_by="test",
            facts={"pressure_class": "EXPLICIT_DEMAND"})
        return ctx

    def test_a_declared_retry_is_idempotent_a_second_look_is_not(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = OutcomeLedger(ledger_path=Path(d) / "outcomes.jsonl")
            ctx = self._seal(ledger)

            first = ledger.record("brick-1", ctx, "NOT_OBSERVED")
            second = ledger.record("brick-1", ctx, "NOT_OBSERVED")

            # GAP CLOSED 2026-09-01, but note carefully WHAT was closed.
            # Without an operation_id these are still two records, and
            # that is correct: looking on Monday and again on Friday and
            # seeing nothing both times is two observations, not one
            # recorded twice. Collapsing them would destroy the
            # silence-versus-absence distinction TERMINAL_UNOBSERVED
            # exists to preserve.
            self.assertNotEqual(first.outcome_id, second.outcome_id)
            self.assertEqual(len(ledger.outcomes_for_brick("brick-1")), 2)

            # What WAS closed: a retry that declares itself a retry is now
            # recognised as one fact. This is the repository's own
            # standing rule for the case -- where an operation cannot be
            # inherently idempotent, require an explicit operation id.
            a = ledger.record("brick-2", ctx, "NOT_OBSERVED", operation_id="OP-X")
            b = ledger.record("brick-2", ctx, "NOT_OBSERVED", operation_id="OP-X")
            self.assertEqual(a.outcome_id, b.outcome_id,
                             "a declared retry must return the original "
                             "record, not append a second")
            self.assertEqual(len(ledger.outcomes_for_brick("brick-2")), 1)

    def test_current_for_brick_hides_the_duplicate_but_all_records_does_not(self):
        # The gap is real precisely because it is partially invisible:
        # the most common read path (current_for_brick) looks fine.
        with tempfile.TemporaryDirectory() as d:
            ledger = OutcomeLedger(ledger_path=Path(d) / "outcomes.jsonl")
            ctx = self._seal(ledger)
            ledger.record("brick-1", ctx, "NOT_OBSERVED")
            ledger.record("brick-1", ctx, "NOT_OBSERVED")

            # Looks idempotent from this angle...
            self.assertIsNotNone(ledger.current_for_brick("brick-1"))
            # ...but the underlying dataset has silently doubled.
            self.assertEqual(len(ledger.all_records()), 2)

    def test_witnessed_outcomes_double_count_the_same_external_signal(self):
        # The sharpest version of the defect: an EXTERNALLY_EVIDENCED
        # state (requires a witness) retried with the SAME witness still
        # produces two independent "a human said so" facts.
        with tempfile.TemporaryDirectory() as d:
            ledger = OutcomeLedger(ledger_path=Path(d) / "outcomes.jsonl")
            ctx = self._seal(ledger)
            w = Witness(observed_by="maintainer_x", mechanism="issue comment",
                       what_was_observed="thanked us for the fix")
            ledger.record("brick-1", ctx, "VALUE_WITNESSED", witness=w)
            ledger.record("brick-1", ctx, "VALUE_WITNESSED", witness=w)
            self.assertEqual(len(ledger.outcomes_for_brick("brick-1")), 2)


class TestReplaySafety_RadarRailSweepDedup(unittest.TestCase):
    """radar_rail.sweep() run twice against the IDENTICAL feed.

    VERDICT: PREVENTED, and by a real mechanism, not luck.
    `sweep()` delegates fetch+dedupe entirely to
    `mouth_github_issues.observe()`, which persists a content hash and
    per-item key set to `state_path` (mouth_common.py::observe()) and
    reports `new_items=()` whenever a re-fetch's content hash matches
    what was last persisted. `sweep()` builds signals only from
    `new_items`, so a second sweep over byte-identical input produces
    zero new signals -- proven here against the real mouth, not
    mocked."""

    def test_a_second_sweep_over_the_identical_feed_yields_no_new_signals(self):
        from foundation.radar_rail import sweep

        def _feed():
            return json.dumps({"items": [
                {"html_url": "https://github.com/acme/r/issues/1",
                 "repository_url": "https://api.github.com/repos/acme/r",
                 "number": 1, "title": "Real problem",
                 "labels": [{"name": "help wanted"}], "comments": 5,
                 "assignees": [], "user": {"login": "dev"},
                 "created_at": "2026-08-01T00:00:00Z",
                 "updated_at": "2026-08-02T00:00:00Z",
                 "state": "open"}]}).encode()

        with tempfile.TemporaryDirectory() as d:
            state_dir = Path(d)
            first = sweep(state_dir, per_page=5, fetch_fn=_feed)
            second = sweep(state_dir, per_page=5, fetch_fn=_feed)

            self.assertEqual(first.fetched_count, 1)
            self.assertGreaterEqual(len(first.signals), 1)
            self.assertEqual(
                second.status, "UNCHANGED",
                "the mouth's content-hash dedupe did not recognise a "
                "byte-identical replay")
            self.assertEqual(
                len(second.signals), 0,
                "REPLAY DUPLICATED A SIGNAL: sweeping the identical feed "
                "twice must yield zero new signals the second time")

    def test_a_second_sweep_after_a_partial_overlap_only_reports_the_new_item(self):
        # Sharper than the byte-identical case: the FEED changes (so the
        # whole-feed content hash differs and status is CHANGED, not
        # UNCHANGED) but one item repeats. The mouth's item-level key
        # dedup, not just the feed-level hash, is what must catch this.
        from foundation.radar_rail import sweep

        def _make(n):
            return json.dumps({"items": [
                {"html_url": f"https://github.com/acme/r/issues/{i}",
                 "repository_url": "https://api.github.com/repos/acme/r",
                 "number": i, "title": f"Real problem {i}",
                 "labels": [{"name": "help wanted"}], "comments": 5,
                 "assignees": [], "user": {"login": "dev"},
                 "created_at": "2026-08-01T00:00:00Z",
                 "updated_at": "2026-08-02T00:00:00Z",
                 "state": "open"} for i in range(n)]}).encode()

        with tempfile.TemporaryDirectory() as d:
            state_dir = Path(d)
            first = sweep(state_dir, per_page=5, fetch_fn=lambda: _make(1))
            second = sweep(state_dir, per_page=5, fetch_fn=lambda: _make(2))

            self.assertEqual(len(first.signals), 1)
            # Only issue #1 (the new one) should appear -- issue #0 must
            # not be re-signalled just because the surrounding feed grew.
            # (`target` is the repo, "acme/r" for both issues -- the
            # per-item dedup key is the issue url, checked via the
            # signal count above, not via a distinct target string.)
            self.assertEqual(len(second.signals), 1)
            self.assertEqual(second.targets, ("acme/r",))


class TestReplaySafety_AutonomousWindowRerunOfACompletedWindow(unittest.TestCase):
    """autonomous_window.run_window() invoked a second time against a
    window that already reached CYCLE_CAP_REACHED (a "completed" window
    in the sense the task names).

    VERDICT: PREVENTED. `resume_or_start()` reads the last checkpointed
    cycle number; `run_window()`'s own loop condition is
    `while cycle < max_cycles`. When the checkpoint already records
    `cycle == max_cycles`, the loop body never executes on the second
    call -- zero new checkpoints, zero new cycle records, zero new
    signals -- proven against the real checkpoint file, not by
    inspecting the source."""

    def _feed(self, n=1):
        return json.dumps({"items": [
            {"html_url": f"https://github.com/acme/r{i}/issues/{i}",
             "repository_url": f"https://api.github.com/repos/acme/r{i}",
             "number": i, "title": f"Real problem {i}",
             "labels": [{"name": "help wanted"}], "comments": 5,
             "assignees": [], "user": {"login": "dev"},
             "created_at": "2026-08-01T00:00:00Z",
             "updated_at": "2026-08-02T00:00:00Z",
             "state": "open"} for i in range(n)]}).encode()

    def test_rerunning_a_cycle_cap_completed_window_does_nothing(self):
        from foundation.autonomous_window import run_window

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            cp = root / "cp.jsonl"
            state_dir = root / "s"

            first = run_window(state_dir, fetch_fn=lambda: self._feed(1),
                               budget_seconds=10, max_cycles=1,
                               checkpoint_path=cp)
            self.assertEqual(first.cycles_run, 1)
            self.assertEqual(first.stop_reason, "CYCLE_CAP_REACHED")

            history_after_first = CheckpointStore(cp).history("AUTONOMOUS_WINDOW")
            self.assertEqual(len(history_after_first), 1)

            second = run_window(state_dir, fetch_fn=lambda: self._feed(1),
                                budget_seconds=10, max_cycles=1,
                                checkpoint_path=cp)

            self.assertEqual(
                second.cycles_run, 0,
                "a window already at its cycle cap must not run again "
                "just because it was invoked a second time")
            self.assertIsNone(second.checkpoint_id)
            self.assertEqual(second.cycles_resumed_from, 1)

            history_after_second = CheckpointStore(cp).history("AUTONOMOUS_WINDOW")
            self.assertEqual(
                len(history_after_second), 1,
                "re-running a completed window must not write a new "
                "checkpoint")

    def test_rerunning_a_no_work_completed_window_re_observes_but_signals_stay_zero(self):
        # The other honest "completed" shape: NO_WORK, not CYCLE_CAP.
        # `fetched_count` on a RadarSweep is the RAW feed's item count
        # (mouth_common.observe()'s item_count), not "new since last
        # time" -- so NO_WORK is reached only when the underlying feed
        # is genuinely empty, and the resumed cycle count still climbs
        # by one honest, non-duplicating attempt each rerun (proven via
        # the checkpoint's own cycle counter below), never replaying an
        # old signal.
        from foundation.autonomous_window import run_window

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            cp = root / "cp.jsonl"
            state_dir = root / "s"

            first = run_window(state_dir, fetch_fn=lambda: b'{"items":[]}',
                               budget_seconds=10, max_cycles=5,
                               checkpoint_path=cp)
            self.assertEqual(first.stop_reason, "NO_WORK")
            self.assertEqual(first.cycles_run, 1)

            second = run_window(state_dir, fetch_fn=lambda: b'{"items":[]}',
                                budget_seconds=10, max_cycles=5,
                                checkpoint_path=cp)
            self.assertEqual(second.stop_reason, "NO_WORK")
            self.assertEqual(second.cycles_resumed_from, 1)
            self.assertEqual(second.cycles_run, 1)
            for r in second.records:
                self.assertEqual(r.signals, 0)

            # The checkpoint's own cycle counter advanced by exactly one
            # per rerun -- a genuine new observation each time, not a
            # replayed one, and never a duplicate SIGNAL count.
            latest = CheckpointStore(cp).resume("AUTONOMOUS_WINDOW")
            self.assertEqual(latest.payload["cycle"], 2)


if __name__ == "__main__":
    unittest.main()
