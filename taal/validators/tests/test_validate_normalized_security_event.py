"""
Normalized Security Event validator tests.

Every rejection must carry WHAT/WHY/WHERE/RULE/EVIDENCE — these tests
check the structured result, never just a boolean. Mirrors
magl/validators/tests/test_validate_magl.py.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from taal.validators.validate_normalized_security_event import (  # noqa: E402
    validate_normalized_security_event,
)

GOOD = """
normalized_security_event:
  id: "sse-001"
  observed_at: "2026-08-19T10:15:00Z"
  source_type: AUDIT_LOG
  raw_reference: "log-store://audit/2026-08-19/entry-4471"
  entity: "user-jsmith"
  observed_action: "attempted login"
  affected_resource: "auth-service"
  related_permission_request_ref: "pr-001"
  signals:
    - "3 failed auth attempts in 10s"
    - "source IP not seen for this entity in the last 30 days"
  confidence: EVIDENCE_SUPPORTED_MODEL
"""

GOOD_NO_REF = """
normalized_security_event:
  id: "sse-002"
  observed_at: "2026-08-19T11:00:00Z"
  source_type: AI_TOOL_REQUEST
  raw_reference: "tool-log://session-99/call-3"
  entity: "agent-alpha"
  observed_action: "requested filesystem write access"
  affected_resource: "/var/data/reports"
  signals:
    - "write scope requested outside declared jurisdiction"
  confidence: TECHNICAL_DESIGN
"""


def _issue_rules(result):
    return {i.rule for i in result.issues}


class TestWellFormed(unittest.TestCase):
    def test_good_document_is_valid(self):
        result = validate_normalized_security_event(GOOD)
        self.assertEqual(result.status, "VALID", msg=[i.to_dict() for i in result.issues])
        self.assertEqual(result.issues, [])
        self.assertEqual(result.event_id, "sse-001")

    def test_good_document_without_optional_ref_is_valid(self):
        result = validate_normalized_security_event(GOOD_NO_REF)
        self.assertEqual(result.status, "VALID", msg=[i.to_dict() for i in result.issues])
        self.assertEqual(result.event_id, "sse-002")


class TestForbiddenVerdictFields(unittest.TestCase):
    """SE-R-9 is the load-bearing separation of this schema (observation
    vs. conclusion). Prove each forbidden field is rejected on its own,
    even inside an otherwise well-formed document."""

    def _with_extra_field(self, name, value):
        return GOOD.replace(
            "  confidence: EVIDENCE_SUPPORTED_MODEL\n",
            f"  confidence: EVIDENCE_SUPPORTED_MODEL\n  {name}: {value}\n",
        )

    def test_verdict_field_is_rejected(self):
        doc = self._with_extra_field("verdict", '"MALICIOUS"')
        result = validate_normalized_security_event(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("SE-R-9", _issue_rules(result))

    def test_threat_label_field_is_rejected(self):
        doc = self._with_extra_field("threat_label", '"brute_force"')
        result = validate_normalized_security_event(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("SE-R-9", _issue_rules(result))

    def test_attack_confirmed_field_is_rejected(self):
        doc = self._with_extra_field("attack_confirmed", "true")
        result = validate_normalized_security_event(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("SE-R-9", _issue_rules(result))

    def test_is_malicious_field_is_rejected(self):
        doc = self._with_extra_field("is_malicious", "true")
        result = validate_normalized_security_event(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("SE-R-9", _issue_rules(result))

    def test_recommended_action_field_is_rejected(self):
        doc = self._with_extra_field("recommended_action", '"lock the account"')
        result = validate_normalized_security_event(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("SE-R-9", _issue_rules(result))

    def test_all_five_forbidden_fields_together_all_reported(self):
        doc = GOOD.replace(
            "  confidence: EVIDENCE_SUPPORTED_MODEL\n",
            "  confidence: EVIDENCE_SUPPORTED_MODEL\n"
            '  verdict: "MALICIOUS"\n'
            '  threat_label: "brute_force"\n'
            "  attack_confirmed: true\n"
            "  is_malicious: true\n"
            '  recommended_action: "lock the account"\n',
        )
        result = validate_normalized_security_event(doc)
        self.assertEqual(result.status, "INVALID")
        se9_issues = [i for i in result.issues if i.rule == "SE-R-9"]
        self.assertEqual(len(se9_issues), 5)


class TestSignalsBlocklist(unittest.TestCase):
    """SE-R-8, the judgment-call rule: a narrow literal blocklist of
    conclusory words inside signals entries."""

    def test_signal_with_malicious_word_is_rejected(self):
        doc = GOOD.replace(
            '    - "3 failed auth attempts in 10s"',
            '    - "this looks malicious"',
        )
        result = validate_normalized_security_event(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("SE-R-8", _issue_rules(result))

    def test_signal_with_attack_word_is_rejected(self):
        doc = GOOD.replace(
            '    - "3 failed auth attempts in 10s"',
            '    - "this is an attack"',
        )
        result = validate_normalized_security_event(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("SE-R-8", _issue_rules(result))

    def test_signal_with_compromised_word_is_rejected(self):
        doc = GOOD.replace(
            '    - "3 failed auth attempts in 10s"',
            '    - "account appears compromised"',
        )
        result = validate_normalized_security_event(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("SE-R-8", _issue_rules(result))

    def test_signal_with_confirmed_word_is_rejected(self):
        doc = GOOD.replace(
            '    - "3 failed auth attempts in 10s"',
            '    - "confirmed unauthorized access"',
        )
        result = validate_normalized_security_event(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("SE-R-8", _issue_rules(result))

    def test_factual_signal_without_blocklisted_words_is_valid(self):
        result = validate_normalized_security_event(GOOD)
        self.assertEqual(result.status, "VALID", msg=[i.to_dict() for i in result.issues])


class TestRequiredFields(unittest.TestCase):
    def test_missing_required_field_is_invalid(self):
        doc = GOOD.replace('  entity: "user-jsmith"\n', "")
        result = validate_normalized_security_event(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("SE-R-4", _issue_rules(result))

    def test_missing_top_level_wrapper_is_invalid(self):
        result = validate_normalized_security_event("something_else:\n  id: x\n")
        self.assertEqual(result.status, "INVALID")
        self.assertIn("SE-R-2", _issue_rules(result))

    def test_non_mapping_wrapper_is_invalid(self):
        result = validate_normalized_security_event(
            'normalized_security_event: "just a string"\n'
        )
        self.assertEqual(result.status, "INVALID")
        self.assertIn("SE-R-2", _issue_rules(result))


class TestEnumsAndShapes(unittest.TestCase):
    def test_invalid_source_type_enum_is_invalid(self):
        doc = GOOD.replace("source_type: AUDIT_LOG", "source_type: CARRIER_PIGEON")
        result = validate_normalized_security_event(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("SE-R-5", _issue_rules(result))

    def test_invalid_confidence_enum_is_invalid(self):
        doc = GOOD.replace(
            "confidence: EVIDENCE_SUPPORTED_MODEL", "confidence: TOTALLY_SURE"
        )
        result = validate_normalized_security_event(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("SE-R-5", _issue_rules(result))

    def test_bad_timestamp_is_invalid(self):
        doc = GOOD.replace(
            'observed_at: "2026-08-19T10:15:00Z"', 'observed_at: "not-a-timestamp"'
        )
        result = validate_normalized_security_event(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("SE-R-5", _issue_rules(result))

    def test_empty_signals_list_is_invalid(self):
        doc = GOOD.replace(
            '  signals:\n    - "3 failed auth attempts in 10s"\n'
            '    - "source IP not seen for this entity in the last 30 days"\n',
            "  signals: []\n",
        )
        result = validate_normalized_security_event(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("SE-R-6", _issue_rules(result))

    def test_blank_related_ref_is_invalid(self):
        doc = GOOD.replace(
            'related_permission_request_ref: "pr-001"',
            'related_permission_request_ref: ""',
        )
        result = validate_normalized_security_event(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("SE-R-7", _issue_rules(result))

    def test_empty_string_field_is_invalid(self):
        doc = GOOD.replace('entity: "user-jsmith"', 'entity: ""')
        result = validate_normalized_security_event(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("SE-R-5", _issue_rules(result))


class TestHardening(unittest.TestCase):
    def test_duplicate_key_is_invalid(self):
        doc = """
normalized_security_event:
  id: "sse-003"
  id: "sse-004"
  observed_at: "2026-08-19T10:15:00Z"
  source_type: AUDIT_LOG
  raw_reference: "ref"
  entity: "user-x"
  observed_action: "did something"
  affected_resource: "res"
  signals:
    - "something happened"
  confidence: UNKNOWN
"""
        result = validate_normalized_security_event(doc)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("SE-R-1", _issue_rules(result))

    def test_unparseable_yaml_is_invalid(self):
        result = validate_normalized_security_event(
            "normalized_security_event: [unclosed"
        )
        self.assertEqual(result.status, "INVALID")
        self.assertIn("SE-R-1", _issue_rules(result))

    def test_oversized_document_is_invalid(self):
        huge = "normalized_security_event:\n  id: \"" + ("A" * 3_000_000) + "\"\n"
        result = validate_normalized_security_event(huge)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("SE-R-1", _issue_rules(result))

    def test_never_raises_on_garbage_input(self):
        for garbage in ["", "\x00\x01\x02", "{{{{{{{", "- - - -", "null"]:
            result = validate_normalized_security_event(garbage)
            self.assertIn(result.status, ("INVALID", "VALID"))

    def test_deeply_nested_anchor_bomb_is_invalid(self):
        bomb = "a: &a [1,1,1,1,1,1,1,1,1,1]\n" + "".join(
            f"b{i}: &b{i} [*a,*a,*a,*a,*a,*a,*a,*a,*a,*a]\n" for i in range(6)
        )
        doc = "normalized_security_event:\n  id: \"x\"\n" + bomb
        result = validate_normalized_security_event(doc)
        self.assertEqual(result.status, "INVALID")


class TestUnknownFields(unittest.TestCase):
    def test_unknown_field_is_recorded_but_not_fatal_alone(self):
        doc = GOOD.replace(
            "  confidence: EVIDENCE_SUPPORTED_MODEL\n",
            '  confidence: EVIDENCE_SUPPORTED_MODEL\n  extra_field: "surprise"\n',
        )
        result = validate_normalized_security_event(doc)
        self.assertEqual(result.status, "VALID", msg=[i.to_dict() for i in result.issues])
        self.assertIn("extra_field", result.unknown_fields)


if __name__ == "__main__":
    unittest.main()
