"""Exactly one thing may repair README's test count.

WHY THIS EXISTS

README's hand-maintained test count drifted and broke the build three
times in two work cells. The response was to build `readme_sync.py` --
a fourth implementation of a capability `autonomy_loop.py` had performed
successfully since 2026-08-29, with verification, rollback, a kill
switch and a receipt that `readme_sync.py` did not have.

That was a search-before-build failure. The duplicate was deleted; this
test is what stops the next one, because the conditions that produced it
(a recurring visible annoyance, an obvious-looking small fix) will recur.

THE DEEPER FINDING THIS TEST DOES NOT COVER

The drift kept happening because `autonomy_loop.py` is never invoked --
cron schedules the sensor (`cron_pulse.py`) and nothing schedules the
actor. That is a scheduling decision recorded in `HUMAN_DECISIONS.md`,
not something a test can assert, and it is deliberately left to a human:
installing a self-committing loop on someone's machine is their call.
"""

import ast
import pathlib
import unittest

# Build outputs are copies of the source tree, not new code. `pip wheel .`
# and an sdist build leave `build/` and `*.egg-info/` behind, each holding a
# duplicate of every production module, and a scan that walks them reports
# the copy as a second network caller -- a false alarm about a file that is
# byte-identical to one already checked. They are gitignored; walking the
# filesystem does not respect that, so the exclusion is explicit.
_BUILD_DIRS = ("build/", "dist/", ".eggs/")


def _is_build_output(rel: str) -> bool:
    return rel.startswith(_BUILD_DIRS) or ".egg-info/" in rel


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

# The one module allowed to repair the count, and the one allowed to
# compute it. Any third party writing README's count is a duplicate.
AUTHORISED_FIXER = "foundation/autonomy_loop.py"
AUTHORISED_COUNTER = "foundation/sentinel.py"


def _production_modules():
    for path in sorted(REPO_ROOT.rglob("*.py")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if "/tests/" in f"/{rel}" or rel.startswith("."):
            continue
        if _is_build_output(rel):
            continue
        yield rel, path



def _enclosing_source(tree, node):
    """Source of the function containing `node`, for local name resolution."""
    import ast as _ast
    best = None
    for fn in _ast.walk(tree):
        if isinstance(fn, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
            for inner in _ast.walk(fn):
                if inner is node:
                    best = fn
    return _ast.unparse(best) if best is not None else ""


def _readme_bound_names(source: str, target: str) -> str:
    """Return the assignment lines binding `target`, so a write through a
    local variable that was built from a README path still counts."""
    if not source or not target:
        return ""
    hits = [ln for ln in source.splitlines()
            if ln.strip().startswith(f"{target} =") or f"{target} =" in ln]
    return "\n".join(hits)


class TestOnlyOneReadmeFixer(unittest.TestCase):

    def test_only_one_module_writes_readme(self):
        writers = set()
        for rel, path in _production_modules():
            try:
                tree = ast.parse(path.read_text(errors="ignore"))
            except SyntaxError:
                continue
            src = path.read_text(errors="ignore")
            if "README.md" not in src:
                continue
            # The write must actually TARGET README.md. An earlier version
            # convicted any module that merely MENTIONED README.md in prose
            # and called write_text for some other file -- it flagged
            # launch_report.py, whose docstring cites README's historical
            # staleness as the reason it generates rather than stores.
            # Same defect as the network test that scanned source text for
            # "socket" and failed on a comment: a guard a docstring can trip
            # is measuring the wrong thing.
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                name = ast.unparse(node.func)
                if not (name.endswith("write_text") or name.endswith("write_bytes")):
                    continue
                target = ast.unparse(node.func).rsplit(".", 1)[0]
                # Resolve the receiver back to a README-bearing expression:
                # either it names README literally, or it is a variable the
                # same function assigned from a README path.
                window = ast.unparse(node)
                enclosing = _enclosing_source(tree, node)
                if "README" in window or "README" in _readme_bound_names(enclosing, target):
                    writers.add(rel)
        self.assertEqual(
            writers, {AUTHORISED_FIXER},
            f"more than one module writes README.md: {sorted(writers)}. "
            f"{AUTHORISED_FIXER} already repairs test-count drift with "
            f"verification, rollback and a receipt -- extend it rather than "
            f"adding a second writer.")

    def test_the_authorised_fixer_still_exists(self):
        """A guard that silently passes because the thing it guards was
        renamed is worse than no guard."""
        src = (REPO_ROOT / AUTHORISED_FIXER).read_text()
        self.assertIn("_attempt_readme_fix", src)
        self.assertIn("_rollback_readme", src)

    def test_the_count_has_exactly_one_implementation(self):
        """sentinel.count_real_tests() defines the quantity. A second
        counter disagreed with it by 5 on the real repository, which
        would have left the drift finding permanently open."""
        counters = set()
        for rel, path in _production_modules():
            try:
                tree = ast.parse(path.read_text(errors="ignore"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    body = ast.unparse(node)
                    if "def test_" in body and "rglob" in body:
                        counters.add(rel)
        self.assertEqual(
            counters, {AUTHORISED_COUNTER},
            f"a second test-counter appeared: {sorted(counters)}. The "
            f"sensor defines the quantity; everything else delegates.")


if __name__ == "__main__":
    unittest.main()
