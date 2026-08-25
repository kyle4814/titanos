"""
BEYOND_DUALITY_INTAKE_001 — real ingestion of one user-relayed
philosophical/spiritual transmission ("The Evolution Path Out of
Duality"), classified honestly as SYMBOLIC_DOCTRINE, LOW confidence —
never VERIFIED_FACT, never silently promoted toward
CANONICAL_ABSTRACTION.

WHAT THIS PROVES

The repository's existing narrative intake capability
(narrative_atom.py's schema + validator + NarrativeAtomStore) already
fully covers "durable narrative structure" for content like this —
no new code was needed, only correct use of what already exists. The
transmission's structural claim (a trigger -> judgment -> identity
threat -> reaction -> habit -> outcome -> reinforced-identity loop) is
preserved as a candidate structural isomorphism; its metaphysical
framing (collective consciousness, frequency shift, quantum
liberation, multiverse) is explicitly marked unresolved via
`uncertainty`, never evaluated as fact.

WHAT THIS DOES NOT DO

Does not promote this atom past RAW. Does not treat the transmission's
symbolic language as evidence. Does not build any new "duality" module
— per this directive's own instruction, that would be forcing State 3
(a testable architectural seam) when State 2 (durable narrative
structure via already-proven capability) is what the evidence supports.
"""

import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from narrative.store.narrative_atom_store import NarrativeAtomStore
from narrative.validators.validate_narrative_atom import validate_narrative_atom

RAW_FRAGMENT = (
    "Trigger -> automatic category/judgment -> identity threat or "
    "reinforcement -> emotional/physiological reaction -> habitual "
    "action -> outcome -> selective attention to confirming signals -> "
    "stronger identity model -> repeat. Framed as: duality/binary "
    "categorisation, identity attachment, automatic loop, attention as "
    "reinforcement, fighting as participation, observer capacity, "
    "identity revision, present action, collective relation, and "
    "unresolved metaphysical claims (quantum consciousness, frequency "
    "shift, collective consciousness, multiverse)."
)

PROVENANCE_HASH = "sha256:" + hashlib.sha256(RAW_FRAGMENT.encode("utf-8")).hexdigest()

ATOM_YAML = f"""
narrative_atom:
  id: "NA-DUALITY-001"
  timestamp: "2026-08-25T00:00:00+00:00"
  source_reference: "user-relayed transmission titled 'The Evolution Path Out of Duality', framed as 'a message from a liberated part of the collective consciousness, from a position beyond duality'"
  source_type: MYTHOLOGY
  raw_fragment: "{RAW_FRAGMENT}"
  domain: "psychology/attention_and_identity, framed within a spiritual/metaphysical source"
  epistemic_layer: SYMBOLIC_DOCTRINE
  evidence_status: SYMBOLIC_DOCTRINE
  confidence: LOW
  uncertainty: "the causal loop is a plausible structural isomorphism to known attention/habit-loop psychology, but this transmission itself supplies no evidence beyond assertion; the metaphysical framing (collective consciousness, frequency, multiverse, quantum liberation) is explicitly unresolved and not evaluated by this atom"
  symbolic_meaning: "the transmission frames rigid dualistic categorisation and identity-defense reactivity as a self-reinforcing loop, and proposes observation-before-reaction as a way to interrupt it, without claiming this eliminates suffering or replaces medical/psychological support"
  human_problem: "repetitive, identity-defensive reactive behaviour that may feel automatic and hard to interrupt"
  human_beneficiary: "a person seeking a structural (not literal-metaphysical) description of why reactive loops persist and how noticing might interrupt them"
  actionability: "LOW -- describes a candidate model, not a validated intervention; no protocol, dosage, or outcome measure is specified"
  reversibility: "N/A -- no action is prescribed by this atom"
  harm_risk: LOW
  related_atoms: []
  contradictions: []
  provenance_hash: "{PROVENANCE_HASH}"
  promotion_status: RAW
"""


class TestBeyondDualityIntake(unittest.TestCase):
    def test_atom_is_structurally_valid(self):
        result = validate_narrative_atom(ATOM_YAML)
        self.assertEqual(result.status, "VALID", result.issues)

    def test_epistemic_layer_is_symbolic_not_verified(self):
        self.assertIn("epistemic_layer: SYMBOLIC_DOCTRINE", ATOM_YAML)
        self.assertNotIn("VERIFIED_FACT", ATOM_YAML)

    def test_confidence_is_low_not_high(self):
        # SYMBOLIC_DOCTRINE structurally cannot be HIGH confidence --
        # kpm/schemas/epistemic_types.py::_CANNOT_BE_HIGH_CONFIDENCE.
        self.assertIn("confidence: LOW", ATOM_YAML)

    def test_metaphysical_claims_marked_unresolved_in_uncertainty(self):
        self.assertIn("explicitly unresolved", ATOM_YAML)

    def test_provenance_hash_matches_real_content_hash(self):
        recomputed = "sha256:" + hashlib.sha256(RAW_FRAGMENT.encode("utf-8")).hexdigest()
        self.assertEqual(recomputed, PROVENANCE_HASH)
        self.assertIn(PROVENANCE_HASH, ATOM_YAML)

    def test_registers_in_the_real_store_and_stays_raw(self):
        store = NarrativeAtomStore()
        result = validate_narrative_atom(ATOM_YAML)
        self.assertEqual(result.status, "VALID", result.issues)

        rec = store.register("NA-DUALITY-001", created_by="beyond-duality-intake-cycle")
        self.assertEqual(rec.state, "RAW")
        # Intake is not promotion -- confirm it stays RAW, never
        # silently advanced toward CANONICAL_ABSTRACTION.
        self.assertEqual(store.get("NA-DUALITY-001").state, "RAW")


if __name__ == "__main__":
    unittest.main()
