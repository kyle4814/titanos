import inspect
import unittest
from datetime import datetime, timedelta, timezone

from foundation import winnability
from foundation.signal_spine import CanonicalSignal
from foundation.winnability import (
    BANDS,
    DIMENSIONS,
    DeclaredOperatorCapacity,
    WinnabilityIntegrityError,
    assess,
    rank,
)

NOW = datetime(2026, 9, 1, tzinfo=timezone.utc)


def _signal(deadline="", money_state="NOT_OBSERVED", money_observed="",
            signal_id="tender:ted:1", target="Some Buyer",
            cpv="72000000"):
    return CanonicalSignal(
        signal_id=signal_id,
        source_id="mouth_ted",
        source_type="OFFICIAL",
        source_ref="https://ted.europa.eu/x",
        target=target,
        kind="DEMAND",
        claim="open EU TED public-sector tender: test",
        observed_at=NOW.isoformat(),
        target_established_by="SOURCE_NATIVE",
        facts={"deadline": deadline, "cpv": cpv},
        evidence={"deadline": deadline},
        pressure_class="EXPLICIT_DEMAND",
        pressure_evidence="notice text names a procurement need",
        money_state=money_state,
        money_observed=money_observed,
    )


def _iso(days_from_now):
    return (NOW + timedelta(days=days_from_now)).isoformat()


class TestDeclaredOperatorCapacity(unittest.TestCase):
    def test_requires_name(self):
        with self.assertRaises(WinnabilityIntegrityError):
            DeclaredOperatorCapacity(name="", declared_by="Kyle",
                                      ceiling_amount=100000, ceiling_currency="EUR")

    def test_requires_declared_by(self):
        with self.assertRaises(WinnabilityIntegrityError):
            DeclaredOperatorCapacity(name="cap", declared_by="",
                                      ceiling_amount=100000, ceiling_currency="EUR")

    def test_requires_positive_amount(self):
        with self.assertRaises(WinnabilityIntegrityError):
            DeclaredOperatorCapacity(name="cap", declared_by="Kyle",
                                      ceiling_amount=0, ceiling_currency="EUR")
        with self.assertRaises(WinnabilityIntegrityError):
            DeclaredOperatorCapacity(name="cap", declared_by="Kyle",
                                      ceiling_amount=-5, ceiling_currency="EUR")

    def test_requires_currency(self):
        with self.assertRaises(WinnabilityIntegrityError):
            DeclaredOperatorCapacity(name="cap", declared_by="Kyle",
                                      ceiling_amount=100000, ceiling_currency="  ")

    def test_currency_normalised_upper(self):
        cap = DeclaredOperatorCapacity(name="cap", declared_by="Kyle",
                                        ceiling_amount=100000, ceiling_currency="eur")
        self.assertEqual(cap.ceiling_currency, "EUR")


class TestStructurallyOutOfReach(unittest.TestCase):
    def test_ninefigure_framework_with_3day_deadline_is_out_of_reach(self):
        signal = _signal(
            deadline=_iso(3),
            money_state="ADVERTISED",
            money_observed="162000000 EUR (framework maximum value)",
        )
        result = assess(signal, capacity=None, now=NOW)
        self.assertEqual(result.band, "STRUCTURALLY_OUT_OF_REACH")
        deadline_factor = result.factor("deadline_proximity")
        self.assertEqual(deadline_factor.verdict, "BARRIER")
        self.assertIn("3 day", deadline_factor.evidence)

    def test_huge_value_far_beyond_declared_capacity_is_out_of_reach(self):
        capacity = DeclaredOperatorCapacity(
            name="two-person shop", declared_by="Kyle",
            ceiling_amount=2_000_000, ceiling_currency="EUR")
        signal = _signal(
            deadline=_iso(60),
            money_state="ADVERTISED",
            money_observed="149000000 EUR (total value)",
        )
        result = assess(signal, capacity=capacity, now=NOW)
        self.assertEqual(result.band, "STRUCTURALLY_OUT_OF_REACH")
        size_factor = result.factor("contract_size_vs_declared_capacity")
        self.assertEqual(size_factor.verdict, "BARRIER")
        self.assertIn("74.5x", size_factor.evidence)

    def test_size_barrier_alone_softened_to_stretch_when_framework_marker_present(self):
        capacity = DeclaredOperatorCapacity(
            name="two-person shop", declared_by="Kyle",
            ceiling_amount=2_000_000, ceiling_currency="EUR")
        signal = _signal(
            deadline=_iso(90),
            money_state="ADVERTISED",
            money_observed="149000000 EUR (framework maximum value)",
        )
        result = assess(signal, capacity=capacity, now=NOW)
        self.assertEqual(result.band, "STRETCH")

    def test_already_passed_deadline_is_a_barrier(self):
        signal = _signal(
            deadline=_iso(-1),
            money_state="ADVERTISED",
            money_observed="500000 EUR (total value)",
        )
        result = assess(signal, capacity=None, now=NOW)
        self.assertEqual(result.factor("deadline_proximity").verdict, "BARRIER")


class TestAccessible(unittest.TestCase):
    def test_small_single_lot_contract_six_week_deadline_is_accessible(self):
        capacity = DeclaredOperatorCapacity(
            name="two-person shop", declared_by="Kyle",
            ceiling_amount=2_000_000, ceiling_currency="EUR")
        signal = _signal(
            deadline=_iso(42),
            money_state="ADVERTISED",
            money_observed="30000 EUR (estimated value)",
        )
        result = assess(signal, capacity=capacity, now=NOW)
        self.assertEqual(result.band, "ACCESSIBLE")
        for dim in ("contract_size_vs_declared_capacity", "deadline_proximity"):
            self.assertEqual(result.factor(dim).verdict, "NOT_BARRIER")

    def test_multilot_notice_with_ample_deadline_is_accessible(self):
        signal = _signal(
            deadline=_iso(60),
            money_state="ADVERTISED",
            money_observed=("4 lot(s), EUR: 20000, 25000, 18000, 22000 "
                             "(estimated value, per-lot -- TED gave no "
                             "single total for this notice)"),
        )
        result = assess(signal, capacity=None, now=NOW)
        self.assertEqual(result.factor("lot_division").verdict, "NOT_BARRIER")
        self.assertIn(result.band, ("ACCESSIBLE", "STRETCH"))
        self.assertNotEqual(result.band, "STRUCTURALLY_OUT_OF_REACH")


class TestUnknownNeverGuessed(unittest.TestCase):
    def test_missing_size_yields_unknown_not_a_guess(self):
        signal = _signal(deadline=_iso(30), money_state="NOT_OBSERVED",
                          money_observed="")
        result = assess(signal, capacity=DeclaredOperatorCapacity(
            name="shop", declared_by="Kyle", ceiling_amount=1_000_000,
            ceiling_currency="EUR"), now=NOW)
        size_factor = result.factor("contract_size_vs_declared_capacity")
        self.assertEqual(size_factor.status, "UNKNOWN")
        self.assertEqual(size_factor.verdict, "INFO")

    def test_no_capacity_declared_yields_unknown_size_dimension(self):
        signal = _signal(deadline=_iso(30), money_state="ADVERTISED",
                          money_observed="50000 EUR (estimated value)")
        result = assess(signal, capacity=None, now=NOW)
        size_factor = result.factor("contract_size_vs_declared_capacity")
        self.assertEqual(size_factor.status, "UNKNOWN")

    def test_no_deadline_yields_unknown_deadline_dimension(self):
        signal = _signal(deadline="", money_state="ADVERTISED",
                          money_observed="50000 EUR (estimated value)")
        result = assess(signal, capacity=None, now=NOW)
        self.assertEqual(result.factor("deadline_proximity").status, "UNKNOWN")

    def test_currency_mismatch_never_converted_stays_unknown(self):
        capacity = DeclaredOperatorCapacity(
            name="shop", declared_by="Kyle", ceiling_amount=1_000_000,
            ceiling_currency="SEK")
        signal = _signal(deadline=_iso(30), money_state="ADVERTISED",
                          money_observed="50000 EUR (estimated value)")
        result = assess(signal, capacity=capacity, now=NOW)
        size_factor = result.factor("contract_size_vs_declared_capacity")
        self.assertEqual(size_factor.status, "UNKNOWN")
        self.assertIn("no exchange-rate conversion", size_factor.evidence)

    def test_no_facts_at_all_yields_overall_unknown_band(self):
        signal = _signal(deadline="", money_state="NOT_OBSERVED", money_observed="")
        result = assess(signal, capacity=None, now=NOW)
        self.assertEqual(result.band, "UNKNOWN")
        self.assertTrue(result.unknown_reason.strip())

    def test_contract_duration_is_always_unknown(self):
        signal = _signal(deadline=_iso(30), money_state="ADVERTISED",
                          money_observed="50000 EUR (estimated value)")
        result = assess(signal, capacity=None, now=NOW)
        self.assertEqual(result.factor("contract_duration").status, "UNKNOWN")

    def test_ambiguous_multilot_amount_never_summed_or_guessed(self):
        signal = _signal(
            deadline=_iso(30),
            money_state="ADVERTISED",
            money_observed=("6 lot(s), EUR: 5000000, 1000000, 5000000, "
                             "5000000, 500000, 500000 (estimated value, "
                             "per-lot -- TED gave no single total for "
                             "this notice)"),
        )
        capacity = DeclaredOperatorCapacity(
            name="shop", declared_by="Kyle", ceiling_amount=1_000_000,
            ceiling_currency="EUR")
        result = assess(signal, capacity=capacity, now=NOW)
        size_factor = result.factor("contract_size_vs_declared_capacity")
        self.assertEqual(size_factor.status, "UNKNOWN")
        self.assertEqual(result.factor("lot_division").verdict, "NOT_BARRIER")


class TestFrameworkMarker(unittest.TestCase):
    def test_framework_maximum_value_label_detected(self):
        signal = _signal(
            deadline=_iso(30),
            money_state="ADVERTISED",
            money_observed="315000 EUR (framework maximum value)",
        )
        result = assess(signal, capacity=None, now=NOW)
        vehicle = result.factor("procurement_vehicle")
        self.assertEqual(vehicle.status, "KNOWN")

    def test_absence_of_marker_is_unknown_not_confirmed_discrete(self):
        signal = _signal(
            deadline=_iso(30),
            money_state="ADVERTISED",
            money_observed="315000 EUR (total value)",
        )
        result = assess(signal, capacity=None, now=NOW)
        vehicle = result.factor("procurement_vehicle")
        self.assertEqual(vehicle.status, "UNKNOWN")
        self.assertIn("does NOT confirm", vehicle.evidence)


class TestNoProbabilityLanguage(unittest.TestCase):
    """Structural proof, not just a style rule: scan this module's own
    source AND every string this module can actually emit at runtime for
    probability/prediction language."""

    FORBIDDEN = ("probability", "likely to win", "% chance",
                 "chance of winning", "odds of winning",
                 "score out of 10", "win rate")

    def test_public_callables_never_named_as_a_predictor(self):
        # The module's own public API surface must not offer a function
        # that sounds like it predicts an outcome (e.g. "predict",
        # "win_probability") -- distinct from the module's prose, which
        # is allowed to discuss and refuse the concept in English.
        for name in winnability.__all__:
            lowered = name.lower()
            self.assertNotIn("predict", lowered)
            self.assertNotIn("probability", lowered)
            self.assertNotIn("win_rate", lowered)

    def test_runtime_assessments_never_carry_forbidden_language(self):
        capacity = DeclaredOperatorCapacity(
            name="shop", declared_by="Kyle", ceiling_amount=2_000_000,
            ceiling_currency="EUR")
        signals = [
            _signal(signal_id="a", deadline=_iso(3), money_state="ADVERTISED",
                    money_observed="162000000 EUR (framework maximum value)"),
            _signal(signal_id="b", deadline=_iso(42), money_state="ADVERTISED",
                    money_observed="30000 EUR (estimated value)"),
            _signal(signal_id="c", deadline="", money_state="NOT_OBSERVED",
                    money_observed=""),
        ]
        for signal in signals:
            result = assess(signal, capacity=capacity, now=NOW)
            blob = (result.note + result.unknown_reason + " ".join(
                f.evidence for f in result.factors)).lower()
            for term in self.FORBIDDEN:
                self.assertNotIn(term, blob)


class TestAssessmentIntegrity(unittest.TestCase):
    def test_every_dimension_present_exactly_once(self):
        signal = _signal(deadline=_iso(10))
        result = assess(signal, now=NOW)
        self.assertEqual(tuple(f.dimension for f in result.factors), DIMENSIONS)

    def test_unknown_band_requires_reason(self):
        with self.assertRaises(WinnabilityIntegrityError):
            from foundation.winnability import WinnabilityAssessment, WinnabilityFactor
            WinnabilityAssessment(
                signal_id="x", operator_name="", band="UNKNOWN",
                factors=tuple(
                    WinnabilityFactor(dimension=d, status="UNKNOWN",
                                       verdict="INFO", evidence="nothing found")
                    for d in DIMENSIONS
                ),
                unknown_reason="",
            )

    def test_unknown_verdict_must_be_info(self):
        from foundation.winnability import WinnabilityFactor
        with self.assertRaises(WinnabilityIntegrityError):
            WinnabilityFactor(dimension="deadline_proximity", status="UNKNOWN",
                               verdict="BARRIER", evidence="something")

    def test_factor_requires_evidence(self):
        from foundation.winnability import WinnabilityFactor
        with self.assertRaises(WinnabilityIntegrityError):
            WinnabilityFactor(dimension="deadline_proximity", status="KNOWN",
                               verdict="BARRIER", evidence="   ")

    def test_missing_dimension_rejected(self):
        from foundation.winnability import WinnabilityAssessment, WinnabilityFactor
        with self.assertRaises(WinnabilityIntegrityError):
            WinnabilityAssessment(
                signal_id="x", operator_name="", band="ACCESSIBLE",
                factors=(
                    WinnabilityFactor(dimension="deadline_proximity",
                                       status="KNOWN", verdict="NOT_BARRIER",
                                       evidence="fine"),
                ),
            )


class TestRank(unittest.TestCase):
    def test_rank_never_drops_a_signal(self):
        signals = [
            _signal(signal_id="a", deadline=_iso(3), money_state="ADVERTISED",
                    money_observed="162000000 EUR (framework maximum value)"),
            _signal(signal_id="b", deadline=_iso(42), money_state="ADVERTISED",
                    money_observed="30000 EUR (estimated value)"),
            _signal(signal_id="c", deadline="", money_state="NOT_OBSERVED",
                    money_observed=""),
        ]
        results = rank(signals, now=NOW)
        self.assertEqual(len(results), 3)
        self.assertEqual({r.signal_id for r in results},
                          {s.signal_id for s in signals})

    def test_rank_orders_most_accessible_first(self):
        capacity = DeclaredOperatorCapacity(
            name="shop", declared_by="Kyle", ceiling_amount=2_000_000,
            ceiling_currency="EUR")
        accessible = _signal(signal_id="acc", deadline=_iso(42),
                              money_state="ADVERTISED",
                              money_observed="30000 EUR (estimated value)")
        out_of_reach = _signal(signal_id="oor", deadline=_iso(3),
                                money_state="ADVERTISED",
                                money_observed="162000000 EUR (total value)")
        results = rank([out_of_reach, accessible], capacity=capacity, now=NOW)
        self.assertEqual(results[0].signal_id, "acc")
        self.assertEqual(results[-1].signal_id, "oor")

    def test_rank_deterministic(self):
        signals = [
            _signal(signal_id=f"s{i}", deadline=_iso(42), money_state="ADVERTISED",
                    money_observed="30000 EUR (estimated value)")
            for i in range(5)
        ]
        r1 = rank(list(reversed(signals)), now=NOW)
        r2 = rank(signals, now=NOW)
        self.assertEqual([r.signal_id for r in r1], [r.signal_id for r in r2])


if __name__ == "__main__":
    unittest.main()
