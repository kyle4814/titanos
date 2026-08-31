"""The capability manifest must be computed, and its central distinction
-- IMPLEMENTED_UNWIRED versus VERIFIED -- must not be collapsible.

The old `CAPABILITY_MANIFEST.json` was hand-typed, carried a dead
`as_of: 2026-08-27`, listed 10 subsystems while `compiler/` and `gems/`
already existed, and said "VERIFIED" for every single entry regardless of
whether anything actually called it. These tests exist to keep the
generator that replaced it honest.
"""

import json
import tempfile
import unittest
from pathlib import Path

from foundation.capability_registry import (
    REPO_ROOT,
    ALL_STATES,
    STATE_IMPLEMENTED_UNWIRED,
    STATE_VERIFIED,
    discover_capabilities,
    write_manifest,
)


class TestDiscoveryWritesNothing(unittest.TestCase):

    def test_discovery_writes_nothing(self):
        """Discovering must never mutate the repository -- the whole
        point of a computed manifest is that reading it is free."""
        before = {p for p in REPO_ROOT.rglob("*") if p.is_file()}
        discover_capabilities(REPO_ROOT)
        after = {p for p in REPO_ROOT.rglob("*") if p.is_file()}
        self.assertEqual(before, after)


class TestStateVocabulary(unittest.TestCase):

    def test_every_state_is_one_of_the_declared_values(self):
        caps = discover_capabilities(REPO_ROOT)
        self.assertTrue(caps, "expected at least one discovered capability")
        for cap in caps:
            self.assertIn(cap.state, ALL_STATES,
                          f"{cap.capability_id} has undeclared state {cap.state!r}")

    def test_all_states_enumerates_exactly_five_values(self):
        """Pinned so a state cannot be added casually.

        Went 4 -> 5 on 2026-09-01 when ENTRYPOINT was split out of
        IMPLEMENTED_UNWIRED. This assertion is the reason that split was
        a deliberate act with a written justification rather than a
        quiet widening of the vocabulary, which is exactly its job.
        """
        self.assertEqual(len(ALL_STATES), 5)
        self.assertEqual(len(set(ALL_STATES)), 5)


class TestEntrypointIsNotUnwired(unittest.TestCase):
    """ENTRYPOINT exists because the registry was wrong about the single
    most-executed module in this repository.

    `foundation/cron_pulse.py` runs hourly under cron and demonstrably
    executes. The original rule classified it IMPLEMENTED_UNWIRED --
    identical to `hells_gate.py`, which has 36 tests and nothing that can
    reach it. Those are different facts and the published number said
    they were the same one."""

    def test_cron_pulse_is_not_reported_as_unwired(self):
        caps = {c.capability_id: c for c in discover_capabilities(REPO_ROOT)}
        cron = caps.get("foundation/cron_pulse.py")
        self.assertIsNotNone(cron, "foundation/cron_pulse.py not discovered")
        self.assertTrue(cron.entrypoint, "cron_pulse.py must have a __main__")
        self.assertNotEqual(
            cron.state, "IMPLEMENTED_UNWIRED",
            "the repository's most-executed module reported as unwired")

    def test_hells_gate_is_still_unwired(self):
        """The distinction must not become a blanket excuse. A tested
        module with no importer AND no __main__ is genuinely unreachable
        and must keep saying so."""
        caps = {c.capability_id: c for c in discover_capabilities(REPO_ROOT)}
        gate = caps.get("foundation/hells_gate.py")
        self.assertIsNotNone(gate)
        self.assertFalse(gate.entrypoint)
        self.assertEqual(gate.state, "IMPLEMENTED_UNWIRED")

    def test_entrypoint_state_requires_tests(self):
        """A `__main__` must not launder an untested module into a
        healthier-sounding state."""
        from foundation.capability_registry import _derive_state
        self.assertEqual(
            _derive_state(has_tests=False, production_importers=0,
                          is_scaffold=False, is_entrypoint=True),
            "UNTESTED")

    def test_importer_still_beats_entrypoint(self):
        """A module that is both imported and runnable is VERIFIED --
        having a __main__ must not downgrade it."""
        from foundation.capability_registry import _derive_state
        self.assertEqual(
            _derive_state(has_tests=True, production_importers=2,
                          is_scaffold=False, is_entrypoint=True),
            "VERIFIED")


class TestImplementedUnwiredIsNotVerified(unittest.TestCase):
    """The single most important assertion in this file. A module with
    real tests and zero production importers must never be reported as
    VERIFIED -- that exact collapse is what let a dozen unwired gates in
    this repository go unnoticed under the old hand-typed manifest."""

    def test_hells_gate_has_tests_and_zero_production_importers(self):
        """`foundation/hells_gate.py` is a real, tested module with no
        production caller anywhere in this repository -- documented as
        such in this repo's own CLAUDE.md ('the rest ... have no
        production caller'). It must classify as IMPLEMENTED_UNWIRED."""
        caps = {c.capability_id: c for c in discover_capabilities(REPO_ROOT)}
        cap = caps.get("foundation/hells_gate.py")
        self.assertIsNotNone(cap, "expected foundation/hells_gate.py to be discovered")
        self.assertTrue(cap.has_tests, "hells_gate.py should have real tests")
        self.assertGreater(cap.test_count, 0)
        self.assertEqual(cap.production_importers, 0,
                         "hells_gate.py has no production importer in this repo")
        self.assertEqual(cap.state, STATE_IMPLEMENTED_UNWIRED)
        self.assertNotEqual(cap.state, STATE_VERIFIED)

    def test_a_module_with_a_real_production_importer_is_verified(self):
        """`foundation/crystal.py` is imported by real production modules
        (`foundation/situation_analysis.py`, `foundation/sentinel_worker.py`)
        -- the mirror-image case, so this file cannot be accused of
        always answering IMPLEMENTED_UNWIRED regardless of the evidence."""
        caps = {c.capability_id: c for c in discover_capabilities(REPO_ROOT)}
        cap = caps.get("foundation/crystal.py")
        self.assertIsNotNone(cap)
        self.assertTrue(cap.has_tests)
        self.assertGreater(cap.production_importers, 0)
        self.assertEqual(cap.state, STATE_VERIFIED)

    def test_repository_actually_has_many_implemented_unwired_modules(self):
        """Not a single cherry-picked example -- this repository's own
        CLAUDE.md documents this as a widespread, load-bearing finding
        ('twelve gate/switch modules exist ... exactly one is load-bearing
        on a real action'). If this count collapsed to a handful, the
        importer-resolution logic would be under-matching real imports."""
        caps = discover_capabilities(REPO_ROOT)
        unwired = [c for c in caps if c.state == STATE_IMPLEMENTED_UNWIRED]
        self.assertGreater(len(unwired), 10,
                           "expected many IMPLEMENTED_UNWIRED modules, "
                           f"found {len(unwired)}")


class TestCoverageExceedsOldManifest(unittest.TestCase):

    def test_real_repo_yields_more_than_ten_capabilities(self):
        """The old hand-typed manifest listed exactly 10 entries. The
        real repository, computed, has substantially more -- that gap
        IS the defect this module exists to fix."""
        caps = discover_capabilities(REPO_ROOT)
        self.assertGreater(len(caps), 10)

    def test_compiler_and_gems_are_discovered(self):
        """The two subsystems the old manifest omitted entirely."""
        ids = {c.capability_id for c in discover_capabilities(REPO_ROOT)
               if c.kind == "SUBSYSTEM"}
        self.assertIn("compiler", ids)
        self.assertIn("gems", ids)

    def test_foundation_modules_are_individually_tracked(self):
        """Roughly 20+ substantial foundation/*.py modules were built
        since the old manifest's as_of date and appeared nowhere in it."""
        module_ids = {c.capability_id for c in discover_capabilities(REPO_ROOT)
                     if c.kind == "MODULE"}
        self.assertGreater(len(module_ids), 20)
        self.assertIn("foundation/crystal.py", module_ids)
        self.assertIn("foundation/hells_gate.py", module_ids)


class TestWriteManifest(unittest.TestCase):

    def _tmp_repo_manifest(self) -> Path:
        d = Path(tempfile.mkdtemp())
        return d / "CAPABILITY_MANIFEST.json"

    def test_write_manifest_regenerating_twice_is_stable_apart_from_timestamp(self):
        tmp_path = self._tmp_repo_manifest()
        try:
            first = write_manifest(REPO_ROOT, manifest_path=tmp_path)
            second = write_manifest(REPO_ROOT, manifest_path=tmp_path)
            first = dict(first)
            second = dict(second)
            first.pop("generated_at")
            second.pop("generated_at")
            self.assertEqual(
                json.dumps(first, sort_keys=True),
                json.dumps(second, sort_keys=True),
                "regenerating twice against an unchanged repository must "
                "produce identical content apart from the timestamp")
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_no_hand_typeable_as_of_field(self):
        tmp_path = self._tmp_repo_manifest()
        try:
            m = write_manifest(REPO_ROOT, manifest_path=tmp_path)
            self.assertNotIn("as_of", m)
            self.assertIn("generated_at", m)
            self.assertIn("generated_by", m)
            self.assertIn("repo_revision", m)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_existing_human_written_prose_survives_regeneration(self):
        """Seed a tmp manifest with hand-written prose under a real
        capability_id (`schema`, which this repository's own
        BUILD_REPORT.md-backed subsystem always resolves to), then
        regenerate and confirm the prose was carried forward verbatim
        rather than discarded or replaced with a generated paragraph."""
        tmp_path = self._tmp_repo_manifest()
        seed = {
            "capabilities": [
                {
                    "capability_id": "schema",
                    "problem_class": "SEED_MARKER_PROBLEM_CLASS",
                    "limitations": "SEED_MARKER_LIMITATIONS",
                    "authority_required": "SEED_MARKER_AUTHORITY",
                }
            ]
        }
        tmp_path.write_text(json.dumps(seed), encoding="utf-8")
        try:
            m = write_manifest(REPO_ROOT, manifest_path=tmp_path)
            entries = {e["capability_id"]: e for e in m["capabilities"]}
            self.assertIn("schema", entries)
            self.assertEqual(entries["schema"]["problem_class"],
                             "SEED_MARKER_PROBLEM_CLASS")
            self.assertEqual(entries["schema"]["limitations"],
                             "SEED_MARKER_LIMITATIONS")
            self.assertEqual(entries["schema"]["authority_required"],
                             "SEED_MARKER_AUTHORITY")
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_new_entry_with_no_prior_prose_says_so_plainly(self):
        """A capability_id that never had human-written prose must not
        get an invented description -- it must say plainly that none was
        recorded."""
        tmp_path = self._tmp_repo_manifest()
        try:
            m = write_manifest(REPO_ROOT, manifest_path=tmp_path)
            entries = {e["capability_id"]: e for e in m["capabilities"]}
            cap = entries.get("foundation/hells_gate.py")
            self.assertIsNotNone(cap)
            self.assertEqual(cap["problem_class"],
                             "no human-written description recorded")
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_write_manifest_actually_writes_the_real_repo_file(self):
        """One real, non-tmp-path invocation against the actual
        `CAPABILITY_MANIFEST.json`, so the generator is proven against
        the artifact it is actually responsible for, not only a scratch
        copy."""
        from foundation.capability_registry import MANIFEST_PATH
        before_text = MANIFEST_PATH.read_text(encoding="utf-8") if \
            MANIFEST_PATH.is_file() else None
        # RESTORE IT AFTERWARDS. Without this the test rewrote the real
        # CAPABILITY_MANIFEST.json on every run -- a fresh timestamp and
        # revision each time -- leaving the working tree permanently
        # dirty and making WORKTREE_CLEAN unsatisfiable for anyone who
        # ran the suite before checking. A test that mutates the
        # repository it is testing is the same pollution class that once
        # wrote 9,828 bytes into foundation/outcome_ledger.jsonl.
        if before_text is not None:
            self.addCleanup(MANIFEST_PATH.write_text, before_text,
                            encoding="utf-8")
        m = write_manifest(REPO_ROOT)
        self.assertTrue(MANIFEST_PATH.is_file())
        self.assertGreater(len(m["capabilities"]), 10)
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(data["generated_by"],
                         "foundation.capability_registry.write_manifest")
        if before_text is not None:
            # Regeneration should not silently drop the schema entry's
            # prose that was present before this test ran.
            before_data = json.loads(before_text)
            before_ids = {e["capability_id"] for e in
                         before_data.get("capabilities", [])}
            if "schema" in before_ids:
                after_ids = {e["capability_id"] for e in data["capabilities"]}
                self.assertIn("schema", after_ids)


if __name__ == "__main__":                                  # pragma: no cover
    unittest.main()
