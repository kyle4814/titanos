import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from foundation import swarm_contract
from foundation.discovery_authorization import DiscoveryBudgetExhausted
from foundation.relevance import CapabilityProfile
from foundation.swarm_contract import (
    AUTHORITY_HOLD,
    BUDGET_EXHAUSTED,
    DRY_RUN_OK,
    INTERNAL_ERROR,
    LIVE_OK,
    SHORTLIST_NOT_REQUESTED,
    SHORTLIST_PRODUCED,
    SHORTLIST_SKIPPED_DRY_RUN,
    VALIDATION_REFUSED,
    WATCH_NOT_REQUESTED,
    WATCH_PRODUCED,
    WATCH_SKIPPED_DRY_RUN,
    SwarmTaskDescriptor,
    run_swarm_task,
)


def _release(ocid="ocds-test-0001", end_date="2026-12-01T00:00:00Z"):
    tender_period = {"endDate": end_date} if end_date is not None else {}
    return {
        "ocid": ocid,
        "tag": ["tender"],
        "date": "2026-09-01T00:00:00Z",
        "buyer": {"name": "Example Council"},
        "tender": {
            "id": ocid,
            "title": "Supply of Widgets",
            "description": "A perfectly ordinary notice.",
            "status": "active",
            "value": {"amount": 50000, "currency": "GBP"},
            "tenderPeriod": tender_period,
        },
    }


def _feed(*releases):
    return json.dumps({"releases": list(releases)}).encode()


class BaseTmpTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.state_dir = self.root / "state"
        self.ledger_path = self.root / "ledger.jsonl"
        self.watch_state_path = self.root / "watch_seen.json"

    def descriptor(self, **overrides):
        fields = dict(
            objective="observe open tenders for widget supply contracts",
            state_dir=self.state_dir,
            ledger_path=self.ledger_path,
        )
        fields.update(overrides)
        return SwarmTaskDescriptor(**fields)


class MalformedDescriptorTests(BaseTmpTest):
    def test_empty_objective_refused_with_named_reason(self):
        result = run_swarm_task(self.descriptor(objective="   "))
        self.assertEqual(result.status, VALIDATION_REFUSED)
        self.assertEqual(result.refused_by, "OBJECTIVE_REQUIRED")
        self.assertTrue(result.reason)

    def test_missing_state_dir_refused(self):
        result = run_swarm_task(self.descriptor(state_dir=""))
        self.assertEqual(result.status, VALIDATION_REFUSED)
        self.assertEqual(result.refused_by, "STATE_DIR_REQUIRED")

    def test_missing_ledger_path_refused(self):
        result = run_swarm_task(self.descriptor(ledger_path=""))
        self.assertEqual(result.status, VALIDATION_REFUSED)
        self.assertEqual(result.refused_by, "LEDGER_PATH_REQUIRED")

    def test_colliding_paths_refused(self):
        result = run_swarm_task(
            self.descriptor(ledger_path=self.state_dir))
        self.assertEqual(result.status, VALIDATION_REFUSED)
        self.assertEqual(result.refused_by, "STATE_DIR_EQUALS_LEDGER_PATH")

    def test_budget_ceiling_exceeded_refused(self):
        result = run_swarm_task(self.descriptor(max_queries=99999))
        self.assertEqual(result.status, VALIDATION_REFUSED)
        self.assertEqual(result.refused_by, "MAX_QUERIES_EXCEEDS_CEILING")

    def test_nonpositive_budget_refused(self):
        result = run_swarm_task(self.descriptor(max_results=0))
        self.assertEqual(result.status, VALIDATION_REFUSED)
        self.assertEqual(result.refused_by, "BUDGET_MUST_BE_POSITIVE")

    def test_unbounded_objective_refused(self):
        result = run_swarm_task(
            self.descriptor(objective="find anything interesting"))
        self.assertEqual(result.status, VALIDATION_REFUSED)
        self.assertIn(result.refused_by,
                       ("OBJECTIVE_UNBOUNDED", "OBJECTIVE_REQUIRED"))

    def test_refusal_never_a_bare_exception_type(self):
        # A completely wrong-typed field must still come back as a
        # structured result, not propagate.
        result = run_swarm_task(self.descriptor(max_queries="not-a-number"))
        self.assertIn(result.status, (VALIDATION_REFUSED, INTERNAL_ERROR))
        self.assertTrue(result.refused_by)


class DryRunTests(BaseTmpTest):
    def test_dry_run_is_default(self):
        descriptor = self.descriptor()
        self.assertFalse(descriptor.live)

    def test_dry_run_performs_no_writes(self):
        result = run_swarm_task(self.descriptor())
        self.assertEqual(result.status, DRY_RUN_OK)
        self.assertFalse(self.state_dir.exists())
        self.assertFalse(self.ledger_path.exists())

    def test_dry_run_counts_stay_zero(self):
        result = run_swarm_task(self.descriptor())
        self.assertEqual(result.signal_count, 0)
        self.assertEqual(result.ledger_records_written, 0)
        self.assertEqual(result.qualified, 0)
        self.assertEqual(result.contracts, 0)
        self.assertEqual(result.cash, 0)


class LiveModeGateTests(BaseTmpTest):
    def test_live_without_authorized_by_is_authority_hold(self):
        result = run_swarm_task(self.descriptor(live=True))
        self.assertEqual(result.status, AUTHORITY_HOLD)
        self.assertEqual(result.refused_by, "LIVE_REQUIRES_AUTHORIZED_BY")
        self.assertIn("LIVE_EXECUTION_AUTHORIZATION", result.requires_human)
        # And, crucially, nothing was written -- the gate fired before
        # any action, exactly like the dry-run path.
        self.assertFalse(self.state_dir.exists())
        self.assertFalse(self.ledger_path.exists())

    def test_live_with_authorized_by_and_stub_fetch_actually_runs(self):
        result = run_swarm_task(
            self.descriptor(live=True, authorized_by="Kyle Graham"),
            _fetch_fn_for_tests=lambda: _feed(_release()),
        )
        self.assertEqual(result.status, LIVE_OK)
        self.assertEqual(result.signal_count, 1)
        self.assertTrue(self.state_dir.exists())
        self.assertTrue(self.ledger_path.exists())
        self.assertEqual(result.qualified, 0)
        self.assertEqual(result.contracts, 0)
        self.assertEqual(result.cash, 0)

    def test_live_empty_feed_is_honest_zero_not_error(self):
        result = run_swarm_task(
            self.descriptor(live=True, authorized_by="Kyle Graham"),
            _fetch_fn_for_tests=lambda: _feed(),
        )
        self.assertEqual(result.status, LIVE_OK)
        self.assertEqual(result.signal_count, 0)


class BudgetExhaustionTests(BaseTmpTest):
    def _exhausted_fetch(self):
        def _raise():
            raise DiscoveryBudgetExhausted(
                "discovery budget exhausted for objective "
                "(simulated for offline test)")
        return _raise

    def test_budget_exhaustion_is_structured_not_a_crash(self):
        result = run_swarm_task(
            self.descriptor(live=True, authorized_by="Kyle Graham"),
            _fetch_fn_for_tests=self._exhausted_fetch(),
        )
        self.assertEqual(result.status, BUDGET_EXHAUSTED)
        self.assertEqual(result.refused_by, "DISCOVERY_BUDGET_EXHAUSTED")
        self.assertTrue(result.reason)


class CashQualifiedContractsInvariantTests(BaseTmpTest):
    def test_cannot_construct_nonzero_result(self):
        with self.assertRaises(AssertionError):
            swarm_contract.SwarmTaskResult(
                status=LIVE_OK, qualified=1, contracts=0, cash=0)
        with self.assertRaises(AssertionError):
            swarm_contract.SwarmTaskResult(
                status=LIVE_OK, qualified=0, contracts=0, cash=1000)

    def test_no_input_can_move_them_off_zero_through_the_entry_point(self):
        # There is no descriptor field that maps to qualified/contracts/
        # cash at all -- attempting to smuggle one through kwargs fails
        # at construction, proving the entry point has no such input.
        with self.assertRaises(TypeError):
            SwarmTaskDescriptor(
                objective="x", state_dir=self.state_dir,
                ledger_path=self.ledger_path, qualified=5)

    def test_live_run_result_always_zero_regardless_of_feed_size(self):
        releases = tuple(_release(ocid=f"ocds-{i}") for i in range(5))
        result = run_swarm_task(
            self.descriptor(live=True, authorized_by="Kyle Graham"),
            _fetch_fn_for_tests=lambda: _feed(*releases),
        )
        self.assertEqual(result.status, LIVE_OK)
        self.assertGreaterEqual(result.signal_count, 1)
        self.assertEqual(result.qualified, 0)
        self.assertEqual(result.contracts, 0)
        self.assertEqual(result.cash, 0)


class ResultVocabularyTests(BaseTmpTest):
    def test_status_always_named(self):
        result = run_swarm_task(self.descriptor())
        self.assertIn(result.status, swarm_contract.STATUSES)

    def test_show_the_math_does_not_raise(self):
        result = run_swarm_task(self.descriptor())
        self.assertIsInstance(result.show_the_math(), str)


def _widget_profile():
    return CapabilityProfile(
        name="widget supply",
        declared_by="test",
        keywords=frozenset({"widget", "widgets"}),
    )


class ShortlistTests(BaseTmpTest):
    def test_dry_run_with_profile_still_writes_nothing(self):
        result = run_swarm_task(
            self.descriptor(shortlist_profile=_widget_profile()))
        self.assertEqual(result.status, DRY_RUN_OK)
        self.assertEqual(result.shortlist_status, SHORTLIST_SKIPPED_DRY_RUN)
        self.assertEqual(result.shortlist_digest, "")
        self.assertFalse(self.state_dir.exists())
        self.assertFalse(self.ledger_path.exists())

    def test_live_without_profile_reports_no_shortlist_explicitly(self):
        result = run_swarm_task(
            self.descriptor(live=True, authorized_by="Kyle Graham"),
            _fetch_fn_for_tests=lambda: _feed(_release()),
        )
        self.assertEqual(result.status, LIVE_OK)
        self.assertEqual(result.shortlist_status, SHORTLIST_NOT_REQUESTED)
        self.assertEqual(result.shortlist_digest, "")
        self.assertEqual(result.shortlist_entry_count, 0)

    def test_live_with_profile_produces_digest_in_result(self):
        result = run_swarm_task(
            self.descriptor(
                live=True, authorized_by="Kyle Graham",
                shortlist_profile=_widget_profile(), shortlist_limit=5),
            _fetch_fn_for_tests=lambda: _feed(_release()),
        )
        self.assertEqual(result.status, LIVE_OK)
        self.assertEqual(result.shortlist_status, SHORTLIST_PRODUCED)
        self.assertIsInstance(result.shortlist_digest, str)
        self.assertIn("OBSERVED PROCUREMENT SIGNALS", result.shortlist_digest)
        self.assertGreaterEqual(result.shortlist_entry_count, 1)
        # qualified/contracts/cash still cannot be nonzero even when a
        # shortlist is produced.
        self.assertEqual(result.qualified, 0)
        self.assertEqual(result.contracts, 0)
        self.assertEqual(result.cash, 0)

    def test_live_with_profile_empty_feed_produces_honest_empty_digest(self):
        result = run_swarm_task(
            self.descriptor(
                live=True, authorized_by="Kyle Graham",
                shortlist_profile=_widget_profile()),
            _fetch_fn_for_tests=lambda: _feed(),
        )
        self.assertEqual(result.status, LIVE_OK)
        self.assertEqual(result.shortlist_status, SHORTLIST_PRODUCED)
        self.assertEqual(result.shortlist_entry_count, 0)
        self.assertIn("No signals in this shortlist", result.shortlist_digest)

    def test_negative_shortlist_limit_refused(self):
        result = run_swarm_task(
            self.descriptor(
                shortlist_profile=_widget_profile(), shortlist_limit=-1))
        self.assertEqual(result.status, VALIDATION_REFUSED)
        self.assertEqual(
            result.refused_by, "SHORTLIST_LIMIT_MUST_BE_NON_NEGATIVE")

    def test_shortlist_status_always_named(self):
        result = run_swarm_task(self.descriptor())
        self.assertIn(result.shortlist_status, swarm_contract.SHORTLIST_STATUSES)


_FIXED_NOW = datetime(2026, 9, 2, tzinfo=timezone.utc)


class WatchTests(BaseTmpTest):
    def test_dry_run_with_watch_writes_nothing_and_reports_skipped(self):
        result = run_swarm_task(
            self.descriptor(watch_state_path=self.watch_state_path))
        self.assertEqual(result.status, DRY_RUN_OK)
        self.assertEqual(result.watch_status, WATCH_SKIPPED_DRY_RUN)
        self.assertEqual(result.watch_new_count, 0)
        self.assertEqual(result.watch_report_text, "")
        self.assertFalse(self.state_dir.exists())
        self.assertFalse(self.ledger_path.exists())
        self.assertFalse(self.watch_state_path.exists())

    def test_watch_disabled_behavior_unchanged(self):
        result = run_swarm_task(
            self.descriptor(live=True, authorized_by="Kyle Graham"),
            _fetch_fn_for_tests=lambda: _feed(_release()),
        )
        self.assertEqual(result.status, LIVE_OK)
        self.assertEqual(result.watch_status, WATCH_NOT_REQUESTED)
        self.assertEqual(result.watch_new_count, 0)
        self.assertEqual(result.watch_closing_count, 0)
        self.assertEqual(result.watch_new_and_closing_count, 0)
        self.assertEqual(result.watch_expired_count, 0)
        self.assertEqual(result.watch_unknown_deadline_count, 0)
        self.assertEqual(result.watch_report_text, "")

    def test_first_live_run_reports_everything_new(self):
        releases = tuple(_release(ocid=f"ocds-{i}") for i in range(3))
        result = run_swarm_task(
            self.descriptor(
                live=True, authorized_by="Kyle Graham",
                watch_state_path=self.watch_state_path, now=_FIXED_NOW),
            _fetch_fn_for_tests=lambda: _feed(*releases),
        )
        self.assertEqual(result.status, LIVE_OK)
        self.assertEqual(result.watch_status, WATCH_PRODUCED)
        self.assertEqual(result.watch_new_count, result.signal_count)
        self.assertGreaterEqual(result.watch_new_count, 1)
        self.assertTrue(self.watch_state_path.exists())
        self.assertIn("NEW SINCE LAST RUN", result.watch_report_text)

    def test_second_identical_live_run_reports_nothing_new(self):
        releases = tuple(_release(ocid=f"ocds-{i}") for i in range(3))
        descriptor = self.descriptor(
            live=True, authorized_by="Kyle Graham",
            watch_state_path=self.watch_state_path, now=_FIXED_NOW)
        first = run_swarm_task(
            descriptor, _fetch_fn_for_tests=lambda: _feed(*releases))
        self.assertEqual(first.watch_status, WATCH_PRODUCED)
        self.assertGreaterEqual(first.watch_new_count, 1)

        # A second live run against the SAME watch_state_path and the
        # SAME underlying notices -- state_dir/ledger_path collision
        # with a prior run's dedup cursor would itself already be an
        # oddity, so use a fresh state_dir/ledger for the second sweep,
        # isolating the one thing under test: the watch seen-set.
        second_descriptor = self.descriptor(
            live=True, authorized_by="Kyle Graham",
            state_dir=self.root / "state2",
            ledger_path=self.root / "ledger2.jsonl",
            watch_state_path=self.watch_state_path, now=_FIXED_NOW)
        second = run_swarm_task(
            second_descriptor,
            _fetch_fn_for_tests=lambda: _feed(*releases))
        self.assertEqual(second.status, LIVE_OK)
        self.assertEqual(second.watch_status, WATCH_PRODUCED)
        self.assertEqual(second.watch_new_count, 0)
        self.assertIn("NEW SINCE LAST RUN (0)", second.watch_report_text)

    def test_crash_mid_run_does_not_mark_unseen_signals_as_seen(self):
        releases = tuple(_release(ocid=f"ocds-{i}") for i in range(2))

        def _raise():
            raise DiscoveryBudgetExhausted(
                "discovery budget exhausted (simulated for offline test)")

        crashed = run_swarm_task(
            self.descriptor(
                live=True, authorized_by="Kyle Graham",
                watch_state_path=self.watch_state_path, now=_FIXED_NOW),
            _fetch_fn_for_tests=_raise,
        )
        self.assertEqual(crashed.status, BUDGET_EXHAUSTED)
        # The crash happened before watch_report() was ever reached --
        # the seen-set file must not exist at all.
        self.assertFalse(self.watch_state_path.exists())

        recovered = run_swarm_task(
            self.descriptor(
                live=True, authorized_by="Kyle Graham",
                watch_state_path=self.watch_state_path, now=_FIXED_NOW),
            _fetch_fn_for_tests=lambda: _feed(*releases),
        )
        self.assertEqual(recovered.status, LIVE_OK)
        self.assertEqual(recovered.watch_status, WATCH_PRODUCED)
        # Nothing from the crashed attempt was marked seen -- every
        # signal in this first REAL run is still reported new.
        self.assertEqual(recovered.watch_new_count, recovered.signal_count)
        self.assertGreaterEqual(recovered.watch_new_count, 1)

    def test_expired_and_unknown_deadline_counts_reported_distinctly(self):
        releases = (
            _release(ocid="ocds-future", end_date="2026-12-01T00:00:00Z"),
            _release(ocid="ocds-past", end_date="2026-01-01T00:00:00Z"),
            _release(ocid="ocds-unknown", end_date=None),
        )
        result = run_swarm_task(
            self.descriptor(
                live=True, authorized_by="Kyle Graham",
                watch_state_path=self.watch_state_path, now=_FIXED_NOW),
            _fetch_fn_for_tests=lambda: _feed(*releases),
        )
        self.assertEqual(result.status, LIVE_OK)
        self.assertEqual(result.watch_status, WATCH_PRODUCED)
        self.assertEqual(result.watch_expired_count, 1)
        self.assertEqual(result.watch_unknown_deadline_count, 1)
        self.assertIn("EXPIRED, STILL IN CORPUS (1)", result.watch_report_text)
        self.assertIn("UNKNOWN DEADLINE (1)", result.watch_report_text)

    def test_watch_state_path_colliding_with_state_dir_refused(self):
        result = run_swarm_task(
            self.descriptor(watch_state_path=self.state_dir))
        self.assertEqual(result.status, VALIDATION_REFUSED)
        self.assertEqual(result.refused_by, "WATCH_STATE_PATH_COLLIDES")

    def test_negative_closing_window_refused(self):
        result = run_swarm_task(
            self.descriptor(
                watch_state_path=self.watch_state_path,
                watch_closing_within_days=-1))
        self.assertEqual(result.status, VALIDATION_REFUSED)
        self.assertEqual(
            result.refused_by, "WATCH_CLOSING_WINDOW_MUST_BE_NON_NEGATIVE")

    def test_watch_status_always_named(self):
        result = run_swarm_task(self.descriptor())
        self.assertIn(result.watch_status, swarm_contract.WATCH_STATUSES)


if __name__ == "__main__":
    unittest.main()
