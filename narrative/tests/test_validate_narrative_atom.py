"""Tests for narrative/validators/validate_narrative_atom.py."""

import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from narrative.validators.validate_narrative_atom import validate_narrative_atom  # noqa: E402

GOOD = """
narrative_atom:
  id: atom-001
  timestamp: "2026-08-25T00:00:00Z"
  source_reference: "session transcript, cosmic-library build log"
  source_type: TECHNICAL_KNOWLEDGE
  raw_fragment: "quarantine stores must never expose a delete method"
  normalized_claim: "append-only stores prevent silent evidence destruction"
  domain: software_architecture
  epistemic_layer: EVIDENCE_SUPPORTED_MODEL
  evidence_status: EVIDENCE_SUPPORTED_MODEL
  confidence: HIGH
  uncertainty: []
  harm_risk: NONE
  provenance_hash: "sha256:{}"
  promotion_status: TESTED
""".format("a" * 64)


class TestWellFormedAtomPasses(unittest.TestCase):
    def test_valid_atom(self):
        r = validate_narrative_atom(GOOD)
        self.assertEqual(r.status, "VALID", r.issues)


class TestMalformedYaml(unittest.TestCase):
    def test_broken_syntax(self):
        r = validate_narrative_atom("narrative_atom: [unclosed")
        self.assertEqual(r.status, "INVALID")
        self.assertEqual(r.issues[0].rule, "NA-R-1")

    def test_missing_wrapper_key(self):
        r = validate_narrative_atom("id: atom-001\n")
        self.assertEqual(r.status, "INVALID")
        self.assertEqual(r.issues[0].rule, "NA-R-2")

    def test_duplicate_key(self):
        text = GOOD + "\nid: atom-002\n"
        # duplicate at document root is fine (two different top-level docs
        # would be a YAML error only if same key repeated in same mapping) —
        # test duplicate WITHIN narrative_atom instead:
        text2 = GOOD.replace("id: atom-001", "id: atom-001\n  id: atom-002")
        r = validate_narrative_atom(text2)
        self.assertEqual(r.status, "INVALID")


class TestRequiredFields(unittest.TestCase):
    def test_missing_required_field(self):
        r = validate_narrative_atom("narrative_atom:\n  id: atom-001\n")
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "NA-R-4" for i in r.issues))


class TestEnums(unittest.TestCase):
    def test_bad_source_type(self):
        r = validate_narrative_atom(GOOD.replace("TECHNICAL_KNOWLEDGE", "NOT_A_TYPE"))
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "NA-R-5" for i in r.issues))

    def test_epistemic_layer_reuses_kpm_vocabulary(self):
        r = validate_narrative_atom(GOOD.replace("EVIDENCE_SUPPORTED_MODEL", "TOTALLY_MADE_UP", 1))
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "NA-R-6" for i in r.issues))

    def test_valid_epistemic_layer_from_real_kpm_set(self):
        from kpm.schemas.epistemic_types import ALL_CLASSIFICATIONS
        self.assertIn("VERIFIED_FACT", ALL_CLASSIFICATIONS)
        r = validate_narrative_atom(GOOD.replace("epistemic_layer: EVIDENCE_SUPPORTED_MODEL",
                                                  "epistemic_layer: VERIFIED_FACT"))
        self.assertEqual(r.status, "VALID", r.issues)

    def test_bad_promotion_status(self):
        r = validate_narrative_atom(GOOD.replace("promotion_status: TESTED", "promotion_status: MADE_UP"))
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "NA-R-7" for i in r.issues))

    def test_bad_confidence(self):
        r = validate_narrative_atom(GOOD.replace("confidence: HIGH", "confidence: SUPER_SURE"))
        self.assertEqual(r.status, "INVALID")

    def test_bad_harm_risk(self):
        r = validate_narrative_atom(GOOD.replace("harm_risk: NONE", "harm_risk: MAYBE"))
        self.assertEqual(r.status, "INVALID")


class TestHumanExperiencePreservationRule(unittest.TestCase):
    """§IX made structural — the single most important rule in this file."""

    def _subjective(self, **extra_lines):
        text = GOOD.replace("source_type: TECHNICAL_KNOWLEDGE", "source_type: PERSONAL_EXPERIENCE")
        for k, v in extra_lines.items():
            text += f"\n  {k}: {v}"
        return text

    def test_missing_external_explanation_status_rejected(self):
        r = validate_narrative_atom(self._subjective())
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "NA-R-12" for i in r.issues))

    def test_experience_valid_with_unknown_external_cause(self):
        """The core doctrine guarantee: the experience is never disputed
        when the external cause is honestly marked UNKNOWN."""
        r = validate_narrative_atom(self._subjective(external_explanation_status="UNKNOWN"))
        self.assertEqual(r.status, "VALID", r.issues)

    def test_verified_fact_evidence_status_without_independent_external_proof_rejected(self):
        text = self._subjective(external_explanation_status="UNKNOWN")
        text = text.replace("evidence_status: EVIDENCE_SUPPORTED_MODEL", "evidence_status: VERIFIED_FACT")
        r = validate_narrative_atom(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "NA-R-12" for i in r.issues))

    def test_verified_fact_with_independently_verified_external_cause_is_allowed(self):
        text = self._subjective(external_explanation_status="VERIFIED_FACT")
        text = text.replace("evidence_status: EVIDENCE_SUPPORTED_MODEL", "evidence_status: VERIFIED_FACT")
        r = validate_narrative_atom(text)
        self.assertEqual(r.status, "VALID", r.issues)

    def test_non_subjective_source_type_does_not_require_external_explanation_status(self):
        r = validate_narrative_atom(GOOD)  # source_type TECHNICAL_KNOWLEDGE
        self.assertEqual(r.status, "VALID", r.issues)


class TestCanonRequiresFalsifiability(unittest.TestCase):
    def test_canonical_without_falsification_criteria_rejected(self):
        text = GOOD.replace("promotion_status: TESTED", "promotion_status: CANONICAL_ABSTRACTION")
        r = validate_narrative_atom(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "NA-R-13" for i in r.issues))

    def test_canonical_with_falsification_criteria_allowed(self):
        text = GOOD.replace("promotion_status: TESTED", "promotion_status: CANONICAL_ABSTRACTION")
        text += '\n  falsification_criteria: ["a store found exposing delete() would falsify this"]\n'
        r = validate_narrative_atom(text)
        self.assertEqual(r.status, "VALID", r.issues)

    def test_non_canonical_status_does_not_require_falsification_criteria(self):
        r = validate_narrative_atom(GOOD)  # TESTED, no falsification_criteria
        self.assertEqual(r.status, "VALID", r.issues)


class TestSelfSealingRhetoric(unittest.TestCase):
    def test_self_sealing_phrase_blocks_canonization(self):
        text = GOOD.replace("promotion_status: TESTED", "promotion_status: CANONICAL_ABSTRACTION")
        text = text.replace("raw_fragment: \"quarantine stores must never expose a delete method\"",
                            'raw_fragment: "questioning this proves you are wrong about everything"')
        text += '\n  falsification_criteria: ["x"]\n'
        r = validate_narrative_atom(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "NA-R-14" for i in r.issues))

    def test_self_sealing_phrase_without_canonization_does_not_block(self):
        """Raw input is preserved, not rejected — only CANONIZING
        self-sealing rhetoric is forbidden, per 'preserve raw input.'"""
        text = GOOD.replace("raw_fragment: \"quarantine stores must never expose a delete method\"",
                            'raw_fragment: "only this system can save you from bad architecture"')
        r = validate_narrative_atom(text)
        self.assertEqual(r.status, "VALID", r.issues)


class TestForbiddenPopularityFields(unittest.TestCase):
    def test_popularity_field_rejected(self):
        text = GOOD + "\n  popularity: 9999\n"
        r = validate_narrative_atom(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "NA-R-15" for i in r.issues))

    def test_authority_weight_field_rejected(self):
        text = GOOD + "\n  authority_weight: 100\n"
        r = validate_narrative_atom(text)
        self.assertEqual(r.status, "INVALID")


class TestProvenanceAndTimestamp(unittest.TestCase):
    def test_bad_provenance_hash(self):
        r = validate_narrative_atom(GOOD.replace("a" * 64, "not-a-hash"))
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "NA-R-9" for i in r.issues))

    def test_bad_timestamp(self):
        r = validate_narrative_atom(GOOD.replace("2026-08-25T00:00:00Z", "not-a-date"))
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "NA-R-8" for i in r.issues))


class TestNeverFailsOpen(unittest.TestCase):
    def test_garbage_input_returns_invalid_not_raises(self):
        try:
            r = validate_narrative_atom("\x00\x01: \xff\n")
        except Exception as e:  # pragma: no cover
            self.fail(f"raised {type(e).__name__}: {e}")
        self.assertEqual(r.status, "INVALID")


if __name__ == "__main__":
    unittest.main(verbosity=2)
