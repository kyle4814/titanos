"""Tests for narrative/schema/narrative_atom.py's state machine and
record-mapping — the parts that aren't exercised by the validator tests."""

import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from narrative.schema.narrative_atom import (  # noqa: E402
    PROMOTION_TRANSITIONS, PROMOTION_STATES, can_promote,
    RECORD_FOR_EPISTEMIC_LAYER, record_for_epistemic_layer, FIVE_RECORDS,
    EPISTEMIC_LAYERS,
)
from kpm.schemas.epistemic_types import ALL_CLASSIFICATIONS  # noqa: E402


class TestStateMachineCoverage(unittest.TestCase):
    def test_every_declared_state_has_a_transitions_entry(self):
        for state in PROMOTION_STATES:
            self.assertIn(state, PROMOTION_TRANSITIONS, state)

    def test_no_transition_targets_an_undeclared_state(self):
        for src, targets in PROMOTION_TRANSITIONS.items():
            for t in targets:
                self.assertIn(t, PROMOTION_STATES, f"{src} -> {t}")


class TestNoBypassToCanon(unittest.TestCase):
    """The doctrine's normal evidentiary path is RAW -> ... -> SUPPORTED
    -> CANONICAL_ABSTRACTION. No shortcut should exist."""

    def test_only_supported_reaches_canonical_abstraction(self):
        reaching = [s for s, t in PROMOTION_TRANSITIONS.items()
                   if "CANONICAL_ABSTRACTION" in t]
        self.assertEqual(reaching, ["SUPPORTED"])

    def test_raw_cannot_jump_directly_to_canonical_abstraction(self):
        self.assertFalse(can_promote("RAW", "CANONICAL_ABSTRACTION"))

    def test_quarantined_cannot_jump_directly_to_canonical_abstraction(self):
        self.assertFalse(can_promote("QUARANTINED", "CANONICAL_ABSTRACTION"))

    def test_symbolic_cannot_jump_directly_to_canonical_abstraction(self):
        self.assertFalse(can_promote("SYMBOLIC", "CANONICAL_ABSTRACTION"))


class TestCanonicalIsNotEternal(unittest.TestCase):
    """Doctrine, verbatim: 'CANONICAL DOES NOT MEAN ETERNAL.'"""

    def test_canonical_abstraction_can_be_challenged_again(self):
        self.assertTrue(can_promote("CANONICAL_ABSTRACTION", "CHALLENGED"))

    def test_canonical_abstraction_is_not_a_dead_end(self):
        self.assertNotEqual(PROMOTION_TRANSITIONS["CANONICAL_ABSTRACTION"], frozenset())


class TestUnknownIsAlwaysReachableFromEveryNonTerminalState(unittest.TestCase):
    """'The Unknown Record is a first-class output, never artificially
    emptied' — operationalized as: every state that isn't already UNKNOWN
    (or a state whose entire purpose is to be more specific than unknown,
    like RAW/OBSERVED which are pre-classification) can route to UNKNOWN."""

    def test_most_states_can_reach_unknown(self):
        exempt = {"UNKNOWN"}  # unknown doesn't need an edge to itself
        for state in PROMOTION_STATES - exempt - {"RAW", "OBSERVED"}:
            self.assertTrue(can_promote(state, "UNKNOWN"), state)


class TestRecordMapping(unittest.TestCase):
    def test_every_epistemic_layer_maps_to_a_declared_record(self):
        for layer in ALL_CLASSIFICATIONS:
            record = record_for_epistemic_layer(layer)
            self.assertIn(record, FIVE_RECORDS, f"{layer} -> {record}")

    def test_verified_fact_maps_to_observation(self):
        self.assertEqual(record_for_epistemic_layer("VERIFIED_FACT"), "OBSERVATION")

    def test_symbolic_doctrine_maps_to_symbolic_record(self):
        self.assertEqual(record_for_epistemic_layer("SYMBOLIC_DOCTRINE"), "SYMBOLIC")

    def test_personal_experience_maps_to_human_record(self):
        self.assertEqual(record_for_epistemic_layer("PERSONAL_EXPERIENCE"), "HUMAN")

    def test_unrecognised_layer_defaults_to_unknown_record_not_observation(self):
        """Fail-closed: an unmapped layer must never default to the
        highest-trust record."""
        self.assertEqual(record_for_epistemic_layer("SOMETHING_NEW"), "UNKNOWN")


class TestEpistemicLayerReusesRealVocabulary(unittest.TestCase):
    def test_epistemic_layers_is_literally_the_kpm_set(self):
        self.assertEqual(EPISTEMIC_LAYERS, ALL_CLASSIFICATIONS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
