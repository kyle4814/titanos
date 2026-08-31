"""Tests for the demand-direction classifier.

The cases below are drawn from a real live sweep, not invented. The
label sets on the WORK_OFFERED cases are the actual labels
`Vynix-Labs/Soroban-state-lens`, `promisszn/soroban-amm` and
`ConvoBrains/zero-cost-crm` carried; the NEED_NOT_EXCLUDED cases are the
actual labels `mlflow/mlflow`, `openssl/openssl` and
`open-telemetry/opentelemetry.io` carried in the same sweep. A
classifier that separates the first group from the second on invented
data has demonstrated nothing.
"""

import unittest

from foundation.demand_direction import (
    DIRECTIONS, MIN_GRADING_AXES, SOLE_AUTHOR_SHARE, REJECTED_DISCRIMINATORS,
    DemandDirection, classify_direction,
)
from foundation.tentacles import github_issue_demand_signal

# The real label set, verbatim from the killing experiment.
VYNIX = ["enhancement", "good first issue", "help wanted", "phase:7",
         "area:tooling", "size:xs", "Stellar Wave", "difficulty:beginner"]
SOROBAN_AMM = ["help wanted", "Stellar Wave", "complexity: medium", "bug"]
ZERO_COST_CRM = ["enhancement", "help wanted", "good first issue", "a11y",
                 "frontend", "easy", "first-timers-only"]
MLFLOW = ["good first issue", "help wanted"]
OPENSSL = ["help wanted"]
OTEL = ["help wanted", "good first issue", "lang:pt",
        "triage:accepted:needs-pr"]


class TestTheFarmIsCaught(unittest.TestCase):

    def test_vynix_is_recruitment(self):
        d = classify_direction(VYNIX)
        self.assertEqual(d.direction, "WORK_OFFERED")
        self.assertTrue(d.is_recruitment())
        self.assertFalse(d.counts_as_demand())

    def test_vynix_convicted_by_grading_depth_not_by_one_label(self):
        d = classify_direction(VYNIX)
        self.assertGreaterEqual(len(d.grading_axes), MIN_GRADING_AXES)
        self.assertEqual(set(d.grading_axes), {"difficulty:", "phase:",
                                               "size:"})

    def test_cohort_label_is_surfaced(self):
        self.assertEqual(classify_direction(VYNIX).cohort_label,
                         "stellar wave")

    def test_reservation_label_alone_convicts(self):
        """`first-timers-only` needs no threshold: the door is closed."""
        d = classify_direction(ZERO_COST_CRM)
        self.assertEqual(d.direction, "WORK_OFFERED")
        self.assertEqual(d.reservation_labels, ("first-timers-only",))
        self.assertEqual(d.grading_axes, ())

    def test_soroban_amm_needs_authorship_to_convict(self):
        """Labels alone are genuinely insufficient here, and the classifier
        says so rather than reaching for a verdict it cannot support."""
        self.assertEqual(classify_direction(SOROBAN_AMM).direction,
                         "NEED_NOT_EXCLUDED")
        self.assertEqual(
            classify_direction(SOROBAN_AMM, sole_author_share=1.0).direction,
            "WORK_OFFERED")


class TestLegitimateProjectsSurvive(unittest.TestCase):
    """The false positives that would have made this instrument worthless."""

    def test_lone_good_first_issue_is_not_a_farm(self):
        for labels in (MLFLOW, OTEL):
            with self.subTest(labels=labels):
                self.assertEqual(classify_direction(labels).direction,
                                 "NEED_NOT_EXCLUDED")

    def test_one_grading_axis_is_triage(self):
        d = classify_direction(OTEL)
        self.assertEqual(d.direction, "NEED_NOT_EXCLUDED")
        self.assertLess(len(d.grading_axes), MIN_GRADING_AXES)

    def test_plain_help_wanted_survives(self):
        self.assertEqual(classify_direction(OPENSSL).direction,
                         "NEED_NOT_EXCLUDED")

    def test_solo_maintainer_with_real_bugs_is_not_a_programme(self):
        """The most important negative control. A one-person project
        writes all of its own issues; that is not a curriculum."""
        d = classify_direction(["help wanted", "bug"], sole_author_share=1.0)
        self.assertEqual(d.direction, "NEED_NOT_EXCLUDED")

    def test_sole_authorship_alone_never_convicts(self):
        for share in (0.9, 0.95, 1.0):
            with self.subTest(share=share):
                self.assertEqual(
                    classify_direction(["bug", "help wanted"],
                                       sole_author_share=share).direction,
                    "NEED_NOT_EXCLUDED")


class TestUnknownIsNotDemand(unittest.TestCase):

    def test_no_labels_is_unknown(self):
        d = classify_direction([])
        self.assertEqual(d.direction, "UNKNOWN")

    def test_unknown_does_not_count_as_demand(self):
        """Unknown is not true. An ask with nothing to read on it must not
        pass the demand gate by default."""
        self.assertFalse(classify_direction([]).counts_as_demand())
        self.assertFalse(classify_direction(["   "]).counts_as_demand())

    def test_every_direction_is_declared(self):
        for labels, share in ((VYNIX, None), (MLFLOW, None), ([], None)):
            self.assertIn(classify_direction(labels, share).direction,
                          DIRECTIONS)


class TestVerdictCarriesItsEvidence(unittest.TestCase):

    def test_every_verdict_states_a_reason(self):
        for labels in (VYNIX, MLFLOW, OPENSSL, ZERO_COST_CRM, []):
            with self.subTest(labels=labels):
                self.assertTrue(classify_direction(labels).reasons)

    def test_need_not_excluded_disclaims_itself(self):
        """The name is the whole point: it must not read as verified
        demand anywhere it is displayed."""
        math = classify_direction(MLFLOW).show_the_math()
        self.assertIn("NOT evidence that a real need exists", math)

    def test_rejected_discriminator_is_recorded(self):
        joined = " ".join(REJECTED_DISCRIMINATORS)
        self.assertIn("fork:star", joined)
        self.assertIn("opentelemetry.io", joined)

    def test_labels_are_case_and_space_insensitive(self):
        self.assertEqual(
            classify_direction(["  FIRST-TIMERS-ONLY  "]).direction,
            "WORK_OFFERED")


class TestDemandGateConsultsDirection(unittest.TestCase):
    """The wiring. A classifier nothing calls changes nothing."""

    def _item(self, labels, **kw):
        base = dict(repo="acme/widget", number=7, title="t", labels=labels,
                    comments=5, assignees=[], state="open",
                    created_at="2026-08-01T00:00:00Z",
                    updated_at="2026-08-30T00:00:00Z",
                    html_url="https://example.invalid/7")
        base.update(kw)
        return base

    def test_recruitment_ask_is_not_explicit_demand(self):
        sig = github_issue_demand_signal(self._item(VYNIX))
        self.assertEqual(sig.pressure_class, "NONE")
        self.assertEqual(sig.evidence["demand_direction"], "WORK_OFFERED")

    def test_real_ask_still_registers_as_demand(self):
        sig = github_issue_demand_signal(self._item(["help wanted"]))
        self.assertEqual(sig.pressure_class, "EXPLICIT_DEMAND")
        self.assertEqual(sig.evidence["demand_direction"],
                         "NEED_NOT_EXCLUDED")

    def test_assignment_gate_still_holds(self):
        """The earlier gate must not have been traded away for this one."""
        sig = github_issue_demand_signal(
            self._item(["help wanted"], assignees=["someone"]))
        self.assertEqual(sig.pressure_class, "NONE")

    def test_recruitment_is_named_in_the_unknowns(self):
        sig = github_issue_demand_signal(self._item(VYNIX))
        self.assertTrue(any("recruitment material" in u
                            for u in sig.unknowns))

    def test_reasons_travel_with_the_signal(self):
        sig = github_issue_demand_signal(self._item(VYNIX))
        self.assertTrue(sig.evidence["direction_reasons"])

    def test_the_spine_independently_refuses_an_unevidenced_claim(self):
        """The second enforcement point, made visible.

        Found by mutation: deleting the direction check from
        `pressure_class` alone does not produce a signal that lies -- it
        produces no signal at all, because `CanonicalSignal.__post_init__`
        separately refuses EXPLICIT_DEMAND with empty pressure_evidence.
        That independent refusal was real but only observable by breaking
        the module, so it is asserted here directly.
        """
        from foundation.signal_spine import CanonicalSignal, SignalIntegrityError
        with self.assertRaises(SignalIntegrityError):
            CanonicalSignal(
                signal_id="X", source_id="s", source_type="PLATFORM",
                source_ref="r", target="acme/widget", kind="DEMAND",
                claim="c", observed_at="2026-08-31T00:00:00+00:00",
                event_at="2026-08-31T00:00:00+00:00",
                source_lineage="l",
                pressure_class="EXPLICIT_DEMAND", pressure_evidence="")

    def test_sole_author_share_reaches_the_classifier(self):
        sig = github_issue_demand_signal(
            self._item(SOROBAN_AMM, sole_author_share=1.0))
        self.assertEqual(sig.evidence["demand_direction"], "WORK_OFFERED")
        self.assertEqual(sig.pressure_class, "NONE")


if __name__ == "__main__":
    unittest.main()
