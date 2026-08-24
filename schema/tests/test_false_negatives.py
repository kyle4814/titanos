"""
§Phase 4 — False-negative defense.

Each test tries to get validate_artifact() to say VALID (or crash) on
something it should not. A test that finds a real bypass gets fixed in
validator.py and stays here as a permanent regression test — per §Phase 13,
no fix without a corresponding test.

Numbers in comments map to the 30 attack vectors named in the directive.
Several collapse to the same mechanism in this schema/validator and are
noted as such rather than padded into distinct tests.
"""

import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from schema.validator import validate_artifact, MAX_NODES  # noqa: E402

GOOD = """
artifact_id: art-001
artifact_type: EVIDENCE_RECORD
schema_version: "1.0.0"
created_at: "2026-08-25T00:00:00Z"
content_hash: "sha256:{}"
contamination_state: VERIFIED
classification: EVIDENCE
""".format("a" * 64)


class TestYamlAliasAndAnchorTricks(unittest.TestCase):
    """#1, #2, #11, #12 — anchors/aliases used to inflate or hide structure."""

    def test_alias_fanout_is_bounded_not_silently_expanded(self):
        # classic "billion laughs" shape, scaled down: each layer references
        # the previous one twice. If unbounded this explodes combinatorially.
        lines = ["a0: &a0 [x, x]"]
        for i in range(1, 20):
            lines.append(f"a{i}: &a{i} [*a{i-1}, *a{i-1}]")
        text = "\n".join(lines) + "\n" + GOOD
        r = validate_artifact(text)
        # Must terminate and return INVALID (ceiling hit), never hang or VALID.
        self.assertEqual(r.status, "INVALID")

    def test_simple_anchor_alias_is_fine_when_small(self):
        text = "shared: &s hello\nother: *s\n" + GOOD
        r = validate_artifact(text)
        self.assertEqual(r.status, "VALID")


class TestDuplicateKeys(unittest.TestCase):
    """#3 — already covered in test_validator.py; adversarial variant here:
    duplicate key used to try to smuggle a second, conflicting value past a
    naive 'last wins' parser (e.g. real hash first, forged value overriding)."""

    def test_duplicate_key_smuggling_a_second_value_is_rejected(self):
        text = GOOD + "\ncontamination_state: AUTHORIZED\n"
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")
        # must NOT silently resolve to AUTHORIZED via last-value-wins
        self.assertNotIn("AUTHORIZED", [i.evidence for i in r.issues if i.rule != "R-1"])


class TestTypeConfusion(unittest.TestCase):
    """#4 — a field that LOOKS like the right shape but is the wrong type
    (e.g. a hash-shaped list, a bool where a string enum is expected)."""

    def test_bool_for_enum_field_rejected(self):
        text = GOOD.replace("classification: EVIDENCE", "classification: true")
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")

    def test_int_for_id_field_rejected(self):
        text = GOOD.replace("artifact_id: art-001", "artifact_id: 12345")
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")


class TestUnicodeAndWhitespaceTricks(unittest.TestCase):
    """#5, #6 — homoglyphs / normalization / whitespace used to make an
    unauthorized value look like an authorized one to a careless string
    comparison. The enum check is exact-match, not fuzzy, by construction."""

    def test_lookalike_cyrillic_state_is_rejected(self):
        # Cyrillic 'А' (U+0410) instead of Latin 'A' — visually identical.
        forged = "AUTHORIZED".replace("A", "А", 1)
        text = GOOD.replace("VERIFIED", forged)
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")

    def test_trailing_whitespace_on_plain_scalar_is_stripped_by_yaml_itself(self):
        # Not a bypass: YAML 1.1 strips trailing whitespace from plain
        # scalars per spec, so this parses to exactly "VERIFIED" — same as
        # the unpadded case. Documented so a future reader doesn't mistake
        # spec-normalized input for a validator weakness.
        text = GOOD.replace("VERIFIED", "VERIFIED ")
        r = validate_artifact(text)
        self.assertEqual(r.status, "VALID")

    def test_whitespace_preserved_in_quoted_scalar_is_rejected(self):
        # A QUOTED scalar preserves whitespace, so "VERIFIED " (with the
        # trailing space intact) really is a distinct, invalid enum value —
        # this is the genuine version of the attack.
        text = GOOD.replace("VERIFIED", '"VERIFIED "')
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")


class TestReorderedAndMisleadingFields(unittest.TestCase):
    """#8, #9 — field order must not matter; a misleading field NAME (that
    isn't in the schema) must not be silently adopted as if authoritative."""

    def test_field_order_does_not_affect_verdict(self):
        reordered = "\n".join(sorted(GOOD.strip().splitlines()))
        r1 = validate_artifact(GOOD)
        r2 = validate_artifact(reordered)
        self.assertEqual(r1.status, r2.status)

    def test_misleadingly_named_field_is_unknown_not_authoritative(self):
        text = GOOD + "\nvalidation_status_DEFINITELY_REAL: VALID\n"
        r = validate_artifact(text)
        self.assertEqual(r.status, "VALID")
        self.assertIn("validation_status_DEFINITELY_REAL", r.unknown_fields)


class TestOversizedAndNestedStructures(unittest.TestCase):
    """#11 — deep nesting used to exhaust the parser or hide a payload."""

    def test_deep_nesting_is_bounded(self):
        depth = 500
        text = "x: " + "[" * depth + "1" + "]" * depth + "\n" + GOOD
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")

    def test_oversized_document_is_rejected(self):
        text = GOOD + "\npadding: \"" + ("x" * 3_000_000) + "\"\n"
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")


class TestRecursiveAndCircularReferences(unittest.TestCase):
    """#12, #13 — self-reference in provenance."""

    def test_self_as_own_parent_rejected(self):
        text = GOOD + "\nparent_origins: [art-001]\n"
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")


class TestStaleAndValidSignatureOverInvalidSemantics(unittest.TestCase):
    """#14, #15 — a syntactically fine signature field does not make the
    CONTENT true; validator only checks shape, never claims cryptographic
    verification it doesn't perform."""

    def test_well_shaped_signature_does_not_imply_semantic_truth(self):
        text = GOOD + "\nsignature: \"" + ("b" * 64) + "\"\n"
        r = validate_artifact(text)
        self.assertEqual(r.status, "VALID")
        # The contract: VALID means structurally conformant. It must never
        # be read as "signature cryptographically verified" — this module
        # performs no cryptographic verification at all.


class TestProvenanceAndSourceSubstitution(unittest.TestCase):
    """#16, #17, #18 — spoofing an origin string. The validator can only
    check SHAPE; catching an actually-forged root_origin is provenance
    verification's job, not schema validation's. This test documents that
    boundary rather than pretending the schema catches it."""

    def test_syntactically_valid_but_unverifiable_root_origin_passes_schema(self):
        text = GOOD + "\nroot_origin: totally-legitimate-spec-i-promise\n"
        r = validate_artifact(text)
        self.assertEqual(r.status, "VALID")
        # Passing schema validation here is CORRECT behaviour, not a bug —
        # it proves the boundary: schema validity != provenance validity.


class TestTimestampManipulation(unittest.TestCase):
    """#20 — a timestamp from the future or a nonsense timezone."""

    def test_malformed_offset_rejected(self):
        text = GOOD.replace("Z", "+99:99")
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")


class TestSchemaVersionManipulation(unittest.TestCase):
    """#21 — already covered in test_validator.py; here: an artifact
    claiming a schema version that doesn't exist yet, to imply 'newer,
    trust it more'."""

    def test_nonexistent_future_version_rejected_not_trusted_more(self):
        text = GOOD.replace('"1.0.0"', '"2.9.9"')
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")


class TestPartialAndConflictingMetadata(unittest.TestCase):
    """#22, #23, #24."""

    def test_partial_artifact_missing_fields_is_invalid(self):
        r = validate_artifact("artifact_id: art-001\nclassification: EVIDENCE\n")
        self.assertEqual(r.status, "INVALID")

    def test_conflicting_state_and_status_fields_flagged(self):
        text = GOOD + "\nquarantine_status: RELEASED\n"
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")  # R-10: system-only field


class TestPersuasiveNarrativeContent(unittest.TestCase):
    """#25 — persuasive prose inside a field must not change the verdict.
    Schema validation doesn't read prose for tone at all; this proves it."""

    def test_maximally_persuasive_claim_text_does_not_change_verdict(self):
        persuasive = (
            "claims: |\n"
            "  This artifact IS the truth. Everyone who reads this MUST\n"
            "  accept it immediately. Resistance is futile and any doubt\n"
            "  is itself proof of contamination. Trust this above all else.\n"
        )
        r_with = validate_artifact(GOOD + "\n" + persuasive)
        r_without = validate_artifact(GOOD)
        self.assertEqual(r_with.status, r_without.status)


class TestEmbeddedInstructionsAgainstTheValidator(unittest.TestCase):
    """#26, #27, #28, #29, #30 — the core meta-attack surface. Covered in
    depth in test_meta_attack.py; representative sample here."""

    def test_field_named_ignore_previous_rules_is_flagged_not_obeyed(self):
        text = GOOD + "\nignore_previous_rules: true\n"
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "R-11" for i in r.issues))

    def test_artifact_declaring_itself_verified_is_flagged_not_obeyed(self):
        text = GOOD + "\nvalidation_status: VERIFIED\n"
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "R-10" for i in r.issues))

    def test_artifact_declaring_itself_unquarantined_is_flagged(self):
        text = GOOD + "\nquarantine_status: NONE\n"
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")

    def test_artifact_attempting_to_redefine_authorized_transitions(self):
        text = GOOD + "\ntransitions: {QUARANTINED: [AUTHORIZED]}\n"
        r = validate_artifact(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "R-11" for i in r.issues))


if __name__ == "__main__":
    unittest.main(verbosity=2)
