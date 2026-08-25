"""
Second real narrative ingestion (not synthetic test data) — companion to
`test_real_ingestion_recursion_guard.py`'s NA-INGEST-001/002.

INPUT (real, from `FIRST_PING.md`'s two closed exchanges, 2026-08-25/26):
the actual GitHub Actions CI result for run 32852929273, and this
repository's actual commit history on `kyle4814/titanos` between
2026-08-25T13:12:02Z and 2026-08-25T16:08:56Z, both retrieved via `gh`
against the real, live, public repository — not authored content.

TWO ATOMS, for the same reason `test_real_ingestion_recursion_guard.py`
used two: NA-EXCHANGE-001 is the specific, directly-observed proof event
(one CI run, VERIFIED_FACT). NA-EXCHANGE-002 is the broader claim
inferred FROM it (a repeated pattern of green CI across 13 commits,
EVIDENCE_SUPPORTED_MODEL — one afternoon's evidence, not a long-term
reliability claim, named explicitly in its own `uncertainty` field).
`related_atoms` on NA-EXCHANGE-002 points back at NA-EXCHANGE-001,
exercised for real by `narrative.composition.checker.check_atom_relations()`
here for the first time against genuinely new content, not the
pre-existing NA-INGEST-001/002 fixtures.
"""

import hashlib
import unittest

import yaml

from narrative.validators.validate_narrative_atom import validate_narrative_atom
from narrative.composition.checker import check_atom_relations

FRAGMENT_1 = (
    "GitHub Actions run 32852929273 (workflow 'tests', push to "
    "kyle4814/titanos@bc2230b) completed with conclusion=success across "
    "all 8 subsystem jobs."
)
FRAGMENT_2 = (
    "13 commits pushed to kyle4814/titanos master between "
    "2026-08-25T13:12:02Z and 2026-08-25T16:08:56Z, all authored by this "
    "session, all with CI green -- generalising NA-EXCHANGE-001's single "
    "proof event into a repeated pattern."
)

ATOM_1_YAML = f"""
narrative_atom:
  id: "NA-EXCHANGE-001"
  timestamp: "2026-08-25T13:22:22+00:00"
  source_reference: "https://github.com/kyle4814/titanos/actions/runs/32852929273"
  source_type: TECHNICAL_KNOWLEDGE
  raw_fragment: "{FRAGMENT_1}"
  domain: "software_engineering/ci_verification"
  epistemic_layer: VERIFIED_FACT
  evidence_status: VERIFIED_FACT
  confidence: HIGH
  uncertainty: "none beyond this run's own scope"
  harm_risk: NONE
  provenance_hash: "sha256:{hashlib.sha256(FRAGMENT_1.encode()).hexdigest()}"
  promotion_status: RAW
"""

ATOM_2_YAML = f"""
narrative_atom:
  id: "NA-EXCHANGE-002"
  timestamp: "2026-08-25T16:08:56+00:00"
  source_reference: "https://github.com/kyle4814/titanos/commits/master"
  source_type: TECHNICAL_KNOWLEDGE
  raw_fragment: "{FRAGMENT_2}"
  domain: "software_engineering/ci_verification"
  epistemic_layer: EVIDENCE_SUPPORTED_MODEL
  evidence_status: EVIDENCE_SUPPORTED_MODEL
  confidence: MEDIUM
  uncertainty: "one repository's commit history over a few hours; not yet a claim about long-term reliability"
  harm_risk: NONE
  provenance_hash: "sha256:{hashlib.sha256(FRAGMENT_2.encode()).hexdigest()}"
  promotion_status: RAW
  related_atoms:
    - "NA-EXCHANGE-001"
"""


class TestRealExchangeAtomsValidate(unittest.TestCase):
    def test_atom_1_valid(self):
        result = validate_narrative_atom(ATOM_1_YAML)
        self.assertEqual(result.status, "VALID", result.issues)

    def test_atom_2_valid(self):
        result = validate_narrative_atom(ATOM_2_YAML)
        self.assertEqual(result.status, "VALID", result.issues)


class TestRealExchangeAtomRelationIntegrity(unittest.TestCase):
    """First real (non-fixture) exercise of check_atom_relations() —
    NA-EXCHANGE-002's related_atoms correctly resolves to NA-EXCHANGE-001
    within the same real-content set."""

    def test_related_atoms_resolves(self):
        docs = [yaml.safe_load(ATOM_1_YAML), yaml.safe_load(ATOM_2_YAML)]
        report = check_atom_relations(docs)
        self.assertEqual(report.verdict, "INTACT", report.findings)

    def test_dangling_reference_is_still_caught_against_real_content(self):
        """Negative control: drop NA-EXCHANGE-001 from the supplied set --
        NA-EXCHANGE-002's related_atoms reference must be refused."""
        docs = [yaml.safe_load(ATOM_2_YAML)]
        report = check_atom_relations(docs)
        self.assertEqual(report.verdict, "REFUSED")
        self.assertTrue(any(
            f.check == "related_atoms_dangling_ref" for f in report.findings
        ))


if __name__ == "__main__":
    unittest.main()
