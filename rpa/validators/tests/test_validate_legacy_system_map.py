"""
Legacy System Map validator tests.

Every rejection must carry WHAT/WHY/WHERE/RULE/EVIDENCE — these tests check
the structured result, never just a boolean. Mirrors
magl/validators/tests/test_validate_magl.py and
kpm/validators/tests/test_validate_blueprint.py.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from rpa.validators.validate_legacy_system_map import (  # noqa: E402
    validate_legacy_system_map,
)
from kpm.schemas.epistemic_types import ALL_CLASSIFICATIONS  # noqa: E402

GOOD = """
legacy_system_map:
  id: "lsm-001"
  organisation_name: "Northwind Traders (pseudonym)"
  version: "1.0.0"
  scanned_at: "2026-08-19T10:00:00Z"
  scan_method: MIXED
  epistemic_status: EVIDENCE_SUPPORTED_MODEL

  nodes:
    - id: "n-ceo"
      type: PERSON
      name: "CEO"
      authority: ["final sign-off on spend over $50k"]
      known_failure_history: []
      criticality: HIGH
    - id: "n-finance-role"
      type: ROLE
      name: "Finance Approver"
      authority: ["approves invoices under $50k"]
      known_failure_history: ["approval queue backed up for 3 weeks in 2024"]
      criticality: MEDIUM
    - id: "n-erp"
      type: SOFTWARE_SYSTEM
      name: "Legacy ERP"
      authority: []
      known_failure_history: ["outage Jan 2025, 6 hours"]
      criticality: MUST_NEVER_STOP
    - id: "n-invoice-store"
      type: DATA_STORE
      name: "Invoice Archive"
      authority: []
      known_failure_history: []
      criticality: LOW
    - id: "n-vendor"
      type: VENDOR
      name: "Acme Supplies"
      authority: []
      known_failure_history: []
      criticality: MEDIUM

  edges:
    - from_node: "n-finance-role"
      to_node: "n-ceo"
      relationship: REPORTS_TO
      is_manual: true
      typical_delay: "1-2 business days"
    - from_node: "n-erp"
      to_node: "n-invoice-store"
      relationship: FEEDS_DATA_TO
      is_manual: false
    - from_node: "n-vendor"
      to_node: "n-erp"
      relationship: VENDOR_OF
      is_manual: false

  boundaries:
    - id: "b-finance"
      description: "Finance department authority boundary"
      contains_node_ids: ["n-finance-role", "n-ceo"]

  jurisdictions:
    - authority_node_id: "n-ceo"
      scope_node_ids: ["n-finance-role"]
      basis: "org chart: CEO holds final approval authority per company bylaws"

  single_points_of_failure: ["n-erp"]
  unknowns: []
"""


class TestGoodDocument(unittest.TestCase):
    def test_well_formed_example_validates_cleanly(self):
        result = validate_legacy_system_map(GOOD)
        self.assertEqual(result.status, "VALID", msg=[i.to_dict() for i in result.issues])
        self.assertEqual(result.issues, [])
        self.assertEqual(result.map_id, "lsm-001")

    def test_result_never_a_bare_bool(self):
        result = validate_legacy_system_map(GOOD)
        self.assertTrue(hasattr(result, "status"))
        self.assertTrue(hasattr(result, "issues"))
        self.assertNotIsInstance(result, bool)


class TestMalformedYaml(unittest.TestCase):
    def test_unparseable_yaml_is_invalid(self):
        result = validate_legacy_system_map("legacy_system_map: [unterminated")
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-1" for i in result.issues))

    def test_duplicate_keys_rejected(self):
        text = """
legacy_system_map:
  id: "lsm-001"
  id: "lsm-002"
  organisation_name: "X"
  version: "1.0.0"
  scanned_at: "2026-08-19T10:00:00Z"
  scan_method: INTERVIEW
  epistemic_status: EVIDENCE_SUPPORTED_MODEL
  nodes: []
  edges: []
  boundaries: []
  jurisdictions: []
  single_points_of_failure: []
  unknowns: []
"""
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-1" for i in result.issues))

    def test_oversized_document_rejected(self):
        big = "legacy_system_map:\n  id: \"" + ("a" * (2_500_000)) + "\"\n"
        result = validate_legacy_system_map(big)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-1" for i in result.issues))

    def test_non_mapping_top_level_rejected(self):
        result = validate_legacy_system_map("- just\n- a\n- list\n")
        self.assertEqual(result.status, "INVALID")

    def test_never_raises_on_garbage_input(self):
        for garbage in ["", "   ", "null", "42", "\t\t\x00", "{{{{{"]:
            result = validate_legacy_system_map(garbage)
            self.assertIn(result.status, ("INVALID", "VALID", "UNKNOWN"))


class TestTopLevelWrapper(unittest.TestCase):
    def test_missing_wrapper_key(self):
        result = validate_legacy_system_map("something_else:\n  id: x\n")
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-2" for i in result.issues))

    def test_wrapper_not_a_mapping(self):
        result = validate_legacy_system_map("legacy_system_map: [1, 2, 3]\n")
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-2" for i in result.issues))


class TestRequiredFields(unittest.TestCase):
    def test_missing_required_top_fields(self):
        result = validate_legacy_system_map("legacy_system_map:\n  id: \"lsm-1\"\n")
        self.assertEqual(result.status, "INVALID")
        rules = {i.rule for i in result.issues}
        self.assertIn("LM-R-4", rules)
        missing_fields = {i.where for i in result.issues if i.rule == "LM-R-4"}
        self.assertIn("legacy_system_map.organisation_name", missing_fields)
        self.assertIn("legacy_system_map.nodes", missing_fields)
        self.assertIn("legacy_system_map.unknowns", missing_fields)

    def test_empty_id_rejected(self):
        text = GOOD.replace('id: "lsm-001"', 'id: ""')
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-5" for i in result.issues))

    def test_empty_organisation_name_rejected(self):
        text = GOOD.replace('organisation_name: "Northwind Traders (pseudonym)"',
                             'organisation_name: ""')
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-5" for i in result.issues))


class TestVersionAndTimestamp(unittest.TestCase):
    def test_non_semver_version_rejected(self):
        text = GOOD.replace('version: "1.0.0"', 'version: "latest"')
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-6" for i in result.issues))

    def test_bad_timestamp_rejected(self):
        text = GOOD.replace('scanned_at: "2026-08-19T10:00:00Z"',
                             'scanned_at: "not-a-timestamp"')
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-7" for i in result.issues))


class TestScanMethodAndEpistemicStatus(unittest.TestCase):
    def test_invalid_scan_method_rejected(self):
        text = GOOD.replace("scan_method: MIXED", "scan_method: PSYCHIC_INTUITION")
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-8" for i in result.issues))

    def test_all_scan_methods_accepted(self):
        for method in ("INTERVIEW", "DOCUMENT_REVIEW", "SYSTEM_LOG_ANALYSIS",
                        "WORKSHOP", "MIXED"):
            text = GOOD.replace("scan_method: MIXED", f"scan_method: {method}")
            result = validate_legacy_system_map(text)
            self.assertEqual(result.status, "VALID",
                              msg=f"{method}: {[i.to_dict() for i in result.issues]}")

    def test_invalid_epistemic_status_rejected(self):
        text = GOOD.replace("epistemic_status: EVIDENCE_SUPPORTED_MODEL",
                             "epistemic_status: TOTALLY_SURE_TRUST_ME")
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-9" for i in result.issues))

    def test_epistemic_status_draws_from_shared_vocabulary(self):
        # Prove this schema does not invent its own vocabulary — every
        # legal value comes from the imported closed set.
        for status in sorted(ALL_CLASSIFICATIONS):
            text = GOOD.replace("epistemic_status: EVIDENCE_SUPPORTED_MODEL",
                                 f"epistemic_status: {status}")
            result = validate_legacy_system_map(text)
            self.assertFalse(
                any(i.rule == "LM-R-9" for i in result.issues),
                msg=f"{status} should be legal: {[i.to_dict() for i in result.issues]}",
            )


class TestNodes(unittest.TestCase):
    def test_zero_nodes_invalid(self):
        text = GOOD.replace(
            GOOD[GOOD.index("  nodes:"):GOOD.index("  edges:")],
            "  nodes: []\n",
        )
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-10" for i in result.issues))

    def test_duplicate_node_id_rejected(self):
        text = GOOD.replace('id: "n-invoice-store"', 'id: "n-erp"')
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-10" and "duplicate" in i.what
                             for i in result.issues))

    def test_invalid_node_type_rejected(self):
        text = GOOD.replace("type: PERSON", "type: ALIEN")
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-10" for i in result.issues))

    def test_invalid_criticality_rejected(self):
        text = GOOD.replace("criticality: HIGH", "criticality: CATASTROPHIC")
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-10" for i in result.issues))

    def test_missing_required_node_field_rejected(self):
        text = GOOD.replace(
            '    - id: "n-vendor"\n      type: VENDOR\n      name: "Acme Supplies"\n'
            '      authority: []\n      known_failure_history: []\n      criticality: MEDIUM\n',
            '    - id: "n-vendor"\n      type: VENDOR\n      name: "Acme Supplies"\n'
            '      authority: []\n      known_failure_history: []\n',
        )
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-10" and "criticality" in i.what
                             for i in result.issues))


class TestEdges(unittest.TestCase):
    def test_dangling_from_node_rejected(self):
        text = GOOD.replace('from_node: "n-finance-role"\n      to_node: "n-ceo"',
                             'from_node: "n-does-not-exist"\n      to_node: "n-ceo"')
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        edge_issues = [i for i in result.issues if i.rule == "LM-R-11"
                       and "unknown node id" in i.what]
        self.assertTrue(edge_issues)
        self.assertIn("n-does-not-exist", edge_issues[0].evidence)

    def test_dangling_to_node_rejected(self):
        text = GOOD.replace('to_node: "n-invoice-store"', 'to_node: "n-ghost"')
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-11" and "unknown node id" in i.what
                             for i in result.issues))

    def test_invalid_relationship_rejected(self):
        text = GOOD.replace("relationship: REPORTS_TO", "relationship: SECRETLY_CONTROLS")
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-11" for i in result.issues))

    def test_is_manual_wrong_type_rejected(self):
        text = GOOD.replace("is_manual: true", 'is_manual: "yes"')
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-11" and "is_manual" in i.what
                             for i in result.issues))

    def test_empty_edges_allowed_but_no_error(self):
        # edges may be empty for a trivial single/few-node map; this is
        # not itself a rejected state at the schema level.
        text = GOOD.replace(
            GOOD[GOOD.index("  edges:"):GOOD.index("  boundaries:")],
            "  edges: []\n",
        )
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "VALID", msg=[i.to_dict() for i in result.issues])


class TestBoundaries(unittest.TestCase):
    def test_dangling_boundary_node_ref_rejected(self):
        text = GOOD.replace('contains_node_ids: ["n-finance-role", "n-ceo"]',
                             'contains_node_ids: ["n-finance-role", "n-nonexistent"]')
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-12" and "unknown node id" in i.what
                             for i in result.issues))

    def test_missing_boundary_description_rejected(self):
        text = GOOD.replace(
            '    - id: "b-finance"\n      description: "Finance department authority boundary"\n',
            '    - id: "b-finance"\n',
        )
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-12" for i in result.issues))


class TestJurisdictions(unittest.TestCase):
    def test_empty_basis_rejected(self):
        text = GOOD.replace(
            'basis: "org chart: CEO holds final approval authority per company bylaws"',
            'basis: ""',
        )
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-13" and "basis" in i.what
                             for i in result.issues))

    def test_missing_basis_rejected(self):
        text = GOOD.replace(
            '    - authority_node_id: "n-ceo"\n      scope_node_ids: ["n-finance-role"]\n'
            '      basis: "org chart: CEO holds final approval authority per company bylaws"\n',
            '    - authority_node_id: "n-ceo"\n      scope_node_ids: ["n-finance-role"]\n',
        )
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-13" and "basis" in i.what
                             for i in result.issues))

    def test_dangling_authority_node_id_rejected(self):
        text = GOOD.replace('authority_node_id: "n-ceo"', 'authority_node_id: "n-phantom"')
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-13" and "unknown node id" in i.what
                             for i in result.issues))

    def test_dangling_scope_node_id_rejected(self):
        text = GOOD.replace('scope_node_ids: ["n-finance-role"]',
                             'scope_node_ids: ["n-finance-role", "n-phantom"]')
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-13" and "unknown node id" in i.what
                             for i in result.issues))


class TestSinglePointsOfFailure(unittest.TestCase):
    def test_dangling_spof_ref_rejected(self):
        text = GOOD.replace('single_points_of_failure: ["n-erp"]',
                             'single_points_of_failure: ["n-erp", "n-fictional"]')
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-14" and "unknown node id" in i.what
                             for i in result.issues))

    def test_empty_spof_allowed(self):
        text = GOOD.replace('single_points_of_failure: ["n-erp"]',
                             'single_points_of_failure: []')
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "VALID", msg=[i.to_dict() for i in result.issues])


class TestUnknownsPreserved(unittest.TestCase):
    def test_missing_unknowns_field_rejected(self):
        text = GOOD.replace("  unknowns: []\n", "")
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-4" and "unknowns" in i.where
                             for i in result.issues))

    def test_nonempty_unknowns_preserved_not_flagged(self):
        text = GOOD.replace(
            "  unknowns: []\n",
            "  unknowns:\n    - \"exact backup cadence for n-erp not confirmed\"\n",
        )
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "VALID", msg=[i.to_dict() for i in result.issues])


class TestDescriptiveOnlyBoundary(unittest.TestCase):
    """LM-R-16: this schema must NEVER accept a prescriptive field. This
    test proves the boundary is enforced by the validator, not merely
    claimed in a docstring."""

    def test_automation_recommendation_field_rejected(self):
        text = GOOD.rstrip() + '\n  automation_recommendation: "replace the ERP with a SaaS product"\n'
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        rule16 = [i for i in result.issues if i.rule == "LM-R-16"]
        self.assertTrue(rule16, msg=[i.to_dict() for i in result.issues])
        self.assertIn("automation_recommendation", rule16[0].where)
        # Belt-and-braces: it also surfaces in unknown_fields, since it is
        # not a member of REQUIRED_TOP_FIELDS either.
        self.assertIn("automation_recommendation", result.unknown_fields)

    def test_proposed_change_field_rejected(self):
        text = GOOD.rstrip() + '\n  proposed_change: "automate the finance approval workflow"\n'
        result = validate_legacy_system_map(text)
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-16" for i in result.issues))

    def test_all_forbidden_fields_rejected(self):
        for f in ("automation_recommendation", "proposed_change",
                   "suggested_fix", "recommended_action", "transformation_plan"):
            text = GOOD.rstrip() + f'\n  {f}: "some prescriptive opinion"\n'
            result = validate_legacy_system_map(text)
            self.assertEqual(result.status, "INVALID", msg=f"{f} should be rejected")
            self.assertTrue(any(i.rule == "LM-R-16" for i in result.issues),
                             msg=f"{f} should trip LM-R-16")


class TestFailClosed(unittest.TestCase):
    def test_never_returns_bare_bool_on_error_path(self):
        result = validate_legacy_system_map(None)  # type: ignore[arg-type]
        self.assertEqual(result.status, "INVALID")
        self.assertTrue(any(i.rule == "LM-R-0" for i in result.issues))


if __name__ == "__main__":
    unittest.main()
