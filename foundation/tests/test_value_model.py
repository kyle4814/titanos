"""The scale's value is in what it refuses to weigh.

Each test below tries to get a number out of the model that the inputs do
not support. A suite that only proved 2 x 3 == 6 would prove nothing:
anyone can multiply.
"""

import unittest
from dataclasses import FrozenInstanceError

from foundation.value_model import (
    NOT_MEASURED,
    SOURCE_STATES,
    DerivedValue,
    ValueInput,
    ValueIntegrityError,
    ValueModel,
)


def _measured(name="transaction_volume", amount=62.0, unit="events"):
    return ValueInput(name=name, unit=unit, status="MEASURED", amount=amount,
                      source="62 rows counted in the webhook_events table")


def _estimated(name="loss_per_event", amount=400.0, unit="AUD"):
    return ValueInput(name=name, unit=unit, status="ESTIMATED", amount=amount,
                      assumption="mean order value of the affected plan")


def _unmeasured(name="loss_per_event"):
    return ValueInput(name=name, unit="AUD", status=NOT_MEASURED)


class TestAnInputCannotMisrepresentItsOrigin(unittest.TestCase):
    def test_not_measured_cannot_carry_a_figure(self):
        """The contradiction that survives into a quote."""
        with self.assertRaises(ValueIntegrityError) as ctx:
            ValueInput(name="revenue_at_risk", unit="AUD",
                       status=NOT_MEASURED, amount=500000.0)
        self.assertIn("only a gap", str(ctx.exception))

    def test_a_measured_claim_with_no_figure_is_refused(self):
        with self.assertRaises(ValueIntegrityError) as ctx:
            ValueInput(name="x", unit="AUD", status="MEASURED",
                       source="the ledger")
        self.assertIn(NOT_MEASURED, str(ctx.exception))

    def test_an_observation_must_name_what_was_observed(self):
        with self.assertRaises(ValueIntegrityError) as ctx:
            ValueInput(name="x", unit="events", status="MEASURED", amount=5.0)
        self.assertIn("names no source", str(ctx.exception))

    def test_our_own_estimate_must_state_its_assumption(self):
        """MEASURED owes a source; ESTIMATED owes an assumption. Different
        debts, because they are different kinds of claim."""
        with self.assertRaises(ValueIntegrityError) as ctx:
            ValueInput(name="x", unit="AUD", status="ESTIMATED", amount=400.0,
                       source="a spreadsheet someone sent")
        self.assertIn("assumption", str(ctx.exception))

    def test_a_figure_with_no_unit_is_refused(self):
        with self.assertRaises(ValueIntegrityError) as ctx:
            ValueInput(name="x", unit="", status="MEASURED", amount=5.0,
                       source="the ledger")
        self.assertIn("no unit", str(ctx.exception))

    def test_a_one_ended_range_is_refused(self):
        with self.assertRaises(ValueIntegrityError) as ctx:
            ValueInput(name="x", unit="AUD", status="RANGE_ESTIMATED",
                       amount=100.0, assumption="based on two comparable months")
        self.assertIn("point estimate in disguise", str(ctx.exception))

    def test_an_upper_bound_on_a_point_claim_is_refused(self):
        """Smuggling a range in under a stronger label."""
        with self.assertRaises(ValueIntegrityError) as ctx:
            ValueInput(name="x", unit="AUD", status="MEASURED", amount=100.0,
                       amount_high=900.0, source="the ledger")
        self.assertIn("RANGE_ESTIMATED", str(ctx.exception))

    def test_an_inverted_range_is_refused(self):
        with self.assertRaises(ValueIntegrityError):
            ValueInput(name="x", unit="AUD", status="RANGE_ESTIMATED",
                       amount=900.0, amount_high=100.0, assumption="a")

    def test_an_invented_source_state_is_refused(self):
        with self.assertRaises(ValueIntegrityError):
            ValueInput(name="x", unit="AUD", status="CONSERVATIVE_ESTIMATE",
                       amount=1.0, source="s")

    def test_the_six_states_are_all_present_and_distinct(self):
        for expected in ("NOT_MEASURED", "MEASURED", "ESTIMATED",
                         "RANGE_ESTIMATED", "CUSTOMER_REPORTED",
                         "VALIDATED_REALIZED"):
            self.assertIn(expected, SOURCE_STATES)
        self.assertEqual(len(set(SOURCE_STATES)), 6)


class TestThePartialMeasurementLie(unittest.TestCase):
    """The whole reason this module exists.

    62 real events x $400 invented = $24,800 that reads as a measurement.
    """

    def test_one_unmeasured_factor_blocks_the_entire_product(self):
        m = ValueModel(
            inputs=(_measured(), _unmeasured()),
            factors=("transaction_volume", "loss_per_event"),
            result_unit="AUD",
        )
        e = m.exposure()
        self.assertEqual(e.status, NOT_MEASURED)
        self.assertIsNone(e.amount)
        self.assertIn("loss_per_event", e.blocked_by)

    def test_the_blocked_figure_is_never_computed_at_all(self):
        """Not computed-then-suppressed. A number that exists gets quoted."""
        m = ValueModel(
            inputs=(_measured(), _unmeasured()),
            factors=("transaction_volume", "loss_per_event"),
            result_unit="AUD",
        )
        self.assertNotIn("24800", str(m.exposure().to_dict()))
        self.assertNotIn("24800", m.render())

    def test_the_refusal_names_the_missing_input(self):
        m = ValueModel(
            inputs=(_measured(), _unmeasured()),
            factors=("transaction_volume", "loss_per_event"),
            result_unit="AUD",
        )
        self.assertIn("loss_per_event", m.exposure().render())

    def test_a_measured_volume_is_still_reported_on_its_own(self):
        """Refusing the product must not suppress the honest input. The
        62 is real and the customer should see it."""
        m = ValueModel(
            inputs=(_measured(), _unmeasured()),
            factors=("transaction_volume", "loss_per_event"),
            result_unit="AUD",
        )
        text = m.render()
        self.assertIn("62 events", text)
        self.assertIn("MEASURED", text)
        self.assertIn("loss_per_event: NOT MEASURED", text)


class TestTheWeakestInputGoverns(unittest.TestCase):
    def test_measured_times_estimated_is_not_measured_strength(self):
        m = ValueModel(inputs=(_measured(), _estimated()),
                       factors=("transaction_volume", "loss_per_event"),
                       result_unit="AUD")
        e = m.exposure()
        self.assertEqual(e.amount, 24800.0)
        self.assertEqual(e.status, "ESTIMATED")

    def test_measured_times_customer_reported_is_customer_reported(self):
        cr = ValueInput(name="loss_per_event", unit="AUD",
                        status="CUSTOMER_REPORTED", amount=400.0,
                        source="stated by the operator on 2026-08-20")
        m = ValueModel(inputs=(_measured(), cr),
                       factors=("transaction_volume", "loss_per_event"),
                       result_unit="AUD")
        self.assertEqual(m.exposure().status, "CUSTOMER_REPORTED")

    def test_measured_times_measured_stays_measured(self):
        """Positive control: the rule must not punish a real measurement."""
        second = ValueInput(name="loss_per_event", unit="AUD", status="MEASURED",
                            amount=400.0, source="the 62 matching Stripe charges")
        m = ValueModel(inputs=(_measured(), second),
                       factors=("transaction_volume", "loss_per_event"),
                       result_unit="AUD")
        e = m.exposure()
        self.assertEqual(e.status, "MEASURED")
        self.assertEqual(e.amount, 24800.0)

    def test_a_range_factor_forces_a_range_result(self):
        rng = ValueInput(name="loss_per_event", unit="AUD",
                         status="RANGE_ESTIMATED", amount=300.0,
                         amount_high=500.0,
                         assumption="cheapest and dearest affected plan")
        e = ValueModel(inputs=(_measured(), rng),
                       factors=("transaction_volume", "loss_per_event"),
                       result_unit="AUD").exposure()
        self.assertEqual(e.status, "RANGE_ESTIMATED")
        self.assertEqual((e.amount, e.amount_high), (18600.0, 31000.0))

    def test_a_range_cannot_be_narrowed_by_a_stronger_sibling(self):
        """A MEASURED factor must not collapse a range into a point."""
        rng = ValueInput(name="loss_per_event", unit="AUD",
                         status="RANGE_ESTIMATED", amount=300.0,
                         amount_high=500.0, assumption="plan spread")
        e = ValueModel(inputs=(_measured(), rng),
                       factors=("transaction_volume", "loss_per_event"),
                       result_unit="AUD").exposure()
        self.assertIsNotNone(e.amount_high)
        self.assertNotEqual(e.amount, e.amount_high)

    def test_validated_realized_does_not_upgrade_its_weaker_sibling(self):
        vr = ValueInput(name="recovered_per_event", unit="AUD",
                        status="VALIDATED_REALIZED", amount=400.0,
                        source="400 refunded per case, observed after the fix")
        m = ValueModel(inputs=(_estimated(name="events_affected", amount=10.0,
                                          unit="events"), vr),
                       factors=("events_affected", "recovered_per_event"),
                       result_unit="AUD")
        self.assertEqual(m.exposure().status, "ESTIMATED")


class TestTheRenderedFigureCarriesItsStatus(unittest.TestCase):
    def test_a_figure_is_never_rendered_bare(self):
        m = ValueModel(inputs=(_measured(), _estimated()),
                       factors=("transaction_volume", "loss_per_event"),
                       result_unit="AUD")
        text = m.exposure().render()
        self.assertIn("24800", text)
        self.assertIn("ESTIMATED", text)

    def test_the_assumption_travels_with_the_number(self):
        m = ValueModel(inputs=(_measured(), _estimated()),
                       factors=("transaction_volume", "loss_per_event"),
                       result_unit="AUD")
        self.assertIn("mean order value", m.exposure().render())

    def test_an_empty_model_reports_not_measured_without_error(self):
        """'VALUE: NOT MEASURED' is a successful execution, not a failure."""
        e = ValueModel().exposure()
        self.assertEqual(e.status, NOT_MEASURED)
        self.assertEqual(e.render(), "NOT MEASURED")
        self.assertFalse(e.is_measured())


class TestTheDerivationItselfIsReviewable(unittest.TestCase):
    def test_a_factor_that_is_not_a_declared_input_is_refused(self):
        """Otherwise the fabrication hides in the derivation, where no
        reviewer looks."""
        with self.assertRaises(ValueIntegrityError) as ctx:
            ValueModel(inputs=(_measured(),),
                       factors=("transaction_volume", "ghost_multiplier"),
                       result_unit="AUD")
        self.assertIn("not an input", str(ctx.exception))

    def test_a_product_must_state_its_result_unit(self):
        with self.assertRaises(ValueIntegrityError):
            ValueModel(inputs=(_measured(), _estimated()),
                       factors=("transaction_volume", "loss_per_event"))

    def test_duplicate_inputs_are_refused(self):
        with self.assertRaises(ValueIntegrityError):
            ValueModel(inputs=(_measured(), _measured()))

    def test_the_model_is_immutable(self):
        m = ValueModel(inputs=(_measured(),))
        with self.assertRaises(FrozenInstanceError):
            m.factors = ("transaction_volume",)

    def test_it_carries_no_price_surface(self):
        """What the defect costs the customer, never what we charge."""
        m = ValueModel(inputs=(_measured(),))
        surface = set(m.to_dict()) | {f for f in dir(m) if not f.startswith("_")}
        for forbidden in ("price", "fee", "quote", "rate_card", "product_id",
                          "discount", "invoice"):
            self.assertNotIn(forbidden, surface)


class TestDerivedValueIsHonestOnItsOwn(unittest.TestCase):
    def test_a_derived_value_can_be_built_unmeasured(self):
        d = DerivedValue(status=NOT_MEASURED, unit="AUD")
        self.assertFalse(d.is_measured())
        self.assertIsNone(d.amount)

    def test_serialisation_is_deterministic(self):
        m = ValueModel(inputs=(_measured(), _estimated()),
                       factors=("transaction_volume", "loss_per_event"),
                       result_unit="AUD")
        self.assertEqual(m.to_dict(), m.to_dict())


if __name__ == "__main__":
    unittest.main()
