import json
import tempfile
import unittest
from pathlib import Path

from foundation import opportunity_cycle
from foundation.outcome_ledger import OutcomeLedger


def _release(ocid="ocds-test-0001", tag=("tender",), status="active",
             title="Supply of Widgets", description="A perfectly ordinary notice.",
             buyer_name="Example Council", amount=50000, currency="GBP",
             deadline="2026-12-01T00:00:00Z", published="2026-09-01T00:00:00Z"):
    return {
        "ocid": ocid,
        "tag": list(tag),
        "date": published,
        "buyer": {"name": buyer_name},
        "tender": {
            "id": ocid,
            "title": title,
            "description": description,
            "status": status,
            "value": {"amount": amount, "currency": currency},
            "tenderPeriod": {"endDate": deadline},
        },
    }


def _feed(*releases):
    return json.dumps({"releases": list(releases)}).encode()


def _make_ledger():
    return OutcomeLedger(ledger_path=Path(tempfile.mkdtemp()) / "ledger.jsonl")


class RunCycleTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.state_dir = Path(self._tmp.name) / "state"

    def tearDown(self):
        self._tmp.cleanup()

    def test_full_chain_runs_end_to_end_and_both_modules_are_invoked(self):
        """A real tender notice must survive: fetch -> parse -> signal
        (tender_radar) -> collapse-by-controlling-party -> ledger record
        (opportunity_pipeline). Assert on evidence only the pipeline half
        of the chain could have produced (a real ledger record keyed by
        an opportunity_id derived from the tender's own buyer), proving
        this is not a shim that just imports both modules."""
        ledger = _make_ledger()
        report = opportunity_cycle.run_cycle(
            self.state_dir, ledger, fetch_fn=lambda: _feed(_release()))

        self.assertEqual(report.sweep_status, "FIRST_SEEN")
        self.assertEqual(report.signal_count, 1)
        self.assertEqual(report.controlling_party_count, 1)
        self.assertEqual(report.controlling_parties, ("example council",))
        self.assertEqual(report.ledger_records_written, 1)
        self.assertEqual(report.qualified, 0)
        self.assertEqual(report.contracts, 0)
        self.assertEqual(report.cash, 0)

        # Proof the pipeline genuinely ran, not just the radar: a real
        # record landed in the ledger the caller supplied, with a note
        # naming the collapsed controlling party.
        records = ledger.all_records()
        self.assertEqual(len(records), 1)
        self.assertIn("example council", records[0].note)
        self.assertEqual(records[0].state, "PENDING")

    def test_three_signals_one_controlling_party_collapse_to_one_opportunity(self):
        ledger = _make_ledger()
        releases = [
            _release(ocid=f"ocds-{i}", buyer_name="Shared Buyer Ltd")
            for i in range(3)
        ]
        report = opportunity_cycle.run_cycle(
            self.state_dir, ledger, fetch_fn=lambda: _feed(*releases))

        self.assertEqual(report.signal_count, 3)
        self.assertEqual(report.controlling_party_count, 1)
        self.assertEqual(report.controlling_parties, ("shared buyer ltd",))
        self.assertEqual(report.ledger_records_written, 1)
        self.assertEqual(len(ledger.all_records()), 1)

    def test_rerunning_the_same_cycle_does_not_double_count_in_the_ledger(self):
        ledger = _make_ledger()
        fetch = lambda: _feed(_release())

        first = opportunity_cycle.run_cycle(self.state_dir, ledger, fetch_fn=fetch)
        self.assertEqual(first.ledger_records_written, 1)
        self.assertEqual(len(ledger.all_records()), 1)

        # Re-running against the same state directory: tender_radar's own
        # dedupe means the second sweep sees no NEW items at all (status
        # UNCHANGED), so the pipeline never even receives a repeat signal.
        second = opportunity_cycle.run_cycle(self.state_dir, ledger, fetch_fn=fetch)
        self.assertEqual(second.sweep_status, "UNCHANGED")
        self.assertEqual(second.signal_count, 0)
        self.assertEqual(second.ledger_records_written, 0)
        self.assertEqual(len(ledger.all_records()), 1)

    def test_failing_source_produces_structured_report_not_a_crash(self):
        ledger = _make_ledger()
        try:
            report = opportunity_cycle.run_cycle(
                self.state_dir, ledger, fetch_fn=lambda: b"not json at all {{{")
        except Exception as exc:  # pragma: no cover - failure path itself
            self.fail(f"run_cycle raised {exc!r} instead of a structured report")

        self.assertEqual(report.sweep_status, "UNAVAILABLE")
        self.assertIsNotNone(report.sweep_error)
        self.assertEqual(report.signal_count, 0)
        self.assertEqual(report.ledger_records_written, 0)
        self.assertEqual(report.qualified, 0)
        self.assertEqual(report.contracts, 0)
        self.assertEqual(report.cash, 0)
        self.assertEqual(len(ledger.all_records()), 0)
        self.assertIn("sweep error", report.show_the_math())

    def test_zero_signals_is_a_valid_outcome(self):
        ledger = _make_ledger()
        report = opportunity_cycle.run_cycle(
            self.state_dir, ledger, fetch_fn=lambda: _feed())

        self.assertEqual(report.signal_count, 0)
        self.assertEqual(report.controlling_party_count, 0)
        self.assertEqual(report.ledger_records_written, 0)
        self.assertEqual(len(ledger.all_records()), 0)
        self.assertIn("zero signals", report.show_the_math())

    def test_cold_start_with_a_non_existent_state_directory_works(self):
        ledger = _make_ledger()
        missing = Path(self._tmp.name) / "never" / "existed"
        self.assertFalse(missing.exists())

        report = opportunity_cycle.run_cycle(
            missing, ledger, fetch_fn=lambda: _feed(_release()))

        self.assertTrue(missing.is_dir())
        self.assertEqual(report.signal_count, 1)
        self.assertEqual(report.ledger_records_written, 1)


if __name__ == "__main__":
    unittest.main()
