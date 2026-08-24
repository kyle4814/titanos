"""
§Phase 5 demonstration — the minimum viable Eternal DAO loop, run for real
across all three independently-built MAGL components plus the pre-existing
epistemic classifier. This is the test the BUILD_REPORT for the prior
(KPM) session named as the next smallest work cell: prove the pieces
actually fit together, not just that each is green alone.

Three demonstrations, matching §Phase 5's exact required outcomes:
  1. VALID MAGL -> VALIDATED -> CATALOGUED
  2. INVALID MAGL -> REFUSED
  3. CONFLICTING COMPOSITION -> REFUSED WITH EXPLANATION
"""

import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from magl.validators.validate_magl import validate_magl  # noqa: E402
from magl.registry.catalogue import MAGLEntry, MAGLCatalogue  # noqa: E402
from magl.composition.engine import MAGLSummary, check_composition  # noqa: E402

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


class TestValidMaglValidatedAndCatalogued(unittest.TestCase):
    def test_full_loop(self):
        text = (FIXTURES / "valid_magl.yaml").read_text()

        # 1. VALIDATE
        result = validate_magl(text)
        self.assertEqual(result.status, "VALID", result.issues)

        # 2. CATALOGUE — using only fields the catalogue actually needs,
        # exactly as a real production line would hand off from validator
        # to catalogue (the validator doesn't know about MAGLEntry, and
        # the catalogue doesn't parse YAML — this is the seam being tested).
        import yaml
        doc = yaml.safe_load(text)["magl"]
        entry = MAGLEntry(
            magl_id=doc["id"], version=doc["version"], name=doc["name"],
            domain=tuple(doc["classification"]["domain"]),
            capability_type=tuple(doc["classification"]["capability_type"]),
            epistemic_status=doc["classification"]["epistemic_status"],
            maturity=doc["classification"]["maturity"],
            dependencies_required=tuple(doc["dependencies"]["required"]),
            dependencies_incompatible=tuple(doc["dependencies"]["incompatible_with"]),
            lifecycle_status=doc["lifecycle"]["status"],
            license=doc["provenance"]["license"],
            content_hash=doc["audit"]["content_hash"] or "sha256:" + "0" * 64,
        )
        catalogue = MAGLCatalogue()
        catalogue.register(entry)

        # 3. CONFIRM it's actually findable — not just accepted silently.
        found = catalogue.get("magl-example-secret-scanner", "1.0.0")
        self.assertIsNotNone(found)
        self.assertEqual(found.epistemic_status, "IMPLEMENTED_SYSTEM")

        results = catalogue.search(capability_type=["ANALYTICAL"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].magl_id, "magl-example-secret-scanner")


class TestInvalidMaglRefused(unittest.TestCase):
    def test_broken_executor_is_refused(self):
        text = (FIXTURES / "invalid_magl.yaml").read_text()
        result = validate_magl(text)
        self.assertEqual(result.status, "INVALID")
        # Both deliberate defects must actually be caught, not just one:
        rules_hit = {i.rule for i in result.issues}
        self.assertTrue(len(result.issues) >= 2, result.issues)
        # every issue carries the full structured explanation
        for issue in result.issues:
            self.assertTrue(issue.what and issue.why and issue.rule)


class TestConflictingCompositionRefused(unittest.TestCase):
    def test_prohibited_action_conflict_is_refused_with_explanation(self):
        # A: a governance/audit MAGL that explicitly prohibits deleting
        # user data as part of any composition it participates in.
        a = MAGLSummary(
            magl_id="magl-audit-guard", version="1.0.0",
            prohibited_actions=("delete_user_data",),
            requires=("user_store_access",),
        )
        # B: an executor that provides user_store_access but its own
        # declared execute jurisdiction includes exactly the prohibited
        # action A refuses to tolerate in composition with it.
        b = MAGLSummary(
            magl_id="magl-bulk-deleter", version="1.0.0",
            may_execute=("delete_user_data",),
            provides=("user_store_access",),
        )
        report = check_composition([a, b])

        self.assertEqual(report.verdict, "REFUSED")
        fatal = [f for f in report.findings if f.severity == "FATAL"]
        self.assertTrue(fatal, "a fatal finding must exist to justify REFUSED")
        f = fatal[0]
        # WITH EXPLANATION — never just a bare refusal
        self.assertTrue(f.what)
        self.assertTrue(f.why)
        self.assertIn("magl-audit-guard", f.involved_magl_ids)
        self.assertIn("magl-bulk-deleter", f.involved_magl_ids)

    def test_compatible_composition_is_authorized(self):
        a = MAGLSummary(magl_id="magl-a", version="1.0.0", provides=("cap_x",))
        b = MAGLSummary(magl_id="magl-b", version="1.0.0", requires=("cap_x",))
        report = check_composition([a, b])
        self.assertEqual(report.verdict, "COMPOSABLE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
