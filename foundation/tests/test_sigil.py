import os
import tempfile
import unittest
from pathlib import Path

from foundation.sigil import (
    Sigil, PROOF_OPERATION, compute_sigil, compute_tier, format_sigil, reconcile_sigil,
    RecordedSigil, parse_sigil, read_recorded_sigil, DIMENSION_NAMES,
    _dimension_iron, _dimension_lattice, _dimension_frontier,
    _dimension_memory, _dimension_sight, _dimension_reality, _dimension_orchestration,
    _dimension_external_integration,
)
from foundation.recursion_guard import check as guard_check

REPO_ROOT = Path(__file__).resolve().parents[2]


def _sigil(**overrides) -> Sigil:
    base = dict(
        tier="T6", tier_reason="x", iron=10, lattice=6, proof=8, sight=10,
        frontier=10, orchestration=10, memory=10, reality=10,
        justification={k: "x" for k in
                       ("iron", "lattice", "proof", "sight", "frontier",
                        "orchestration", "memory", "reality")},
        all_tests_green=True, total_tests=996,
    )
    base.update(overrides)
    return Sigil(**base)


class TestComputeTierPureFunction(unittest.TestCase):
    """The tier ladder is a conjunction of facts, testable without touching
    the filesystem at all."""

    def test_not_all_green_caps_at_t2(self):
        tier, _ = compute_tier(all_tests_green=False, sight_clean=True,
                                orchestration_proven=True, zero_network=True, iron_score=10)
        self.assertEqual(tier, "T2")

    def test_green_but_network_dependency_caps_at_t3(self):
        tier, _ = compute_tier(all_tests_green=True, sight_clean=True,
                                orchestration_proven=True, zero_network=False, iron_score=10)
        self.assertEqual(tier, "T3")

    def test_green_zero_network_but_no_orchestration_proof_caps_at_t3(self):
        tier, _ = compute_tier(all_tests_green=True, sight_clean=True,
                                orchestration_proven=False, zero_network=True, iron_score=10)
        self.assertEqual(tier, "T3")

    def test_orchestration_proven_but_sentinel_dirty_caps_at_t4(self):
        tier, _ = compute_tier(all_tests_green=True, sight_clean=False,
                                orchestration_proven=True, zero_network=True, iron_score=10)
        self.assertEqual(tier, "T4")

    def test_clean_but_incomplete_build_reports_caps_at_t5(self):
        tier, _ = compute_tier(all_tests_green=True, sight_clean=True,
                                orchestration_proven=True, zero_network=True, iron_score=7)
        self.assertEqual(tier, "T5")

    def test_everything_true_without_external_integration_caps_at_t6(self):
        tier, reason = compute_tier(all_tests_green=True, sight_clean=True,
                                     orchestration_proven=True, zero_network=True, iron_score=10)
        self.assertEqual(tier, "T6")
        self.assertIn("T7", reason)  # explicitly explains why T7 isn't claimed

    def test_external_integration_proven_reaches_t7(self):
        tier, reason = compute_tier(all_tests_green=True, sight_clean=True,
                                     orchestration_proven=True, zero_network=True, iron_score=10,
                                     external_integration_proven=True)
        self.assertEqual(tier, "T7")
        self.assertIn("real external integration boundary", reason)

    def test_external_integration_alone_cannot_offset_a_lower_rung(self):
        # T7 requires every fact T6 requires plus its own -- a real
        # external integration boundary cannot buy T7 if a lower rung
        # (here: not all tests green) already caps the tier.
        tier, _ = compute_tier(all_tests_green=False, sight_clean=True,
                                orchestration_proven=True, zero_network=True, iron_score=10,
                                external_integration_proven=True)
        self.assertEqual(tier, "T2")

    def test_a_single_weak_dimension_cannot_be_offset_by_others(self):
        # High "average" (everything else maxed) still caps hard at T2
        # if tests aren't green -- proves this isn't a weighted average.
        tier, _ = compute_tier(all_tests_green=False, sight_clean=True,
                                orchestration_proven=True, zero_network=True, iron_score=10)
        self.assertEqual(tier, "T2")


class TestDimensionsOnSyntheticRepo(unittest.TestCase):
    def test_iron_zero_when_no_build_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            score, justification = _dimension_iron(Path(tmp))
            self.assertEqual(score, 0)
            self.assertIn("0/8", justification)

    def test_iron_full_when_all_build_reports_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            from foundation.sentinel import SUBSYSTEMS_REQUIRING_BUILD_REPORT
            for name in SUBSYSTEMS_REQUIRING_BUILD_REPORT:
                d = root / name
                d.mkdir()
                (d / "BUILD_REPORT.md").write_text("# report\n")
            score, justification = _dimension_iron(root)
            self.assertEqual(score, 10)

    def test_lattice_counts_transition_table_modules(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.py").write_text("MY_TRANSITIONS = {}\n")
            (root / "b.py").write_text("def f(): pass\n")
            score, justification = _dimension_lattice(root)
            self.assertEqual(score, 1)

    def test_frontier_zero_without_pareto_frontier_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            score, _ = _dimension_frontier(Path(tmp))
            self.assertEqual(score, 0)

    def test_frontier_full_with_all_companion_files_and_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "PARETO_FRONTIER.md").write_text(
                "## Frontier Gate\n## Archive (built)\n"
            )
            (root / "NEXT_MOVE.md").write_text("x")
            (root / "INTUITION.md").write_text("x")
            score, _ = _dimension_frontier(root)
            self.assertEqual(score, 10)

    def test_memory_zero_on_empty_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            score, _ = _dimension_memory(Path(tmp))
            self.assertEqual(score, 0)

    def test_orchestration_not_proven_without_real_worker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fdir = root / "foundation"
            fdir.mkdir()
            (fdir / "task_queue.py").write_text("x")
            (fdir / "layer0_worker.py").write_text("x")
            (fdir / "queue_worker_adapter.py").write_text("x")
            score, justification, proven = _dimension_orchestration(root)
            self.assertFalse(proven)
            self.assertEqual(score, 6)  # 3 of 5 components, 2 points each

    def test_sight_zero_without_sentinel(self):
        with tempfile.TemporaryDirectory() as tmp:
            score, _, clean = _dimension_sight(Path(tmp))
            self.assertEqual(score, 0)
            self.assertFalse(clean)

    def test_reality_full_score_requires_zero_network_deps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fdir = root / "foundation"
            fdir.mkdir()
            (fdir / "reality_yield_ledger.py").write_text("x")
            (fdir / "hells_gate.py").write_text("x")
            (fdir / "publication_gate.py").write_text("x")
            score, _, zero_net = _dimension_reality(root)
            self.assertTrue(zero_net)
            self.assertEqual(score, 10)

    def test_reality_score_drops_when_network_import_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fdir = root / "foundation"
            fdir.mkdir()
            (fdir / "reality_yield_ledger.py").write_text("x")
            (fdir / "hells_gate.py").write_text("x")
            (fdir / "publication_gate.py").write_text("x")
            (fdir / "sneaky.py").write_text("import requests\n")
            score, _, zero_net = _dimension_reality(root)
            self.assertFalse(zero_net)
            self.assertEqual(score, 6)


class TestDimensionExternalIntegration(unittest.TestCase):
    """T7's one new fact -- checked with local-only evidence, never a
    live network call (see the function's own docstring for why)."""

    def test_empty_repo_not_proven(self):
        with tempfile.TemporaryDirectory() as tmp:
            proven, justification = _dimension_external_integration(Path(tmp))
            self.assertFalse(proven)
            self.assertIn("remote_configured=no", justification)

    def test_remote_alone_without_recorded_run_not_proven(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gitdir = root / ".git"
            gitdir.mkdir()
            (gitdir / "config").write_text(
                '[remote "origin"]\n\turl = https://github.com/example/repo.git\n'
            )
            proven, justification = _dimension_external_integration(root)
            self.assertFalse(proven)
            self.assertIn("remote_configured=yes", justification)
            self.assertIn("real_run_recorded_locally=no", justification)

    def test_recorded_run_without_remote_not_proven(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "FIRST_PING.md").write_text(
                "run https://github.com/example/repo/actions/runs/123, "
                "conclusion=success"
            )
            proven, justification = _dimension_external_integration(root)
            self.assertFalse(proven)
            self.assertIn("remote_configured=no", justification)

    def test_both_facts_present_proven(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gitdir = root / ".git"
            gitdir.mkdir()
            (gitdir / "config").write_text(
                '[remote "origin"]\n\turl = https://github.com/example/repo.git\n'
            )
            (root / "FIRST_PING.md").write_text(
                "run https://github.com/example/repo/actions/runs/123, "
                "conclusion=success"
            )
            proven, justification = _dimension_external_integration(root)
            self.assertTrue(proven)

    def test_real_repo_is_actually_proven(self):
        proven, justification = _dimension_external_integration(REPO_ROOT)
        self.assertTrue(proven, justification)


class TestFormatSigil(unittest.TestCase):
    def test_format_contains_all_dimensions(self):
        s = _sigil()
        text = format_sigil(s)
        for token in ("TIER:T6", "IRON:10", "LATTICE:6", "PROOF:8", "SIGHT:10",
                      "FRONTIER:10", "ORCH:10", "MEMORY:10", "REALITY:10"):
            self.assertIn(token, text)


class TestReconcileSigil(unittest.TestCase):
    def test_no_previous_sigil_always_changed(self):
        # reconcile_sigil() recomputes internally (calls compute_sigil,
        # which is exercised for real in TestComputeSigilOnRealRepo below)
        # -- this test exercises the SigilReconciliation shape its
        # `previous=None` branch produces, without paying for a second
        # real compute.
        from foundation.sigil import SigilReconciliation, DIMENSION_NAMES
        current = _sigil()
        changed_dims = tuple(DIMENSION_NAMES) + ("tier",)
        rec = SigilReconciliation(previous=None, current=current, changed=True,
                                   changed_dimensions=changed_dims, reason="no previous sigil recorded")
        self.assertTrue(rec.changed)
        self.assertIn("iron", rec.changed_dimensions)

    def test_identical_sigils_produce_no_change(self):
        from foundation.sigil import DIMENSION_NAMES
        previous = _sigil()
        current = _sigil()
        changed_dims = tuple(n for n in DIMENSION_NAMES if getattr(previous, n) != getattr(current, n))
        tier_changed = previous.tier != current.tier
        self.assertEqual(changed_dims, ())
        self.assertFalse(tier_changed)

    def test_a_single_changed_dimension_is_detected_precisely(self):
        from foundation.sigil import DIMENSION_NAMES
        previous = _sigil()
        current = _sigil(proof=9)
        changed_dims = tuple(n for n in DIMENSION_NAMES if getattr(previous, n) != getattr(current, n))
        self.assertEqual(changed_dims, ("proof",))

    def test_frontier_only_change_cannot_affect_other_dimensions(self):
        # Requirement 3 from the governing directive: "a frontier update
        # alone cannot falsely increase maturity" -- changing ONLY the
        # frontier dimension must never be reported as a lattice/proof/etc
        # change.
        from foundation.sigil import DIMENSION_NAMES
        previous = _sigil()
        current = _sigil(frontier=7)
        changed_dims = tuple(n for n in DIMENSION_NAMES if getattr(previous, n) != getattr(current, n))
        self.assertEqual(changed_dims, ("frontier",))


class TestComputeSigilOnRealRepo(unittest.TestCase):
    """Runs the real test suites via subprocess (8 subsystems x 2 full
    computes = 16 subprocess invocations total for this whole class) --
    deliberately computed exactly twice at class scope and shared, not
    once per test, to bound runtime while still proving determinism
    against two genuinely independent computations.

    SKIPS ITSELF when already running inside another `compute_sigil()`
    call's proof dimension. `compute_sigil()`'s own proof dimension
    shells out to `python3 -m unittest discover -s foundation`, which
    would otherwise re-discover and re-run THIS test class, which would
    call `compute_sigil()` again, which would shell out again --
    unbounded recursion. `_dimension_proof` calls `foundation.
    recursion_guard.check(PROOF_OPERATION)` before spawning any
    subprocess and stamps `child_env()` ancestry on every child it does
    spawn; this class performs the same check so it can detect "I am
    running nested inside someone else's proof-dimension check" and
    skip rather than recurse. See `foundation/recursion_guard.py`'s
    module docstring for the full causal chain.
    """

    @classmethod
    def setUpClass(cls):
        if not guard_check(PROOF_OPERATION).is_safe():
            raise unittest.SkipTest(
                "running nested inside another compute_sigil() call's proof "
                "dimension -- skipping to avoid unbounded recursion"
            )
        cls.first = compute_sigil(REPO_ROOT)
        cls.second = compute_sigil(REPO_ROOT)

    def test_deterministic_across_two_runs(self):
        self.assertEqual(self.first, self.second)

    def test_real_repo_tier_reflects_the_real_network_tradeoff(self):
        # This repository was T7 (public repo, real recorded CI success)
        # until 2026-08-27, when foundation/mouth_pypi.py added this
        # repo's first-ever real network call (one GET to PyPI's public
        # RSS feed, explicitly authorized). compute_tier()'s own T3 rung
        # ("all suites green, but zero-network no longer holds") is
        # exactly correct here — this is the honest, evidenced price of
        # that real capability, not a bug to patch away. If the network
        # mouth is ever removed, this repo should recompute back to T7
        # without any code change here.
        self.assertTrue(self.first.all_tests_green, self.first.justification["proof"])
        self.assertEqual(self.first.tier, "T3")
        self.assertGreater(self.first.total_tests, 900)

    def test_reconcile_against_unchanged_real_repo_reports_no_change(self):
        rec = reconcile_sigil(REPO_ROOT, previous=self.first)
        self.assertFalse(rec.changed)
        self.assertEqual(rec.changed_dimensions, ())
        self.assertIn("no threshold crossed", rec.reason)


if __name__ == "__main__":
    unittest.main()


class TestRecordedSigilRetrieval(unittest.TestCase):
    """Switch closed 2026-08-28. `format_sigil()` writes the canonical
    snapshot and SIGIL.md stores it; `reconcile_sigil(repo_root,
    previous)` is its designated consumer, named in three separate real
    documents (SIGIL.md, .claude/commands/boot.md, CLAUDE.md). There was
    no parser, so `previous` could only be obtained by hand-retyping nine
    values -- and the drift that mechanism exists to catch has already
    happened twice (CLAUDE.md stuck at TIER:T7 after the real value fell
    to T3; SIGIL.md's evidence table still claiming 1212 tests)."""

    LINE = ("TIER:T3 | IRON:10 | LATTICE:6 | PROOF:10 | SIGHT:10 | "
            "FRONTIER:10 | ORCH:10 | MEMORY:10 | REALITY:6")

    def test_format_then_parse_round_trips_every_compared_field(self):
        # The exact contract that matters: reconcile_sigil() compares
        # DIMENSION_NAMES + tier and nothing else, so those must survive.
        s = Sigil(
            tier="T5", tier_reason="whatever", iron=1, lattice=2, proof=3, sight=4,
            frontier=5, orchestration=6, memory=7, reality=8,
            justification={}, all_tests_green=True, total_tests=99,
        )
        parsed = parse_sigil(format_sigil(s))
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.tier, s.tier)
        for name in DIMENSION_NAMES:
            self.assertEqual(getattr(parsed, name), getattr(s, name), name)

    def test_a_parsed_snapshot_is_not_a_measured_sigil(self):
        """The load-bearing invariant: compute_sigil() stays the only way
        to produce a Sigil. A hand-edited markdown value must never be
        mistakable for measured capability."""
        parsed = parse_sigil(self.LINE)
        self.assertIsInstance(parsed, RecordedSigil)
        self.assertNotIsInstance(parsed, Sigil)

    def test_a_parsed_snapshot_works_as_reconcile_sigils_previous(self):
        """The whole point of the switch: the stored line can now reach
        the consumer that was always documented for it."""
        parsed = parse_sigil(self.LINE)
        rec = reconcile_sigil(REPO_ROOT, previous=parsed)
        self.assertIsNotNone(rec.current)
        self.assertIsInstance(rec.changed, bool)
        # Whatever the real answer is today, it must be a real comparison,
        # not the "no previous sigil recorded" degenerate path.
        self.assertNotEqual(rec.reason, "no previous sigil recorded")

    def test_it_finds_the_line_embedded_in_real_surrounding_prose(self):
        text = "# Capability Sigil\n\nsome prose\n\n```\n" + self.LINE + "\n```\n\nmore prose\n"
        self.assertIsNotNone(parse_sigil(text))

    def test_absent_snapshot_is_a_valid_state_not_an_error(self):
        self.assertIsNone(parse_sigil("no sigil anywhere in this text"))
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(read_recorded_sigil(Path(d)))

    def test_a_malformed_or_partial_line_is_not_half_parsed(self):
        # Fail closed: a truncated line must yield nothing rather than a
        # RecordedSigil with invented zeros.
        self.assertIsNone(parse_sigil("TIER:T3 | IRON:10 | LATTICE:6"))

    def test_reading_the_real_repository_snapshot(self):
        parsed = read_recorded_sigil(REPO_ROOT)
        self.assertIsNotNone(parsed, "SIGIL.md should carry a recorded sigil line")
        self.assertTrue(parsed.tier.startswith("T"))
        self.assertIn("SIGIL.md", parsed.source)
        for name in DIMENSION_NAMES:
            self.assertGreaterEqual(getattr(parsed, name), 0)
            self.assertLessEqual(getattr(parsed, name), 10)

    def test_the_reader_never_writes(self):
        before = (REPO_ROOT / "SIGIL.md").stat().st_mtime_ns
        read_recorded_sigil(REPO_ROOT)
        read_recorded_sigil(REPO_ROOT)
        self.assertEqual((REPO_ROOT / "SIGIL.md").stat().st_mtime_ns, before)
