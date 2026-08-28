import hashlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestAuthorityPulseInertByDefault(unittest.TestCase):
    """The real, default target (RELEASE_ID against the real ledger path)
    has no issued release -- running the script as-is today must be a
    safe, receipted no-op, never an error and never a silent action."""

    def test_default_state_has_no_pulse_authority_release(self):
        from foundation.authority_pulse import LEDGER_PATH, RELEASE_ID
        from foundation.authority_sigil import ReleaseLedger

        ledger = ReleaseLedger(ledger_path=LEDGER_PATH if LEDGER_PATH.exists() else None)
        self.assertIsNone(
            ledger.get_release(RELEASE_ID),
            "a real release must not already exist -- this script is meant "
            "to ship inert until a human separately issues one",
        )

    def test_main_denies_and_exits_zero_when_no_release_exists(self):
        import foundation.authority_pulse as ap
        # main() uses the real LEDGER_PATH by design (it's the cron-shaped
        # entry point) -- since no release named RELEASE_ID exists there,
        # this must DENY and still return 0.
        #
        # Redirected to temp paths, added 2026-08-28: calling main()
        # unredirected appends a real DENY ActionRecord to the real
        # foundation/authority_ledger.jsonl and a real receipt to the real
        # tick log on every test run. The ledger is this repository's
        # append-only record of what authority was ever exercised -- a test
        # must never be able to write into it, because an auditor reading
        # it later cannot tell a test artifact from a real denial. The
        # DENY behaviour is what's under test here, not which file it
        # lands in; the unredirected real-script path is covered
        # separately below, with its own restore.
        with tempfile.TemporaryDirectory() as d, \
             mock.patch.object(ap, "LEDGER_PATH", Path(d) / "ledger.jsonl"), \
             mock.patch.object(ap, "TICK_LOG_PATH", Path(d) / "tick_log.jsonl"):
            result = ap.main()
        self.assertEqual(result, 0)


class TestAuthorityPulseAsRealScript(unittest.TestCase):
    """Invoke the actual file as a subprocess -- the real thing a cron
    entry would run, not just the imported function."""

    def _restore_after(self, path: Path) -> None:
        """Snapshot a real machine-local file and put it back afterwards.

        The subprocess below is deliberately the genuine cron-shaped
        invocation -- its whole value is that nothing is mocked -- so it
        unavoidably writes to the real default ledger and tick log. A
        subprocess cannot be redirected without giving authority_pulse.py
        an env-overridable ledger path, which would be a far worse thing
        to add to an authority component than this restore is. Added
        2026-08-28 after finding real test-written records in both files.
        """
        existed = path.exists()
        before = path.read_bytes() if existed else None

        def restore():
            if existed:
                path.write_bytes(before)
            elif path.exists():
                path.unlink()

        self.addCleanup(restore)

    def test_script_runs_as_a_real_process_and_exits_zero(self):
        from foundation.authority_pulse import LEDGER_PATH, TICK_LOG_PATH
        self._restore_after(LEDGER_PATH)
        self._restore_after(TICK_LOG_PATH)
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "foundation" / "authority_pulse.py")],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("authority_pulse tick:", proc.stdout)
        self.assertIn("admitted=False", proc.stdout)  # no real release exists


class TestAuthorityPulseWithARealIssuedRelease(unittest.TestCase):
    """Prove the bridge actually works end to end when a release does
    exist -- using a temporary ledger path, never the real default one,
    so this test cannot itself activate anything live."""

    def test_tick_admits_and_writes_a_receipt_against_a_real_temp_ledger(self):
        from foundation.authority_runtime import read_tick_log, tick
        from foundation.authority_sigil import ReleaseLedger, issue_release

        with tempfile.TemporaryDirectory() as d:
            ledger_path = Path(d) / "ledger.jsonl"
            tick_log_path = Path(d) / "tick_log.jsonl"
            ledger = ReleaseLedger(ledger_path=ledger_path)
            issue_release(
                ledger, release_id="PULSE_AUTHORITY_001",
                authority_class="ZERO_SPEND_READ_ONLY",
                allowed_capabilities=frozenset({"RUN_PULSE_SWEEP"}),
                allowed_targets=frozenset({str(REPO_ROOT)}),
                max_actions_per_period=1, period_seconds=3600,
                issued_by="test", duration_seconds=3600,
            )
            result = tick(ledger, "PULSE_AUTHORITY_001", str(REPO_ROOT), log_path=tick_log_path)
            self.assertTrue(result.admitted)
            self.assertIsNotNone(result.raw_finding_count)
            self.assertEqual(len(read_tick_log(tick_log_path)), 1)

            # Simulate the cron-restart case: a fresh ledger object
            # reading the same file, a second tick, budget now exhausted.
            fresh_ledger = ReleaseLedger(ledger_path=ledger_path)
            result2 = tick(fresh_ledger, "PULSE_AUTHORITY_001", str(REPO_ROOT), log_path=tick_log_path)
            self.assertFalse(result2.admitted)



class TestTheAuthoritySuiteDoesNotMutateLiveAuthorityState(unittest.TestCase):
    """The switch closed 2026-08-28, and the regression that keeps it closed.

    THE DEFECT, FOUND BY FINGERPRINTING LIVE FILES ACROSS A FULL RUN:
    running the test suite was appending real records to
    `foundation/authority_ledger.jsonl` (24 DENY ActionRecords) and
    `foundation/authority_runtime_tick_log.jsonl` (48 receipts, some
    carrying release_id 'R1' and /tmp/... targets that leaked out of
    temp-dir tests). Three separate call sites did it: authority_pulse's
    main() test, its subprocess test, and two tick() calls in
    test_authority_runtime.py that omitted `log_path` and silently fell
    back to the real default.

    WHY THIS MATTERS MORE THAN ORDINARY TEST HYGIENE: the ledger is the
    append-only record of what authority was ever exercised, and it has
    no delete surface by design. Records written by a test are
    indistinguishable from records written by a real invocation, so the
    audit trail -- the entire point of the ledger -- silently degrades
    every time anyone runs the suite. It also falsified a written claim:
    HUMAN_DECISIONS.md item 13 states the real ledger does not exist.

    Budget was never at risk (`actions_in_window()` counts only ADMIT,
    and every test-written record is DENY), so this corrupted the audit
    trail rather than the enforcement -- bad, but bounded.
    """

    def _fingerprint(self, path: Path):
        if not path.exists():
            return None
        return (path.stat().st_size, hashlib.sha256(path.read_bytes()).hexdigest())

    def test_the_sibling_authority_suites_leave_the_real_files_untouched(self):
        """Runs the two authority test modules that do NOT contain this
        test. Deliberately excludes test_authority_pulse itself: a
        unittest module that shells out to run its own module recurses
        without bound -- the exact failure foundation/recursion_guard.py
        was built for after compute_sigil() hit it for real. The one
        genuinely unredirectable call site in this module (the real-script
        subprocess) is covered by its own snapshot/restore instead."""
        from foundation.authority_pulse import LEDGER_PATH, TICK_LOG_PATH

        before = {p: self._fingerprint(p) for p in (LEDGER_PATH, TICK_LOG_PATH)}

        proc = subprocess.run(
            [sys.executable, "-m", "unittest",
             "foundation.tests.test_authority_sigil",
             "foundation.tests.test_authority_runtime"],
            cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=300,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr[-3000:])

        after = {p: self._fingerprint(p) for p in (LEDGER_PATH, TICK_LOG_PATH)}
        for path in (LEDGER_PATH, TICK_LOG_PATH):
            self.assertEqual(
                before[path], after[path],
                f"{path.name} was mutated by the authority test suite -- a test "
                f"must never write to real machine-local authority state",
            )

    def test_the_real_script_subprocess_restores_what_it_wrote(self):
        """The restore path itself, proven rather than assumed."""
        from foundation.authority_pulse import LEDGER_PATH, TICK_LOG_PATH

        before = {p: self._fingerprint(p) for p in (LEDGER_PATH, TICK_LOG_PATH)}
        suite = unittest.TestLoader().loadTestsFromName(
            "foundation.tests.test_authority_pulse.TestAuthorityPulseAsRealScript"
        )
        # stream=StringIO, deliberately: a TextTestRunner writing to the
        # default stderr emits its own "Ran 1 test" line into the parent
        # process's stderr, and foundation/sigil.py::_dimension_proof()
        # parses exactly that pattern out of a subsystem run's stderr --
        # taking the FIRST match. Unredirected, this test silently made
        # compute_sigil() report 798 total tests instead of ~1500 and
        # broke test_sigil's real-repo assertion. Found by running it.
        result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
        self.assertTrue(result.wasSuccessful())

        after = {p: self._fingerprint(p) for p in (LEDGER_PATH, TICK_LOG_PATH)}
        for path in (LEDGER_PATH, TICK_LOG_PATH):
            self.assertEqual(before[path], after[path], f"{path.name} not restored")

    def test_the_real_ledger_has_never_admitted_anything(self):
        """Independent of the above: whatever is in the real ledger today,
        nothing has ever been ADMITTED against it. This is the claim
        HUMAN_DECISIONS.md item 13 actually depends on -- the primitive
        being inert -- and it is stronger than 'the file does not exist'."""
        from foundation.authority_pulse import LEDGER_PATH
        from foundation.authority_sigil import ReleaseLedger

        if not LEDGER_PATH.exists():
            return  # a fresh clone: nothing to check
        ledger = ReleaseLedger(ledger_path=LEDGER_PATH)
        self.assertEqual(
            [a for a in ledger.all_actions() if a.result == "ADMIT"], [],
            "an ADMIT exists in the real ledger -- authority was actually "
            "exercised here, which no session has ever authorized",
        )
        self.assertEqual(
            ledger.all_releases(), (),
            "a ReleaseCode exists in the real ledger -- see HUMAN_DECISIONS.md "
            "item 13(b), which requires Kyle's explicit answer first",
        )


if __name__ == "__main__":
    unittest.main()
