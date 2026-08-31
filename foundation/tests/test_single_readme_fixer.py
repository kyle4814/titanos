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
        yield rel, path


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
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    name = ast.unparse(node.func)
                    if name.endswith("write_text") or name.endswith("write_bytes"):
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
