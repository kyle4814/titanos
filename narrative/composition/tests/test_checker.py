"""
Tests for narrative/composition/checker.py --
TRANSMISSION_DIGESTION_CONTINUITY_001's Cross-Atom Law.

Uses yaml.safe_load on real fixture text already established as real,
non-synthetic input in narrative/tests/test_real_ingestion_recursion_
guard.py (NA-INGEST-001/002) for the valid-relation proof, plus
minimal synthetic dicts for the dangling/self-reference boundary
cases -- mirroring rpa/composition/tests/test_checker.py's exact
pattern.
"""

import hashlib
import unittest

import yaml

from narrative.composition.checker import check_atom_relations

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
  source_reference: "commit 93b3e89"
  source_type: FAILURE_REPORT
  raw_fragment: "{FRAGMENT_1}"
  domain: "software_engineering/recursion_safety"
  epistemic_layer: VERIFIED_FACT
  evidence_status: VERIFIED_FACT
  confidence: HIGH
  uncertainty: "none beyond the reported run's own scope"
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
  uncertainty: "bounds one proven failure path"
  harm_risk: NONE
  provenance_hash: "sha256:{hashlib.sha256(FRAGMENT_2.encode()).hexdigest()}"
  promotion_status: RAW
  related_atoms:
    - "NA-INGEST-001"
"""


def _atom(atom_id, related_atoms=None, contradictions=None):
    doc = {"narrative_atom": {"id": atom_id}}
    if related_atoms is not None:
        doc["narrative_atom"]["related_atoms"] = related_atoms
    if contradictions is not None:
        doc["narrative_atom"]["contradictions"] = contradictions
    return doc


class TestRealRelationIsIntact(unittest.TestCase):
    def test_real_ingest_002_related_atoms_resolves(self):
        """NA-INGEST-002.related_atoms == ['NA-INGEST-001'] is real,
        already-established data (narrative/tests/test_real_ingestion_
        recursion_guard.py) -- the exact reference this cycle's own
        recon found nothing resolving. Proven intact here for the
        first time."""
        atom_1 = yaml.safe_load(ATOM_1_YAML)
        atom_2 = yaml.safe_load(ATOM_2_YAML)
        report = check_atom_relations([atom_1, atom_2])
        self.assertEqual(report.verdict, "INTACT")
        self.assertEqual(report.findings, [])


class TestDanglingReferencesRefused(unittest.TestCase):
    def test_related_atoms_dangling_ref_is_refused(self):
        atom = _atom("NA-X", related_atoms=["NA-DOES-NOT-EXIST"])
        report = check_atom_relations([atom])
        self.assertEqual(report.verdict, "REFUSED")
        self.assertTrue(any(f.check == "related_atoms_dangling_ref" for f in report.findings))
        self.assertIn("NA-DOES-NOT-EXIST", report.findings[0].involved_ids)

    def test_contradictions_dangling_ref_is_refused(self):
        atom = _atom("NA-X", contradictions=["NA-DOES-NOT-EXIST"])
        report = check_atom_relations([atom])
        self.assertEqual(report.verdict, "REFUSED")
        self.assertTrue(any(f.check == "contradictions_dangling_ref" for f in report.findings))

    def test_multiple_broken_references_all_reported_not_just_first(self):
        atom = _atom("NA-X", related_atoms=["NA-NOPE-1"], contradictions=["NA-NOPE-2"])
        report = check_atom_relations([atom])
        self.assertEqual(report.verdict, "REFUSED")
        self.assertEqual(len(report.findings), 2)


class TestSelfReferenceRefused(unittest.TestCase):
    def test_related_atoms_self_reference_is_refused(self):
        atom = _atom("NA-X", related_atoms=["NA-X"])
        report = check_atom_relations([atom])
        self.assertEqual(report.verdict, "REFUSED")
        self.assertTrue(any(f.check == "related_atoms_self_reference" for f in report.findings))

    def test_contradictions_self_reference_is_refused(self):
        atom = _atom("NA-X", contradictions=["NA-X"])
        report = check_atom_relations([atom])
        self.assertEqual(report.verdict, "REFUSED")
        self.assertTrue(any(f.check == "contradictions_self_reference" for f in report.findings))


class TestValidCrossReferenceIsIntact(unittest.TestCase):
    def test_two_atoms_referencing_each_other_is_intact(self):
        a = _atom("NA-A", related_atoms=["NA-B"])
        b = _atom("NA-B", related_atoms=["NA-A"])
        report = check_atom_relations([a, b])
        self.assertEqual(report.verdict, "INTACT")


class TestNoRelationDoesNotPromoteEitherAtom(unittest.TestCase):
    def test_intact_relation_reports_no_promotion_claim(self):
        """A checked, resolved relation is a structural fact, never
        evidence either atom's content is correct -- this checker's
        Finding/Report types carry no epistemic_layer, confidence, or
        promotion field at all, structurally incapable of asserting one."""
        a = _atom("NA-A", related_atoms=["NA-B"])
        b = _atom("NA-B")
        report = check_atom_relations([a, b])
        self.assertEqual(report.verdict, "INTACT")
        self.assertNotIn("epistemic_layer", report.to_dict())
        self.assertNotIn("promotion_status", report.to_dict())


class TestPartialInputsDoNotFalsePositive(unittest.TestCase):
    def test_no_documents_at_all_is_intact(self):
        report = check_atom_relations([])
        self.assertEqual(report.verdict, "INTACT")
        self.assertEqual(report.findings, [])

    def test_atom_with_no_related_atoms_field_is_intact(self):
        report = check_atom_relations([_atom("NA-X")])
        self.assertEqual(report.verdict, "INTACT")


class TestDeterminism(unittest.TestCase):
    def test_repeated_check_is_deterministic(self):
        atom = _atom("NA-X", related_atoms=["NA-NOPE"])
        r1 = check_atom_relations([atom])
        r2 = check_atom_relations([atom])
        self.assertEqual(r1.to_dict(), r2.to_dict())


if __name__ == "__main__":
    unittest.main()
