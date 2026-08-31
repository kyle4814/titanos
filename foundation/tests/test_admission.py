"""A queue is proven by what it refuses, not by what it accepts.

Throughput is a capacity measurement and never a truth signal. Every test
here tries to make the loading dock accept work it has not earned, or to
let a count of admissions start standing in for value.
"""

import unittest

from foundation.admission import (
    AdmissionLedger,
    AdmissionRefused,
    AdmittedWork,
    TERMINAL_STATES,
    WORK_STATES,
    WorkIntegrityError,
    can_transition,
    work_identity,
)


class _Mission:
    """Duck-typed stand-in with exactly the fields InvestigationMission has.

    Clearly synthetic. The real object is exercised in the live section.
    """

    def __init__(self, target="acme/widget",
                 question="build it and run the reproduction",
                 stops=("the behaviour is already fixed at HEAD",),
                 disqualifiers=(), unknowns=("licence unread",),
                 opportunity_id="OPP-1", classification="SOURCE_NATIVE"):
        self.target = target
        self.next_cheapest_experiment = question
        self.stop_conditions = stops
        self.disqualifiers = disqualifiers
        self.unknowns = unknowns
        self.opportunity_id = opportunity_id
        self.classification = classification


class TestTheGateRefuses(unittest.TestCase):
    def test_M_a_mission_with_no_bounded_question_is_refused(self):
        with self.assertRaises(AdmissionRefused) as c:
            AdmissionLedger().admit(_Mission(question="   "))
        self.assertEqual(c.exception.reason, "NO_BOUNDED_QUESTION")

    def test_M_a_mission_that_cannot_end_is_refused(self):
        """Work that cannot end is work that eats days."""
        with self.assertRaises(AdmissionRefused) as c:
            AdmissionLedger().admit(_Mission(stops=()))
        self.assertEqual(c.exception.reason, "NO_STOP_CONDITION")
        self.assertIn("when to walk away", c.exception.detail)

    def test_M_a_disqualified_mission_is_refused(self):
        with self.assertRaises(AdmissionRefused) as c:
            AdmissionLedger().admit(
                _Mission(disqualifiers=("SECURITY_SENSITIVE",)))
        self.assertEqual(c.exception.reason, "DISQUALIFIED")

    def test_M_the_same_question_twice_is_a_duplicate(self):
        led = AdmissionLedger()
        led.admit(_Mission())
        with self.assertRaises(AdmissionRefused) as c:
            led.admit(_Mission())
        self.assertEqual(c.exception.reason, "DUPLICATE")

    def test_M_already_concluded_work_is_not_silently_requeued(self):
        led = AdmissionLedger()
        w = led.admit(_Mission())
        led.claim(w.work_id, "demonblade")
        led.conclude(w.work_id, "DISPROVEN")
        with self.assertRaises(AdmissionRefused) as c:
            led.admit(_Mission())
        self.assertEqual(c.exception.reason, "ALREADY_CONCLUDED")
        self.assertIn("needs new evidence", c.exception.detail)

    def test_a_refusal_always_carries_a_canonical_reason(self):
        with self.assertRaises(WorkIntegrityError):
            AdmissionRefused("BECAUSE_I_SAID_SO", "no")

    def test_a_genuinely_different_question_on_one_target_is_admitted(self):
        """Positive control: a repository can honestly support several
        investigations, and collapsing them would refuse real work."""
        led = AdmissionLedger()
        a = led.admit(_Mission(question="run the reproduction"))
        b = led.admit(_Mission(question="check whether the fix compiles"))
        self.assertNotEqual(a.work_id, b.work_id)

    def test_identity_ignores_presentation_not_meaning(self):
        self.assertEqual(work_identity("Acme/Widget", "Run  The Test"),
                         work_identity("acme/widget", "run the test"))
        self.assertNotEqual(work_identity("a/b", "x"),
                            work_identity("a/b", "y"))


class TestClaimingPreventsDoubleWork(unittest.TestCase):
    def test_M_the_same_work_cannot_be_claimed_twice(self):
        led = AdmissionLedger()
        w = led.admit(_Mission())
        led.claim(w.work_id, "investigator-a")
        with self.assertRaises(AdmissionRefused) as c:
            led.claim(w.work_id, "investigator-b")
        self.assertEqual(c.exception.reason, "DUPLICATE")
        self.assertIn("investigator-a", c.exception.detail)

    def test_a_claim_must_name_who(self):
        led = AdmissionLedger()
        w = led.admit(_Mission())
        with self.assertRaises(WorkIntegrityError):
            led.claim(w.work_id, "  ")

    def test_claiming_unknown_work_is_refused(self):
        with self.assertRaises(WorkIntegrityError):
            AdmissionLedger().claim("WU-nope", "someone")

    def test_open_work_excludes_concluded_units(self):
        led = AdmissionLedger()
        a = led.admit(_Mission(question="q1"))
        b = led.admit(_Mission(question="q2"))
        led.claim(a.work_id, "x")
        led.conclude(a.work_id, "DISPROVEN")
        open_ids = {w.work_id for w in led.open_work()}
        self.assertIn(b.work_id, open_ids)
        self.assertNotIn(a.work_id, open_ids)


class TestTerminalFactsStaySeparate(unittest.TestCase):
    def test_M_disproven_is_a_productive_output_not_a_failure(self):
        led = AdmissionLedger()
        w = led.admit(_Mission())
        led.claim(w.work_id, "demonblade")
        done = led.conclude(w.work_id, "DISPROVEN")
        self.assertTrue(done.is_terminal())
        self.assertFalse(done.produced_value())
        self.assertNotIn("FAILED", WORK_STATES)

    def test_every_terminal_fact_is_distinguishable(self):
        for state in ("DISPROVEN", "EVIDENCE_INSUFFICIENT", "AMBIGUOUS",
                      "WITHHELD", "SECURITY_SENSITIVE",
                      "HUMAN_REVIEW_REQUIRED", "QUALIFIED"):
            self.assertIn(state, TERMINAL_STATES)
        self.assertEqual(len(set(TERMINAL_STATES)), len(TERMINAL_STATES))

    def test_M_only_qualified_counts_as_value(self):
        """The one place a throughput count could start lying."""
        led = AdmissionLedger()
        for i, state in enumerate(("DISPROVEN", "EVIDENCE_INSUFFICIENT",
                                   "AMBIGUOUS", "WITHHELD")):
            w = led.admit(_Mission(question=f"q{i}"))
            led.claim(w.work_id, "x")
            self.assertFalse(led.conclude(w.work_id, state).produced_value())

    def test_M_qualified_requires_the_receipt_that_qualified_it(self):
        led = AdmissionLedger()
        w = led.admit(_Mission())
        led.claim(w.work_id, "x")
        with self.assertRaises(WorkIntegrityError) as c:
            led.conclude(w.work_id, "QUALIFIED")
        self.assertIn("cannot promote itself", str(c.exception))

    def test_qualified_with_a_receipt_is_accepted(self):
        led = AdmissionLedger()
        w = led.admit(_Mission())
        led.claim(w.work_id, "x")
        done = led.conclude(w.work_id, "QUALIFIED", receipt_id="R-1")
        self.assertTrue(done.produced_value())
        self.assertEqual(done.receipt_id, "R-1")


class TestTheStateMachineIsATable(unittest.TestCase):
    def test_M_work_cannot_skip_claiming(self):
        led = AdmissionLedger()
        w = led.admit(_Mission())
        with self.assertRaises(WorkIntegrityError) as c:
            led.conclude(w.work_id, "DISPROVEN")
        self.assertIn("illegal transition", str(c.exception))

    def test_M_a_terminal_state_is_final(self):
        led = AdmissionLedger()
        w = led.admit(_Mission())
        led.claim(w.work_id, "x")
        led.conclude(w.work_id, "DISPROVEN")
        with self.assertRaises(WorkIntegrityError):
            led.conclude(w.work_id, "QUALIFIED", receipt_id="R-1")

    def test_illegal_transitions_are_absent_from_the_table_not_if_checked(self):
        for state in TERMINAL_STATES:
            self.assertFalse(can_transition(state, "CLAIMED"), state)
            self.assertFalse(can_transition(state, "ADMITTED"), state)
        self.assertFalse(can_transition("ADMITTED", "QUALIFIED"))
        self.assertTrue(can_transition("ADMITTED", "CLAIMED"))


class TestNoTimeTravelAndNoOrphans(unittest.TestCase):
    def test_M_admitted_work_must_reference_a_sealed_context(self):
        with self.assertRaises(WorkIntegrityError) as c:
            AdmittedWork(work_id="WU-1", target="a/b", question="q",
                         state="ADMITTED", pre_action_id="not-sealed")
        self.assertIn("sealed pre-action context", str(c.exception))

    def test_the_sealed_context_survives_every_transition(self):
        led = AdmissionLedger()
        w = led.admit(_Mission(), facts={"gravity": 1300, "hands": 3})
        sealed = led.context_for(w.work_id)
        led.claim(w.work_id, "x")
        led.conclude(w.work_id, "QUALIFIED", receipt_id="R-1")
        after = led.context_for(w.work_id)
        self.assertEqual(after.context_id, sealed.context_id)
        self.assertTrue(after.is_intact())
        self.assertEqual(dict(after.facts)["gravity"], 1300)

    def test_M_a_brick_cannot_attach_to_unqualified_work(self):
        """Second, independent refusal of the payload-without-receipt
        collapse that gold_brick.py already refuses."""
        led = AdmissionLedger()
        w = led.admit(_Mission())
        led.claim(w.work_id, "x")
        led.conclude(w.work_id, "DISPROVEN")
        with self.assertRaises(WorkIntegrityError) as c:
            led.attach_brick(w.work_id, "GB-abc")
        self.assertIn("not a brick", str(c.exception))

    def test_a_brick_attaches_to_qualified_work(self):
        led = AdmissionLedger()
        w = led.admit(_Mission())
        led.claim(w.work_id, "x")
        led.conclude(w.work_id, "QUALIFIED", receipt_id="R-1")
        linked = led.attach_brick(w.work_id, "GB-abc")
        self.assertEqual(linked.brick_id, "GB-abc")
        self.assertEqual(linked.receipt_id, "R-1")


class TestThroughputIsNotValue(unittest.TestCase):
    def test_the_ledger_is_append_only(self):
        surface = {m for m in dir(AdmissionLedger) if not m.startswith("_")}
        for banned in ("delete", "remove", "update", "edit", "clear", "pop"):
            self.assertNotIn(banned, surface)

    def test_M_there_is_no_headline_throughput_number(self):
        """A factory optimises whatever single number it is shown."""
        led = AdmissionLedger()
        w = led.admit(_Mission())
        report = led.capacity_report()
        self.assertIsInstance(report, dict)
        for banned in ("total", "score", "rate", "ratio", "per_day",
                       "success_rate", "bricks_per_day"):
            self.assertNotIn(banned, report)

    def test_capacity_counts_states_not_achievements(self):
        led = AdmissionLedger()
        a = led.admit(_Mission(question="q1"))
        led.admit(_Mission(question="q2"))
        led.claim(a.work_id, "x")
        led.conclude(a.work_id, "DISPROVEN")
        report = led.capacity_report()
        self.assertEqual(report.get("DISPROVEN"), 1)
        self.assertEqual(report.get("ADMITTED"), 1)

    def test_history_is_preserved_not_overwritten(self):
        led = AdmissionLedger()
        w = led.admit(_Mission())
        led.claim(w.work_id, "x")
        led.conclude(w.work_id, "DISPROVEN")
        states = [r.state for r in led.history_for(w.work_id)]
        self.assertEqual(states, ["ADMITTED", "CLAIMED", "DISPROVEN"])


if __name__ == "__main__":
    unittest.main()
