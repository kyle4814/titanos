import os
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from foundation import sigil
from foundation.sigil import (
    Sigil, PROOF_OPERATION, compute_sigil, compute_tier, format_sigil, reconcile_sigil,
    RecordedSigil, parse_sigil, read_recorded_sigil, DIMENSION_NAMES,
    _dimension_iron, _dimension_lattice, _dimension_frontier,
    _dimension_memory, _dimension_sight, _dimension_reality, _dimension_orchestration,
    _dimension_external_integration, _defines,
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
                (d / "BUILD_REPORT.md").write_text(
                    "# report\n\nheading plus body -- a bare heading no longer counts.\n")
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
            # Real symbol definitions, not placeholder text: since
            # 2026-08-29 these dimensions require the module to actually
            # define its named capability, not merely exist.
            (fdir / "task_queue.py").write_text("class TaskQueue: pass\nclass Task: pass\n")
            (fdir / "layer0_worker.py").write_text(
                "def should_halt(): pass\nclass CycleRecord: pass\n")
            (fdir / "queue_worker_adapter.py").write_text(
                "def make_worker_perform(): pass\ndef make_worker_verify(): pass\n")
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
            (fdir / "reality_yield_ledger.py").write_text(
                "class YieldComponent: pass\nclass LedgerEntry: pass\n")
            (fdir / "hells_gate.py").write_text(
                "class HellsGateArtifact: pass\nclass HellsGateDecision: pass\n")
            (fdir / "publication_gate.py").write_text(
                "class PublicationSwitch: pass\nclass PublicationDecision: pass\n")
            score, _, zero_net = _dimension_reality(root)
            self.assertTrue(zero_net)
            self.assertEqual(score, 10)

    def test_reality_score_drops_when_network_import_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fdir = root / "foundation"
            fdir.mkdir()
            (fdir / "reality_yield_ledger.py").write_text(
                "class YieldComponent: pass\nclass LedgerEntry: pass\n")
            (fdir / "hells_gate.py").write_text(
                "class HellsGateArtifact: pass\nclass HellsGateDecision: pass\n")
            (fdir / "publication_gate.py").write_text(
                "class PublicationSwitch: pass\nclass PublicationDecision: pass\n")
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
        # Optional skip for the tight dev loop: `TITAN_SKIP_REALREPO_SIGIL=1`
        # (set by `run_all_tests.sh --fast`) skips this ~4-minute class.
        # Default/unset runs it in full — pre-commit and CI keep full coverage.
        if os.environ.get("TITAN_SKIP_REALREPO_SIGIL") == "1":
            raise unittest.SkipTest(
                "TITAN_SKIP_REALREPO_SIGIL=1 -- real-repo sigil skipped in fast mode"
            )
        # The two computes are genuinely independent (that is the whole
        # point -- proving determinism across two separate real computations).
        # Independent means they can run CONCURRENTLY: wall time drops from
        # first+second to ~max(first, second), halving this class's cost with
        # zero loss of what it proves. Both run at guard depth 0 in this one
        # process, so each passes the guard and stamps depth-1 ancestry on its
        # own child subprocesses, exactly as a sequential pair did.
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=2) as pool:
            f1 = pool.submit(compute_sigil, REPO_ROOT)
            f2 = pool.submit(compute_sigil, REPO_ROOT)
            cls.first = f1.result()
            cls.second = f2.result()

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

    @unittest.skipIf(os.environ.get("TITAN_SKIP_REALREPO_SIGIL") == "1",
                     "fast mode: real-repo reconcile (full PROOF) skipped")
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


class TestDefinesRejectsHollowModules(unittest.TestCase):
    """The reproduced defect: capability dimensions used to score on bare
    Path.exists(), so a directory of EMPTY files with the right names
    scored identically to the real repository. See _defines()'s docstring
    for the original reproduction."""

    def _hollow_repo(self, tmp: str) -> Path:
        r = Path(tmp)
        (r / "foundation").mkdir()
        for n in ("task_queue.py", "layer0_worker.py", "queue_worker_adapter.py",
                  "sentinel_worker.py", "crystal.py", "sentinel.py",
                  "secret_scanner.py", "reality_yield_ledger.py",
                  "hells_gate.py", "publication_gate.py"):
            (r / "foundation" / n).write_text("")
        (r / "foundation" / "tests").mkdir()
        (r / "foundation" / "tests" / "test_closed_loop_reality.py").write_text("")
        (r / "MEMORY_MAP.md").write_text("")
        (r / "foundation" / "task_queue.py").write_text("recovery_handoff")
        (r / "PARETO_FRONTIER.md").write_text("## Archive (built)")
        return r

    def test_empty_file_with_the_right_name_scores_nothing_for_orchestration(self):
        with tempfile.TemporaryDirectory() as d:
            score, _justification, proven = _dimension_orchestration(self._hollow_repo(d))
            self.assertEqual(score, 0)
            self.assertFalse(proven)

    def test_empty_file_with_the_right_name_does_not_earn_crystal_credit(self):
        with tempfile.TemporaryDirectory() as d:
            score, justification = _dimension_memory(self._hollow_repo(d))
            self.assertIn("crystal=no", justification)
            self.assertLess(score, 10)

    def test_empty_gate_modules_do_not_earn_full_reality_credit(self):
        with tempfile.TemporaryDirectory() as d:
            hollow, _j, _obelisk = _dimension_reality(self._hollow_repo(d))
            real, _j2, _o2 = _dimension_reality(REPO_ROOT)
            self.assertLess(hollow, real)

    def test_real_repository_scores_are_unchanged_by_the_stricter_check(self):
        # The other half of the proof: tightening the check must not
        # penalise the real repository. If this fails, the symbol names
        # in sigil.py are wrong, not the repository.
        self.assertEqual(_dimension_orchestration(REPO_ROOT)[0], 10)
        self.assertEqual(_dimension_memory(REPO_ROOT)[0], 10)
        self.assertEqual(_dimension_sight(REPO_ROOT)[0], 10)

    def test_defines_finds_indented_class_methods(self):
        # Regression for a real bug in this helper's first draft: a "^"
        # anchor with no leading-whitespace allowance reported a fully
        # populated TestCase file as defining no tests.
        self.assertTrue(_defines(
            REPO_ROOT / "foundation" / "tests" / "test_closed_loop_reality.py", "test_"))

    def test_defines_is_false_for_a_missing_file(self):
        self.assertFalse(_defines(REPO_ROOT / "foundation" / "no_such_module.py", "anything"))

    def test_defines_requires_every_named_symbol_not_just_one(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "partial.py"
            p.write_text("class Present:\n    pass\n")
            self.assertTrue(_defines(p, "Present"))
            self.assertFalse(_defines(p, "Present", "Absent"))

    def test_defines_does_not_match_a_mere_mention(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "mention.py"
            p.write_text("# TaskQueue is discussed here\nx = 'TaskQueue'\n")
            self.assertFalse(_defines(p, "TaskQueue"))


if __name__ == "__main__":
    unittest.main()


class TestGuardRejectsBeforeAnySubprocessSpawns(unittest.TestCase):
    """`_dimension_proof`'s load-bearing ordering claim, enforced.

    Its docstring states: "`guard_check()` is called FIRST, before any
    subprocess is created ... no subprocess is spawned at all for the
    repeat entry, not merely a spawned child noticing later that it
    should stop."

    That claim was NOT enforced. `test_recursion_guard.py` proves the
    guard function returns BLOCKED_REPEAT in isolation;
    `TestComputeSigilOnRealRepo` uses `guard_check` only to skip ITSELF.
    Neither asserts that `_dimension_proof` spawns ZERO subprocesses on
    the rejected trajectory, so moving the guard below the loop — or
    ignoring its verdict — would have kept every test green.

    Verified 2026-08-29 before writing this: the property currently
    HOLDS (0 spawn calls under blocked ancestry). This is an unenforced
    claim being converted to a gate, not a reproduced defect.

    The damage it prevents is not hypothetical. This repository's own
    history records 50+ forked `unittest` processes in under three
    minutes when the guard was absent — the incident that caused
    `recursion_guard.py` to exist.

    TWO INDEPENDENT LENSES, failing for different reasons:
      A) TRAJECTORY — under blocked ancestry, `subprocess.run` is never
         called. Catches: guard moved after the loop, verdict ignored.
      B) STRUCTURE — in the source, the guard's early-return precedes
         every `subprocess` call. Catches a spawn added on some branch
         the runtime case does not happen to exercise, which lens A
         would miss.
    """

    def _blocked_env(self):
        from foundation.recursion_guard import child_env
        return child_env(PROOF_OPERATION)

    def test_a_trajectory_rejected_entry_spawns_nothing(self):
        from foundation import sigil as sigil_mod
        calls = []

        # Returns a REALISTIC fake, not None. Found while attacking this
        # test: a None-returning mock made a guard bypass surface as an
        # AttributeError crash rather than a clean assertion failure --
        # detection by accident, not by the gate. With a usable fake the
        # mutated code runs to completion and `calls` itself is the
        # evidence.
        class _Fake:
            returncode = 0
            stdout = "Ran 0 tests in 0.0s\n\nOK\n"
            stderr = ""

        def _fake_run(*a, **k):
            calls.append(a)
            return _Fake()

        with mock.patch.dict(os.environ, self._blocked_env(), clear=False):
            with mock.patch.object(sigil_mod.subprocess, "run", side_effect=_fake_run):
                score, justification, green, total = sigil_mod._dimension_proof(REPO_ROOT)
        self.assertEqual(
            calls, [],
            "a guard-blocked _dimension_proof spawned a subprocess -- the "
            "repeat entry must be rejected BEFORE any process is created",
        )
        self.assertEqual(score, 0)
        self.assertFalse(green)
        self.assertIn("guard-blocked", justification)

    def test_a2_unblocked_entry_still_spawns(self):
        # Positive control: without this, lens A would pass trivially if
        # _dimension_proof stopped spawning altogether. subprocess.run is
        # mocked so no real suites run.
        #
        # MUST CLEAR THE GUARD ANCESTRY EXPLICITLY. Found by running this
        # suite the way compute_sigil() actually runs it -- inside its own
        # PROOF_OPERATION-stamped child process. There the guard correctly
        # blocks, nothing spawns, and a version of this test that merely
        # INHERITED the ambient environment failed, breaking the real-repo
        # sigil computation. A test asserting "the unblocked path spawns"
        # must establish that it is unblocked rather than assume it.
        from foundation import sigil as sigil_mod
        from foundation.recursion_guard import _OPERATION_ENV, _DEPTH_ENV
        calls = []

        class _Fake:
            returncode = 0
            stdout = "Ran 0 tests in 0.0s\n\nOK\n"
            stderr = ""

        def _fake_run(*a, **k):
            calls.append(a)
            return _Fake()

        clean_env = {k: v for k, v in os.environ.items()
                     if k not in (_OPERATION_ENV, _DEPTH_ENV)}
        with mock.patch.dict(os.environ, clean_env, clear=True):
            self.assertTrue(
                guard_check(PROOF_OPERATION).is_safe(),
                "precondition: this control requires an unblocked ancestry")
            with mock.patch.object(sigil_mod.subprocess, "run", side_effect=_fake_run):
                sigil_mod._dimension_proof(REPO_ROOT)
        self.assertTrue(
            calls, "the unblocked path must still spawn -- otherwise the "
                   "rejected-path assertion proves nothing")

    def test_b_structure_guard_return_precedes_every_subprocess_call(self):
        # Source-level dominance check. Independent of lens A: it fails
        # even for a spawn on a branch no runtime case exercises.
        import ast
        tree = ast.parse(Path(sigil.__file__).read_text())
        fn = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "_dimension_proof"
        )

        guard_return_line = None
        for node in ast.walk(fn):
            # the `if not guard.is_safe(): return ...` early exit
            if isinstance(node, ast.If):
                has_return = any(isinstance(c, ast.Return) for c in ast.walk(node))
                mentions_guard = any(
                    isinstance(c, ast.Name) and c.id == "guard" for c in ast.walk(node.test)
                )
                if has_return and mentions_guard:
                    guard_return_line = node.lineno
                    break
        self.assertIsNotNone(
            guard_return_line,
            "_dimension_proof no longer has a guard early-return -- the "
            "ordering invariant cannot hold without one")

        spawn_lines = [
            node.lineno for node in ast.walk(fn)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "subprocess"
            and node.func.attr == "run"
        ]
        self.assertTrue(spawn_lines, "expected a real subprocess.run call site")
        self.assertTrue(
            all(line > guard_return_line for line in spawn_lines),
            f"a subprocess.run at line(s) {spawn_lines} is not after the guard "
            f"early-return at line {guard_return_line} -- a repeat entry could "
            f"reach process creation before rejection",
        )


class ProofTimeoutTests(unittest.TestCase):
    """MEASURED 2026-09-04: the `foundation` child suite takes 128.8
    seconds. The limit was 120.

    A TimeoutExpired sets all_green=False, which caps PROOF at
    `min(4, total // 200)` instead of the green formula, which fails
    run_all_tests.sh's foundation suite. So the whole-repository gate
    passed or failed according to machine load -- twice failing and four
    times passing in one evening on identical code. It read as flakiness
    and was a deterministic cliff the suite had grown across.
    """

    def test_the_limit_clears_the_measured_duration_with_room(self):
        from foundation.sigil import PROOF_SUBSYSTEM_TIMEOUT_SECONDS
        self.assertGreater(PROOF_SUBSYSTEM_TIMEOUT_SECONDS, 128.8)
        # Not a bare "greater than the measurement" -- that would put us
        # back on the cliff after ordinary growth.
        self.assertGreaterEqual(PROOF_SUBSYSTEM_TIMEOUT_SECONDS, 400)

    def test_the_timeout_is_named_not_inlined(self):
        """It was the literal `timeout=120` buried in a subprocess call,
        which is why nobody noticed the suite growing past it."""
        from pathlib import Path
        from foundation import sigil
        src = Path(sigil.__file__).read_text(encoding="utf-8")
        self.assertIn("timeout=PROOF_SUBSYSTEM_TIMEOUT_SECONDS", src)
        self.assertNotIn("timeout=120", src)

    def test_a_timeout_is_reported_differently_from_a_failure(self):
        """The deeper defect: both produced all_green=False and an
        identically degraded score, so a slow suite reported as a broken
        one and sent the reader hunting a test that does not exist."""
        from pathlib import Path
        from foundation import sigil
        src = Path(sigil.__file__).read_text(encoding="utf-8")
        self.assertIn("TIMED OUT after", src)
        self.assertIn("not a test failure", src)
