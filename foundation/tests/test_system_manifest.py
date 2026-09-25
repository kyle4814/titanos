"""The manifest must be computed, and must not lie.

A cleanroom reconstruction test on 2026-09-01 -- an engineer given the
repository and no conversation history -- named a machine-generated
state file as the single highest-value missing artifact, because every
hand-maintained snapshot here has drifted and then misled somebody.
These tests exist to keep this one honest.
"""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from foundation.system_manifest import (
    REPO_ROOT, SystemManifest, compute_manifest, format_manifest,
)


class TestItIsComputedNotStored(unittest.TestCase):

    def test_computing_writes_nothing(self):
        """The whole point. A manifest that persists itself becomes the
        next stale snapshot."""
        before = {p for p in REPO_ROOT.rglob("*") if p.is_file()}
        compute_manifest(REPO_ROOT)
        after = {p for p in REPO_ROOT.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_digest_is_stable_across_runs(self):
        """Two runs against an unchanged repository must agree, or the
        digest cannot be used to detect drift."""
        a = compute_manifest(REPO_ROOT)
        b = compute_manifest(REPO_ROOT)
        self.assertEqual(a.digest(), b.digest())

    def test_digest_excludes_the_timestamp(self):
        a = compute_manifest(REPO_ROOT)
        self.assertNotIn(a.computed_at, json.dumps(a.to_dict()).replace(
            a.computed_at, "", 1))
        self.assertEqual(a.digest(), compute_manifest(REPO_ROOT).digest())

    def test_it_never_claims_the_suite_is_green(self):
        """test_functions is an inventory. Saying otherwise would be the
        exact overclaim this module was built against."""
        text = format_manifest(compute_manifest(REPO_ROOT))
        self.assertIn("INVENTORY, not a pass count", text)


class TestItReportsRealNumbers(unittest.TestCase):
    # One computation shared by read-only assertions (V12 Frontier 04): the
    # manifest is a frozen snapshot of an unchanged repository, and none of
    # these tests mutates it. Tests about computing it twice live above.

    @classmethod
    def setUpClass(cls):
        cls.m = compute_manifest(REPO_ROOT)

    def test_it_finds_the_real_test_inventory(self):
        self.assertGreater(self.m.test_functions, 1000)
        self.assertGreater(self.m.test_modules, 50)

    def test_it_counts_open_human_decisions_not_headings(self):
        """An earlier version counted `###` headings and reported 1
        against a real 13."""
        self.assertGreater(self.m.open_human_decisions, 5)

    def test_resolved_decisions_are_excluded_from_open(self):
        self.assertGreaterEqual(self.m.resolved_human_decisions, 1)

    def test_it_locates_the_durable_ledgers(self):
        """Assert the manifest KNOWS the ledgers, not that this machine has
        run them.

        This previously required >= 3 present. Four of the five durable
        ledgers are gitignored runtime state, so a fresh clone has one --
        and this assertion failed there for eight consecutive CI runs while
        every local run passed, because it was measuring accumulated local
        history rather than the manifest's behaviour.

        What the manifest actually owes is: know every ledger it tracks,
        and report each one's presence correctly. Absence is a fact about
        the checkout, not a defect in the reporter."""
        self.assertGreaterEqual(len(self.m.durable_ledgers), 3,
                                "the manifest must track the known ledgers")
        for name, info in self.m.durable_ledgers.items():
            self.assertIn("present", info,
                          f"{name} reports no presence verdict")
            self.assertEqual(
                info["present"], (REPO_ROOT / name).exists(),
                f"{name}: reported presence disagrees with the filesystem")

    def test_a_legacy_receipt_head_is_flagged_not_called_verified(self):
        joined = " ".join(self.m.notes)
        if self.m.receipt_head and not self.m.receipt_head.startswith("OC-chain"):
            self.assertIn("CHAIN_UNVERIFIED_LEGACY", joined + format_manifest(self.m))


class TestItDetectsStaleNextMove(unittest.TestCase):
    """The cleanroom test found NEXT_MOVE.md asserting a git state that
    contradicted reality, with nothing checking."""

    def test_a_next_move_citing_an_old_commit_is_flagged(self):
        m = compute_manifest(REPO_ROOT)
        if m.next_move_stale:
            self.assertIn("STALE", format_manifest(m))

    def test_a_repo_without_next_move_reports_nowhere(self):
        with tempfile.TemporaryDirectory() as d:
            m = compute_manifest(Path(d))
            self.assertEqual(m.next_move_recorded_in, "")
            self.assertIsNone(m.next_move_stale)


class TestItSurvivesAnEmptyRepository(unittest.TestCase):
    """A manifest that crashes on an unfamiliar tree is useless to the
    fresh worker it exists for."""

    def test_it_does_not_raise_on_an_empty_directory(self):
        with tempfile.TemporaryDirectory() as d:
            m = compute_manifest(Path(d))
            self.assertIsInstance(m, SystemManifest)
            self.assertEqual(m.python_modules, 0)

    def test_format_works_on_an_empty_repository(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIn("SYSTEM MANIFEST", format_manifest(compute_manifest(Path(d))))


_REAL_RUN = subprocess.run


def _fake_git(fail_args, exc=None):
    """subprocess.run stand-in: the git call whose args start with
    `fail_args` raises `exc` (or exits 128); `cat-file` claims every hash
    is a commit; everything else runs for real."""
    def run(cmd, *a, **kw):
        if cmd[:1] == ["git"] and cmd[1:1 + len(fail_args)] == list(fail_args):
            if exc is not None:
                raise exc
            return subprocess.CompletedProcess(cmd, 128, "", "fatal")
        if cmd[:3] == ["git", "cat-file", "-t"]:
            return subprocess.CompletedProcess(cmd, 0, "commit\n", "")
        return _REAL_RUN(cmd, *a, **kw)
    return run


class TestGitFailureIsUnknownNotClean(unittest.TestCase):
    """UNKNOWN does not equal true. A failed or timed-out `git status`
    used to collapse into "" and so into worktree_clean=True -- a
    directory that is not a repository at all was reported clean in the
    same manifest that called its revision UNKNOWN."""

    def test_a_non_repository_is_unknown_not_clean(self):
        with tempfile.TemporaryDirectory() as d:
            m = compute_manifest(Path(d))
            self.assertIsNone(m.worktree_clean)
            self.assertTrue(any("UNKNOWN" in n for n in m.notes), m.notes)
            # Clean renders as no suffix at all; UNKNOWN must be explicit.
            rev_line = next(l for l in format_manifest(m).splitlines()
                            if "repo_revision" in l)
            self.assertTrue(rev_line.endswith("(WORKTREE UNKNOWN)"), rev_line)

    def test_a_status_timeout_is_unknown_not_clean(self):
        timeout = subprocess.TimeoutExpired(["git", "status"], 15)
        with tempfile.TemporaryDirectory() as d, mock.patch(
                "foundation.system_manifest.subprocess.run",
                side_effect=_fake_git(("status",), timeout)):
            m = compute_manifest(Path(d))
        self.assertIsNone(m.worktree_clean)
        self.assertIsNot(m.worktree_clean, True)
        self.assertTrue(any("git status failed or timed out" in n
                            for n in m.notes), m.notes)

    def test_a_failed_head_lookup_does_not_crash_the_next_move_check(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "NEXT_MOVE.md").write_text("Built at abc1234.\n")
            with mock.patch("foundation.system_manifest.subprocess.run",
                            side_effect=_fake_git(("rev-parse", "HEAD"))):
                m = compute_manifest(Path(d))
        self.assertEqual(m.next_move_recorded_in, "NEXT_MOVE.md")
        self.assertTrue(m.next_move_stale)


if __name__ == "__main__":
    unittest.main()
