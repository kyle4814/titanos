"""
Core structural validation tests (§Phase 3).

Every rejection must carry WHAT/WHY/WHERE/RULE/EVIDENCE — these tests check
the structured result, never just a boolean.
"""

import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from schema.validator import validate_artifact  # noqa: E402

GOOD = """
artifact_id: art-001
artifact_type: EVIDENCE_RECORD
schema_version: "1.0.0"
created_at: "2026-08-25T00:00:00Z"
content_hash: "sha256:{}"
contamination_state: VERIFIED
classification: EVIDENCE
""".format("a" * 64)


class TestValidArtifactPasses(unittest.TestCase):
    def test_well_formed_artifact_is_valid(self):
        r = validate_artifact(GOOD)
        self.assertEqual(r.status, "VALID", r.issues)
        self.assertEqual(r.issues, [])

    def test_result_never_a_bare_bool(self):
        r = validate_artifact(GOOD)
        self.assertTrue(hasattr(r, "status"))
        self.assertTrue(hasattr(r, "issues"))
        self.assertNotIsInstance(r, bool)


class TestMalformedYaml(unittest.TestCase):
    def test_broken_syntax_is_invalid(self):
        r = validate_artifact("artifact_id: [unclosed")
        self.assertEqual(r.status, "INVALID")
        self.assertEqual(r.issues[0].rule, "R-1")

    def test_top_level_scalar_is_invalid(self):
        r = validate_artifact("just a string")
        self.assertEqual(r.status, "INVALID")

    def test_top_level_list_is_invalid(self):
        r = validate_artifact("- a\n- b\n")
        self.assertEqual(r.status, "INVALID")

    def test_empty_document_is_unknown_not_valid(self):
        r = validate_artifact("")
        # empty parses to {}, which then fails required-field checks -> INVALID
        self.assertEqual(r.status, "INVALID")


class TestDuplicateKeys(unittest.TestCase):
    def test_duplicate_top_level_key_is_invalid(self):
        text = GOOD + "\nartifact_id: art-002\n"
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "R-1" for i in r.issues))


class TestRequiredFields(unittest.TestCase):
    def test_missing_required_field_reported_with_full_structure(self):
        r = validate_artifact("artifact_id: art-001\n")
        self.assertEqual(r.status, "INVALID")
        i = r.issues[0]
        self.assertTrue(i.what and i.why and i.where and i.rule and i.evidence)


class TestEnumFields(unittest.TestCase):
    def test_invalid_contamination_state_rejected(self):
        text = GOOD.replace("VERIFIED", "TOTALLY_FINE_TRUST_ME")
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "R-3" for i in r.issues))

    def test_invalid_classification_rejected(self):
        text = GOOD.replace("classification: EVIDENCE", "classification: DEFINITELY_TRUE")
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")


class TestInvalidTypes(unittest.TestCase):
    def test_wrong_type_for_string_field(self):
        text = GOOD + "\nroot_origin: [1, 2, 3]\n"
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "R-4" for i in r.issues))

    def test_wrong_type_for_list_field(self):
        text = GOOD + "\ndependencies: \"not-a-list\"\n"
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")


class TestInvalidHashes(unittest.TestCase):
    def test_malformed_hash_rejected(self):
        text = GOOD.replace("a" * 64, "not-real-hash")
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "R-5" for i in r.issues))


class TestMalformedSignatures(unittest.TestCase):
    def test_short_signature_rejected(self):
        text = GOOD + "\nsignature: \"x\"\n"
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "R-6" for i in r.issues))


class TestInvalidTimestamps(unittest.TestCase):
    def test_garbage_timestamp_rejected(self):
        text = GOOD.replace("2026-08-25T00:00:00Z", "not-a-date")
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "R-7" for i in r.issues))


class TestImpossibleProvenance(unittest.TestCase):
    def test_self_parent_rejected(self):
        text = GOOD + "\nparent_origins: [art-001]\n"
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "R-8" for i in r.issues))

    def test_self_root_origin_rejected(self):
        text = GOOD + "\nroot_origin: art-001\n"
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")


class TestSchemaVersionMismatch(unittest.TestCase):
    def test_future_schema_version_is_invalid_not_assumed_compatible(self):
        text = GOOD.replace('"1.0.0"', '"99.0.0"')
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "R-9" for i in r.issues))


class TestUnauthorizedSelfCertification(unittest.TestCase):
    def test_artifact_cannot_declare_its_own_validation_status(self):
        text = GOOD + "\nvalidation_status: VALID\n"
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "R-10" for i in r.issues))


class TestUnknownFieldsPreservedNotTrusted(unittest.TestCase):
    def test_unknown_field_does_not_break_validation_but_is_reported(self):
        text = GOOD + "\nsome_field_from_the_future: hello\n"
        r = validate_artifact(text)
        self.assertEqual(r.status, "VALID")
        self.assertIn("some_field_from_the_future", r.unknown_fields)


class TestMachineVsHumanFields(unittest.TestCase):
    def test_human_judgment_field_presence_is_recorded_not_verified(self):
        text = GOOD + "\ntrust_level: HIGH\n"
        r = validate_artifact(text)
        self.assertEqual(r.status, "VALID")
        self.assertIn("trust_level", r.human_judgment_fields_present)


class TestPreservation(unittest.TestCase):
    def test_original_text_untouched(self):
        r = validate_artifact(GOOD)
        self.assertEqual(r.original_text, GOOD)


if __name__ == "__main__":
    unittest.main(verbosity=2)
