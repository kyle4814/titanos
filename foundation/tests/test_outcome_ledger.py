"""The system must never grade its own homework and call it calibration.

Every test here tries to make an outcome claim more than the world said,
or to let the system learn a fact after the decision and pretend it knew.
"""

import json
import unittest
from dataclasses import replace

import tempfile
from pathlib import Path

from foundation.outcome_ledger import (
    CHAIN_UNVERIFIED_LEGACY,
    CHAIN_VERIFIED,
    EXTERNALLY_EVIDENCED_STATES,
    OUTCOME_STATES,
    OutcomeIntegrityError,
    LedgerTampered,
    OutcomeLedger,
    OutcomeRecord,
    PreActionContext,
    TERMINAL_UNOBSERVED,
    Witness,
    freeze_pre_action,
    _DEFAULT_LEDGER_PATH,
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


class TestDisprovenIsItsOwnState(unittest.TestCase):
    """A killing experiment's verdict must not collapse into a neighbour.

    Added when the radar first positively excluded a target before any
    approach was made. NOT_OBSERVED would have understated it (the world
    was not silent -- it answered clearly), and DECLINED would have
    overstated it (nobody refused us; no contact was ever made).
    """

    def test_disproven_is_a_declared_state(self):
        self.assertIn("DISPROVEN", OUTCOME_STATES)

    def test_disproven_needs_no_witness(self):
        """It is our own finding about a public artifact, not a claim
        about what a person did, so it must not sit behind the witness
        requirement that guards the externally-evidenced states."""
        self.assertNotIn("DISPROVEN", EXTERNALLY_EVIDENCED_STATES)

    def test_disproven_is_not_confusable_with_its_neighbours(self):
        for other in ("NOT_OBSERVED", "DECLINED", "UNKNOWN"):
            self.assertNotEqual("DISPROVEN", other)

    def test_disproven_records_without_a_witness(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = OutcomeLedger(Path(d) / "l.jsonl")
            ctx = freeze_pre_action(
                target="acme/widget", target_established_by="SOURCE_NATIVE",
                facts={"verdict": "excluded"},
                disqualifiers=("contributor-onboarding programme",))
            rec = ledger.record(brick_id="KE-1", context=ctx,
                                state="DISPROVEN")
            self.assertEqual(rec.state, "DISPROVEN")
            self.assertIsNone(rec.witness)


def _read_lines(path: Path) -> list[str]:
    return [ln for ln in path.read_text().splitlines() if ln.strip()]


def _write_lines(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n")


class TestHashChainDetectsDeletionAndReordering(unittest.TestCase):
    """The actual gap this feature closes. Before it, each record only
    content-addressed itself -- deleting or reordering a whole LINE left
    every surviving line individually self-consistent, and replay would
    silently reconstruct a shorter or reordered history. Every case here
    proves the chain, not just the per-record digest, is what changed."""

    def setUp(self):
        self.path = Path(tempfile.mkdtemp()) / "l.jsonl"

    def _four_line_ledger(self) -> OutcomeLedger:
        """One sealed context plus three outcomes -- four chained lines,
        enough to have a genuine middle to delete or swap."""
        led = OutcomeLedger(ledger_path=self.path)
        ctx = _ctx()
        led.record("GB-a", ctx, "NOT_OBSERVED")
        led.record("GB-a", ctx, "ACCEPTED_BY_PLATFORM")
        led.record("GB-a", ctx, "HUMAN_RESPONDED", _witness())
        return led

    def test_M_deleting_a_middle_line_is_detected(self):
        self._four_line_ledger()
        lines = _read_lines(self.path)
        self.assertEqual(len(lines), 4)
        del lines[1]                       # remove the first OUTCOME line
        _write_lines(self.path, lines)
        with self.assertRaises(LedgerTampered) as c:
            OutcomeLedger(ledger_path=self.path)
        msg = str(c.exception)
        self.assertIn("line", msg)
        self.assertTrue(any(w in msg for w in ("deleted", "reordered")))

    def test_M_deleting_the_last_middle_line_before_the_tail_is_detected(self):
        """Distinct from the truncated-final-line case: this deletion
        still leaves a well-formed final line, so it must be caught by the
        chain check, not mistaken for a crash artifact."""
        self._four_line_ledger()
        lines = _read_lines(self.path)
        del lines[2]                       # remove the middle OUTCOME line
        _write_lines(self.path, lines)
        with self.assertRaises(LedgerTampered):
            OutcomeLedger(ledger_path=self.path)

    def test_M_reordering_two_lines_is_detected(self):
        self._four_line_ledger()
        lines = _read_lines(self.path)
        lines[1], lines[2] = lines[2], lines[1]     # swap two middle lines
        _write_lines(self.path, lines)
        with self.assertRaises(LedgerTampered) as c:
            OutcomeLedger(ledger_path=self.path)
        self.assertIn("line", str(c.exception))

    def test_M_mutating_an_outcome_records_content_is_detected(self):
        """`is_intact()` only ever covered PreActionContext. An OUTCOME
        line's own content had no self-check before the chain existed."""
        self._four_line_ledger()
        lines = _read_lines(self.path)
        obj = json.loads(lines[1])
        self.assertEqual(obj["kind"], "OUTCOME")
        obj["note"] = "this note was never written by the ledger"
        lines[1] = json.dumps(obj, sort_keys=True)
        _write_lines(self.path, lines)
        with self.assertRaises(LedgerTampered) as c:
            OutcomeLedger(ledger_path=self.path)
        self.assertIn("altered in place", str(c.exception))

    def test_a_truncated_final_line_still_degrades_gracefully(self):
        """A genuine crash artifact (killed mid-append) must not raise --
        that is a different failure mode from tampering in the middle."""
        self._four_line_ledger()
        raw = self.path.read_text()
        self.path.write_text(raw[:-20])    # simulate a killed process
        try:
            reloaded = OutcomeLedger(ledger_path=self.path)
        except Exception as exc:           # noqa: BLE001 -- the point
            self.fail(f"a truncated trailing write must not raise; it is a "
                      f"crash artifact, not tampering. Raised: {exc!r}")
        self.assertGreaterEqual(len(reloaded.all_records()), 2)

    def test_round_trip_write_reload_all_chain_verified(self):
        led = self._four_line_ledger()
        outcome_ids = [r.outcome_id for r in led.all_records()]
        self.assertEqual(len(outcome_ids), 3)
        for oid in outcome_ids:
            self.assertEqual(led.chain_status(oid), CHAIN_VERIFIED)

        reloaded = OutcomeLedger(ledger_path=self.path)
        self.assertEqual(len(reloaded.all_records()), 3)
        for oid in outcome_ids:
            self.assertEqual(reloaded.chain_status(oid), CHAIN_VERIFIED)
        for ctx, _ in reloaded.pairs():
            self.assertEqual(reloaded.chain_status(ctx.context_id),
                             CHAIN_VERIFIED)


class TestLegacyUnchainedLedgerStillLoads(unittest.TestCase):
    """The real on-disk ledger predates this feature and has no hash
    fields at all. It must keep loading, and must never be reported as
    chain-verified merely because loading did not raise."""

    # A FRESH CLONE HAS NO LEDGER, AND THAT IS A VALID STATE.
    #
    # `foundation/outcome_ledger.jsonl` is gitignored on purpose -- it is
    # machine-local operational history, and .gitignore says so in as many
    # words: "a fresh clone correctly reports these logs as 'never fired
    # yet'". These two tests nonetheless asserted the file was present, so
    # they could only pass on a machine that had already run the system.
    #
    # That is why CI was red for at least eight consecutive commits while
    # every local run reported green. The tests were not measuring the
    # ledger's behaviour; they were measuring whether they were running on
    # Kyle's laptop. The claim they exist to defend is already proven
    # environment-independently by
    # `test_a_synthetic_legacy_file_loads_and_reports_unverifiable` below.
    #
    # So both states are now asserted rather than one being assumed: with a
    # ledger, the legacy records must load and report UNVERIFIED_LEGACY;
    # without one, construction must still succeed and report zero records
    # rather than raising. Skipping would have hidden the second case,
    # which is the case a new contributor actually hits first.

    def test_the_real_repository_ledger_loads_without_raising(self):
        try:
            led = OutcomeLedger(ledger_path=_DEFAULT_LEDGER_PATH)
        except Exception as exc:           # noqa: BLE001 -- the point
            self.fail(f"the pre-existing, unchained ledger must still load. "
                      f"Raised: {exc!r}")
        if not _DEFAULT_LEDGER_PATH.exists():
            self.assertEqual(
                len(led.all_records()), 0,
                "a fresh clone has no ledger; it must report empty, not "
                "fabricate records")
            return
        self.assertGreater(len(led.all_records()), 0)

    def test_a_legacy_record_is_reported_unverifiable_not_verified(self):
        led = OutcomeLedger(ledger_path=_DEFAULT_LEDGER_PATH)
        if not _DEFAULT_LEDGER_PATH.exists():
            self.assertEqual(len(led.all_records()), 0)
            self.assertEqual(len(list(led.pairs())), 0)
            return
        self.assertGreater(len(led.all_records()), 0)
        for record in led.all_records():
            self.assertEqual(led.chain_status(record.outcome_id),
                             CHAIN_UNVERIFIED_LEGACY)
        for ctx, _ in led.pairs():
            self.assertEqual(led.chain_status(ctx.context_id),
                             CHAIN_UNVERIFIED_LEGACY)

    def test_a_synthetic_legacy_file_loads_and_reports_unverifiable(self):
        """Same claim as above, but on a throwaway file this test controls
        end to end, independent of whatever the real ledger currently
        contains."""
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "legacy.jsonl"
            ctx = _ctx()
            legacy_context = {
                "kind": "CONTEXT", "context_id": ctx.context_id,
                "target": ctx.target,
                "target_established_by": ctx.target_established_by,
                "facts": dict(ctx.facts), "unknowns": list(ctx.unknowns),
                "disqualifiers": list(ctx.disqualifiers),
                "frozen_at": ctx.frozen_at}
            legacy_outcome = {
                "kind": "OUTCOME", "outcome_id": "OC-legacy1",
                "brick_id": "GB-legacy", "pre_action_id": ctx.context_id,
                "state": "NOT_OBSERVED", "note": "", "recorded_at": "x",
                "supersedes": None, "witness": None}
            _write_lines(path, [
                json.dumps(legacy_context, sort_keys=True),
                json.dumps(legacy_outcome, sort_keys=True)])

            led = OutcomeLedger(ledger_path=path)
            self.assertEqual(len(led.all_records()), 1)
            self.assertEqual(led.chain_status(ctx.context_id),
                             CHAIN_UNVERIFIED_LEGACY)
            self.assertEqual(led.chain_status("OC-legacy1"),
                             CHAIN_UNVERIFIED_LEGACY)

    def test_appending_after_legacy_records_works_and_chains_from_there(self):
        """The chain cannot retroactively cover unhashed history -- it
        must start clean (previous_hash="") right after it, not refuse to
        start at all."""
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "legacy.jsonl"
            ctx = _ctx()
            legacy_outcome = {
                "kind": "OUTCOME", "outcome_id": "OC-legacy1",
                "brick_id": "GB-legacy", "pre_action_id": ctx.context_id,
                "state": "NOT_OBSERVED", "note": "", "recorded_at": "x",
                "supersedes": None, "witness": None}
            legacy_context = {
                "kind": "CONTEXT", "context_id": ctx.context_id,
                "target": ctx.target,
                "target_established_by": ctx.target_established_by,
                "facts": dict(ctx.facts), "unknowns": list(ctx.unknowns),
                "disqualifiers": list(ctx.disqualifiers),
                "frozen_at": ctx.frozen_at}
            _write_lines(path, [
                json.dumps(legacy_context, sort_keys=True),
                json.dumps(legacy_outcome, sort_keys=True)])

            led = OutcomeLedger(ledger_path=path)
            new_rec = led.record("GB-new", ctx, "ACCEPTED_BY_PLATFORM")

            # The freshly appended line chains cleanly...
            self.assertEqual(led.chain_status(new_rec.outcome_id),
                             CHAIN_VERIFIED)
            # ...while the legacy lines are still honestly unverifiable.
            self.assertEqual(led.chain_status("OC-legacy1"),
                             CHAIN_UNVERIFIED_LEGACY)

            # And a fresh process reloading the whole file must not raise
            # -- legacy lines followed by one real chained line is exactly
            # the shape this feature is required to tolerate.
            reloaded = OutcomeLedger(ledger_path=path)
            self.assertEqual(len(reloaded.all_records()), 2)
            self.assertEqual(reloaded.chain_status(new_rec.outcome_id),
                             CHAIN_VERIFIED)
            self.assertEqual(reloaded.chain_status("OC-legacy1"),
                             CHAIN_UNVERIFIED_LEGACY)

            # The new line's own previous_hash on disk is "" -- it cannot
            # chain to hashless history, so it honestly starts fresh.
            written = json.loads(_read_lines(path)[-1])
            self.assertEqual(written["previous_hash"], "")


class TestReplaySafety(unittest.TestCase):
    """A retry must not double a real-world fact.

    Found by a replay-safety audit and reproduced before the fix:
    `record()` minted `outcome_id` from the wall clock and the record
    count, so calling it twice with identical arguments appended two
    permanent, independently-chained records of one event -- silently
    doubling a fact in the dataset the system calibrates against.

    The fix is opt-in on purpose. Two observations of the same brick at
    different times ARE two facts; only a caller knows whether it is
    looking again or retrying.
    """

    def _ledger(self, d):
        return OutcomeLedger(ledger_path=Path(d) / "l.jsonl")

    def _ctx(self):
        return freeze_pre_action(target="acme/w",
                                 target_established_by="SOURCE_NATIVE",
                                 facts={"k": "v"})

    def test_a_declared_retry_returns_the_original_record(self):
        with tempfile.TemporaryDirectory() as d:
            L = self._ledger(d); ctx = self._ctx()
            a = L.record("B", ctx, "NOT_OBSERVED", operation_id="OP-1")
            b = L.record("B", ctx, "NOT_OBSERVED", operation_id="OP-1")
            self.assertEqual(a.outcome_id, b.outcome_id)
            self.assertEqual(len(L.all_records()), 1)

    def test_a_second_genuine_observation_is_still_two_facts(self):
        """The half that keeps the fix honest. Collapsing these would
        destroy the silence-versus-absence distinction."""
        with tempfile.TemporaryDirectory() as d:
            L = self._ledger(d); ctx = self._ctx()
            L.record("B", ctx, "NOT_OBSERVED")
            L.record("B", ctx, "NOT_OBSERVED")
            self.assertEqual(len(L.all_records()), 2)

    def test_the_guarantee_survives_a_process_restart(self):
        """An in-memory-only index would evaporate at exactly the moment
        a retry is most likely -- after a crash."""
        with tempfile.TemporaryDirectory() as d:
            ctx = self._ctx()
            first = self._ledger(d).record("B", ctx, "NOT_OBSERVED",
                                           operation_id="OP-2")
            reloaded = self._ledger(d)
            again = reloaded.record("B", ctx, "NOT_OBSERVED",
                                    operation_id="OP-2")
            self.assertEqual(first.outcome_id, again.outcome_id)
            self.assertEqual(len(reloaded.all_records()), 1)

    def test_different_operation_ids_are_different_facts(self):
        with tempfile.TemporaryDirectory() as d:
            L = self._ledger(d); ctx = self._ctx()
            L.record("B", ctx, "NOT_OBSERVED", operation_id="OP-A")
            L.record("B", ctx, "NOT_OBSERVED", operation_id="OP-B")
            self.assertEqual(len(L.all_records()), 2)

    def test_a_witnessed_retry_does_not_double_a_human_attestation(self):
        """The sharpest case: an externally-evidenced state retried with
        the same witness must not become two independent 'a human said
        so' facts."""
        with tempfile.TemporaryDirectory() as d:
            L = self._ledger(d); ctx = self._ctx()
            w = Witness(observed_by="a.person", mechanism="email",
                        what_was_observed="they replied and declined")
            a = L.record("B", ctx, "DECLINED", witness=w, operation_id="OP-3")
            b = L.record("B", ctx, "DECLINED", witness=w, operation_id="OP-3")
            self.assertEqual(a.outcome_id, b.outcome_id)
            self.assertEqual(len(L.all_records()), 1)
