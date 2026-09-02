"""Tests for `foundation/scheduled_brief.py`. Offline only -- every test
here uses `fetch_notices_fn` to inject notices; nothing opens a socket."""

import inspect
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from foundation import scheduled_brief
from foundation.qualification import OperatorProfile
from foundation.relevance import CapabilityProfile
from foundation.scheduled_brief import (
    BRIEF_FILENAME_RE,
    DEFAULT_RETAIN_COUNT,
    LockHeld,
    ScheduledBriefIntegrityError,
    acquire_lock,
    brief_filename,
    enforce_retention,
    release_lock,
    run_scheduled_brief_cycle,
    write_brief_file,
)


SOLO = OperatorProfile(
    name="solo operator (AU)",
    staff_count=1,
    certifications=frozenset(),
    insurance_cover_eur=None,
    corporate_references=(),
    languages=frozenset({"ENG"}),
)

CAP = CapabilityProfile(
    name="pentest", declared_by="operator",
    keywords=frozenset({"security"}),
)

NOW = datetime(2026, 9, 2, 12, 0, 0, tzinfo=timezone.utc)


def notice(pn, deadline="", title="Security assessment services"):
    raw = {
        "publication-number": pn,
        "notice-title": {"eng": [title]},
    }
    if deadline:
        raw["deadline-receipt-request"] = deadline
    return raw


class TempRepo:
    def __enter__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        return self.root

    def __exit__(self, *exc):
        self._tmp.cleanup()


class TestBriefFilename(unittest.TestCase):
    def test_matches_own_pattern(self):
        name = brief_filename(NOW)
        self.assertRegex(name, BRIEF_FILENAME_RE.pattern)

    def test_naive_datetime_treated_as_utc(self):
        naive = datetime(2026, 9, 2, 12, 0, 0)
        self.assertEqual(brief_filename(naive), brief_filename(NOW))


class TestOneCycleWritesABrief(unittest.TestCase):
    def test_empty_result_still_writes_a_brief(self):
        with TempRepo() as root:
            result = run_scheduled_brief_cycle(
                root, operator=SOLO, capability=CAP, now=NOW,
                fetch_notices_fn=lambda: [])
            self.assertEqual(result.action, "WROTE_RAN_CLEAN")
            self.assertIsNotNone(result.brief_path)
            brief_path = Path(result.brief_path)
            self.assertTrue(brief_path.exists())
            text = brief_path.read_text(encoding="utf-8")
            self.assertIn("RAN_CLEAN", text)

    def test_latest_md_mirrors_the_dated_file(self):
        with TempRepo() as root:
            result = run_scheduled_brief_cycle(
                root, operator=SOLO, capability=CAP, now=NOW,
                fetch_notices_fn=lambda: [notice("1-2026")])
            dated_text = Path(result.brief_path).read_text(encoding="utf-8")
            latest = root / "briefs" / "LATEST.md"
            self.assertTrue(latest.exists())
            self.assertEqual(latest.read_text(encoding="utf-8"), dated_text)

    def test_receipt_written_for_every_run_including_no_op(self):
        with TempRepo() as root:
            run_scheduled_brief_cycle(
                root, operator=SOLO, capability=CAP, now=NOW,
                fetch_notices_fn=lambda: [])
            log = root / "foundation" / scheduled_brief.RECEIPT_LOG_NAME
            self.assertTrue(log.exists())
            lines = log.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)
            self.assertIn("RAN_CLEAN", lines[0])


class TestDiffedOutput(unittest.TestCase):
    """The daily file leads with what changed -- hunt_loop's own diff,
    reused verbatim via render_hunt_cycle()."""

    def test_second_run_reports_zero_new_when_nothing_changed(self):
        with TempRepo() as root:
            r1 = run_scheduled_brief_cycle(
                root, operator=SOLO, capability=CAP, now=NOW,
                fetch_notices_fn=lambda: [notice("1-2026")])
            r2 = run_scheduled_brief_cycle(
                root, operator=SOLO, capability=CAP,
                now=NOW + timedelta(hours=1),
                fetch_notices_fn=lambda: [notice("1-2026")])
            self.assertEqual(r1.action, "WROTE_RAN_WITH_CHANGES")  # a brand-new notice
            text2 = Path(r2.brief_path).read_text(encoding="utf-8")
            self.assertIn("0 new since last run", text2)

    def test_new_notice_appears_in_new_section(self):
        with TempRepo() as root:
            run_scheduled_brief_cycle(
                root, operator=SOLO, capability=CAP, now=NOW,
                fetch_notices_fn=lambda: [notice("1-2026")])
            r2 = run_scheduled_brief_cycle(
                root, operator=SOLO, capability=CAP,
                now=NOW + timedelta(hours=1),
                fetch_notices_fn=lambda: [notice("1-2026"), notice("2-2026")])
            self.assertEqual(r2.action, "WROTE_RAN_WITH_CHANGES")
            text2 = Path(r2.brief_path).read_text(encoding="utf-8")
            self.assertIn("NEW:", text2)
            self.assertIn("2-2026", text2)


class TestSingleInstanceLock(unittest.TestCase):
    def test_second_overlapping_run_is_skipped_not_crashed(self):
        with TempRepo() as root:
            lock_path = root / scheduled_brief.LOCK_FILENAME
            acquire_lock(lock_path)
            try:
                result = run_scheduled_brief_cycle(
                    root, operator=SOLO, capability=CAP, now=NOW,
                    fetch_notices_fn=lambda: [notice("1-2026")])
                self.assertEqual(result.action, "SKIPPED_LOCKED")
                self.assertIsNone(result.brief_path)
                # no brief written while locked out
                self.assertFalse((root / "briefs").exists())
            finally:
                release_lock(lock_path)

    def test_acquire_lock_raises_lock_held_when_already_present(self):
        with TempRepo() as root:
            lock_path = root / "l.lock"
            acquire_lock(lock_path)
            with self.assertRaises(LockHeld):
                acquire_lock(lock_path)
            release_lock(lock_path)

    def test_lock_released_after_a_clean_run(self):
        with TempRepo() as root:
            lock_path = root / scheduled_brief.LOCK_FILENAME
            run_scheduled_brief_cycle(
                root, operator=SOLO, capability=CAP, now=NOW,
                fetch_notices_fn=lambda: [])
            self.assertFalse(lock_path.exists())


class TestLockReleasedOnFailure(unittest.TestCase):
    """Explicit proof of the safety rule: a crash mid-cycle must not
    leave the lock held, or every future scheduled run goes silent
    forever."""

    def test_lock_released_when_fetch_notices_fn_raises(self):
        with TempRepo() as root:
            lock_path = root / scheduled_brief.LOCK_FILENAME

            def boom():
                raise RuntimeError("simulated network failure")

            result = run_scheduled_brief_cycle(
                root, operator=SOLO, capability=CAP, now=NOW,
                fetch_notices_fn=boom)
            # hunt_loop.run_one_hunt_cycle() catches this internally and
            # returns STOPPED_HUNT_ERROR rather than raising -- still
            # must not leave the lock held.
            self.assertEqual(result.action, "STOPPED_HUNT_ERROR")
            self.assertFalse(lock_path.exists())
            # A stop result still writes no dated brief file since
            # hunt_loop already receipted the failure in its own log --
            # but the scheduled-brief receipt must still exist.
            log = root / "foundation" / scheduled_brief.RECEIPT_LOG_NAME
            self.assertTrue(log.exists())

    def test_lock_released_when_an_unexpected_exception_occurs(self):
        """`retain_count=0` makes `enforce_retention()` raise
        `ScheduledBriefIntegrityError` AFTER the hunt cycle already
        succeeded and the brief was already written -- an unexpected
        failure past hunt_loop's own try/except, inside this module's
        own logic, proving the outer guard here also releases the lock
        rather than only the inner one `hunt_loop` already covers."""
        with TempRepo() as root:
            lock_path = root / scheduled_brief.LOCK_FILENAME
            result = run_scheduled_brief_cycle(
                root, operator=SOLO, capability=CAP,
                now=NOW, fetch_notices_fn=lambda: [notice("1-2026")],
                retain_count=0)
            self.assertEqual(result.action, "FAILED_UNEXPECTED")
            self.assertIn("ScheduledBriefIntegrityError", result.detail)
            self.assertFalse(lock_path.exists())
            self.assertIsNotNone(result.brief_path)
            self.assertTrue(Path(result.brief_path).exists())


class TestKillSwitch(unittest.TestCase):
    def test_hunt_stop_file_stops_the_cycle(self):
        with TempRepo() as root:
            (root / ".hunt_stop").touch()
            result = run_scheduled_brief_cycle(
                root, operator=SOLO, capability=CAP, now=NOW,
                fetch_notices_fn=lambda: [notice("1-2026")])
            self.assertEqual(result.action, "STOPPED_KILL_SWITCH")
            self.assertFalse((root / scheduled_brief.LOCK_FILENAME).exists())


class TestRetention(unittest.TestCase):
    def test_keeps_only_last_n(self):
        with TempRepo() as root:
            briefs_dir = root / "briefs"
            briefs_dir.mkdir()
            base = NOW
            for i in range(5):
                write_brief_file(briefs_dir, base + timedelta(hours=i), f"run {i}")
            deleted = enforce_retention(briefs_dir, 3)
            remaining = sorted(p.name for p in briefs_dir.iterdir()
                                if BRIEF_FILENAME_RE.match(p.name))
            self.assertEqual(len(remaining), 3)
            self.assertEqual(len(deleted), 2)
            # newest three survive
            self.assertNotIn(brief_filename(base), remaining)
            self.assertIn(brief_filename(base + timedelta(hours=4)), remaining)

    def test_never_deletes_files_it_did_not_create(self):
        with TempRepo() as root:
            briefs_dir = root / "briefs"
            briefs_dir.mkdir()
            stray = briefs_dir / "README.md"
            stray.write_text("do not touch", encoding="utf-8")
            latest = briefs_dir / "LATEST.md"
            latest.write_text("latest", encoding="utf-8")
            for i in range(5):
                write_brief_file(briefs_dir, NOW + timedelta(hours=i), f"run {i}")
            enforce_retention(briefs_dir, 1)
            self.assertTrue(stray.exists())
            self.assertTrue(latest.exists())

    def test_retain_count_below_one_refuses(self):
        with TempRepo() as root:
            briefs_dir = root / "briefs"
            briefs_dir.mkdir()
            with self.assertRaises(ScheduledBriefIntegrityError):
                enforce_retention(briefs_dir, 0)

    def test_default_retain_count_is_thirty(self):
        self.assertEqual(DEFAULT_RETAIN_COUNT, 30)

    def test_end_to_end_retention_via_full_cycle(self):
        with TempRepo() as root:
            for i in range(35):
                run_scheduled_brief_cycle(
                    root, operator=SOLO, capability=CAP,
                    now=NOW + timedelta(hours=i),
                    fetch_notices_fn=lambda: [], retain_count=5)
            briefs_dir = root / "briefs"
            dated = [p for p in briefs_dir.iterdir() if BRIEF_FILENAME_RE.match(p.name)]
            self.assertEqual(len(dated), 5)


class TestNoOutwardAction(unittest.TestCase):
    """This module must be structurally incapable of an outbound
    action -- same check `hunt_loop.py` already applies to itself."""

    FORBIDDEN_SUBSTRINGS = (
        "send", "apply", "contact", "email", "submit", "notify",
        "publish", "register", "subscribe", "post", "create_account",
    )

    def test_no_public_callable_names_an_outbound_verb(self):
        for name in scheduled_brief.__all__:
            obj = getattr(scheduled_brief, name)
            if not callable(obj):
                continue
            lowered = name.lower()
            for bad in self.FORBIDDEN_SUBSTRINGS:
                self.assertNotIn(
                    bad, lowered,
                    f"public callable {name!r} contains forbidden verb {bad!r}")

    def test_no_module_level_function_names_an_outbound_verb(self):
        for name, obj in inspect.getmembers(scheduled_brief, inspect.isfunction):
            if obj.__module__ != scheduled_brief.__name__:
                continue
            lowered = name.lower()
            for bad in self.FORBIDDEN_SUBSTRINGS:
                self.assertNotIn(
                    bad, lowered,
                    f"function {name!r} contains forbidden verb {bad!r}")


class TestProfileLoadFailure(unittest.TestCase):
    def test_missing_profile_still_produces_a_brief_and_a_receipt(self):
        """Point `operator_cli`'s real and example profile paths at
        nonexistent files (via monkeypatch, not by editing
        operator_cli.py -- outside this module's file territory) so
        `load_operator_profile()` genuinely raises `ProfileLoadError`,
        and prove the FAILED_PROFILE branch still writes a brief and a
        receipt rather than crashing or going silent."""
        from foundation import operator_cli

        with TempRepo() as root:
            bogus = root / "does_not_exist.json"
            orig_real, orig_example = operator_cli.PROFILE_PATH, operator_cli.PROFILE_EXAMPLE_PATH
            operator_cli.PROFILE_PATH = bogus
            operator_cli.PROFILE_EXAMPLE_PATH = bogus
            try:
                result = run_scheduled_brief_cycle(
                    root, capability=CAP, now=NOW,
                    fetch_notices_fn=lambda: [notice("1-2026")])
            finally:
                operator_cli.PROFILE_PATH = orig_real
                operator_cli.PROFILE_EXAMPLE_PATH = orig_example

            self.assertEqual(result.action, "FAILED_PROFILE")
            self.assertIsNotNone(result.brief_path)
            self.assertTrue(Path(result.brief_path).exists())
            self.assertFalse((root / scheduled_brief.LOCK_FILENAME).exists())
            log = root / "foundation" / scheduled_brief.RECEIPT_LOG_NAME
            self.assertTrue(log.exists())


if __name__ == "__main__":
    unittest.main()


class TestCronBriefShowsTheClassifiedView(unittest.TestCase):
    """The cron path must not show less than the hand-run path.

    `render_hunt_cycle()` is the diff -- correct to lead with -- but it
    is not the classified, deadline-ranked view `operator_cli brief`
    produces. This file is the one the operator actually reads each
    morning, because cron writes it. Leaving the two different meant the
    unattended surface silently omitted the notice class, so a
    MARKET_ENGAGEMENT notice (answerable by anyone, no turnover, no
    insurance, no references) rendered identically to a COMPETITIVE
    tender that would eliminate him on all three.

    Same shape as the loop that was TED-only while `brief` was
    three-source: the surface trusted most, showing the least."""

    def _notice(self, pn="222222-2026", title="Preliminary market engagement notice"):
        return {
            "publication-number": pn,
            "notice-title": {"eng": [title]},
            "buyer-name": {"eng": ["Some Buyer"]},
            "procedure-type": ["open"],
            "submission-language": ["ENG"],
            "selection-criterion-lot": ["slc-suit-reg-prof"],
        }

    def test_the_written_brief_contains_the_classified_section(self):
        with TempRepo() as root:
            run_scheduled_brief_cycle(
                root, operator=SOLO, capability=CAP, now=NOW,
                fetch_notices_fn=lambda: [self._notice()])
            latest = (root / "briefs" / "LATEST.md").read_text(encoding="utf-8")
        self.assertIn("MORNING BRIEF", latest,
                      "cron brief must carry the same view as `brief`")

    def test_the_diff_still_leads(self):
        with TempRepo() as root:
            run_scheduled_brief_cycle(
                root, operator=SOLO, capability=CAP, now=NOW,
                fetch_notices_fn=lambda: [self._notice()])
            latest = (root / "briefs" / "LATEST.md").read_text(encoding="utf-8")
        self.assertLess(latest.index("RAN_"), latest.index("MORNING BRIEF"),
                        "what changed must come before the full view")

    def test_a_stopped_cycle_carries_no_report_and_does_not_crash(self):
        """A STOPPED_* cycle has no HuntReport, so the classified view
        cannot be built. That must degrade quietly rather than raise.

        It also writes no brief at all -- deliberate, and asserted here
        rather than assumed: a kill switch means the operator turned
        this off, which is a different state from a run that found
        nothing. Confusing the two would have this test arguing with
        TestKillSwitch."""
        with TempRepo() as root:
            (root / ".hunt_stop").write_text("stop")
            result = run_scheduled_brief_cycle(
                root, operator=SOLO, capability=CAP, now=NOW,
                fetch_notices_fn=lambda: [self._notice()])
            self.assertEqual(result.action, "STOPPED_KILL_SWITCH")
            self.assertFalse((root / "briefs" / "LATEST.md").exists())
