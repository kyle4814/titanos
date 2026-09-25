"""`sentinel.iter_files_pruned` must return exactly what the code it replaced
returned: `root.rglob(pattern)` filtered by excluded path parts.

It exists only to stop the walk entering `corpus/` and `.git/`, whose files
every caller discards anyway (V12 Frontier 04). The speed-up is only
legitimate if the result set is identical, so this file pins identity:
on edge cases (symlinks, hidden entries, excluded names above the root)
and on the real repository. It also checks that nothing is cached: a new
or deleted file is reflected on the very next call.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from foundation.sentinel import _EXCLUDED_DIRS, iter_files_pruned

REPO_ROOT = Path(__file__).resolve().parents[2]


def _reference(root: Path, pattern: str, excluded=_EXCLUDED_DIRS) -> list[Path]:
    """The replaced implementation, verbatim in behaviour."""
    return sorted(p for p in root.rglob(pattern)
                  if not any(part in excluded for part in p.parts))


class TestEquivalentToRglobPlusFilter(unittest.TestCase):

    def _tree(self, td: str) -> Path:
        root = Path(td) / "repo"
        for d in ("a/b", "corpus/deep", ".git/objects", "__pycache__",
                  "node_modules/pkg", "build", "dist", ".hidden", "real",
                  "a/corpus"):
            (root / d).mkdir(parents=True, exist_ok=True)
        (root / "a/dir_named.py").mkdir()                        # dir matching *.py
        for f in ("a/test_a.py", "a/b/mod.py", "a/b/test_b.py",
                  "corpus/deep/test_c.py", "corpus/x.py", ".git/objects/test_g.py",
                  "__pycache__/test_p.py", "node_modules/pkg/test_n.py",
                  "build/test_bd.py", "dist/d.py", ".hidden/test_h.py",
                  ".hidden/.dot.py", "real/test_r.py", "a/corpus/test_nested.py",
                  "a/notpy.txt", "a/test_upper.PY"):
            (root / f).write_text("x = 1\n")
        os.symlink(root / "real", root / "linkdir")              # dir symlink
        os.symlink(root / "a/test_a.py", root / "a/test_link.py")  # file symlink
        os.symlink(root / "missing.py", root / "a/test_broken.py")  # broken
        os.symlink(root / "corpus", root / "corpus_link")          # into excluded
        return root

    def test_synthetic_edge_cases_match_exactly(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._tree(td)
            for pattern in ("test_*.py", "*.py", "*"):
                with self.subTest(pattern=pattern):
                    got = list(iter_files_pruned(root, pattern))
                    self.assertEqual(sorted(got), _reference(root, pattern))

    def test_excluded_name_above_root_still_excludes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "corpus" / "inner"
            root.mkdir(parents=True)
            (root / "test_x.py").write_text("")
            self.assertEqual(list(iter_files_pruned(root, "test_*.py")), [])
            self.assertEqual(_reference(root, "test_*.py"), [])

    def test_custom_exclusion_set_is_honoured(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._tree(td)
            excluded = frozenset({"a"})
            self.assertEqual(sorted(iter_files_pruned(root, "*.py", excluded)),
                             _reference(root, "*.py", excluded))

    def test_order_is_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._tree(td)
            first = list(iter_files_pruned(root, "*.py"))
            self.assertEqual(first, list(iter_files_pruned(root, "*.py")))

    def test_nothing_is_cached_between_calls(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._tree(td)
            before = set(iter_files_pruned(root, "*.py"))
            (root / "a/b/new_test.py").write_text("")
            (root / "a/b/mod.py").unlink()
            after = set(iter_files_pruned(root, "*.py"))
            self.assertIn(root / "a/b/new_test.py", after)
            self.assertNotIn(root / "a/b/mod.py", after)
            self.assertEqual(sorted(after), _reference(root, "*.py"))
            self.assertNotEqual(before, after)


class TestEquivalentOnTheRealRepository(unittest.TestCase):

    def test_real_repo_matches_for_every_pattern_the_callers_use(self):
        for pattern in ("test_*.py", "*.py"):
            with self.subTest(pattern=pattern):
                got = list(iter_files_pruned(REPO_ROOT, pattern))
                self.assertEqual(sorted(got), _reference(REPO_ROOT, pattern))
                self.assertTrue(got, "the real repository has files matching this")


if __name__ == "__main__":
    unittest.main()
