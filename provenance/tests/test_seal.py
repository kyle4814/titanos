"""Tests for provenance/seal.py — the release-manifest sealing script.

WHY THESE TESTS LOOK LIKE THIS

`provenance/seal.py` has zero functions or classes. Every line is a
top-level statement: it hashes every file under the whole repository,
builds a manifest for each one, computes a release hash, and
**unconditionally overwrites `releases/RELEASE-001.json` on disk** — all
of it executes the instant the module is imported, not behind an
`if __name__ == "__main__":` guard. `import provenance.seal` is
therefore not a safe thing to do from a test: it is a full run of the
release pipeline against the real repository, with a real write to a
file this task's write-scope does not include. These tests never import
`provenance.seal` for that reason — doing so would itself be the kind of
out-of-scope side effect this task was explicitly told to avoid.

What IS tested:

1. The module's actual structure, read as source text / parsed as an
   AST — never executed — which is exactly how the "no `__main__` guard,
   no function boundaries" finding above was established, and lets that
   finding be asserted mechanically instead of just claimed in prose.
2. The real `provenance` library functions `seal.py` calls
   (`hash_file`, `content_hash`, `new_session_id`, `build_manifest`,
   `verify_lineage`, imported from the *external* `titanos-provenance`
   package, not from `seal.py` itself) — these are pure functions with
   no side effects beyond reading the one file path handed to them, so
   they can be exercised directly against throwaway fixtures. This is
   the "whatever is testable without triggering the unsafe part"
   surface: seal.py's OWN assembly logic stays untested (it cannot be
   exercised without running the whole unsafe script), but the pieces it
   assembles are verified individually.

Tests in group 2 are gated with `unittest.skipUnless` on the external
package actually being importable, and say so in their docstrings — a
test that fails only because an optional external dependency is absent
is noise, not signal.

REAL DEFECT FOUND while writing these tests: `seal.py`'s own module
docstring and this repository's task description both describe the
external dependency as reached via a `TITANOS_PROVENANCE_PATH`
environment variable. It is not. `seal.py` line 9 hardcodes the literal
string `sys.path.insert(0, "/home/tech2/titanos-provenance")` — no
`os.environ` lookup anywhere in the file. On any machine where that
exact absolute path does not exist, `import provenance` fails with
`ModuleNotFoundError`, unconditionally, with no way to redirect it
short of editing the script. `TestHardcodedDependencyPath` below asserts
this concretely.
"""
from __future__ import annotations

import ast
import importlib
import sys
import tempfile
import unittest
from pathlib import Path

SEAL_PATH = Path(__file__).resolve().parents[1] / "seal.py"
HARDCODED_DEP_PATH = "/home/tech2/titanos-provenance"


def _external_provenance_available() -> bool:
    if not Path(HARDCODED_DEP_PATH).is_dir():
        return False
    if HARDCODED_DEP_PATH not in sys.path:
        sys.path.insert(0, HARDCODED_DEP_PATH)
    try:
        importlib.import_module("provenance")
    except ImportError:
        return False
    return True


EXTERNAL_PROVENANCE_AVAILABLE = _external_provenance_available()
SKIP_REASON = (
    f"external dependency not present at {HARDCODED_DEP_PATH} — this is "
    "expected on any machine other than the one seal.py hardcodes; the "
    "test is skipped, not failed, per this task's own instruction that a "
    "missing optional dependency should skip cleanly rather than report "
    "as a failure."
)


class TestSealSourceStructure(unittest.TestCase):
    """Static structural checks — parsed as an AST, never executed.
    These document why the module cannot be safely imported in a test,
    rather than just asserting that claim in prose."""

    @classmethod
    def setUpClass(cls):
        cls.source = SEAL_PATH.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source, filename=str(SEAL_PATH))

    def test_module_defines_no_functions_or_classes(self):
        """The real reason this module cannot be unit tested by import:
        there is no function or class boundary anywhere in it to call
        selectively — every statement is top-level and runs on import."""
        defs = [n for n in ast.walk(self.tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        self.assertEqual(defs, [], "seal.py has no functions/classes; all "
                          "logic is top-level script code")

    def test_module_has_no_main_guard(self):
        """No `if __name__ == "__main__":` guard exists, so there is no
        way to import this module without running its full body —
        confirmed structurally, not just by the absence-of-defs test
        above (a module could theoretically have top-level code AFTER a
        guarded block; this checks the specific guard pattern is absent)."""
        has_guard = any(
            isinstance(n, ast.If)
            and isinstance(n.test, ast.Compare)
            and isinstance(n.test.left, ast.Name)
            and n.test.left.id == "__name__"
            for n in self.tree.body
        )
        self.assertFalse(has_guard, "seal.py unexpectedly gained a "
                          "__main__ guard — if so, it may now be safely "
                          "importable and these tests should be revisited")

    def test_release_output_path_is_hardcoded_relative_to_repo_root(self):
        """Documents exactly what an import would write, and where —
        `releases/RELEASE-001.json` relative to `LIB`, which is computed
        as `Path(__file__).resolve().parents[1]` (this file's own repo
        root). A future change to this path should be a deliberate,
        reviewed edit, not a silent drift — this test pins the literal
        strings that currently determine it."""
        self.assertIn('parents[1]', self.source)
        self.assertIn('"releases"', self.source)
        self.assertIn('RELEASE-001.json', self.source)

    def test_release_defaults_to_unsigned_and_unauthorized(self):
        """Fail-closed defaults matter here: a script that hashes and
        writes a release manifest as a side effect of being imported had
        better default every trust-bearing field to the least-privileged
        value. Static check that these literals are still present,
        unweakened, in the source."""
        self.assertIn('"signature_status": "UNSIGNED"', self.source)
        self.assertIn('"human_release_authorization": "NOT_GRANTED"', self.source)
        self.assertIn('"publication_status": "CANDIDATE_ONLY_DO_NOT_PUBLISH"', self.source)

    def test_release_hash_is_computed_excluding_itself(self):
        """The release_hash field must not be included in its own hash
        input, or the hash would not be reproducible (computing it a
        second time would see a different `release` dict, itself
        containing the hash from the first computation). Verified by
        checking the actual exclusion expression is present."""
        self.assertIn('if k != "release_hash"', self.source)


class TestHardcodedDependencyPath(unittest.TestCase):
    """The TITANOS_PROVENANCE_PATH mismatch documented in this file's
    module docstring."""

    def setUp(self):
        self.source = SEAL_PATH.read_text(encoding="utf-8")

    def test_no_environment_variable_is_consulted(self):
        """seal.py never reads os.environ for the dependency path — the
        idea that it's configurable via TITANOS_PROVENANCE_PATH does not
        match the actual source. A failure here means seal.py was
        changed to actually support the env var, which would be a real
        improvement worth updating this test (and the module docstring
        above) to reflect."""
        self.assertNotIn("os.environ", self.source)
        self.assertNotIn("TITANOS_PROVENANCE_PATH", self.source)

    def test_dependency_path_is_a_literal_absolute_string(self):
        """The actual mechanism: one hardcoded absolute path, inserted
        at the front of sys.path. Portability finding: this only works
        on a machine with titanos-provenance cloned at exactly this
        path."""
        self.assertIn(f'sys.path.insert(0, "{HARDCODED_DEP_PATH}")', self.source)


@unittest.skipUnless(EXTERNAL_PROVENANCE_AVAILABLE, SKIP_REASON)
class TestUnderlyingProvenanceLibraryFunctions(unittest.TestCase):
    """The pure functions seal.py assembles into its unsafe top-level
    script — exercised directly, never through seal.py itself. Proves
    the pieces are individually sound without running the unsafe whole.
    """

    @classmethod
    def setUpClass(cls):
        from provenance import (  # type: ignore[import-not-found]
            build_manifest, content_hash, hash_file, new_session_id,
            verify_lineage,
        )
        cls.build_manifest = staticmethod(build_manifest)
        cls.content_hash = staticmethod(content_hash)
        cls.hash_file = staticmethod(hash_file)
        cls.new_session_id = staticmethod(new_session_id)
        cls.verify_lineage = staticmethod(verify_lineage)

    def test_hash_file_is_deterministic_for_identical_content(self):
        """Two files with identical bytes must hash identically — the
        basic property seal.py relies on to detect real content changes
        between releases."""
        with tempfile.TemporaryDirectory() as d:
            a = Path(d) / "a.txt"
            b = Path(d) / "b.txt"
            a.write_text("same content\n", encoding="utf-8")
            b.write_text("same content\n", encoding="utf-8")
            self.assertEqual(self.hash_file(a), self.hash_file(b))

    def test_hash_file_differs_for_different_content(self):
        """The inverse property: a single-byte difference must not
        collide. A failure here would mean the release manifest could
        not be trusted to distinguish artifacts."""
        with tempfile.TemporaryDirectory() as d:
            a = Path(d) / "a.txt"
            b = Path(d) / "b.txt"
            a.write_text("content one\n", encoding="utf-8")
            b.write_text("content two\n", encoding="utf-8")
            self.assertNotEqual(self.hash_file(a), self.hash_file(b))

    def test_content_hash_is_deterministic_for_equal_dicts(self):
        """seal.py's own release_hash relies on this: hashing the same
        logical dict twice (even if constructed independently) must
        give the same result, or the release would not be
        reproducible."""
        d1 = {"a": 1, "b": "two"}
        d2 = {"b": "two", "a": 1}  # different insertion order
        self.assertEqual(self.content_hash(d1), self.content_hash(d2))

    def test_new_session_id_produces_distinct_values(self):
        """seal.py calls this once at module scope and reuses it for
        every artifact's manifest in the run. Each call must be capable
        of producing a fresh id, or session identity would be a
        constant rather than a real session boundary."""
        ids = {self.new_session_id() for _ in range(5)}
        self.assertEqual(len(ids), 5)

    def test_build_manifest_round_trips_through_verify_lineage(self):
        """Reproduces, in miniature and in a temp directory, exactly
        what seal.py's loop does for one artifact: hash a file, build a
        manifest for it, and confirm verify_lineage accepts the result.
        This is the closest these tests come to exercising seal.py's own
        logic — without ever importing seal.py itself."""
        with tempfile.TemporaryDirectory() as d:
            artifact = Path(d) / "doctrine.yaml"
            artifact.write_text("id: D\nversion: 1\n", encoding="utf-8")
            doctrine_hash = self.hash_file(artifact)
            session = self.new_session_id()
            manifest = self.build_manifest(
                artifact_type="root",
                content_hash_value=doctrine_hash,
                source_revision="test-rev",
                pipeline_version="test-pipe",
                doctrine_version="1",
                doctrine_hash=doctrine_hash,
                agent_session_id=session,
                parent_artifacts=(),
                status="CANDIDATE",
            )
            result = self.verify_lineage({manifest.artifact_id: manifest.to_dict()})
        self.assertTrue(result.overall)


if __name__ == "__main__":
    unittest.main()
