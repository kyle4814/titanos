import json
import tempfile
import unittest
from pathlib import Path

from foundation import opportunity_cycle
from foundation.mouth_ted import MOUTH_ID as TED_MOUTH_ID
from foundation.outcome_ledger import OutcomeLedger
from foundation.tender_radar import MOUTH_ID as UK_MOUTH_ID


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


def _ted_notice(pub_number="533561-2026", title="Server Maintenance",
                 description="Ongoing server maintenance contract.",
                 buyer_name="Example Council", deadline="2026-12-01T00:00:00Z"):
    return {
        "publication-number": pub_number,
        "notice-title": {"eng": title},
        "description-proc": {"eng": description},
        "buyer-name": {"eng": buyer_name},
        "deadline-receipt-request": [deadline],
    }


def _ted_feed(*notices):
    return json.dumps(
        {"notices": list(notices), "totalNoticeCount": len(notices)}).encode()


def _make_ledger():
    return OutcomeLedger(ledger_path=Path(tempfile.mkdtemp()) / "ledger.jsonl")


class RunCycleTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.state_dir = Path(self._tmp.name) / "state"

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self, ledger=None, **kwargs):
        ledger = ledger or _make_ledger()
        return ledger, opportunity_cycle.run_cycle(self.state_dir, ledger, **kwargs)

    # -- both sources contribute to one merged pipeline run -----------

    def test_both_sources_contribute_to_one_merged_pipeline_run(self):
        ledger, report = self._run(fetch_fns={
            UK_MOUTH_ID: lambda: _feed(_release(buyer_name="UK Buyer Ltd")),
            TED_MOUTH_ID: lambda: _ted_feed(_ted_notice(buyer_name="EU Buyer GmbH")),
        })

        self.assertEqual(report.sweep_status, "OK")
        self.assertIsNone(report.sweep_error)
        self.assertEqual(report.signal_count, 2)
        self.assertEqual(report.controlling_party_count, 2)
        self.assertEqual(
            report.controlling_parties, ("eu buyer gmbh", "uk buyer ltd"))
        self.assertEqual(report.ledger_records_written, 2)
        self.assertEqual(report.qualified, 0)
        self.assertEqual(report.contracts, 0)
        self.assertEqual(report.cash, 0)

        self.assertEqual(len(report.source_results), 2)
        by_id = {r.source_id: r for r in report.source_results}
        self.assertEqual(by_id[UK_MOUTH_ID].signal_count, 1)
        self.assertEqual(by_id[TED_MOUTH_ID].signal_count, 1)
        self.assertIsNone(by_id[UK_MOUTH_ID].error)
        self.assertIsNone(by_id[TED_MOUTH_ID].error)

        # Proof the pipeline genuinely ran on the merged set: two real
        # ledger records, one per distinct controlling party.
        self.assertEqual(len(ledger.all_records()), 2)

    # -- a buyer present in BOTH sources collapses to one opportunity --

    def test_shared_buyer_across_both_sources_collapses_to_one_opportunity(self):
        ledger, report = self._run(fetch_fns={
            UK_MOUTH_ID: lambda: _feed(_release(buyer_name="Shared Buyer Ltd")),
            TED_MOUTH_ID: lambda: _ted_feed(
                _ted_notice(buyer_name="Shared Buyer Ltd")),
        })

        self.assertEqual(report.signal_count, 2)
        self.assertEqual(report.controlling_party_count, 1)
        self.assertEqual(report.controlling_parties, ("shared buyer ltd",))
        self.assertEqual(report.ledger_records_written, 1)
        self.assertEqual(len(ledger.all_records()), 1)
        # The one record's note names both signals having been collapsed
        # together, not just one of them.
        self.assertIn("2 signal(s)", ledger.all_records()[0].note)

    # -- one source failing still returns the other's signals AND ------
    # -- reports the failure explicitly ---------------------------------

    def test_one_source_failing_still_returns_the_others_signals_and_reports_it(self):
        ledger, report = self._run(fetch_fns={
            UK_MOUTH_ID: lambda: _feed(_release(buyer_name="Survivor Ltd")),
            TED_MOUTH_ID: lambda: b"not json at all {{{",
        })

        self.assertEqual(report.sweep_status, "PARTIAL")
        self.assertIsNotNone(report.sweep_error)
        self.assertIn(TED_MOUTH_ID, report.sweep_error)

        # The surviving source's signal must not be silently lost.
        self.assertEqual(report.signal_count, 1)
        self.assertEqual(report.controlling_parties, ("survivor ltd",))
        self.assertEqual(report.ledger_records_written, 1)
        self.assertEqual(len(ledger.all_records()), 1)

        by_id = {r.source_id: r for r in report.source_results}
        self.assertEqual(by_id[UK_MOUTH_ID].status, "FIRST_SEEN")
        self.assertEqual(by_id[UK_MOUTH_ID].signal_count, 1)
        self.assertIsNone(by_id[UK_MOUTH_ID].error)
        self.assertEqual(by_id[TED_MOUTH_ID].status, "UNAVAILABLE")
        self.assertEqual(by_id[TED_MOUTH_ID].signal_count, 0)
        self.assertIsNotNone(by_id[TED_MOUTH_ID].error)

        # A partial cycle must be visibly distinguishable from a clean
        # one in the printed report, not just in structured fields.
        math = report.show_the_math()
        self.assertIn("PARTIAL", math)
        self.assertIn(TED_MOUTH_ID, math)

    # -- both failing is a structured report, not a crash --------------

    def test_both_sources_failing_is_a_structured_report_not_a_crash(self):
        ledger, report = self._run(fetch_fns={
            UK_MOUTH_ID: lambda: b"not json at all {{{",
            TED_MOUTH_ID: lambda: b"also not json {{{",
        })

        self.assertEqual(report.sweep_status, "ALL_SOURCES_FAILED")
        self.assertIsNotNone(report.sweep_error)
        self.assertEqual(report.signal_count, 0)
        self.assertEqual(report.ledger_records_written, 0)
        self.assertEqual(report.qualified, 0)
        self.assertEqual(report.contracts, 0)
        self.assertEqual(report.cash, 0)
        self.assertEqual(len(ledger.all_records()), 0)
        for r in report.source_results:
            self.assertEqual(r.status, "UNAVAILABLE")
            self.assertIsNotNone(r.error)

    # -- zero signals is a valid outcome --------------------------------

    def test_zero_signals_from_both_sources_is_a_valid_outcome(self):
        ledger, report = self._run(fetch_fns={
            UK_MOUTH_ID: lambda: _feed(),
            TED_MOUTH_ID: lambda: _ted_feed(),
        })

        self.assertEqual(report.sweep_status, "OK")
        self.assertEqual(report.signal_count, 0)
        self.assertEqual(report.controlling_party_count, 0)
        self.assertEqual(report.ledger_records_written, 0)
        self.assertEqual(len(ledger.all_records()), 0)
        self.assertIn("zero signals", report.show_the_math())

    # -- cold start still works -----------------------------------------

    def test_cold_start_with_a_non_existent_state_directory_works(self):
        missing = Path(self._tmp.name) / "never" / "existed"
        self.assertFalse(missing.exists())
        ledger = _make_ledger()

        report = opportunity_cycle.run_cycle(
            missing, ledger, fetch_fns={
                UK_MOUTH_ID: lambda: _feed(_release()),
                TED_MOUTH_ID: lambda: _ted_feed(_ted_notice()),
            })

        self.assertTrue(missing.is_dir())
        self.assertEqual(report.signal_count, 2)
        self.assertEqual(report.ledger_records_written, 1)  # same buyer name

    # -- re-running does not double-count in the ledger ------------------

    def test_rerunning_the_same_cycle_does_not_double_count_in_the_ledger(self):
        ledger = _make_ledger()
        fetch_fns = {
            UK_MOUTH_ID: lambda: _feed(_release()),
            TED_MOUTH_ID: lambda: _ted_feed(_ted_notice()),
        }

        first = opportunity_cycle.run_cycle(
            self.state_dir, ledger, fetch_fns=fetch_fns)
        self.assertEqual(first.signal_count, 2)
        self.assertGreaterEqual(len(ledger.all_records()), 1)
        records_after_first = len(ledger.all_records())

        second = opportunity_cycle.run_cycle(
            self.state_dir, ledger, fetch_fns=fetch_fns)
        self.assertEqual(second.sweep_status, "OK")
        self.assertEqual(second.signal_count, 0)
        self.assertEqual(second.ledger_records_written, 0)
        self.assertEqual(len(ledger.all_records()), records_after_first)
        for r in second.source_results:
            self.assertEqual(r.status, "UNCHANGED")

    # -- backwards compatibility: legacy single fetch_fn call shape ------

    def test_legacy_single_fetch_fn_still_works_and_isolates_the_other_source(self):
        """The exact call shape `swarm_contract.py` uses today:
        `run_cycle(state_dir, ledger, fetch_fn=..., now=...)` with one
        fetcher shaped for the UK OCDS feed. The TED source receives the
        same bytes, cannot parse them (no 'notices' key), and is reported
        as an isolated UNAVAILABLE -- it must never be silently skipped
        or crash the cycle, and it must never reach the real network."""
        ledger, report = self._run(fetch_fn=lambda: _feed(_release()))

        self.assertEqual(report.signal_count, 1)
        self.assertEqual(report.ledger_records_written, 1)

        by_id = {r.source_id: r for r in report.source_results}
        self.assertEqual(by_id[UK_MOUTH_ID].signal_count, 1)
        self.assertEqual(by_id[TED_MOUTH_ID].status, "UNAVAILABLE")
        self.assertEqual(by_id[TED_MOUTH_ID].signal_count, 0)
        self.assertIsNotNone(by_id[TED_MOUTH_ID].error)
        self.assertEqual(report.sweep_status, "PARTIAL")


if __name__ == "__main__":
    unittest.main()


class TestGateRefusalDoesNotDiscardOtherSources(unittest.TestCase):
    """Blue-team pass 008, CRITICAL, reproduced live.

    Signals are merged and written to the ledger ONCE, after the whole
    source loop. `run_cycle` used to re-raise a gate refusal from inside
    that loop — deliberately, so a budget or authorization refusal could
    not be downgraded into an ordinary bad day. The reasoning was right;
    the consequence was that one source's accounting destroyed every other
    source's already-fetched, lawfully-obtained notices.

    Reproduced: one source's budget pre-exhausted, another holding a real
    notice → run_cycle() raised, ledger ended with ZERO records.
    """

    def test_one_sources_refusal_leaves_the_others_signals_intact(self):
        from unittest import mock
        from foundation.discovery_authorization import DiscoveryBudgetExhausted

        payload = json.dumps({"notices": [{
            "publication-number": "1-2026", "buyer-name": {"eng": "A Buyer"},
            "notice-title": {"eng": "IT services"},
            "deadline-receipt-request": ["2030-01-01T00:00:00+01:00"]}]}).encode()

        def refuse(*a, **k):
            raise DiscoveryBudgetExhausted("discovery budget exhausted")

        # Inject the refusal at the UK sweeper. A live budget cannot be
        # exhausted here: passing `fetch_fn` bypasses `fetch_feed`, so
        # nothing is ever charged offline.
        with mock.patch.object(opportunity_cycle, "_SOURCE_SWEEPERS",
                               {**opportunity_cycle._SOURCE_SWEEPERS,
                                UK_MOUTH_ID: refuse}):
            with tempfile.TemporaryDirectory() as d:
                ledger = OutcomeLedger(ledger_path=Path(d) / "l.jsonl")
                report = opportunity_cycle.run_cycle(
                    Path(d) / "state", ledger, fetch_fn=lambda: payload)
                records = len(ledger.all_records())

        refused = [r for r in report.source_results
                   if r.status == opportunity_cycle._GATE_REFUSED_STATUS]
        self.assertTrue(refused, "the refusal must be recorded, not swallowed")
        self.assertNotEqual(
            report.signal_count, 0,
            "the other source's signals were discarded by an unrelated "
            "source's budget refusal")
        self.assertNotEqual(records, 0, "ledger write was lost")

    def test_a_gate_refusal_is_not_reported_as_an_ordinary_failure(self):
        """REFUSED_BY_GATE must stay distinct from UNAVAILABLE. One is an
        authority fact, the other is a bad day at the remote end, and a
        caller escalates on only one of them."""
        self.assertNotEqual(opportunity_cycle._GATE_REFUSED_STATUS, "UNAVAILABLE")
