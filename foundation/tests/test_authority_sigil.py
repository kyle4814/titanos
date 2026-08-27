import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from foundation.authority_sigil import (
    AuthoritySigilError, ReleaseLedger, authorize_action, evaluate,
    issue_release, revoke_release,
)

NOW = datetime(2026, 8, 27, 12, 0, 0, tzinfo=timezone.utc)


def _issue(ledger, **overrides):
    kwargs = dict(
        release_id="R1", authority_class="ZERO_SPEND_READ_ONLY",
        allowed_capabilities=frozenset({"RUN_PULSE_SWEEP"}),
        allowed_targets=frozenset({"/repo"}),
        max_actions_per_period=3, period_seconds=3600,
        issued_by="Kyle", duration_seconds=3600, now=NOW,
    )
    kwargs.update(overrides)
    return issue_release(ledger, **kwargs)


class TestIssueReleaseValidation(unittest.TestCase):
    def setUp(self):
        self.ledger = ReleaseLedger(ledger_path=None)

    def test_valid_issue_succeeds(self):
        rc = _issue(self.ledger)
        self.assertEqual(rc.release_id, "R1")
        self.assertEqual(rc.authority_class, "ZERO_SPEND_READ_ONLY")

    def test_unknown_authority_class_rejected(self):
        with self.assertRaises(AuthoritySigilError):
            _issue(self.ledger, authority_class="ANYTHING_GOES")

    def test_empty_capabilities_rejected(self):
        with self.assertRaises(AuthoritySigilError):
            _issue(self.ledger, allowed_capabilities=frozenset())

    def test_empty_targets_rejected(self):
        with self.assertRaises(AuthoritySigilError):
            _issue(self.ledger, allowed_targets=frozenset())

    def test_zero_budget_rejected(self):
        with self.assertRaises(AuthoritySigilError):
            _issue(self.ledger, max_actions_per_period=0)

    def test_zero_period_rejected(self):
        with self.assertRaises(AuthoritySigilError):
            _issue(self.ledger, period_seconds=0)

    def test_missing_issuer_rejected(self):
        with self.assertRaises(AuthoritySigilError):
            _issue(self.ledger, issued_by="   ")

    def test_non_expiring_release_rejected(self):
        with self.assertRaises(AuthoritySigilError):
            _issue(self.ledger, duration_seconds=0)

    def test_duplicate_release_id_rejected(self):
        _issue(self.ledger)
        with self.assertRaises(AuthoritySigilError):
            _issue(self.ledger)


class TestEvaluateFailClosed(unittest.TestCase):
    def setUp(self):
        self.ledger = ReleaseLedger(ledger_path=None)
        _issue(self.ledger)

    def test_unknown_release_denied(self):
        d = evaluate(self.ledger, "NOPE", "RUN_PULSE_SWEEP", "/repo", now=NOW)
        self.assertFalse(d.admitted)

    def test_valid_action_admitted(self):
        d = evaluate(self.ledger, "R1", "RUN_PULSE_SWEEP", "/repo", now=NOW)
        self.assertTrue(d.admitted)

    def test_capability_not_in_scope_denied(self):
        d = evaluate(self.ledger, "R1", "SPEND_MONEY", "/repo", now=NOW)
        self.assertFalse(d.admitted)

    def test_target_not_in_scope_denied(self):
        d = evaluate(self.ledger, "R1", "RUN_PULSE_SWEEP", "/somewhere/else", now=NOW)
        self.assertFalse(d.admitted)

    def test_expired_release_denied(self):
        past_expiry = NOW + timedelta(hours=2)  # release expires 1h after NOW
        d = evaluate(self.ledger, "R1", "RUN_PULSE_SWEEP", "/repo", now=past_expiry)
        self.assertFalse(d.admitted)
        self.assertIn("expired", d.reasons[0])

    def test_exactly_at_expiry_denied(self):
        exactly_expiry = NOW + timedelta(seconds=3600)
        d = evaluate(self.ledger, "R1", "RUN_PULSE_SWEEP", "/repo", now=exactly_expiry)
        self.assertFalse(d.admitted)

    def test_just_before_expiry_admitted(self):
        just_before = NOW + timedelta(seconds=3599)
        d = evaluate(self.ledger, "R1", "RUN_PULSE_SWEEP", "/repo", now=just_before)
        self.assertTrue(d.admitted)


class TestRevocation(unittest.TestCase):
    def test_revoked_release_denied_even_if_unexpired_and_in_scope(self):
        ledger = ReleaseLedger(ledger_path=None)
        _issue(ledger)
        revoke_release(ledger, "R1")
        d = evaluate(ledger, "R1", "RUN_PULSE_SWEEP", "/repo", now=NOW)
        self.assertFalse(d.admitted)
        self.assertIn("revoked", d.reasons[0])

    def test_revoking_unknown_release_is_not_an_error(self):
        ledger = ReleaseLedger(ledger_path=None)
        revoke_release(ledger, "NEVER_ISSUED")  # must not raise

    def test_revocation_is_permanent_within_the_ledger(self):
        ledger = ReleaseLedger(ledger_path=None)
        _issue(ledger)
        revoke_release(ledger, "R1")
        # No un-revoke function exists in this module's public surface.
        import foundation.authority_sigil as mod
        self.assertNotIn("unrevoke_release", mod.__all__)
        self.assertFalse(hasattr(mod, "unrevoke_release"))


class TestNoSelfWideningSurface(unittest.TestCase):
    def test_no_expand_or_renew_or_increase_budget_function_exists(self):
        import foundation.authority_sigil as mod
        forbidden = ("expand_scope", "renew", "increase_budget", "widen", "grant_more")
        for name in forbidden:
            self.assertFalse(hasattr(mod, name), f"{name} must not exist on this module")

    def test_release_code_is_frozen(self):
        ledger = ReleaseLedger(ledger_path=None)
        rc = _issue(ledger)
        with self.assertRaises(Exception):
            rc.max_actions_per_period = 999999  # frozen dataclass -> raises


class TestBudgetEnforcement(unittest.TestCase):
    def test_budget_exhausted_after_max_actions(self):
        ledger = ReleaseLedger(ledger_path=None)
        _issue(ledger, max_actions_per_period=2)
        d1 = authorize_action(ledger, "R1", "RUN_PULSE_SWEEP", "/repo", now=NOW)
        d2 = authorize_action(ledger, "R1", "RUN_PULSE_SWEEP", "/repo", now=NOW)
        d3 = authorize_action(ledger, "R1", "RUN_PULSE_SWEEP", "/repo", now=NOW)
        self.assertTrue(d1.admitted)
        self.assertTrue(d2.admitted)
        self.assertFalse(d3.admitted)
        self.assertIn("budget exhausted", d3.reasons[0])

    def test_denied_attempts_do_not_consume_budget(self):
        ledger = ReleaseLedger(ledger_path=None)
        _issue(ledger, max_actions_per_period=1)
        # denied: wrong target, does not consume budget
        authorize_action(ledger, "R1", "RUN_PULSE_SWEEP", "/wrong", now=NOW)
        d = authorize_action(ledger, "R1", "RUN_PULSE_SWEEP", "/repo", now=NOW)
        self.assertTrue(d.admitted)  # budget still available

    def test_budget_resets_outside_the_trailing_window(self):
        ledger = ReleaseLedger(ledger_path=None)
        _issue(ledger, max_actions_per_period=1, period_seconds=60)
        d1 = authorize_action(ledger, "R1", "RUN_PULSE_SWEEP", "/repo", now=NOW)
        later = NOW + timedelta(seconds=61)
        d2 = authorize_action(ledger, "R1", "RUN_PULSE_SWEEP", "/repo", now=later)
        self.assertTrue(d1.admitted)
        self.assertTrue(d2.admitted)  # trailing window has rolled past d1

    def test_every_attempt_is_recorded_admit_or_deny(self):
        ledger = ReleaseLedger(ledger_path=None)
        _issue(ledger)
        authorize_action(ledger, "R1", "RUN_PULSE_SWEEP", "/wrong", now=NOW)
        authorize_action(ledger, "R1", "RUN_PULSE_SWEEP", "/repo", now=NOW)
        actions = ledger.all_actions()
        self.assertEqual(len(actions), 2)
        self.assertEqual({a.result for a in actions}, {"ADMIT", "DENY"})


class TestPersistenceAcrossRestart(unittest.TestCase):
    def test_ledger_survives_a_fresh_construction_from_disk(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "ledger.jsonl"
            l1 = ReleaseLedger(ledger_path=path)
            _issue(l1, max_actions_per_period=1)
            authorize_action(l1, "R1", "RUN_PULSE_SWEEP", "/repo", now=NOW)

            # Simulate a process restart: fresh object, same file.
            l2 = ReleaseLedger(ledger_path=path)
            self.assertIsNotNone(l2.get_release("R1"))
            # Budget consumption also survived -- second attempt is denied.
            d2 = authorize_action(l2, "R1", "RUN_PULSE_SWEEP", "/repo", now=NOW)
            self.assertFalse(d2.admitted)

    def test_truncated_trailing_line_does_not_crash_replay(self):
        # Real crash simulation: a process killed mid-write can only ever
        # leave the LAST line incomplete -- everything before it is a
        # completed, durable write. Found and fixed 2026-08-28 (was
        # previously an uncaught json.JSONDecodeError on restart, forcing
        # a destructive manual recovery that would have silently reset
        # all budget/revocation state).
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "ledger.jsonl"
            l1 = ReleaseLedger(ledger_path=path)
            _issue(l1)
            with open(path, "a") as f:
                f.write('{"kind": "ACTION", "release_id": "R1", "capability": "RUN_PU')  # truncated, no newline

            l2 = ReleaseLedger(ledger_path=path)  # must not raise
            self.assertIsNotNone(l2.get_release("R1"))
            # The truncated ACTION record must not be counted -- budget
            # reflects only what was actually, durably written.
            self.assertEqual(l2.actions_in_window("R1", datetime(2000, 1, 1, tzinfo=timezone.utc)), 0)

    def test_malformed_json_line_in_the_middle_is_skipped_not_fatal(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "ledger.jsonl"
            l1 = ReleaseLedger(ledger_path=path)
            _issue(l1)
            with open(path, "a") as f:
                f.write("not even json at all\n")
                f.write('{"kind": "REVOKE", "release_id": "R1"}\n')

            l2 = ReleaseLedger(ledger_path=path)  # must not raise
            self.assertTrue(l2.is_revoked("R1"))  # the valid line after the bad one still replays

    def test_revocation_survives_a_fresh_construction_from_disk(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "ledger.jsonl"
            l1 = ReleaseLedger(ledger_path=path)
            _issue(l1)
            revoke_release(l1, "R1")

            l2 = ReleaseLedger(ledger_path=path)
            self.assertTrue(l2.is_revoked("R1"))
            self.assertFalse(evaluate(l2, "R1", "RUN_PULSE_SWEEP", "/repo", now=NOW).admitted)


if __name__ == "__main__":
    unittest.main()
