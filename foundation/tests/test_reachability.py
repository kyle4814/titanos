"""Tests for `foundation/reachability.py`. Offline; the synthetic
package fixtures below are written to a temp dir, so no test depends on
the real repository's current shape."""

import tempfile
import unittest
from pathlib import Path

from foundation.reachability import (
    INTENT_CATEGORIES,
    REACHABILITY_INTENT,
    ReachabilityError,
    ReachabilityReport,
    format_reachability,
    scan_reachability,
)


class TestEveryUnreachableModuleIsClassified(unittest.TestCase):
    """The reachability finding is only honest if it stays current. If a
    future module becomes tested-but-unreachable, it must be classified in
    REACHABILITY_INTENT (or wired) — this test fails loudly until it is,
    so 'unreachable, intent unknown' can never silently return."""

    def test_every_real_unreachable_module_has_an_intent(self):
        report = scan_reachability(Path(__file__).resolve().parents[2])
        missing = [m.name for m in report.unreachable
                   if m.name not in REACHABILITY_INTENT]
        self.assertEqual(
            missing, [],
            f"unclassified unreachable module(s): {missing} — add each to "
            f"REACHABILITY_INTENT with a docstring-cited reason, or wire it.")

    def test_every_intent_uses_a_valid_category_and_a_reason(self):
        for name, (cat, reason) in REACHABILITY_INTENT.items():
            self.assertIn(cat, INTENT_CATEGORIES, name)
            self.assertTrue(reason.strip(), name)

    def test_the_report_names_the_categories(self):
        report = scan_reachability(Path(__file__).resolve().parents[2])
        out = format_reachability(report)
        if report.unreachable:
            for cat in INTENT_CATEGORIES:
                self.assertIn(cat, out)


def _repo(**files):
    """Build a throwaway repo: {relative_path: text}."""
    root = Path(tempfile.mkdtemp())
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return root


class TestTheFailureThisWasBuiltFor(unittest.TestCase):
    """Three times in three days a module was built, tested, documented
    and left unreachable. Each was found by accident, one cycle late."""

    def test_a_tested_module_nobody_imports_is_unreachable(self):
        root = _repo(**{
            "foundation/orphan.py": "def work(): return 1\n",
            "foundation/tests/test_orphan.py": "from foundation.orphan import work\n",
        })
        r = scan_reachability(root)
        self.assertEqual([m.name for m in r.unreachable], ["orphan"])

    def test_a_test_file_importing_it_does_not_count_as_a_caller(self):
        """The whole distinction. spec_crossref had 39 tests importing
        it and no way to run it."""
        root = _repo(**{
            "foundation/orphan.py": "x = 1\n",
            "foundation/tests/test_orphan.py": "from foundation.orphan import x\n",
        })
        r = scan_reachability(root)
        self.assertEqual(r.modules[0].importers, ())
        self.assertEqual(r.modules[0].reach, "UNREACHABLE")

    def test_a_module_imported_by_production_code_is_reachable(self):
        root = _repo(**{
            "foundation/used.py": "x = 1\n",
            "foundation/caller.py": "from foundation.used import x\n",
            "foundation/tests/test_used.py": "pass\n",
        })
        r = scan_reachability(root)
        used = [m for m in r.modules if m.name == "used"][0]
        self.assertEqual(used.reach, "IMPORTED")
        self.assertEqual(r.unreachable, ())


class TestEntryPointsAreReachable(unittest.TestCase):
    """A module nothing imports but that runs itself is not lost -- a
    human or a cron line has a way in. Counting those as unreachable
    would have flagged autonomy_loop and scheduled_brief, which run on
    a schedule."""

    def test_dunder_main_counts(self):
        root = _repo(**{
            "foundation/tool.py": 'if __name__ == "__main__":\n    pass\n',
            "foundation/tests/test_tool.py": "pass\n",
        })
        self.assertEqual(scan_reachability(root).modules[0].reach, "ENTRY_POINT")

    def test_a_main_function_counts(self):
        root = _repo(**{"foundation/tool.py": "def main():\n    pass\n",
                        "foundation/tests/test_tool.py": "pass\n"})
        self.assertEqual(scan_reachability(root).modules[0].reach, "ENTRY_POINT")

    def test_a_cli_function_counts(self):
        root = _repo(**{"foundation/tool.py": "def _cli():\n    pass\n",
                        "foundation/tests/test_tool.py": "pass\n"})
        self.assertEqual(scan_reachability(root).modules[0].reach, "ENTRY_POINT")

    def test_main_mentioned_in_a_comment_does_not_count(self):
        root = _repo(**{"foundation/tool.py": "# def main() would go here\nx=1\n",
                        "foundation/tests/test_tool.py": "pass\n"})
        self.assertEqual(scan_reachability(root).modules[0].reach, "UNREACHABLE")


class TestUntestedIsADifferentProblem(unittest.TestCase):
    def test_an_untested_unreachable_module_is_not_counted(self):
        """A module nobody tests and nobody calls is dead weight, not a
        lost capability. Mixing the two buries the ones that matter."""
        root = _repo(**{"foundation/deadweight.py": "x = 1\n"})
        r = scan_reachability(root)
        self.assertEqual(r.unreachable, ())
        self.assertEqual(r.tested, ())


class TestItReportsFactsNotVerdicts(unittest.TestCase):
    def test_the_render_says_unreachable_is_not_a_verdict(self):
        root = _repo(**{"foundation/orphan.py": "x=1\n",
                        "foundation/tests/test_orphan.py": "pass\n"})
        out = format_reachability(scan_reachability(root))
        self.assertIn("FACT, not a verdict", out)
        self.assertIn("DELIBERATE_GATE", out)

    def test_a_fully_reached_package_says_so_plainly(self):
        root = _repo(**{
            "foundation/used.py": "x=1\n",
            "foundation/caller.py": "from foundation.used import x\n",
            "foundation/tests/test_used.py": "pass\n",
        })
        out = format_reachability(scan_reachability(root))
        self.assertIn("finished-and-forgotten", out)

    def test_the_percentage_is_over_tested_modules_not_all_modules(self):
        root = _repo(**{
            "foundation/orphan.py": "x=1\n",
            "foundation/tests/test_orphan.py": "pass\n",
            "foundation/untested.py": "y=1\n",
        })
        r = scan_reachability(root)
        self.assertEqual(r.percentage_unreachable, 100.0)


class TestIntegrity(unittest.TestCase):
    def test_a_missing_package_directory_is_refused(self):
        with self.assertRaises(ReachabilityError):
            scan_reachability(Path("/nonexistent/repo"))

    def test_an_empty_package_is_refused(self):
        root = _repo(**{"foundation/__init__.py": "\n"})
        with self.assertRaises(ReachabilityError):
            scan_reachability(root)

    def test_format_refuses_a_non_report(self):
        with self.assertRaises(ReachabilityError):
            format_reachability("UNREACHABLE")

    def test_it_never_imports_the_modules_it_scans(self):
        """Importing them to test reachability would execute them."""
        from foundation import reachability
        src = Path(reachability.__file__).read_text(encoding="utf-8")
        self.assertNotIn("importlib", src)
        self.assertNotIn("__import__", src)


if __name__ == "__main__":
    unittest.main()
