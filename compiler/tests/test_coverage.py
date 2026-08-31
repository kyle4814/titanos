"""Tests for compiler/coverage.py — the doctrine <-> code <-> test checker.

WHY THESE TESTS EXIST

`compiler/coverage.py` is the module that decides whether a doctrine's
claimed enforcement actually exists on disk. Until now the only tests in
`compiler/tests/` (`test_workspace_root.py`) exercise it exclusively
through subprocess calls against this repository's real doctrine files —
useful for regression, but they never call `check_invariant` /
`check_doctrine` directly, so the actual decision function that produces
STALE_CLAIM / CONSISTENT / UNCHECKABLE / UNDERCLAIMED / INVALID_STATUS has
zero direct unit coverage. These tests close that gap using synthetic,
self-contained fixtures (temp directories with known file/symbol content)
so they do not depend on, or drift with, this repository's real doctrine
files.

Every test asserts a real decision boundary in the checker, not trivia.
Where the module's actual behaviour diverges from its own stated design
promise (see its docstring: "structured result, not a crash" / "REFUSES
rather than silently passing"), the test still asserts the TRUE current
behaviour and is marked "KNOWN GAP" — a real finding, not a bug being
quietly normalized as a feature.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import compiler.coverage as coverage  # noqa: E402


def _mkfile(root: Path, rel: str, content: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


class TestCheckInvariantDecisionBoundary(unittest.TestCase):
    """The real decision boundary: does `enforced_at` point at a symbol
    that exists, or doesn't? This is the exact defect shape (F-006) the
    module's own docstring says it exists to catch."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        _mkfile(self.root, "src/guard.py", "def enforce_rule():\n    return True\n")

    def test_enforced_status_with_real_symbol_is_consistent(self):
        """The happy path: ENFORCED + a symbol that genuinely exists in
        the named file must verify as CONSISTENT. If this fails, the
        checker rejects legitimate enforcement — false positives would
        make every doctrine unusable."""
        inv = {"id": "I-1", "status": "ENFORCED",
               "enforced_at": "src/guard.py::enforce_rule"}
        finding = coverage.check_invariant(self.root, inv)
        self.assertEqual(finding.verdict, "CONSISTENT")
        self.assertTrue(finding.file_exists)
        self.assertTrue(finding.symbol_found)

    def test_enforced_status_with_missing_symbol_is_stale_claim(self):
        """The exact F-006 shape: doctrine claims ENFORCED, the file
        exists, but the named symbol does not appear in it. Must be
        STALE_CLAIM, not CONSISTENT — a symbol that vanished (renamed,
        deleted) must not be able to hide behind a still-existing file."""
        inv = {"id": "I-2", "status": "ENFORCED",
               "enforced_at": "src/guard.py::this_symbol_does_not_exist"}
        finding = coverage.check_invariant(self.root, inv)
        self.assertEqual(finding.verdict, "STALE_CLAIM")
        self.assertTrue(finding.file_exists)
        self.assertFalse(finding.symbol_found)

    def test_enforced_status_with_missing_file_is_stale_claim(self):
        """A claim pointing at a file that was deleted entirely must also
        be STALE_CLAIM, with file_exists=False and symbol_found left
        unknown (None) rather than falsely reported as found or not."""
        inv = {"id": "I-3", "status": "ENFORCED",
               "enforced_at": "src/does_not_exist.py::whatever"}
        finding = coverage.check_invariant(self.root, inv)
        self.assertEqual(finding.verdict, "STALE_CLAIM")
        self.assertFalse(finding.file_exists)
        self.assertIsNone(finding.symbol_found)

    def test_partial_status_also_requires_evidence(self):
        """PARTIAL is in STATUS_REQUIRES_CODE alongside ENFORCED — a
        PARTIAL claim pointing at nothing real must also refuse, not just
        ENFORCED claims."""
        inv = {"id": "I-4", "status": "PARTIAL",
               "enforced_at": "src/does_not_exist.py::whatever"}
        finding = coverage.check_invariant(self.root, inv)
        self.assertEqual(finding.verdict, "STALE_CLAIM")

    def test_not_enforced_status_with_no_code_is_consistent(self):
        """A doctrine honestly declaring NOT_ENFORCED, pointing at nothing
        that exists, must be CONSISTENT — the doctrine is allowed to
        describe something not yet built, provided it says so."""
        inv = {"id": "I-5", "status": "NOT_ENFORCED",
               "enforced_at": "src/does_not_exist.py::whatever"}
        finding = coverage.check_invariant(self.root, inv)
        self.assertEqual(finding.verdict, "CONSISTENT")

    def test_not_enforced_status_with_real_code_is_underclaimed(self):
        """The mirror-image defect: doctrine says NOT_ENFORCED but the
        code actually exists. Must be UNDERCLAIMED — doctrine is stale
        relative to code, and this must be flagged, not silently ignored,
        or a doctrine could permanently under-report real enforcement."""
        inv = {"id": "I-6", "status": "NOT_ENFORCED",
               "enforced_at": "src/guard.py::enforce_rule"}
        finding = coverage.check_invariant(self.root, inv)
        self.assertEqual(finding.verdict, "UNDERCLAIMED")

    def test_invalid_status_is_rejected_before_checking_evidence(self):
        """A status outside the declared vocabulary must fail fast as
        INVALID_STATUS, without even attempting to resolve enforced_at —
        an unknown status word is not evidence of anything."""
        inv = {"id": "I-7", "status": "TOTALLY_ENFORCED_TRUST_ME",
               "enforced_at": "src/guard.py::enforce_rule"}
        finding = coverage.check_invariant(self.root, inv)
        self.assertEqual(finding.verdict, "INVALID_STATUS")
        self.assertIsNone(finding.file_exists)


class TestCommaJoinedEnforcedAt(unittest.TestCase):
    """The documented rule: `enforced_at` must be ONE `path::symbol` per
    invariant, never a comma-joined list of multiple references. This
    tests whether the code actually enforces that, structurally or not.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        _mkfile(self.root, "src/a.py", "def rule_a():\n    pass\n")
        _mkfile(self.root, "src/b.py", "def rule_b():\n    pass\n")

    def test_comma_joined_enforced_at_is_not_parsed_as_multiple_refs(self):
        """KNOWN GAP: the code has no special handling for a comma-joined
        `enforced_at` (e.g. "src/a.py::rule_a, src/b.py::rule_b", the
        real shape found in
        magl/constitution/OBELISK_INVARIANTS.yaml's JURISDICTION_MODEL
        obligation). `_resolve` splits on the FIRST "::" only, so
        everything after it — including the second path and symbol — is
        treated as one literal symbol string to search for. That string
        will almost never appear verbatim in the first file, so this
        degrades to STALE_CLAIM even when both individual symbols
        genuinely exist. This IS a refusal (not a silent pass), so it is
        safe rather than dangerous — but the failure reason
        ("symbol not found") is misleading: it reads as "enforcement is
        missing" when the real defect is "this invariant's enforced_at
        violates the one-path::symbol-per-invariant convention." The
        compiler does not distinguish those two cases."""
        inv = {
            "id": "I-8",
            "status": "ENFORCED",
            "enforced_at": "src/a.py::rule_a, src/b.py::rule_b",
        }
        finding = coverage.check_invariant(self.root, inv)
        # Resolves against the first path only; the "symbol" is the
        # entire remainder of the string, comma and all.
        self.assertTrue(finding.file_exists)
        self.assertEqual(finding.verdict, "STALE_CLAIM")
        self.assertFalse(finding.symbol_found)

    def test_single_ref_from_the_same_pair_verifies_cleanly(self):
        """Control: splitting the same claim into two separate invariants,
        each with exactly one path::symbol, verifies correctly — proving
        the STALE_CLAIM above is an artefact of comma-joining, not of the
        underlying enforcement being genuinely absent."""
        inv_a = {"id": "I-8a", "status": "ENFORCED", "enforced_at": "src/a.py::rule_a"}
        inv_b = {"id": "I-8b", "status": "ENFORCED", "enforced_at": "src/b.py::rule_b"}
        self.assertEqual(coverage.check_invariant(self.root, inv_a).verdict, "CONSISTENT")
        self.assertEqual(coverage.check_invariant(self.root, inv_b).verdict, "CONSISTENT")


class TestUncheckableClaimsDoNotBlockAcceptance(unittest.TestCase):
    """Whether the checker REFUSES or silently passes when it genuinely
    cannot verify a claim."""

    def test_prose_enforced_at_is_uncheckable_not_a_failure(self):
        """An ENFORCED claim whose `enforced_at` is prose ("AST scan of
        the package source", the real value used in doctrine-001.yaml)
        cannot be resolved to a file, so it is marked UNCHECKABLE rather
        than STALE_CLAIM — the module's documented design choice: it
        will not fail a claim it cannot check, only claims it CAN check
        and finds false."""
        inv = {"id": "I-9", "status": "ENFORCED",
               "enforced_at": "AST scan of the package source"}
        finding = coverage.check_invariant(Path("/nonexistent"), inv)
        self.assertEqual(finding.verdict, "UNCHECKABLE")

    def test_known_gap_uncheckable_enforced_claims_report_as_accepted(self):
        """KNOWN GAP: at the doctrine level, `check_doctrine`'s `failed`
        set is {STALE_CLAIM, INVALID_STATUS, UNDERCLAIMED} — UNCHECKABLE
        is not in it. So a doctrine consisting entirely of one ENFORCED
        invariant with prose `enforced_at` reports `result: ACCEPTED`,
        even though not a single claim in it was actually verified. This
        contradicts the module's own docstring ("REFUSAL IS THE SUCCESS
        PATH" / a status is "a CLAIM ... this compiler's job is to refuse
        claims that the filesystem contradicts") only in the narrow case
        where the filesystem can neither confirm nor contradict — the
        module documents this as "unverified by automation" in the
        finding detail, but that caveat lives inside `findings[]`, not in
        the top-level `result` field a caller might check in isolation."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            doctrine_path = _mkfile(root, "doctrine.yaml", yaml.safe_dump({
                "id": "D-UNCHECKABLE", "version": "1",
                "invariants": [{
                    "id": "I-ONLY", "status": "ENFORCED",
                    "enforced_at": "AST scan of the package source",
                }],
            }))
            report = coverage.check_doctrine(doctrine_path, root)
        self.assertEqual(report["result"], "ACCEPTED")
        self.assertEqual(report["failed"], 0)
        self.assertEqual(report["uncheckable"], 1)
        self.assertEqual(report["consistent"], 0)


class TestCheckDoctrineStructuralCases(unittest.TestCase):
    """Empty doctrine sets, malformed YAML, and missing files — should
    each produce a structured result rather than crash, per the module's
    own stated design. Tested against what actually happens."""

    def test_empty_invariants_list_is_trivially_accepted(self):
        """A doctrine with zero invariants has nothing to be wrong about
        — 0 checked, 0 failed, ACCEPTED. Not a crash, not a false
        REFUSED."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            doctrine_path = _mkfile(root, "empty.yaml", yaml.safe_dump({
                "id": "D-EMPTY", "version": "1", "invariants": [],
            }))
            report = coverage.check_doctrine(doctrine_path, root)
        self.assertEqual(report["invariants_checked"], 0)
        self.assertEqual(report["failed"], 0)
        self.assertEqual(report["result"], "ACCEPTED")

    def test_doctrine_with_no_invariants_key_at_all_is_also_accepted(self):
        """`doc.get("invariants", [])` defaults to empty — a YAML file
        that never declares the key at all must behave identically to an
        explicit empty list, not crash on a missing key."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            doctrine_path = _mkfile(root, "no_invariants.yaml",
                                     yaml.safe_dump({"id": "D-NONE", "version": "1"}))
            report = coverage.check_doctrine(doctrine_path, root)
        self.assertEqual(report["invariants_checked"], 0)
        self.assertEqual(report["result"], "ACCEPTED")

    def test_known_gap_malformed_yaml_crashes_rather_than_returns_a_result(self):
        """KNOWN GAP: `check_doctrine` calls `yaml.safe_load(...)` with no
        try/except. Malformed YAML raises `yaml.YAMLError` straight out
        of `check_doctrine`, uncaught — this is a genuine crash, not the
        "structured result, not a crash" behaviour the module's own
        docstring promises for "malformed YAML, a missing file, and an
        empty doctrine set." Two of those three actually crash; only the
        empty-doctrine-set case is truly handled gracefully (see the two
        tests above)."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            doctrine_path = _mkfile(root, "malformed.yaml",
                                     "invariants: [this is: not: valid: yaml:\n")
            with self.assertRaises(yaml.YAMLError):
                coverage.check_doctrine(doctrine_path, root)

    def test_known_gap_missing_doctrine_file_crashes_rather_than_returns_a_result(self):
        """KNOWN GAP: same crash-not-structured-result gap for a
        doctrine file that simply does not exist. `check_doctrine` calls
        `doctrine_path.read_text()` directly with no existence check or
        try/except, so this raises `FileNotFoundError` uncaught rather
        than returning e.g. a `result: ERROR` structured record."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            missing = root / "does_not_exist.yaml"
            with self.assertRaises(FileNotFoundError):
                coverage.check_doctrine(missing, root)


class TestCheckDoctrineAggregateBehaviour(unittest.TestCase):
    """Aggregate-level behaviour: a doctrine mixing consistent and
    inconsistent invariants must REFUSE as a whole, and the specific
    invariant(s) at fault must be identifiable in the report."""

    def test_one_stale_claim_among_several_consistent_ones_refuses_the_whole_doctrine(self):
        """A single false claim must fail the entire doctrine — coverage
        is not averaged or partially credited. This is the module's
        stated purpose: any misstatement makes the doctrine not compile."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _mkfile(root, "src/real.py", "def works():\n    pass\n")
            doctrine_path = _mkfile(root, "mixed.yaml", yaml.safe_dump({
                "id": "D-MIXED", "version": "1",
                "invariants": [
                    {"id": "GOOD", "status": "ENFORCED",
                     "enforced_at": "src/real.py::works"},
                    {"id": "BAD", "status": "ENFORCED",
                     "enforced_at": "src/real.py::does_not_exist"},
                ],
            }))
            report = coverage.check_doctrine(doctrine_path, root)
        self.assertEqual(report["result"], "REFUSED")
        self.assertEqual(report["failed"], 1)
        self.assertEqual(report["consistent"], 1)
        stale_ids = [f["invariant_id"] for f in report["findings"]
                     if f["verdict"] == "STALE_CLAIM"]
        self.assertEqual(stale_ids, ["BAD"])

    def test_declared_test_file_missing_warns_but_does_not_refuse(self):
        """A CONSISTENT invariant (real enforced_at) whose declared
        `test` file does not exist gets a WARNING appended to its detail
        string, but this does not move it out of CONSISTENT or make the
        doctrine REFUSED — untested enforcement is flagged, not blocked.
        Worth asserting explicitly since it is easy to assume (wrongly)
        that a missing test file fails the whole doctrine."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _mkfile(root, "src/real.py", "def works():\n    pass\n")
            doctrine_path = _mkfile(root, "untested.yaml", yaml.safe_dump({
                "id": "D-UNTESTED-ENFORCEMENT", "version": "1",
                "invariants": [{
                    "id": "GOOD_NO_TEST", "status": "ENFORCED",
                    "enforced_at": "src/real.py::works",
                    "test": "tests/does_not_exist_test.py",
                }],
            }))
            report = coverage.check_doctrine(doctrine_path, root)
        self.assertEqual(report["result"], "ACCEPTED")
        finding = report["findings"][0]
        self.assertEqual(finding["verdict"], "CONSISTENT")
        self.assertIn("WARNING", finding["detail"])
        self.assertFalse(finding["test_exists"])


class TestResolveWorkspaceRoot(unittest.TestCase):
    """The workspace-root precedence rule: CLI override > declared
    `workspace_root` > doctrine file's own directory."""

    def test_explicit_override_always_wins(self):
        with tempfile.TemporaryDirectory() as d:
            doctrine_path = _mkfile(Path(d), "d.yaml",
                                     yaml.safe_dump({"workspace_root": "somewhere/else"}))
            override = Path("/tmp/explicit-override")
            self.assertEqual(
                coverage.resolve_workspace_root(doctrine_path, override), override)

    def test_declared_workspace_root_is_relative_to_the_doctrine_files_directory(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "elsewhere").mkdir()
            doctrine_path = _mkfile(root, "doctrine_dir/d.yaml",
                                     yaml.safe_dump({"workspace_root": "../elsewhere"}))
            resolved = coverage.resolve_workspace_root(doctrine_path)
            self.assertEqual(resolved, (root / "elsewhere").resolve())

    def test_no_declaration_falls_back_to_doctrine_files_own_directory(self):
        with tempfile.TemporaryDirectory() as d:
            doctrine_path = _mkfile(Path(d), "d.yaml", yaml.safe_dump({"id": "X"}))
            self.assertEqual(coverage.resolve_workspace_root(doctrine_path),
                              doctrine_path.parent)

    def test_malformed_yaml_falls_back_to_doctrine_files_own_directory_gracefully(self):
        """Unlike `check_doctrine`, `resolve_workspace_root` DOES catch
        `yaml.YAMLError` (and `OSError`) and degrades to the doctrine
        file's own directory rather than raising — the one place in this
        module that genuinely matches the "structured result, not a
        crash" promise."""
        with tempfile.TemporaryDirectory() as d:
            doctrine_path = _mkfile(Path(d), "d.yaml",
                                     "invariants: [not: valid: yaml:\n")
            self.assertEqual(coverage.resolve_workspace_root(doctrine_path),
                              doctrine_path.parent)

    def test_missing_file_falls_back_to_its_own_would_be_directory_gracefully(self):
        with tempfile.TemporaryDirectory() as d:
            missing = Path(d) / "nope.yaml"
            self.assertEqual(coverage.resolve_workspace_root(missing), missing.parent)


class TestMainEntrypoint(unittest.TestCase):
    """The CLI wrapper's own contract: usage/exit-code behaviour."""

    def test_no_arguments_prints_usage_and_exits_2(self):
        self.assertEqual(coverage.main(["coverage.py"]), 2)

    def test_accepted_doctrine_exits_0(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _mkfile(root, "src/real.py", "def works():\n    pass\n")
            doctrine_path = _mkfile(root, "d.yaml", yaml.safe_dump({
                "id": "D", "version": "1",
                "invariants": [{"id": "GOOD", "status": "ENFORCED",
                                 "enforced_at": "src/real.py::works"}],
            }))
            self.assertEqual(coverage.main(["coverage.py", str(doctrine_path), str(root)]), 0)

    def test_refused_doctrine_exits_1(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            doctrine_path = _mkfile(root, "d.yaml", yaml.safe_dump({
                "id": "D", "version": "1",
                "invariants": [{"id": "BAD", "status": "ENFORCED",
                                 "enforced_at": "src/nope.py::nope"}],
            }))
            self.assertEqual(coverage.main(["coverage.py", str(doctrine_path), str(root)]), 1)


if __name__ == "__main__":
    unittest.main()

