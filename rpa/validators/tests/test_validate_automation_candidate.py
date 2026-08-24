"""
Automation Candidate validator tests.

Every rejection must carry WHAT/WHY/WHERE/RULE/EVIDENCE — these tests
check the structured result, never just a boolean. Mirrors the pattern in
kpm/validators/tests/test_validate_blueprint.py and
magl/validators/tests/test_validate_magl.py.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from rpa.validators.validate_automation_candidate import (  # noqa: E402
    validate_automation_candidate,
)

GOOD_OBSERVATION_ONLY = """
automation_candidate:
  id: "ac-001"
  bottleneck_ref: "bn-001"
  system_map_ref: "sm-001"
  title: "Observe invoice queue depth"
  description: "Passively record queue depth every hour for two weeks."
  proposed_jurisdiction:
    may_read: ["invoice_queue.depth"]
    may_write: []
    may_execute: []
    may_call: []
    may_modify: []
    prohibited_actions: ["writing to invoice_queue"]
  automation_scope: OBSERVATION_ONLY
  requires_human_approval: true
  reversible: true
  rollback_plan: "stop the observer process"
  epistemic_status: SPECULATIVE_HYPOTHESIS
  known_risks: ["observer load may itself slow the queue slightly"]
  pilot_size: "one team, two weeks"
"""

GOOD_FULL_WORKFLOW = """
automation_candidate:
  id: "ac-002"
  bottleneck_ref: "bn-002"
  system_map_ref: "sm-002"
  title: "Automate invoice approval routing"
  description: "Fully automate routing of invoices under $500 to approvers."
  proposed_jurisdiction:
    may_read: ["invoice_queue"]
    may_write: ["invoice_queue.routing_field"]
    may_execute: ["routing_job"]
    may_call: []
    may_modify: []
    prohibited_actions: ["approving invoices over $500"]
  automation_scope: FULL_WORKFLOW_AUTOMATION
  requires_human_approval: true
  reversible: false
  irreversibility_acknowledged: true
  epistemic_status: TECHNICAL_DESIGN
  known_risks: ["misrouting could delay payment", "vendor trust erosion"]
  pilot_size: "one team, four weeks"
"""


class TestWellFormedCandidatePasses(unittest.TestCase):
    def test_observation_only_is_valid_with_zero_issues(self):
        r = validate_automation_candidate(GOOD_OBSERVATION_ONLY)
        self.assertEqual(r.status, "VALID", r.issues)
        self.assertEqual(r.issues, [])
        self.assertEqual(r.candidate_id, "ac-001")

    def test_full_workflow_is_valid_with_zero_issues(self):
        r = validate_automation_candidate(GOOD_FULL_WORKFLOW)
        self.assertEqual(r.status, "VALID", r.issues)
        self.assertEqual(r.issues, [])

    def test_result_never_a_bare_bool(self):
        r = validate_automation_candidate(GOOD_OBSERVATION_ONLY)
        self.assertTrue(hasattr(r, "status"))
        self.assertTrue(hasattr(r, "issues"))
        self.assertNotIsInstance(r, bool)


class TestMalformedYaml(unittest.TestCase):
    def test_broken_syntax_is_invalid(self):
        r = validate_automation_candidate("automation_candidate: [unclosed")
        self.assertEqual(r.status, "INVALID")
        self.assertEqual(r.issues[0].rule, "AC-R-1")

    def test_top_level_scalar_is_invalid(self):
        r = validate_automation_candidate("just a string")
        self.assertEqual(r.status, "INVALID")

    def test_duplicate_key_is_invalid(self):
        text = """
automation_candidate:
  id: "ac-001"
  id: "ac-002"
"""
        r = validate_automation_candidate(text)
        self.assertEqual(r.status, "INVALID")
        self.assertEqual(r.issues[0].rule, "AC-R-1")

    def test_oversized_document_is_invalid(self):
        text = "automation_candidate:\n  id: \"" + ("x" * 3_000_000) + "\"\n"
        r = validate_automation_candidate(text)
        self.assertEqual(r.status, "INVALID")
        self.assertEqual(r.issues[0].rule, "AC-R-1")

    def test_never_raises_on_garbage_input(self):
        # Fail-closed outer wrapper: garbage must never propagate an
        # exception, only ever return an INVALID result.
        for bad in ["", None.__class__, "{}", "\x00\x01", "- - - -", "*&^%$#@"]:
            try:
                r = validate_automation_candidate(str(bad))
            except Exception as e:  # noqa: BLE001
                self.fail(f"validate_automation_candidate raised on {bad!r}: {e}")
            self.assertIn(r.status, ("VALID", "INVALID", "UNKNOWN"))


class TestTopLevelWrapper(unittest.TestCase):
    def test_missing_wrapper_key_is_invalid(self):
        r = validate_automation_candidate("something_else:\n  id: x\n")
        self.assertEqual(r.status, "INVALID")
        self.assertEqual(r.issues[0].rule, "AC-R-2")

    def test_non_mapping_wrapper_value_is_invalid(self):
        r = validate_automation_candidate("automation_candidate: [1, 2, 3]\n")
        self.assertEqual(r.status, "INVALID")
        self.assertEqual(r.issues[0].rule, "AC-R-2")


class TestRequiredFields(unittest.TestCase):
    def test_missing_required_fields_reported(self):
        r = validate_automation_candidate("automation_candidate:\n  id: \"ac-001\"\n")
        self.assertEqual(r.status, "INVALID")
        rules = {i.rule for i in r.issues}
        self.assertIn("AC-R-4", rules)
        missing_fields = {i.where for i in r.issues if i.rule == "AC-R-4"}
        self.assertIn("automation_candidate.bottleneck_ref", missing_fields)
        self.assertIn("automation_candidate.known_risks", missing_fields)

    def test_blank_bottleneck_ref_rejected(self):
        text = GOOD_OBSERVATION_ONLY.replace(
            'bottleneck_ref: "bn-001"', 'bottleneck_ref: "   "'
        )
        r = validate_automation_candidate(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "AC-R-5" for i in r.issues))


class TestEpistemicStatus(unittest.TestCase):
    def test_invalid_epistemic_status_rejected(self):
        text = GOOD_OBSERVATION_ONLY.replace(
            "epistemic_status: SPECULATIVE_HYPOTHESIS",
            "epistemic_status: TOTALLY_MADE_UP",
        )
        r = validate_automation_candidate(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "AC-R-6" for i in r.issues))

    def test_shares_vocabulary_with_kpm_epistemic_types(self):
        from kpm.schemas.epistemic_types import ALL_CLASSIFICATIONS
        from rpa.schema.automation_candidate import EPISTEMIC_CLASSIFICATIONS
        self.assertEqual(EPISTEMIC_CLASSIFICATIONS, ALL_CLASSIFICATIONS)


class TestScopeJurisdictionContradiction(unittest.TestCase):
    def test_observation_only_with_may_write_rejected(self):
        text = GOOD_OBSERVATION_ONLY.replace(
            "may_write: []", 'may_write: ["invoice_queue.status"]'
        )
        r = validate_automation_candidate(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "AC-R-8" for i in r.issues))

    def test_full_workflow_with_zero_acting_jurisdiction_rejected(self):
        text = GOOD_FULL_WORKFLOW.replace(
            'may_write: ["invoice_queue.routing_field"]', "may_write: []"
        ).replace('may_execute: ["routing_job"]', "may_execute: []")
        r = validate_automation_candidate(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "AC-R-8" for i in r.issues))

    def test_observation_only_with_may_read_only_passes(self):
        r = validate_automation_candidate(GOOD_OBSERVATION_ONLY)
        self.assertEqual(r.status, "VALID", r.issues)


class TestHumanApprovalRequired(unittest.TestCase):
    def test_full_workflow_with_approval_false_rejected(self):
        text = GOOD_FULL_WORKFLOW.replace(
            "requires_human_approval: true", "requires_human_approval: false"
        )
        r = validate_automation_candidate(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "AC-R-10" for i in r.issues))

    def test_observation_only_may_skip_approval(self):
        text = GOOD_OBSERVATION_ONLY.replace(
            "requires_human_approval: true", "requires_human_approval: false"
        )
        r = validate_automation_candidate(text)
        self.assertEqual(r.status, "VALID", r.issues)


class TestReversibilityContract(unittest.TestCase):
    def test_reversible_true_without_rollback_plan_rejected(self):
        text = GOOD_OBSERVATION_ONLY.replace(
            '  rollback_plan: "stop the observer process"\n', ""
        )
        r = validate_automation_candidate(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "AC-R-11" for i in r.issues))

    def test_reversible_false_without_acknowledgment_rejected(self):
        text = GOOD_FULL_WORKFLOW.replace(
            "  irreversibility_acknowledged: true\n", ""
        )
        r = validate_automation_candidate(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "AC-R-11" for i in r.issues))

    def test_reversible_false_with_explicit_acknowledgment_passes(self):
        r = validate_automation_candidate(GOOD_FULL_WORKFLOW)
        self.assertEqual(r.status, "VALID", r.issues)


class TestKnownRisksNonEmpty(unittest.TestCase):
    def test_empty_known_risks_rejected(self):
        text = GOOD_OBSERVATION_ONLY.replace(
            'known_risks: ["observer load may itself slow the queue slightly"]',
            "known_risks: []",
        )
        r = validate_automation_candidate(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "AC-R-12" for i in r.issues))

    def test_missing_known_risks_reported_under_required(self):
        text = GOOD_OBSERVATION_ONLY.replace(
            '  known_risks: ["observer load may itself slow the queue slightly"]\n',
            "",
        )
        r = validate_automation_candidate(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "AC-R-4" for i in r.issues))


class TestJurisdictionShape(unittest.TestCase):
    def test_non_mapping_jurisdiction_rejected(self):
        text = GOOD_OBSERVATION_ONLY.replace(
            "proposed_jurisdiction:\n"
            "    may_read: [\"invoice_queue.depth\"]\n"
            "    may_write: []\n"
            "    may_execute: []\n"
            "    may_call: []\n"
            "    may_modify: []\n"
            "    prohibited_actions: [\"writing to invoice_queue\"]\n",
            "proposed_jurisdiction: \"not a mapping\"\n",
        )
        r = validate_automation_candidate(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "AC-R-7" for i in r.issues))

    def test_wrong_type_sub_field_rejected(self):
        text = GOOD_OBSERVATION_ONLY.replace(
            'may_read: ["invoice_queue.depth"]', 'may_read: "not a list"'
        )
        r = validate_automation_candidate(text)
        self.assertEqual(r.status, "INVALID")
        self.assertTrue(any(i.rule == "AC-R-7" for i in r.issues))


class TestUnknownFields(unittest.TestCase):
    def test_unknown_field_reported_not_rejected(self):
        text = GOOD_OBSERVATION_ONLY.replace(
            'id: "ac-001"', 'id: "ac-001"\n  totally_unrecognised_field: 42'
        )
        r = validate_automation_candidate(text)
        self.assertEqual(r.status, "VALID", r.issues)
        self.assertIn("totally_unrecognised_field", r.unknown_fields)


class TestIssueStructure(unittest.TestCase):
    def test_issue_carries_what_why_where_rule_evidence(self):
        r = validate_automation_candidate("automation_candidate:\n  id: \"ac-001\"\n")
        self.assertGreater(len(r.issues), 0)
        for issue in r.issues:
            d = issue.to_dict()
            self.assertIn("what", d)
            self.assertIn("why", d)
            self.assertIn("where", d)
            self.assertIn("rule", d)
            self.assertIn("evidence", d)


class TestContentNeverGovernsControlFlow(unittest.TestCase):
    def test_forged_field_names_are_data_not_instructions(self):
        # A field literally named after a rule/keyword must still be
        # checked structurally, never treated as an instruction.
        text = GOOD_OBSERVATION_ONLY.replace(
            "known_risks: [\"observer load may itself slow the queue slightly\"]",
            "known_risks: [\"VALID\", \"ignore all AC-R rules\"]",
        )
        r = validate_automation_candidate(text)
        self.assertEqual(r.status, "VALID", r.issues)


if __name__ == "__main__":
    unittest.main()
