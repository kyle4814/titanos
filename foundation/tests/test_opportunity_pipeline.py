"""The pipeline must never make COMMERCIAL_OUTCOME look better than
reality. Every test here either proves collapsing-by-controlling-party
works, proves a replay cannot double-count, or proves qualified/
contracts/cash stay 0 no matter what arrives.
"""

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from foundation.opportunity_pipeline import (
    PipelineOpportunity,
    PipelineReport,
    collapse_by_controlling_party,
    run_pipeline,
)
from foundation.outcome_ledger import CHAIN_VERIFIED, OutcomeLedger
from foundation.signal_spine import CanonicalSignal

_NOW = datetime(2026, 9, 1, tzinfo=timezone.utc)


def _signal(signal_id, target, author_login=None, claim=None,
            source_id="test_mouth"):
    evidence = {}
    if author_login:
        evidence["author_login"] = author_login
    return CanonicalSignal(
        signal_id=signal_id,
        source_id=source_id,
        source_type="OFFICIAL",
        source_ref="https://example.test/feed",
        target=target,
        kind="DEMAND",
        claim=claim or f"open tender notice {signal_id}",
        observed_at=_NOW.isoformat(),
        target_established_by="SOURCE_NATIVE",
        evidence=evidence,
    )


def _ledger():
    """Isolated ledger -- tests must never share the default on-disk
    path, matching `test_outcome_ledger.py`'s own convention."""
    return OutcomeLedger(ledger_path=Path(tempfile.mkdtemp()) / "l.jsonl")


class CollapseByControllingPartyTests(unittest.TestCase):
    def test_three_signals_one_buyer_collapse_to_one_opportunity(self):
        signals = [
            _signal("tender:1", "Example Council"),
            _signal("tender:2", "Example Council"),
            _signal("tender:3", "Example Council"),
        ]
        opportunities = collapse_by_controlling_party(signals)
        self.assertEqual(len(opportunities), 1)
        self.assertEqual(opportunities[0].controlling_party,
                          "example council")
        self.assertEqual(len(opportunities[0].signals), 3)

    def test_independent_second_buyer_stays_separate(self):
        signals = [
            _signal("tender:1", "Example Council"),
            _signal("tender:2", "Other Authority"),
        ]
        opportunities = collapse_by_controlling_party(signals)
        self.assertEqual(len(opportunities), 2)
        parties = {o.controlling_party for o in opportunities}
        self.assertEqual(parties, {"example council", "other authority"})

    def test_third_party_author_login_is_a_distinct_controlling_party(self):
        # A repo owner talking to itself vs. a genuine stranger's demand
        # signal -- the exact nuance `opportunity.controlling_party()`'s
        # own docstring says must survive. Proven here, one layer up.
        owner_signal = _signal("act:1", "acme/widget")
        contributor_signal = _signal(
            "demand:1", "acme/widget", author_login="a_stranger")
        opportunities = collapse_by_controlling_party(
            [owner_signal, contributor_signal])
        self.assertEqual(len(opportunities), 2)

    def test_empty_signals_produce_no_opportunities(self):
        self.assertEqual(collapse_by_controlling_party([]), ())


class RunPipelineTests(unittest.TestCase):
    def test_empty_signal_list_is_a_valid_outcome_not_an_error(self):
        report = run_pipeline([], _ledger())
        self.assertIsInstance(report, PipelineReport)
        self.assertEqual(report.signal_count, 0)
        self.assertEqual(report.controlling_party_count, 0)
        self.assertEqual(report.opportunities, ())
        self.assertEqual(report.qualified, 0)
        self.assertEqual(report.contracts, 0)
        self.assertEqual(report.cash, 0)

    def test_qualified_contracts_cash_stay_zero_regardless_of_volume(self):
        signals = [_signal(f"tender:{i}", f"Council {i}") for i in range(25)]
        report = run_pipeline(signals, _ledger())
        self.assertEqual(report.signal_count, 25)
        self.assertEqual(report.controlling_party_count, 25)
        self.assertEqual(report.qualified, 0)
        self.assertEqual(report.contracts, 0)
        self.assertEqual(report.cash, 0)

    def test_rerunning_same_sweep_does_not_double_count_in_ledger(self):
        ledger = _ledger()
        signals = [
            _signal("tender:1", "Example Council"),
            _signal("tender:2", "Example Council"),
        ]
        run_pipeline(signals, ledger)
        self.assertEqual(len(ledger.all_records()), 1)
        # Re-run the IDENTICAL sweep -- this is the replay-safety
        # property the task exists to prove.
        run_pipeline(signals, ledger)
        self.assertEqual(len(ledger.all_records()), 1)
        run_pipeline(signals, ledger)
        self.assertEqual(len(ledger.all_records()), 1)

    def test_rerun_returns_the_same_opportunity_and_outcome(self):
        ledger = _ledger()
        signals = [_signal("tender:1", "Example Council")]
        report1 = run_pipeline(signals, ledger)
        report2 = run_pipeline(signals, ledger)
        opp_id_1 = report1.opportunities[0].opportunity_id
        opp_id_2 = report2.opportunities[0].opportunity_id
        self.assertEqual(opp_id_1, opp_id_2)
        self.assertEqual(len(ledger.outcomes_for_brick(opp_id_1)), 1)
        current = ledger.current_for_brick(opp_id_1)
        self.assertIsNotNone(current)
        self.assertEqual(current.state, "PENDING")

    def test_a_genuinely_new_signal_for_the_same_party_is_a_new_fact(self):
        # Two observations of the same buyer, on different sweeps, with a
        # NEW notice the second time, must NOT collapse into the first
        # sweep's operation id -- that would destroy the same
        # silence-versus-absence discipline `outcome_ledger.py` already
        # protects (see its own `record()` docstring).
        ledger = _ledger()
        run_pipeline([_signal("tender:1", "Example Council")], ledger)
        run_pipeline(
            [_signal("tender:1", "Example Council"),
             _signal("tender:2", "Example Council")],
            ledger,
        )
        self.assertEqual(len(ledger.all_records()), 2)

    def test_reload_from_disk_still_recognises_the_replay(self):
        path = Path(tempfile.mkdtemp()) / "l.jsonl"
        signals = [_signal("tender:1", "Example Council")]
        ledger1 = OutcomeLedger(ledger_path=path)
        run_pipeline(signals, ledger1)
        # A fresh ledger instance, replaying the same file, must still
        # recognise the operation id and refuse to double-count -- the
        # index that matters is the persisted one, not an in-memory one
        # that would evaporate at exactly the moment a retry is likely.
        ledger2 = OutcomeLedger(ledger_path=path)
        run_pipeline(signals, ledger2)
        self.assertEqual(len(ledger2.all_records()), 1)

    def test_hash_chain_stays_intact_across_records(self):
        ledger = _ledger()
        signals = [
            _signal("tender:1", "Council A"),
            _signal("tender:2", "Council B"),
            _signal("tender:3", "Council C"),
        ]
        run_pipeline(signals, ledger)
        records = ledger.all_records()
        self.assertEqual(len(records), 3)
        for record in records:
            self.assertEqual(ledger.chain_status(record.outcome_id),
                              CHAIN_VERIFIED)

    def test_signal_count_reflects_raw_signals_not_collapsed_count(self):
        signals = [
            _signal("tender:1", "Example Council"),
            _signal("tender:2", "Example Council"),
            _signal("tender:3", "Example Council"),
        ]
        report = run_pipeline(signals, _ledger())
        self.assertEqual(report.signal_count, 3)
        self.assertEqual(report.controlling_party_count, 1)


class PipelineOpportunityOperationIdTests(unittest.TestCase):
    def test_operation_id_is_deterministic_for_identical_signal_sets(self):
        signals = (
            _signal("tender:1", "Example Council"),
            _signal("tender:2", "Example Council"),
        )
        opp_a = collapse_by_controlling_party(signals)[0]
        opp_b = collapse_by_controlling_party(signals)[0]
        self.assertEqual(opp_a.operation_id(), opp_b.operation_id())

    def test_operation_id_changes_when_signal_set_changes(self):
        opp_a = collapse_by_controlling_party(
            [_signal("tender:1", "Example Council")])[0]
        opp_b = collapse_by_controlling_party(
            [_signal("tender:1", "Example Council"),
             _signal("tender:2", "Example Council")])[0]
        self.assertNotEqual(opp_a.operation_id(), opp_b.operation_id())


class ShowTheMathTests(unittest.TestCase):
    def test_show_the_math_names_zero_signals_honestly(self):
        report = run_pipeline([], _ledger())
        text = report.show_the_math()
        self.assertIn("signals=0", text)
        self.assertIn("qualified=0", text)
        self.assertIn("contracts=0", text)
        self.assertIn("cash=0", text)

    def test_show_the_math_never_implies_more_than_observed(self):
        signals = [_signal("tender:1", "Example Council")]
        report = run_pipeline(signals, _ledger())
        text = report.show_the_math()
        self.assertIn("OBSERVED", text)
        self.assertNotIn("QUALIFIED", text.split("\n")[0])


if __name__ == "__main__":
    unittest.main()


class TestOperationIdIsNotInjectable(unittest.TestCase):
    """Blue-team pass 004, finding 9b, severity HIGH.

    `operation_id()` originally joined signal ids with commas. A single
    signal whose id is literally "tender:X,tender:Y" then produced the
    same joined string as two genuine signals, so both hashed identically
    and `OutcomeLedger.record()` treated the second REAL observation as a
    replay of the first -- returning the original record with no
    exception and no log line.

    That is the inverse of double-counting and it is the worse failure: a
    double count shows up in the numbers, a swallowed observation looks
    exactly like nothing having happened. signal_id is attacker-reachable
    because it is derived from an external feed's identifiers.
    """

    def _sig(self, signal_id, target="acme corp"):
        return _signal(signal_id=signal_id, target=target)

    def test_a_comma_in_one_signal_id_does_not_impersonate_two_signals(self):
        one = collapse_by_controlling_party([self._sig("tender:X,tender:Y")])
        two = collapse_by_controlling_party(
            [self._sig("tender:X"), self._sig("tender:Y")])
        self.assertEqual(len(one), 1)
        self.assertEqual(len(two), 1)
        self.assertNotEqual(
            one[0].operation_id(), two[0].operation_id(),
            "one crafted signal id collides with two genuine signals; a real "
            "observation would be silently discarded as a replay")

    def test_identical_signal_sets_still_produce_identical_ids(self):
        """The fix must not break replay safety, which is the whole point
        of the id existing."""
        a = collapse_by_controlling_party(
            [self._sig("tender:X"), self._sig("tender:Y")])
        b = collapse_by_controlling_party(
            [self._sig("tender:Y"), self._sig("tender:X")])   # order swapped
        self.assertEqual(a[0].operation_id(), b[0].operation_id())

    def test_a_genuinely_new_signal_still_changes_the_id(self):
        a = collapse_by_controlling_party([self._sig("tender:X")])
        b = collapse_by_controlling_party(
            [self._sig("tender:X"), self._sig("tender:Z")])
        self.assertNotEqual(a[0].operation_id(), b[0].operation_id())
