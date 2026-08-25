"""
First real narrative ingestion (not synthetic test data).

INPUT (verbatim, supplied 2026-08-25): a report of the recursion-guard
incident and fix — compute_sigil()'s proof dimension recursively
forking without bound, discovered by watching process count climb past
50 forked `unittest` processes, fixed via foundation/recursion_guard.py,
proven by 37/37 targeted tests, 8/8 subsystem regression, zero orphaned
processes, commit 93b3e89.

TWO ATOMS, NOT ONE — because the input contains two genuinely different
epistemic claims that must not be collapsed together:

NA-INGEST-001 (VERIFIED_FACT): the specific, directly-observed proof
event — exact test counts, exact commit, exact process-residue result.
Nothing here is generalised.

NA-INGEST-002 (EVIDENCE_SUPPORTED_MODEL): the durable invariant
generalised FROM that proof event ("protected execution ancestry must
survive the process boundary..."). This is INFERRED from NA-INGEST-001,
not itself directly observed — a broader claim than the one proof event
can fully establish on its own, so it does not get VERIFIED_FACT status.
`related_atoms` points it back at NA-INGEST-001, and its own
`uncertainty` field carries the input's stated limitation (the guard
bounds the one proven failure path, not every possible cyclic execution
pattern) rather than inventing a third atom for it.

Neither atom is promoted past CLASSIFIED here. Reaching CONNECTED,
CHALLENGED, TESTED, or SUPPORTED requires the narrative promotion
process this ingestion run does not perform (cross-referencing other
atoms, independent challenge, etc.) — and CANONICAL_ABSTRACTION requires
review by someone other than the atom's creator, which a single
ingestion run structurally cannot provide. This test explicitly proves
that boundary holds rather than assuming it.
"""

import hashlib
import unittest

from narrative.store.narrative_atom_store import IllegalAtomTransition, NarrativeAtomStore
from narrative.validators.validate_narrative_atom import validate_narrative_atom

FRAGMENT_1 = (
    "compute_sigil() proof-dimension recursion bounded by execution-ancestry "
    "guard. 37/37 targeted tests passed. 8/8 subsystem regression suites "
    "passed. No persistent orphaned unittest processes remained. Commit 93b3e89."
)
FRAGMENT_2 = (
    "Durable invariant candidate: protected execution ancestry must survive "
    "the process boundary where recursive spawning can occur; re-entry of "
    "the same protected operation in active ancestry must be blocked before "
    "it can multiply descendant work."
)

ATOM_1_YAML = f"""
narrative_atom:
  id: "NA-INGEST-001"
  timestamp: "2026-08-25T00:00:00+00:00"
  source_reference: "commit 93b3e89, foundation/tests/test_recursion_guard.py, foundation/tests/test_sigil.py"
  source_type: FAILURE_REPORT
  raw_fragment: "{FRAGMENT_1}"
  domain: "software_engineering/recursion_safety"
  epistemic_layer: VERIFIED_FACT
  evidence_status: VERIFIED_FACT
  confidence: HIGH
  uncertainty: "none beyond the reported run's own scope (this repository, this commit)"
  harm_risk: NONE
  provenance_hash: "sha256:{hashlib.sha256(FRAGMENT_1.encode()).hexdigest()}"
  promotion_status: RAW
"""

ATOM_2_YAML = f"""
narrative_atom:
  id: "NA-INGEST-002"
  timestamp: "2026-08-25T00:00:00+00:00"
  source_reference: "inferred from NA-INGEST-001"
  source_type: TECHNICAL_KNOWLEDGE
  raw_fragment: "{FRAGMENT_2}"
  domain: "software_engineering/recursion_safety"
  epistemic_layer: EVIDENCE_SUPPORTED_MODEL
  evidence_status: EVIDENCE_SUPPORTED_MODEL
  confidence: MEDIUM
  uncertainty: "bounds the one proven recursive subprocess failure path; does not prove universal detection of every possible cyclic execution pattern outside protected operations and the implemented execution boundary"
  harm_risk: NONE
  provenance_hash: "sha256:{hashlib.sha256(FRAGMENT_2.encode()).hexdigest()}"
  promotion_status: RAW
  related_atoms:
    - "NA-INGEST-001"
"""


class TestRealIngestion(unittest.TestCase):
    def test_atom_1_validates_against_real_schema(self):
        result = validate_narrative_atom(ATOM_1_YAML)
        self.assertEqual(result.status, "VALID", result.issues)

    def test_atom_2_validates_against_real_schema(self):
        result = validate_narrative_atom(ATOM_2_YAML)
        self.assertEqual(result.status, "VALID", result.issues)

    def test_both_atoms_register_in_the_real_store(self):
        store = NarrativeAtomStore()
        rec1 = store.register("NA-INGEST-001", created_by="real-ingestion-run")
        rec2 = store.register("NA-INGEST-002", created_by="real-ingestion-run")
        self.assertEqual(rec1.state, "RAW")
        self.assertEqual(rec2.state, "RAW")

    def test_classification_promotion_is_inspectable(self):
        store = NarrativeAtomStore()
        store.register("NA-INGEST-001", created_by="real-ingestion-run")
        rec = store.promote("NA-INGEST-001", "OBSERVED", reason="proof event directly reported")
        rec = store.promote("NA-INGEST-001", "CLASSIFIED", reason="epistemic_layer=VERIFIED_FACT assigned")
        self.assertEqual(rec.state, "CLASSIFIED")
        self.assertEqual(len(rec.history), 3)  # register + OBSERVED + CLASSIFIED

    def test_promotion_to_canonical_abstraction_is_not_silently_granted(self):
        # This ingestion run has no independent reviewer -- proving that
        # the store genuinely refuses self-promotion, not merely that we
        # chose not to call promote() further.
        store = NarrativeAtomStore()
        store.register("NA-INGEST-002", created_by="real-ingestion-run")
        store.promote("NA-INGEST-002", "OBSERVED", reason="x")
        store.promote("NA-INGEST-002", "CLASSIFIED", reason="x")
        # CLASSIFIED cannot even reach CANONICAL_ABSTRACTION directly --
        # the transition table itself has no such edge.
        with self.assertRaises(IllegalAtomTransition):
            store.promote("NA-INGEST-002", "CANONICAL_ABSTRACTION",
                           reason="x", reviewed_by="someone-else")

    def test_history_remains_inspectable_after_classification(self):
        store = NarrativeAtomStore()
        store.register("NA-INGEST-001", created_by="real-ingestion-run")
        store.promote("NA-INGEST-001", "OBSERVED", reason="x")
        rec = store.get("NA-INGEST-001")
        self.assertEqual([h["to"] for h in rec.history], ["RAW", "OBSERVED"])

    def test_duplicate_ingestion_of_same_atom_id_rejected(self):
        store = NarrativeAtomStore()
        store.register("NA-INGEST-001", created_by="real-ingestion-run")
        with self.assertRaises(ValueError):
            store.register("NA-INGEST-001", created_by="second-attempt")


if __name__ == "__main__":
    unittest.main()
