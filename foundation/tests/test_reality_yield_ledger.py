"""Tests for foundation/reality_yield_ledger.py."""

from __future__ import annotations

import unittest

from foundation.reality_yield_ledger import (
    YieldComponent,
    LedgerEntry,
    RealityYieldLedger,
    net_reality_yield,
    YIELD_NAMES,
    COST_NAMES,
)


def make_valid_yield_components() -> list[YieldComponent]:
    return [
        YieldComponent(
            name="VERIFIED_BENEFIT",
            value=12.0,
            evidence="Production incident count dropped from 4/week to "
                      "0/week over the 3 weeks after rollout, measured by "
                      "the incident tracker.",
        ),
        YieldComponent(
            name="REUSABILITY",
            value=3.0,
            evidence="The same validation function was imported and used "
                     "unmodified by two other modules in this repo, "
                     "confirmed by grep.",
        ),
    ]


def make_valid_cost_components() -> list[YieldComponent]:
    return [
        YieldComponent(
            name="COMPUTE_COST",
            value=2.0,
            evidence="CI run time increased by 45 seconds per run, measured "
                     "across the last 20 CI runs.",
        ),
    ]


class TestFirstValidEntry(unittest.TestCase):
    """First test: a fully valid, honestly-evidenced entry passes cleanly."""

    def test_valid_entry_records_and_computes_net_yield(self) -> None:
        ledger = RealityYieldLedger()
        entry = ledger.record(
            entry_id="e1",
            subject="cache-invalidation-lesson",
            yield_components=make_valid_yield_components(),
            cost_components=make_valid_cost_components(),
            assessed_by="kyle",
        )
        self.assertEqual(entry.entry_id, "e1")
        self.assertEqual(net_reality_yield(entry), 12.0 + 3.0 - 2.0)
        self.assertEqual(ledger.recommendation("e1"), "CONTINUE_CAUTIOUSLY")


class TestYieldComponentValidation(unittest.TestCase):
    def test_negative_value_rejected(self) -> None:
        with self.assertRaises(ValueError):
            YieldComponent(
                name="VERIFIED_BENEFIT",
                value=-1.0,
                evidence="Measured directly from the production dashboard.",
            )

    def test_negative_cost_value_rejected_even_though_it_is_a_cost(self) -> None:
        # Costs are entered as positive magnitudes too — sign comes from
        # which side of the equation the name belongs to.
        with self.assertRaises(ValueError):
            YieldComponent(
                name="COMPUTE_COST",
                value=-5.0,
                evidence="Observed directly in the billing dashboard.",
            )

    def test_zero_value_is_allowed(self) -> None:
        component = YieldComponent(
            name="SYSTEMIC_RISK",
            value=0.0,
            evidence="No incidents observed in the 30-day monitoring window.",
        )
        self.assertEqual(component.value, 0.0)

    def test_empty_evidence_rejected(self) -> None:
        with self.assertRaises(ValueError):
            YieldComponent(name="VERIFIED_BENEFIT", value=5.0, evidence="")

    def test_whitespace_only_evidence_rejected(self) -> None:
        with self.assertRaises(ValueError):
            YieldComponent(name="VERIFIED_BENEFIT", value=5.0, evidence="   ")

    def test_unrecognised_component_name_rejected(self) -> None:
        with self.assertRaises(ValueError):
            YieldComponent(
                name="VIBES",
                value=5.0,
                evidence="Observed directly last week.",
            )

    def test_is_yield_and_is_cost_flags(self) -> None:
        y = YieldComponent(
            name="INFORMATION_GAIN", value=1.0,
            evidence="Logged and reviewed after the fact.",
        )
        c = YieldComponent(
            name="SYSTEMIC_RISK", value=1.0,
            evidence="Observed one rollback event in production logs.",
        )
        self.assertTrue(y.is_yield())
        self.assertFalse(y.is_cost())
        self.assertTrue(c.is_cost())
        self.assertFalse(c.is_yield())


class TestForwardLookingLanguageRejection(unittest.TestCase):
    """The load-bearing test and variants: confident numbers don't buy a pass."""

    def test_impressive_forward_looking_claim_is_rejected(self) -> None:
        # Large, optimistic-sounding VERIFIED_BENEFIT and INFORMATION_GAIN
        # values, but the evidence text is a forecast, not an observation.
        # The rejection must happen regardless of how good the numbers look.
        with self.assertRaises(ValueError) as ctx:
            YieldComponent(
                name="VERIFIED_BENEFIT",
                value=500.0,
                evidence=(
                    "This will generate significant value once deployed "
                    "at scale."
                ),
            )
        self.assertIn("forward-looking", str(ctx.exception))

    def test_second_impressive_component_same_subject_also_rejected(self) -> None:
        with self.assertRaises(ValueError):
            YieldComponent(
                name="INFORMATION_GAIN",
                value=999.0,
                evidence="This is expected to eventually inform every "
                         "future decision the system makes.",
            )

    def test_record_rejects_entry_with_one_bad_component_among_good_ones(self) -> None:
        # Siblings being well-evidenced does not rescue the bad component.
        ledger = RealityYieldLedger()
        good = make_valid_yield_components()
        with self.assertRaises(ValueError):
            bad = YieldComponent(
                name="ERROR_REDUCTION",
                value=200.0,
                evidence="This will reduce errors dramatically once adopted "
                         "org-wide.",
            )
            ledger.record(
                entry_id="e-bad",
                subject="some-pathway",
                yield_components=[*good, bad],
                cost_components=[],
                assessed_by="kyle",
            )

    def test_forecast_word_projected_rejected(self) -> None:
        with self.assertRaises(ValueError):
            YieldComponent(
                name="REUSABILITY",
                value=10.0,
                evidence="Projected to be reused across three more teams.",
            )

    def test_forecast_word_anticipated_rejected(self) -> None:
        with self.assertRaises(ValueError):
            YieldComponent(
                name="COMPUTE_COST",
                value=1.0,
                evidence="Anticipated compute overhead is negligible.",
            )

    def test_honest_past_tense_evidence_is_accepted(self) -> None:
        # Sanity check: rewriting a forecast into an observation passes.
        component = YieldComponent(
            name="VERIFIED_BENEFIT",
            value=500.0,
            evidence="Generated significant measured value after deployment "
                     "at scale, per the Q3 usage report.",
        )
        self.assertEqual(component.value, 500.0)


class TestRecordValidation(unittest.TestCase):
    def test_empty_entry_both_sides_empty_rejected(self) -> None:
        ledger = RealityYieldLedger()
        with self.assertRaises(ValueError):
            ledger.record(
                entry_id="e2",
                subject="empty-subject",
                yield_components=[],
                cost_components=[],
                assessed_by="kyle",
            )

    def test_only_cost_components_is_a_valid_assessment(self) -> None:
        ledger = RealityYieldLedger()
        entry = ledger.record(
            entry_id="e3",
            subject="pure-cost-subject",
            yield_components=[],
            cost_components=make_valid_cost_components(),
            assessed_by="kyle",
        )
        self.assertEqual(net_reality_yield(entry), -2.0)

    def test_only_yield_components_is_a_valid_assessment(self) -> None:
        ledger = RealityYieldLedger()
        entry = ledger.record(
            entry_id="e4",
            subject="pure-yield-subject",
            yield_components=make_valid_yield_components(),
            cost_components=[],
            assessed_by="kyle",
        )
        self.assertGreater(net_reality_yield(entry), 0)

    def test_duplicate_entry_id_rejected(self) -> None:
        ledger = RealityYieldLedger()
        ledger.record(
            entry_id="dup",
            subject="s",
            yield_components=make_valid_yield_components(),
            cost_components=[],
            assessed_by="kyle",
        )
        with self.assertRaises(ValueError):
            ledger.record(
                entry_id="dup",
                subject="s",
                yield_components=make_valid_yield_components(),
                cost_components=[],
                assessed_by="kyle",
            )

    def test_missing_assessed_by_rejected(self) -> None:
        ledger = RealityYieldLedger()
        with self.assertRaises(ValueError):
            ledger.record(
                entry_id="e5",
                subject="s",
                yield_components=make_valid_yield_components(),
                cost_components=[],
                assessed_by="",
            )

    def test_missing_subject_rejected(self) -> None:
        ledger = RealityYieldLedger()
        with self.assertRaises(ValueError):
            ledger.record(
                entry_id="e6",
                subject="",
                yield_components=make_valid_yield_components(),
                cost_components=[],
                assessed_by="kyle",
            )

    def test_yield_component_passed_on_cost_side_rejected(self) -> None:
        ledger = RealityYieldLedger()
        with self.assertRaises(ValueError):
            ledger.record(
                entry_id="e7",
                subject="s",
                yield_components=[],
                cost_components=make_valid_yield_components(),
                assessed_by="kyle",
            )

    def test_cost_component_passed_on_yield_side_rejected(self) -> None:
        ledger = RealityYieldLedger()
        with self.assertRaises(ValueError):
            ledger.record(
                entry_id="e8",
                subject="s",
                yield_components=make_valid_cost_components(),
                cost_components=[],
                assessed_by="kyle",
            )

    def test_supersedes_unknown_entry_rejected(self) -> None:
        ledger = RealityYieldLedger()
        with self.assertRaises(KeyError):
            ledger.record(
                entry_id="e9",
                subject="s",
                yield_components=make_valid_yield_components(),
                cost_components=[],
                assessed_by="kyle",
                supersedes="nonexistent",
            )


class TestRecommendationThreeWayBranch(unittest.TestCase):
    def test_positive_net_yields_continue_cautiously(self) -> None:
        ledger = RealityYieldLedger()
        ledger.record(
            entry_id="pos",
            subject="s",
            yield_components=[
                YieldComponent(
                    name="VERIFIED_BENEFIT", value=10.0,
                    evidence="Measured directly in production over 2 weeks.",
                )
            ],
            cost_components=[
                YieldComponent(
                    name="COMPUTE_COST", value=1.0,
                    evidence="Observed in the last billing cycle.",
                )
            ],
            assessed_by="kyle",
        )
        self.assertEqual(ledger.recommendation("pos"), "CONTINUE_CAUTIOUSLY")

    def test_zero_net_yields_hold_and_review(self) -> None:
        ledger = RealityYieldLedger()
        ledger.record(
            entry_id="zero",
            subject="s",
            yield_components=[
                YieldComponent(
                    name="VERIFIED_BENEFIT", value=5.0,
                    evidence="Measured directly in the observed test window.",
                )
            ],
            cost_components=[
                YieldComponent(
                    name="COMPUTE_COST", value=5.0,
                    evidence="Measured directly in the observed test window.",
                )
            ],
            assessed_by="kyle",
        )
        self.assertEqual(ledger.recommendation("zero"), "HOLD_AND_REVIEW")

    def test_negative_net_yields_throttle_or_terminate(self) -> None:
        ledger = RealityYieldLedger()
        ledger.record(
            entry_id="neg",
            subject="s",
            yield_components=[
                YieldComponent(
                    name="VERIFIED_BENEFIT", value=1.0,
                    evidence="Measured directly in the observed test window.",
                )
            ],
            cost_components=[
                YieldComponent(
                    name="SYSTEMIC_RISK", value=8.0,
                    evidence="Observed two rollback incidents traced back to "
                             "this pathway in the incident log.",
                )
            ],
            assessed_by="kyle",
        )
        self.assertEqual(ledger.recommendation("neg"), "THROTTLE_OR_TERMINATE")

    def test_recommendation_unknown_entry_raises_keyerror(self) -> None:
        ledger = RealityYieldLedger()
        with self.assertRaises(KeyError):
            ledger.recommendation("does-not-exist")


class TestNegativeYieldIsHonestlyRecorded(unittest.TestCase):
    """The ledger records bad news, it doesn't prevent it from existing."""

    def test_ledger_accepts_and_preserves_a_deeply_negative_assessment(self) -> None:
        ledger = RealityYieldLedger()
        entry = ledger.record(
            entry_id="disaster",
            subject="risky-pathway",
            yield_components=[
                YieldComponent(
                    name="REUSABILITY", value=1.0,
                    evidence="Reused once, confirmed by grep.",
                )
            ],
            cost_components=[
                YieldComponent(
                    name="SYSTEMIC_RISK", value=50.0,
                    evidence="Caused a production outage lasting 6 hours, "
                             "per the incident postmortem.",
                ),
                YieldComponent(
                    name="REVERSIBILITY_COST", value=20.0,
                    evidence="Rolling this back required a manual data "
                             "migration, logged in the runbook.",
                ),
            ],
            assessed_by="kyle",
        )
        net = net_reality_yield(entry)
        self.assertLess(net, 0)
        self.assertEqual(net, 1.0 - 70.0)
        self.assertEqual(ledger.get("disaster"), entry)
        self.assertEqual(ledger.recommendation("disaster"), "THROTTLE_OR_TERMINATE")


class TestGetAndAppendOnlyBehaviour(unittest.TestCase):
    def test_get_missing_entry_returns_none(self) -> None:
        ledger = RealityYieldLedger()
        self.assertIsNone(ledger.get("nope"))

    def test_no_delete_surface(self) -> None:
        ledger = RealityYieldLedger()
        for forbidden in ("delete", "purge", "clear", "remove"):
            self.assertFalse(
                hasattr(ledger, forbidden),
                f"RealityYieldLedger must not expose a '{forbidden}' method",
            )

    def test_entry_history_records_recorded_event(self) -> None:
        ledger = RealityYieldLedger()
        entry = ledger.record(
            entry_id="hist1",
            subject="s",
            yield_components=make_valid_yield_components(),
            cost_components=[],
            assessed_by="kyle",
        )
        self.assertEqual(len(entry.history), 1)
        self.assertEqual(entry.history[0]["event"], "RECORDED")


class TestSupersessionAndHistoryFor(unittest.TestCase):
    def test_history_for_unknown_subject_is_empty_tuple(self) -> None:
        ledger = RealityYieldLedger()
        self.assertEqual(ledger.history_for("never-recorded"), ())

    def test_history_for_returns_entries_in_recording_order(self) -> None:
        ledger = RealityYieldLedger()
        e1 = ledger.record(
            entry_id="s1",
            subject="shared-subject",
            yield_components=make_valid_yield_components(),
            cost_components=[],
            assessed_by="kyle",
        )
        e2 = ledger.record(
            entry_id="s2",
            subject="shared-subject",
            yield_components=[
                YieldComponent(
                    name="VERIFIED_BENEFIT", value=1.0,
                    evidence="Re-measured a month later against production logs.",
                )
            ],
            cost_components=[],
            assessed_by="kyle",
            supersedes="s1",
        )
        history = ledger.history_for("shared-subject")
        self.assertEqual(history, (e1, e2))

    def test_superseded_entry_still_visible_in_history_after_downgrade(self) -> None:
        # An earlier optimistic assessment must remain visible even after
        # being superseded by a worse one — never silently replaced.
        ledger = RealityYieldLedger()
        optimistic = ledger.record(
            entry_id="opt",
            subject="reassessed-pathway",
            yield_components=[
                YieldComponent(
                    name="VERIFIED_BENEFIT", value=100.0,
                    evidence="Measured a large benefit in the initial "
                             "two-week pilot window.",
                )
            ],
            cost_components=[],
            assessed_by="kyle",
        )
        self.assertEqual(ledger.recommendation("opt"), "CONTINUE_CAUTIOUSLY")

        downgraded = ledger.record(
            entry_id="downgrade",
            subject="reassessed-pathway",
            yield_components=[],
            cost_components=[
                YieldComponent(
                    name="SYSTEMIC_RISK", value=500.0,
                    evidence="Observed a severe production incident traced "
                             "to this pathway three months after the pilot, "
                             "per the incident report.",
                )
            ],
            assessed_by="kyle",
            supersedes="opt",
        )
        self.assertEqual(ledger.recommendation("downgrade"), "THROTTLE_OR_TERMINATE")

        history = ledger.history_for("reassessed-pathway")
        self.assertEqual(len(history), 2)
        self.assertIn(optimistic, history)
        self.assertIn(downgraded, history)
        self.assertEqual(downgraded.supersedes, "opt")
        # The original optimistic entry is untouched by the downgrade.
        self.assertEqual(ledger.recommendation("opt"), "CONTINUE_CAUTIOUSLY")


if __name__ == "__main__":
    unittest.main()
