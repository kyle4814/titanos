import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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
        # entry point) -- since no release named RELEASE_ID exists there
        # (proven above), this must DENY and still return 0.
        result = ap.main()
        self.assertEqual(result, 0)


class TestAuthorityPulseAsRealScript(unittest.TestCase):
    """Invoke the actual file as a subprocess -- the real thing a cron
    entry would run, not just the imported function."""

    def test_script_runs_as_a_real_process_and_exits_zero(self):
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


if __name__ == "__main__":
    unittest.main()
