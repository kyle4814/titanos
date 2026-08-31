"""The manifest must be computed, and must not lie.

A cleanroom reconstruction test on 2026-09-01 -- an engineer given the
repository and no conversation history -- named a machine-generated
state file as the single highest-value missing artifact, because every
hand-maintained snapshot here has drifted and then misled somebody.
These tests exist to keep this one honest.
"""

import json
import tempfile
import unittest
from pathlib import Path

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

    def setUp(self):
        self.m = compute_manifest(REPO_ROOT)

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


if __name__ == "__main__":
    unittest.main()
