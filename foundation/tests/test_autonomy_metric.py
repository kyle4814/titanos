"""Tests for foundation/autonomy_metric.py.

Covers the honest-current-state case (ratio 0.0, one READ_ONLY scheduled
entry, real crontab), a synthetic repo where a MUTATING entry is wired
up (ratio must move off zero), crontab-unavailable handling, and the
structural constraints the module promises never to violate: it must
name what it does not mean, it must surface HONEST_LIMITS, and it must
never write to disk.
"""
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from foundation.autonomy_metric import (
    HONEST_LIMITS,
    measure_autonomy,
    show_the_math,
)


class TestRealRepoStateToday(unittest.TestCase):
    """The actual, current state of this repository. This is the case
    the whole module exists to report honestly."""

    def test_ratio_is_zero_when_no_mutating_entry_is_scheduled(self):
        m = measure_autonomy(Path(__file__).resolve().parent.parent.parent)
        self.assertEqual(m.scheduled_mutating_count, 0)
        self.assertEqual(m.autonomy_ratio, 0.0)

    def test_the_one_real_cron_entry_classifies_read_only(self):
        m = measure_autonomy(Path(__file__).resolve().parent.parent.parent)
        cron_entries = [e for e in m.scheduled_entrypoints
                        if e.script_path and e.script_path.endswith("cron_pulse.py")]
        # crontab may be unavailable in some sandboxes; only assert
        # classification when we actually observed the entry.
        if cron_entries:
            self.assertEqual(cron_entries[0].classification, "READ_ONLY")


class TestSyntheticMutatingSchedule(unittest.TestCase):
    """A fabricated repo where a scheduled entry genuinely commits --
    the ratio must move off zero to prove the module isn't hardwired
    to always report 0.0."""

    def _build_repo(self, tmp: Path) -> Path:
        (tmp / "foundation").mkdir()
        (tmp / "foundation" / "__init__.py").write_text("")
        (tmp / "foundation" / "harmless.py").write_text(
            "def helper():\n    return 1\n"
        )
        # A genuinely mutating entrypoint: opens a non-telemetry file in
        # write mode AND shells out to `git commit`.
        (tmp / "foundation" / "mutator.py").write_text(
            "import subprocess\n"
            "def do_work():\n"
            "    with open('output.txt', 'w') as f:\n"
            "        f.write('hi')\n"
            "    subprocess.run(['git', 'commit', '-am', 'auto'])\n"
            "if __name__ == '__main__':\n"
            "    do_work()\n"
        )
        (tmp / "foundation" / "readonly_thing.py").write_text(
            "def observe():\n"
            "    return 1\n"
            "if __name__ == '__main__':\n"
            "    observe()\n"
        )
        return tmp

    def test_synthetic_mutating_entry_yields_nonzero_ratio(self):
        with tempfile.TemporaryDirectory() as td:
            repo = self._build_repo(Path(td))
            fake_crontab = (
                f"3 * * * * cd {repo} && /usr/bin/python3 "
                f"foundation/mutator.py >> {repo}/out.log 2>&1\n"
            )
            fake_result = subprocess.CompletedProcess(
                args=["crontab", "-l"], returncode=0, stdout=fake_crontab, stderr=""
            )
            with mock.patch("subprocess.run", return_value=fake_result):
                m = measure_autonomy(repo)

        self.assertEqual(len(m.scheduled_entrypoints), 1)
        self.assertEqual(m.scheduled_entrypoints[0].classification, "MUTATING")
        self.assertGreater(m.scheduled_mutating_count, 0)
        self.assertGreater(m.autonomy_ratio, 0.0)

    def test_readonly_synthetic_entry_keeps_ratio_zero(self):
        with tempfile.TemporaryDirectory() as td:
            repo = self._build_repo(Path(td))
            fake_crontab = (
                f"3 * * * * cd {repo} && /usr/bin/python3 "
                f"foundation/readonly_thing.py >> {repo}/out.log 2>&1\n"
            )
            fake_result = subprocess.CompletedProcess(
                args=["crontab", "-l"], returncode=0, stdout=fake_crontab, stderr=""
            )
            with mock.patch("subprocess.run", return_value=fake_result):
                m = measure_autonomy(repo)

        self.assertEqual(m.scheduled_entrypoints[0].classification, "READ_ONLY")
        self.assertEqual(m.autonomy_ratio, 0.0)


class TestCrontabUnavailable(unittest.TestCase):
    def test_missing_crontab_binary_does_not_crash(self):
        with mock.patch("subprocess.run", side_effect=FileNotFoundError()):
            m = measure_autonomy(Path(__file__).resolve().parent.parent.parent)
        self.assertFalse(m.crontab_available)
        self.assertEqual(m.scheduled_entrypoints, ())
        self.assertTrue(any("crontab" in n for n in m.notes))

    def test_no_crontab_for_user_nonzero_exit_does_not_crash(self):
        no_crontab = subprocess.CompletedProcess(
            args=["crontab", "-l"], returncode=1, stdout="", stderr="no crontab for tech2\n"
        )
        with mock.patch("subprocess.run", return_value=no_crontab):
            m = measure_autonomy(Path(__file__).resolve().parent.parent.parent)
        self.assertFalse(m.crontab_available)
        self.assertEqual(m.scheduled_entrypoints, ())


class TestShowTheMathDisclaimer(unittest.TestCase):
    def test_disclaims_what_the_ratio_does_not_mean(self):
        m = measure_autonomy(Path(__file__).resolve().parent.parent.parent)
        text = show_the_math(m)
        self.assertIn("DOES NOT MEAN", text)
        self.assertIn("WORK", text)
        self.assertIn("unattended", text)

    def test_show_the_math_surfaces_every_honest_limit(self):
        m = measure_autonomy(Path(__file__).resolve().parent.parent.parent)
        text = show_the_math(m)
        for limit in HONEST_LIMITS:
            self.assertIn(limit, text)


class TestHonestLimits(unittest.TestCase):
    def test_honest_limits_is_non_empty(self):
        self.assertGreater(len(HONEST_LIMITS), 0)

    def test_honest_limits_names_actor_blindness(self):
        joined = " ".join(HONEST_LIMITS).lower()
        self.assertIn("who or what typed", joined)
        self.assertIn("ai-invoked", joined)


class TestWritesNothing(unittest.TestCase):
    def test_measurement_writes_nothing_to_disk(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "foundation").mkdir()
            (repo / "foundation" / "__init__.py").write_text("")
            (repo / "HUMAN_DECISIONS.md").write_text("1. an open item\n")

            before = sorted(p.relative_to(repo).as_posix()
                            for p in repo.rglob("*") if p.is_file())
            with mock.patch("subprocess.run",
                            side_effect=FileNotFoundError()):
                m = measure_autonomy(repo)
                show_the_math(m)
            after = sorted(p.relative_to(repo).as_posix()
                           for p in repo.rglob("*") if p.is_file())
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
