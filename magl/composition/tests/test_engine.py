"""Tests for magl/composition/engine.py."""

from __future__ import annotations

import unittest

from magl.composition.engine import MAGLSummary, check_composition


def _magl(magl_id: str, **kwargs) -> MAGLSummary:
    defaults = dict(magl_id=magl_id, version="1.0.0")
    defaults.update(kwargs)
    return MAGLSummary(**defaults)


class TestCompatibleComposition(unittest.TestCase):
    def test_two_compatible_magls_are_composable(self):
        a = _magl("a", provides=("cap.x",))
        b = _magl("b", requires=("cap.x",))
        report = check_composition([a, b])
        self.assertEqual(report.verdict, "COMPOSABLE")
        self.assertFalse(report.fatal_findings())

    def test_findings_never_dropped_even_when_composable(self):
        a = _magl("a", provides=("cap.x",))
        b = _magl("b", requires=("cap.x",))
        report = check_composition([a, b])
        # No-op steps (1, 5, 8, 9) must still appear.
        checks_seen = {f.check for f in report.findings}
        for expected in (
            "1_schema_compatibility", "5_side_effects",
            "8_conflicting_invariants", "9_provenance_conflicts",
            "7_privilege_escalation",
        ):
            self.assertIn(expected, checks_seen)


class TestJurisdictionConflict(unittest.TestCase):
    def test_prohibited_action_granted_elsewhere_is_fatal(self):
        a = _magl("a", prohibited_actions=("delete_user_data",))
        b = _magl("b", may_execute=("delete_user_data",))
        report = check_composition([a, b])
        self.assertEqual(report.verdict, "REFUSED")
        fatals = [f for f in report.fatal_findings()
                  if f.check == "2_jurisdiction_comparison"]
        self.assertEqual(len(fatals), 1)
        self.assertEqual(set(fatals[0].involved_magl_ids), {"a", "b"})


class TestIncompatibilityDeclaration(unittest.TestCase):
    def test_declared_incompatible_pair_present_is_fatal(self):
        a = _magl("a", dependencies_incompatible=("b",))
        b = _magl("b")
        report = check_composition([a, b])
        self.assertEqual(report.verdict, "REFUSED")
        fatals = [f for f in report.fatal_findings()
                  if f.check == "4_incompatibility_comparison"]
        self.assertEqual(len(fatals), 1)
        self.assertEqual(set(fatals[0].involved_magl_ids), {"a", "b"})

    def test_incompatibility_naming_absent_magl_is_not_flagged(self):
        a = _magl("a", dependencies_incompatible=("nonexistent",))
        b = _magl("b")
        report = check_composition([a, b])
        fatals = [f for f in report.fatal_findings()
                  if f.check == "4_incompatibility_comparison"]
        self.assertEqual(fatals, [])


class TestCircularDependency(unittest.TestCase):
    def test_three_way_requires_provides_cycle_is_fatal(self):
        a = _magl("a", requires=("z",), provides=("x",))
        b = _magl("b", requires=("x",), provides=("y",))
        c = _magl("c", requires=("y",), provides=("z",))
        report = check_composition([a, b, c])
        self.assertEqual(report.verdict, "REFUSED")
        fatals = [f for f in report.fatal_findings()
                  if f.check == "6_circular_dependency"]
        self.assertEqual(len(fatals), 1)
        self.assertEqual(set(fatals[0].involved_magl_ids), {"a", "b", "c"})

    def test_no_cycle_when_chain_is_linear(self):
        a = _magl("a", requires=("x",))
        b = _magl("b", requires=("y",), provides=("x",))
        c = _magl("c", provides=("y",))
        report = check_composition([a, b, c])
        fatals = [f for f in report.fatal_findings()
                  if f.check == "6_circular_dependency"]
        self.assertEqual(fatals, [])


class TestMissingDependency(unittest.TestCase):
    def test_unsatisfied_dependencies_required_is_warning_not_fatal(self):
        a = _magl("a", dependencies_required=("some-other-magl-capability",))
        b = _magl("b")
        report = check_composition([a, b])
        # Judgment call: MISSING_DEPENDENCY is WARNING, not FATAL — it may
        # be satisfied externally to this composed set.
        self.assertEqual(report.verdict, "COMPOSABLE")
        warnings = [f for f in report.findings
                    if f.check == "3_dependency_comparison"
                    and f.severity == "WARNING"]
        self.assertEqual(len(warnings), 1)
        self.assertIn("a", warnings[0].involved_magl_ids)

    def test_satisfied_dependency_required_produces_no_warning(self):
        a = _magl("a", dependencies_required=("cap.thing",))
        b = _magl("b", provides=("cap.thing",))
        report = check_composition([a, b])
        warnings = [f for f in report.findings
                    if f.check == "3_dependency_comparison"]
        self.assertEqual(warnings, [])


class TestJurisdictionUnionInvariant(unittest.TestCase):
    def test_composed_jurisdiction_is_exactly_union_of_individual(self):
        a = _magl("a", may_write=("w1",), may_execute=("e1",))
        b = _magl("b", may_call=("c1",), may_publish=("p1",))
        c = _magl("c", may_modify=("m1",))
        report = check_composition([a, b, c])

        composed_union: set[str] = set()
        for m in (a, b, c):
            composed_union.update(m.granted_actions())

        expected = {"w1", "e1", "c1", "p1", "m1"}
        self.assertEqual(composed_union, expected)

        invariant_findings = [f for f in report.findings
                               if f.check == "7_privilege_escalation"]
        self.assertEqual(len(invariant_findings), 1)
        self.assertEqual(invariant_findings[0].severity, "INFO")
        self.assertIn("union", invariant_findings[0].what.lower() +
                       invariant_findings[0].why.lower())


class TestEmptyAndSingletonComposition(unittest.TestCase):
    def test_empty_composition_is_trivially_composable(self):
        report = check_composition([])
        self.assertEqual(report.verdict, "COMPOSABLE")
        self.assertFalse(report.fatal_findings())

    def test_single_magl_composition_is_trivially_composable(self):
        a = _magl("a", prohibited_actions=("anything",), may_execute=("anything",))
        report = check_composition([a])
        # A single MAGL can't conflict with itself in this engine's model.
        self.assertEqual(report.verdict, "COMPOSABLE")
        self.assertFalse(report.fatal_findings())


class TestMultipleIndependentFatalFindings(unittest.TestCase):
    def test_all_fatal_reasons_reported_not_just_first(self):
        a = _magl(
            "a",
            prohibited_actions=("delete_user_data",),
            dependencies_incompatible=("b",),
        )
        b = _magl("b", may_execute=("delete_user_data",))
        report = check_composition([a, b])
        self.assertEqual(report.verdict, "REFUSED")
        checks = {f.check for f in report.fatal_findings()}
        self.assertIn("2_jurisdiction_comparison", checks)
        self.assertIn("4_incompatibility_comparison", checks)


if __name__ == "__main__":
    unittest.main()
