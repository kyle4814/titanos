"""The system must never grade its own homework and call it calibration.

Every test here tries to make an outcome claim more than the world said,
or to let the system learn a fact after the decision and pretend it knew.
"""

import unittest
from dataclasses import replace

import tempfile
from pathlib import Path

from foundation.outcome_ledger import (
    EXTERNALLY_EVIDENCED_STATES,
    OutcomeIntegrityError,
    LedgerTampered,
    OutcomeLedger,
    OutcomeRecord,
    PreActionContext,
    TERMINAL_UNOBSERVED,
    Witness,
    freeze_pre_action,
)


def _led():
    """Isolated ledger. Tests must never share the default on-disk path --
    records would accumulate across tests and across runs."""
    return OutcomeLedger(ledger_path=Path(tempfile.mkdtemp()) / "l.jsonl")


def _ctx(**kw):
    base = dict(target="acme/widget", target_established_by="SOURCE_NATIVE",
                facts={"gravity": 1300, "convergences": 2, "hands": 3,
                       "span_days": 5.5},
                unknowns=("whether the ask is already claimed",))
    base.update(kw)
    return freeze_pre_action(**base)


def _witness(**kw):
    base = dict(observed_by="the maintainer of acme/widget",
                mechanism="replied on the issue thread",
                what_was_observed="said the reproduction was correct")
    base.update(kw)
    return Witness(**base)


class TestNoTimeTravel(unittest.TestCase):
    """The sealed envelope. Written before the world answers, never after."""

    def test_a_context_is_content_addressed(self):
        a, b = _ctx(), _ctx()
        self.assertEqual(a.context_id, b.context_id)
        self.assertTrue(a.context_id.startswith("PA-"))
        self.assertTrue(a.is_intact())

    def test_M_altering_a_sealed_context_is_detectable(self):
        ctx = _ctx()
        tampered = replace(ctx, facts={"gravity": 99999})
        self.assertFalse(tampered.is_intact())
        self.assertNotEqual(tampered.digest(), ctx.digest())

    def test_M_the_ledger_refuses_a_tampered_context(self):
        led = _led()
        with self.assertRaises(OutcomeIntegrityError) as c:
            led.seal(replace(_ctx(), facts={"gravity": 99999}))
        self.assertIn("altered after", str(c.exception))

    def test_M_a_sealed_context_cannot_be_replaced_by_a_different_one(self):
        """The substitution this whole design exists to prevent."""
        led = _led()
        ctx = _ctx()
        led.seal(ctx)
        forged = PreActionContext(
            context_id=ctx.context_id, target="acme/widget",
            target_established_by="SOURCE_NATIVE",
            facts={"gravity": 99999}, unknowns=())
        with self.assertRaises(OutcomeIntegrityError):
            led.seal(forged)

    def test_an_id_cannot_be_assigned_by_hand(self):
        with self.assertRaises(OutcomeIntegrityError) as c:
            PreActionContext(context_id="whatever-i-like", target="a/b",
                             target_established_by="SOURCE_NATIVE", facts={})
        self.assertIn("content-derived", str(c.exception))

    def test_M_an_outcome_cannot_edit_what_we_knew(self):
        """Recording a result leaves the sealed belief byte-identical."""
        led = _led()
        ctx = _ctx()
        before = ctx.digest()
        rec = led.record("GB-abc", ctx, "VALUE_WITNESSED", _witness())
        after = led.context_for(rec)
        self.assertEqual(after.digest(), before)
        self.assertEqual(dict(after.facts)["gravity"], 1300)

    def test_the_context_records_when_it_was_frozen(self):
        self.assertTrue(_ctx().frozen_at)


class TestSilenceIsNotFailure(unittest.TestCase):
    def test_M_unobserved_states_are_not_negative_results(self):
        led = _led()
        for state in TERMINAL_UNOBSERVED:
            r = led.record("GB-abc", _ctx(), state)
            self.assertTrue(r.is_unobserved(), state)
            self.assertFalse(r.is_negative(), state)
            self.assertFalse(r.counts_as_external_evidence(), state)

    def test_only_an_identifiable_human_saying_no_is_a_no(self):
        led = _led()
        r = led.record("GB-abc", _ctx(), "DECLINED",
                       _witness(what_was_observed="said it is out of scope"))
        self.assertTrue(r.is_negative())
        self.assertFalse(r.is_unobserved())

    def test_not_observed_and_declined_are_different_facts(self):
        led = _led()
        silent = led.record("GB-a", _ctx(), "NOT_OBSERVED")
        refused = led.record("GB-b", _ctx(), "DECLINED", _witness(
            what_was_observed="closed as wontfix"))
        self.assertNotEqual(silent.state, refused.state)
        self.assertNotEqual(silent.is_negative(), refused.is_negative())


class TestTheSystemCannotWitnessItself(unittest.TestCase):
    def test_M_value_witnessed_requires_a_witness(self):
        led = _led()
        with self.assertRaises(OutcomeIntegrityError) as c:
            led.record("GB-abc", _ctx(), "VALUE_WITNESSED")
        self.assertIn("evidence about a server", str(c.exception))

    def test_M_every_externally_evidenced_state_requires_one(self):
        led = _led()
        for state in EXTERNALLY_EVIDENCED_STATES:
            with self.assertRaises(OutcomeIntegrityError, msg=state):
                led.record("GB-abc", _ctx(), state)

    def test_M_this_system_cannot_name_itself_as_the_witness(self):
        """'TitanOS observed that TitanOS created value' is not evidence."""
        for name in ("TitanOS", "Demonblade", "Claude", "the system",
                     "internal", "the model"):
            with self.assertRaises(OutcomeIntegrityError, msg=name):
                Witness(observed_by=name, mechanism="looked at it",
                        what_was_observed="it was good")

    def test_a_witness_must_say_how_it_was_observed(self):
        for missing in ("observed_by", "mechanism", "what_was_observed"):
            with self.assertRaises(OutcomeIntegrityError):
                _witness(**{missing: "   "})

    def test_a_real_external_witness_is_accepted(self):
        """Positive control: the discipline must not make evidence
        impossible, only unearned."""
        led = _led()
        r = led.record("GB-abc", _ctx(), "VALUE_WITNESSED", _witness())
        self.assertTrue(r.counts_as_external_evidence())
        self.assertIn("maintainer", r.witness.observed_by)


class TestTransportIsNotValue(unittest.TestCase):
    def test_M_platform_acceptance_is_not_value_witnessed(self):
        """A machine accepting a request says nothing about a human."""
        led = _led()
        r = led.record("GB-abc", _ctx(), "ACCEPTED_BY_PLATFORM")
        self.assertNotEqual(r.state, "VALUE_WITNESSED")
        self.assertFalse(r.counts_as_external_evidence())
        self.assertIsNone(r.witness)

    def test_M_transport_is_not_in_the_externally_evidenced_set(self):
        """Asserted directly, so promoting it convicts as a FAILURE rather
        than incidentally raising somewhere else."""
        self.assertNotIn("ACCEPTED_BY_PLATFORM", EXTERNALLY_EVIDENCED_STATES)
        self.assertNotIn("DELIVERY_ATTEMPTED", EXTERNALLY_EVIDENCED_STATES)
        for state in EXTERNALLY_EVIDENCED_STATES:
            self.assertIn(state, ("HUMAN_RESPONDED", "VALUE_WITNESSED",
                                  "VALUE_REALIZED", "CASH_REALIZED",
                                  "DECLINED"), state)

    def test_platform_acceptance_needs_no_witness_because_it_claims_nothing(self):
        led = _led()
        self.assertEqual(
            led.record("GB-abc", _ctx(), "ACCEPTED_BY_PLATFORM").state,
            "ACCEPTED_BY_PLATFORM")

    def test_the_ladder_keeps_every_rung_separate(self):
        from foundation.outcome_ledger import OUTCOME_STATES
        for a, b in (("DELIVERY_ATTEMPTED", "ACCEPTED_BY_PLATFORM"),
                     ("ACCEPTED_BY_PLATFORM", "HUMAN_RESPONDED"),
                     ("HUMAN_RESPONDED", "VALUE_WITNESSED"),
                     ("VALUE_WITNESSED", "VALUE_REALIZED"),
                     ("VALUE_REALIZED", "CASH_REALIZED")):
            self.assertIn(a, OUTCOME_STATES)
            self.assertIn(b, OUTCOME_STATES)
            self.assertNotEqual(a, b)


class TestTheOutcomeMustAttachToSomething(unittest.TestCase):
    def test_M_an_outcome_must_name_its_artifact(self):
        with self.assertRaises(OutcomeIntegrityError) as c:
            OutcomeRecord(outcome_id="OC-1", brick_id="  ",
                          pre_action_id="PA-abc", state="PENDING")
        self.assertIn("cannot calibrate anything", str(c.exception))

    def test_M_an_outcome_must_reference_a_sealed_context(self):
        with self.assertRaises(OutcomeIntegrityError) as c:
            OutcomeRecord(outcome_id="OC-1", brick_id="GB-abc",
                          pre_action_id="just-a-string", state="PENDING")
        self.assertIn("nothing to compare", str(c.exception))

    def test_an_unknown_state_is_refused(self):
        with self.assertRaises(OutcomeIntegrityError):
            OutcomeRecord(outcome_id="OC-1", brick_id="GB-abc",
                          pre_action_id="PA-abc", state="WENT_GREAT")


class TestTheLedgerIsAppendOnly(unittest.TestCase):
    def test_there_is_no_delete_or_update_surface(self):
        surface = {m for m in dir(OutcomeLedger) if not m.startswith("_")}
        for banned in ("delete", "remove", "update", "edit", "clear", "pop",
                       "set_state", "amend"):
            self.assertNotIn(banned, surface)

    def test_a_correction_supersedes_rather_than_overwrites(self):
        led = _led()
        ctx = _ctx()
        first = led.record("GB-abc", ctx, "NOT_OBSERVED")
        second = led.record("GB-abc", ctx, "HUMAN_RESPONDED", _witness(),
                            supersedes=first.outcome_id)
        self.assertEqual(len(led.outcomes_for_brick("GB-abc")), 2)
        self.assertEqual(led.current_for_brick("GB-abc").outcome_id,
                         second.outcome_id)
        # ...and the original is still there.
        self.assertIn(first, led.all_records())

    def test_pairs_give_belief_then_result_never_the_reverse(self):
        led = _led()
        led.record("GB-a", _ctx(), "NOT_OBSERVED")
        led.record("GB-b", _ctx(target="other/thing"), "VALUE_WITNESSED",
                   _witness())
        pairs = led.pairs()
        self.assertEqual(len(pairs), 2)
        for context, outcome in pairs:
            self.assertTrue(context.is_intact())
            self.assertEqual(outcome.pre_action_id, context.context_id)

    def test_a_brick_with_no_outcome_reports_none_not_a_failure(self):
        self.assertIsNone(_led().current_for_brick("GB-never"))


if __name__ == "__main__":
    unittest.main()


class TestDurabilityAcrossTheProcessBoundary(unittest.TestCase):
    """Calibration needs outcomes to ACCUMULATE. A dataset held only in
    memory cannot accumulate past a process exit, which made the stated
    bottleneck -- outcome volume -- unreachable by construction."""

    def setUp(self):
        self.path = Path(tempfile.mkdtemp()) / "l.jsonl"

    def test_M_records_survive_a_new_ledger_over_the_same_file(self):
        a = OutcomeLedger(ledger_path=self.path)
        ctx = _ctx()
        a.record("GB-abc", ctx, "ACCEPTED_BY_PLATFORM")
        a.record("GB-abc", ctx, "NOT_OBSERVED", note="nobody replied")

        b = OutcomeLedger(ledger_path=self.path)      # a fresh process
        self.assertEqual(len(b.outcomes_for_brick("GB-abc")), 2)
        self.assertEqual(b.current_for_brick("GB-abc").state, "NOT_OBSERVED")

    def test_M_the_sealed_context_survives_reload_intact(self):
        a = OutcomeLedger(ledger_path=self.path)
        ctx = _ctx()
        a.record("GB-abc", ctx, "NOT_OBSERVED")
        b = OutcomeLedger(ledger_path=self.path)
        reloaded = b.context_for(b.all_records()[0])
        self.assertIsNotNone(reloaded)
        self.assertTrue(reloaded.is_intact())
        self.assertEqual(reloaded.context_id, ctx.context_id)
        self.assertEqual(dict(reloaded.facts)["gravity"], 1300)

    def test_M_tampering_with_a_sealed_context_on_disk_is_caught(self):
        """The no-time-travel guarantee is worthless if it holds in memory
        and not across the process boundary."""
        a = OutcomeLedger(ledger_path=self.path)
        a.record("GB-abc", _ctx(), "NOT_OBSERVED")
        raw = self.path.read_text()
        self.path.write_text(raw.replace('"gravity": 1300', '"gravity": 99999'))
        with self.assertRaises(LedgerTampered) as c:
            OutcomeLedger(ledger_path=self.path)
        self.assertIn("has been altered", str(c.exception))

    def test_a_truncated_trailing_write_loses_only_that_record(self):
        """A crash mid-append must never force destructive manual
        recovery of the whole dataset."""
        a = OutcomeLedger(ledger_path=self.path)
        ctx = _ctx()
        a.record("GB-abc", ctx, "ACCEPTED_BY_PLATFORM")
        a.record("GB-abc", ctx, "NOT_OBSERVED")
        raw = self.path.read_text()
        self.path.write_text(raw[:-25])          # simulate a killed process
        try:
            b = OutcomeLedger(ledger_path=self.path)
        except Exception as exc:                 # noqa: BLE001 -- the point
            self.fail(f"a truncated trailing write must not abort the whole "
                      f"ledger; that forces destructive manual recovery and "
                      f"silently resets the dataset. Raised: {exc!r}")
        self.assertGreaterEqual(len(b.all_records()), 1)
        self.assertTrue(b.pairs())

    def test_pairs_survive_reload_so_calibration_can_accumulate(self):
        a = OutcomeLedger(ledger_path=self.path)
        a.record("GB-a", _ctx(), "NOT_OBSERVED")
        a.record("GB-b", _ctx(target="other/thing"), "VALUE_WITNESSED",
                 _witness())
        b = OutcomeLedger(ledger_path=self.path)
        pairs = b.pairs()
        self.assertEqual(len(pairs), 2)
        for context, outcome in pairs:
            self.assertTrue(context.is_intact())
            self.assertEqual(outcome.pre_action_id, context.context_id)

    def test_an_in_memory_only_ledger_is_still_possible(self):
        """Passing None keeps the old behaviour for callers that genuinely
        want a scratch ledger -- tests, dry runs."""
        led = OutcomeLedger(ledger_path=None)
        led.record("GB-abc", _ctx(), "NOT_OBSERVED")
        self.assertEqual(len(led.all_records()), 1)

    def test_a_witness_survives_the_round_trip(self):
        a = OutcomeLedger(ledger_path=self.path)
        a.record("GB-abc", _ctx(), "VALUE_WITNESSED", _witness())
        b = OutcomeLedger(ledger_path=self.path)
        w = b.all_records()[0].witness
        self.assertIsNotNone(w)
        self.assertIn("maintainer", w.observed_by)
        self.assertTrue(w.mechanism)
