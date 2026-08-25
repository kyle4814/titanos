"""
JUDGMENT_PRESERVATION_002 -- proof that a real, reachable epistemic
collapse is closed.

FINDING: five append-only record dataclasses (kpm/schemas/
epistemic_types.py::Claim, narrative/store/narrative_atom_store.py::
AtomRecord, kpm/promotion/state_machine.py::PromotionRecord,
firewall/quarantine.py::QuarantineRecord, foundation/flow_switch.py::
FlowSwitchRecord) were plain mutable @dataclass types with a public
state/classification field. A caller holding a reference obtained from
any store's own get() method could bypass every guard
(reclassify()'s FORBIDDEN_TRANSITIONS/MissingEvidence,
promote()'s can_promote()/SelfCanonizationForbidden,
PromotionStore.promote()'s can_transition()/SelfPromotionForbidden,
QuarantineStore.transition()'s reviewed_by requirement,
FlowSwitchStore.transition()'s can_transition() including the
deliberately-absent SIGNAL_COLLAPSE exit edges) by simply assigning
the field directly -- reproduced for real before this fix, not
hypothesized. All five are now frozen dataclasses; the guarded
store/module functions use object.__setattr__ internally (the
standard, minimal escape hatch), so legitimate transitions are
unaffected and illegal direct mutation now raises
dataclasses.FrozenInstanceError.

NOT fixed (deliberately, named as a residual limitation, not silently
left unexamined): foundation/task_queue.py::Task.state has the same
theoretical shape, but Task also has attempts/result/failure_reason
mutated directly and routinely by task_queue.run() outside any guard
-- freezing it would require a materially larger refactor than any of
the five fixed here, none of which had non-guarded externally-mutated
fields.
"""

import dataclasses
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from firewall.quarantine import QuarantineStore
from foundation.flow_switch import FlowSwitchStore
from kpm.promotion.state_machine import PromotionStore, SelfPromotionForbidden
from kpm.schemas.epistemic_types import (
    ForbiddenTransition, MissingEvidence, classify_claim, reclassify,
)
from narrative.store.narrative_atom_store import (
    NarrativeAtomStore, SelfCanonizationForbidden,
)


class TestClaimImmutability(unittest.TestCase):
    def test_direct_classification_mutation_now_raises(self):
        c = classify_claim("c1", "x", "SPECULATIVE_HYPOTHESIS", "alice")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            c.classification = "VERIFIED_FACT"

    def test_forbidden_transition_still_blocked_via_guarded_path(self):
        c = classify_claim("c2", "x", "SPECULATIVE_HYPOTHESIS", "alice")
        with self.assertRaises(ForbiddenTransition):
            reclassify(c, "VERIFIED_FACT", "trying to escalate", "alice")

    def test_missing_evidence_still_blocked_via_guarded_path(self):
        c = classify_claim("c3", "x", "UNKNOWN", "alice")
        with self.assertRaises(MissingEvidence):
            reclassify(c, "VERIFIED_FACT", "no evidence supplied", "alice")

    def test_legitimate_reclassification_still_works(self):
        c = classify_claim("c4", "x", "UNKNOWN", "alice")
        reclassify(c, "VERIFIED_FACT", "found proof", "alice", evidence_refs=("doc-1",))
        self.assertEqual(c.classification, "VERIFIED_FACT")
        self.assertEqual(len(c.history), 2)


class TestAtomRecordImmutability(unittest.TestCase):
    def test_direct_state_mutation_now_raises(self):
        store = NarrativeAtomStore()
        rec = store.register("NA-IMMUT-1", created_by="bob")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            rec.state = "CANONICAL_ABSTRACTION"
        self.assertEqual(store.get("NA-IMMUT-1").state, "RAW")

    def test_self_canonization_still_blocked_via_guarded_path(self):
        store = NarrativeAtomStore()
        store.register("NA-IMMUT-2", created_by="bob")
        store.promote("NA-IMMUT-2", "CLASSIFIED", reason="x")
        store.promote("NA-IMMUT-2", "CONNECTED", reason="x")
        store.promote("NA-IMMUT-2", "CHALLENGED", reason="x")
        store.promote("NA-IMMUT-2", "TESTED", reason="x")
        store.promote("NA-IMMUT-2", "SUPPORTED", reason="x")
        with self.assertRaises(SelfCanonizationForbidden):
            store.promote("NA-IMMUT-2", "CANONICAL_ABSTRACTION", reason="x", reviewed_by="bob")

    def test_legitimate_promotion_still_works(self):
        store = NarrativeAtomStore()
        store.register("NA-IMMUT-3", created_by="bob")
        rec = store.promote("NA-IMMUT-3", "CLASSIFIED", reason="x")
        self.assertEqual(rec.state, "CLASSIFIED")


class TestPromotionRecordImmutability(unittest.TestCase):
    def test_direct_state_mutation_now_raises(self):
        store = PromotionStore()
        rec = store.register("bp-1", created_by="carol")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            rec.state = "STABLE"
        self.assertEqual(store.get("bp-1").state, "RAW")

    def test_self_promotion_still_blocked_via_guarded_path(self):
        store = PromotionStore()
        store.register("bp-2", created_by="carol")
        store.promote("bp-2", "DISTILLED", reason="x", created_by="carol")
        store.promote("bp-2", "PROVISIONAL", reason="x", created_by="carol")
        store.promote("bp-2", "TESTED", reason="x", created_by="carol")
        with self.assertRaises(SelfPromotionForbidden):
            store.promote("bp-2", "STABLE", reason="x", reviewed_by="carol", created_by="carol")


class TestQuarantineRecordImmutability(unittest.TestCase):
    def test_direct_state_mutation_now_raises(self):
        store = QuarantineStore()
        rec = store.quarantine(artifact_id="art-1", content="hello", reason="x", provenance={})
        with self.assertRaises(dataclasses.FrozenInstanceError):
            rec.state = "VERIFIED"
        self.assertEqual(store.get("art-1").state, "QUARANTINED")


class TestFlowSwitchRecordImmutability(unittest.TestCase):
    def test_direct_mode_mutation_now_raises(self):
        store = FlowSwitchStore()
        rec = store.start_session("sess-1", "NORMAL")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            rec.mode = "SIGNAL_COLLAPSE"
        self.assertEqual(store.get("sess-1").mode, "NORMAL")


class TestHistoryStillAppendsUnderFreezing(unittest.TestCase):
    """Confirms the fix did not accidentally break the append-only
    history list -- freezing blocks attribute REASSIGNMENT, not
    in-place mutation of a list an attribute already points to."""

    def test_history_list_grows_normally(self):
        store = NarrativeAtomStore()
        store.register("NA-IMMUT-HIST", created_by="bob")
        rec = store.promote("NA-IMMUT-HIST", "CLASSIFIED", reason="x")
        self.assertEqual(len(rec.history), 2)  # registered + this promotion


if __name__ == "__main__":
    unittest.main()
