"""
Integration test for foundation/cron_pulse.py::main() -- the one process
in this repository that actually runs unattended, live, on a real
crontab entry (confirmed 2026-08-28: 29 real ticks over ~23 hours,
0 errors, 0 CHANGED mouth observations, 0 pulse findings).

WHY THIS FILE EXISTS

Every function cron_pulse.py calls is independently unit-tested
(sentinel.pulse_sweep, mouth_pypi/mouth_github_releases.observe,
dependency_pressure.evaluate_dependency_pressure) -- but main()'s own
wiring of them together, specifically the CHANGED -> pressure-finding ->
receipt branch, had never been exercised by any test, and had never
fired for real in 29 live ticks either (no real PyYAML release has
happened since this cron entry started). That branch is therefore a
genuinely unverified piece of the one live 24/7 loop this repository
has -- this closes that gap using the same fetch_fn-injection pattern
already established in test_mouth_common.py, not a new test strategy.

Does not modify the real MOUTHS state files or logs -- monkeypatches
cron_pulse.MOUTHS to point at a temp directory for the duration of each
test.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import foundation.cron_pulse as cron_pulse
from foundation.mouth_common import observe


class TestCronPulseChangedBranchIntegration(unittest.TestCase):
    """RUN 1 / RUN 2 continuity proof for the untested branch: a real
    CHANGED-with-newer-version observation, run through the actual
    main() code path (not a mocked-out version of it)."""

    def _run_main_with_fake_pypi_release(self, tmp_dir: Path, new_version: str):
        state_path = tmp_dir / "mouth_pypi_state.json"
        pulse_log = tmp_dir / "pulse_log.jsonl"
        pressure_log = tmp_dir / "dependency_pressure_log.jsonl"
        mouth_log = tmp_dir / "mouth_pypi_pyyaml_releases_log.jsonl"

        def fake_observe(_state_path, now=None):
            # A real CHANGED MouthObservation, produced through the real
            # observe() state machine (not hand-constructed), so the
            # first call is FIRST_SEEN and this second call is genuinely
            # CHANGED against durable prior state -- exactly the real
            # mouth's own contract.
            items_old = ({"key": "a", "title": "6.0.3"},)
            items_new = ({"key": "a", "title": "6.0.3"}, {"key": "b", "title": new_version})
            observe("pypi_pyyaml_releases", state_path, lambda: b"v1", lambda raw: items_old)
            return observe("pypi_pyyaml_releases", state_path, lambda: b"v2", lambda raw: items_new)

        fake_mouths = (
            (cron_pulse.mouth_pypi.MOUTH_ID, fake_observe, state_path, "PyYAML"),
        )

        with mock.patch.object(cron_pulse, "MOUTHS", fake_mouths), \
             mock.patch.object(cron_pulse, "LOG_PATH", pulse_log), \
             mock.patch.object(cron_pulse, "DEPENDENCY_PRESSURE_LOG_PATH", pressure_log), \
             mock.patch.object(cron_pulse, "REPO_ROOT", tmp_dir):
            # main() derives its per-mouth log path from REPO_ROOT/foundation,
            # so give it that real subdirectory to write into.
            (tmp_dir / "foundation").mkdir(exist_ok=True)
            with mock.patch.object(
                cron_pulse, "REQUIREMENTS_PATH",
                Path("requirements.txt").resolve(),  # the real, real pinned file
            ):
                result = cron_pulse.main()

        return result, pressure_log

    def test_a_newer_real_release_produces_a_real_pressure_finding(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_dir = Path(d)
            result, pressure_log = self._run_main_with_fake_pypi_release(
                tmp_dir, new_version="9.9.9",
            )
            self.assertEqual(result, 0)  # main() must not crash or exit non-zero
            self.assertTrue(pressure_log.exists(), "the untested branch never wrote a receipt")
            records = [json.loads(l) for l in pressure_log.read_text().splitlines() if l.strip()]
            self.assertEqual(len(records), 1)
            self.assertIn("9.9.9", records[0]["observation"])
            self.assertEqual(records[0]["confidence"], "HIGH")

    def test_an_equal_release_produces_an_informational_not_actionable_finding(self):
        # Negative control -- proves the branch discriminates real
        # pressure from noise: a receipt is still written (evidence of
        # the check having run), but it must never claim actionable
        # pressure when the pinned version is already current.
        with tempfile.TemporaryDirectory() as d:
            tmp_dir = Path(d)
            result, pressure_log = self._run_main_with_fake_pypi_release(
                tmp_dir, new_version="6.0.3",  # same as pinned -- no real pressure
            )
            self.assertEqual(result, 0)
            self.assertTrue(pressure_log.exists())
            records = [json.loads(l) for l in pressure_log.read_text().splitlines() if l.strip()]
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["recommended_next_action"], "NONE_REQUIRED")
            self.assertNotEqual(records[0]["confidence"], "HIGH_ACTIONABLE")  # no such value exists; sanity guard

    def test_run_2_can_see_run_1s_receipt_from_a_fresh_read(self):
        """The RUN 1 -> RUN 2 continuity proof this pass's protocol
        requires: after main() exits (process boundary simulated by
        discarding all local state), a fresh, independent read of the
        durable log reconstructs what happened -- no in-memory state
        survives between the two reads."""
        with tempfile.TemporaryDirectory() as d:
            tmp_dir = Path(d)
            self._run_main_with_fake_pypi_release(tmp_dir, new_version="9.9.9")

            # RUN 2: a completely independent process reading only the
            # durable artifact, no reference to anything from RUN 1.
            pressure_log = tmp_dir / "dependency_pressure_log.jsonl"
            fresh_records = [
                json.loads(l) for l in Path(pressure_log).read_text().splitlines() if l.strip()
            ]
            self.assertEqual(len(fresh_records), 1)
            self.assertIn("PyYAML", fresh_records[0]["observation"])


if __name__ == "__main__":
    unittest.main()


class TestPulseLogWriteFailureDoesNotAbortTheTick(unittest.TestCase):
    """Adversarial review 2026-08-28: cron_pulse.main()'s own pulse_log
    write was unguarded while the per-mouth loop below it was guarded, so
    a disk-full or permission error on that FIRST write raised uncaught
    and aborted the entire tick before either mouth ran -- silently
    contradicting this module's own docstring promise that one component's
    failure 'must never prevent pulse_sweep() or any other mouth from
    running'."""

    def test_an_unwritable_pulse_log_still_lets_the_mouths_run(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            (tmp / "foundation").mkdir()
            mouth_log = tmp / "foundation" / "mouth_probe_log.jsonl"
            unwritable = tmp / "nonexistent-dir" / "pulse_log.jsonl"  # parent absent -> OSError

            def fake_observe(_state_path, now=None):
                return observe("probe", tmp / "probe_state.json",
                               lambda: b"v1", lambda raw: ({"key": "a", "title": "1.0.0"},))

            with mock.patch.object(cron_pulse, "MOUTHS", (("probe", fake_observe, tmp / "s.json", None),)), \
                 mock.patch.object(cron_pulse, "LOG_PATH", unwritable), \
                 mock.patch.object(cron_pulse, "REPO_ROOT", tmp):
                result = cron_pulse.main()

            self.assertEqual(result, 0, "the whole tick aborted on an unwritable pulse log")
            self.assertTrue(mouth_log.exists(), "the mouth never ran because the pulse write died first")


class TestOneMouthsWriteFailureDoesNotStopLaterMouths(unittest.TestCase):
    """Adversarial review 2026-08-28, after an earlier pass fixed only the
    FIRST write in cron_pulse.py: the per-mouth fallback write targeted the
    SAME path that had just failed, under the SAME condition, unguarded --
    so it raised a second time, uncaught, aborting main() and stopping the
    MOUTHS loop. Every mouth after the failing one got NO record at all,
    not even UNAVAILABLE."""

    def _mouth(self, tmp, mouth_id):
        def observe_fn(_state_path, now=None):
            return observe(mouth_id, tmp / f"{mouth_id}_state.json",
                           lambda: b"v1", lambda raw: ({"key": "a", "title": "1.0.0"},))
        return observe_fn

    def test_a_failing_first_mouth_does_not_prevent_the_second(self):
        real_open = Path.open

        def fake_open(self, mode="r", *a, **kw):
            if self.name == "mouth_FIRST_log.jsonl" and "a" in mode:
                raise OSError("simulated disk full")
            return real_open(self, mode, *a, **kw)

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            (tmp / "foundation").mkdir()
            mouths = (
                ("FIRST", self._mouth(tmp, "FIRST"), tmp / "f.json", None),
                ("SECOND", self._mouth(tmp, "SECOND"), tmp / "s.json", None),
            )
            with mock.patch.object(cron_pulse, "MOUTHS", mouths), \
                 mock.patch.object(cron_pulse, "LOG_PATH", tmp / "foundation" / "pulse_log.jsonl"), \
                 mock.patch.object(cron_pulse, "REPO_ROOT", tmp), \
                 mock.patch.object(Path, "open", fake_open):
                result = cron_pulse.main()

            self.assertEqual(result, 0, "the tick aborted instead of degrading")
            self.assertTrue((tmp / "foundation" / "mouth_SECOND_log.jsonl").exists(),
                            "the second mouth never ran because the first mouth's "
                            "write failure crashed the loop")

    def test_a_totally_unwritable_run_still_exits_zero(self):
        real_open = Path.open

        def fake_open(self, mode="r", *a, **kw):
            if "a" in mode:
                raise OSError("everything is read-only")
            return real_open(self, mode, *a, **kw)

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            (tmp / "foundation").mkdir()
            mouths = (("ONLY", self._mouth(tmp, "ONLY"), tmp / "o.json", None),)
            with mock.patch.object(cron_pulse, "MOUTHS", mouths), \
                 mock.patch.object(cron_pulse, "LOG_PATH", tmp / "foundation" / "pulse_log.jsonl"), \
                 mock.patch.object(cron_pulse, "REPO_ROOT", tmp), \
                 mock.patch.object(Path, "open", fake_open):
                self.assertEqual(cron_pulse.main(), 0)


class TestPulseSweepFailureDoesNotStopTheMouths(unittest.TestCase):
    """Hunt-surface rotation 2026-08-28: pulse_sweep(REPO_ROOT) itself was
    called unguarded at the top of main(). Now that every check inside it
    is isolated (found and fixed the same cycle), this is narrow
    defense-in-depth -- but the same principle this file already commits
    to for every other component applies: if pulse_sweep() ever raises
    for any reason, the mouths -- carefully protected elsewhere -- must
    still run."""

    def test_a_crashing_pulse_sweep_still_lets_mouths_run(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            (tmp / "foundation").mkdir()

            def observe_fn(_state_path, now=None):
                return observe("ONLY", tmp / "only_state.json",
                               lambda: b"v1", lambda raw: ({"key": "a", "title": "1.0.0"},))

            with mock.patch.object(cron_pulse, "pulse_sweep", side_effect=RuntimeError("boom")), \
                 mock.patch.object(cron_pulse, "MOUTHS", (("ONLY", observe_fn, tmp / "s.json", None),)), \
                 mock.patch.object(cron_pulse, "LOG_PATH", tmp / "foundation" / "pulse_log.jsonl"), \
                 mock.patch.object(cron_pulse, "REPO_ROOT", tmp):
                result = cron_pulse.main()

            self.assertEqual(result, 0)
            self.assertFalse((tmp / "foundation" / "pulse_log.jsonl").exists(),
                             "no pulse record should exist when the sweep itself failed")
            self.assertTrue((tmp / "foundation" / "mouth_ONLY_log.jsonl").exists(),
                            "the mouth never ran because pulse_sweep()'s crash was uncaught")
