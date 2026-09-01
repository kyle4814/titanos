import json
import tempfile
import unittest
from pathlib import Path

from foundation import swarm_contract
from foundation.discovery_authorization import DiscoveryBudgetExhausted
from foundation.swarm_contract import (
    AUTHORITY_HOLD,
    BUDGET_EXHAUSTED,
    DRY_RUN_OK,
    INTERNAL_ERROR,
    LIVE_OK,
    VALIDATION_REFUSED,
    SwarmTaskDescriptor,
    run_swarm_task,
)


def _release(ocid="ocds-test-0001"):
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
            "tenderPeriod": {"endDate": "2026-12-01T00:00:00Z"},
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


if __name__ == "__main__":
    unittest.main()
