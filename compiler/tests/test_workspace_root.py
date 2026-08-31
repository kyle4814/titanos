"""Regression tests for compiler/coverage.py::resolve_workspace_root.

WHY THIS FILE EXISTS (2026-08-28, cycle german_config_001)

`compiler/` had zero tests. The compiler itself was never invoked by any
CI job, cron entry, or sentinel check — it existed, worked, and was never
run. When it finally WAS run this cycle against the obvious-looking root
(this repository), it returned REFUSED with 5 STALE_CLAIM, which reads
exactly like real doctrine drift. It was not drift: doctrine-002's
`enforced_at` paths are relative to `/home/tech2`, the parent, because the
invariants it governs live in the sibling `titanos_launch/` repo. Nothing
recorded that fact anywhere.

A checker whose correct invocation is undocumented produces false
REFUSALs, and a false REFUSAL is worse than no checker — it teaches
readers to ignore the tool. These tests lock in the fix.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COVERAGE = REPO_ROOT / "compiler" / "coverage.py"
DOCTRINE = REPO_ROOT / "doctrine" / "doctrine-002.yaml"


def _run(*args):
    proc = subprocess.run(
        [sys.executable, str(COVERAGE), *[str(a) for a in args]],
        capture_output=True, text=True,
    )
    return proc.returncode, json.loads(proc.stdout) if proc.stdout else None


# THE EXTERNAL WORKSPACE THESE DOCTRINES GOVERN
#
# `doctrine/*.yaml` declare `workspace_root: "../.."`, so their
# `enforced_at` paths resolve into SIBLING repositories of this one. Those
# siblings exist on the author's machine and are not part of this
# repository, so in a plain checkout -- CI, or any new contributor's first
# clone -- they are simply absent and every claim resolves to a missing
# file.
#
# The tests below that assert a real doctrine ACCEPTS were therefore
# asserting "this is the author's laptop", and they failed in CI for at
# least eight consecutive commits while every local run reported green.
#
# The compiler is right to report those unresolvable claims as
# STALE_CLAIM: from inside this repository an absent sibling and a moved
# file are genuinely indistinguishable, and a checker that guessed would
# be worse than one that refuses. (Adding an EXTERNAL_WORKSPACE_ABSENT
# verdict was tried and reverted -- it could not tell an absent checkout
# from a misconfigured root, so it also excused the wrong-root case that
# `test_a_wrong_declared_root_still_refuses` correctly pins.)
#
# So the environment dependency is declared here, where it belongs,
# instead of being silently assumed. Tests that need the siblings skip
# with a stated reason; every test that does NOT need them keeps running
# everywhere, which is most of this file.

def _external_workspace_present() -> bool:
    """True when the sibling repositories the doctrines point at are here.

    Probes doctrine-002 only -- the ACTIVE doctrine, whose claims all
    resolve when the workspace is present. doctrine-001 is deliberately
    preserved with one genuinely missing file (its I-06 STALE_CLAIM is the
    historical record doctrine-002 was authored to correct), so probing it
    would report "absent" even on a machine that has everything.
    """
    import yaml as _yaml
    path = REPO_ROOT / "doctrine" / "doctrine-002.yaml"
    if not path.exists():
        return False
    root = (REPO_ROOT / "doctrine" / "../..").resolve()
    tops = {str(inv.get("enforced_at") or "").split("::", 1)[0].split("/", 1)[0]
            for inv in (_yaml.safe_load(path.read_text(encoding="utf-8"))
                        or {}).get("invariants", [])
            if "/" in str(inv.get("enforced_at") or "")}
    return bool(tops) and all((root / t).exists() for t in tops)


EXTERNAL_WORKSPACE = _external_workspace_present()
needs_external = unittest.skipUnless(
    EXTERNAL_WORKSPACE,
    "the sibling repositories these doctrines govern are not present in "
    "this checkout; the claims resolve to missing files and the compiler "
    "correctly refuses. Nothing is wrong with the doctrine or the compiler "
    "-- the code under audit simply is not here.")


class TestWorkspaceRootResolution(unittest.TestCase):
    @needs_external
    def test_declared_root_makes_the_real_doctrine_accepted(self):
        """The whole point: default invocation, no CLI root, must ACCEPT."""
        code, report = _run(DOCTRINE)
        self.assertEqual(code, 0)
        self.assertEqual(report["result"], "ACCEPTED")
        self.assertEqual(report["failed"], 0)
        self.assertEqual(report["workspace_root_source"], "declared_or_default")

    def test_removing_the_declaration_reproduces_the_false_refusal(self):
        """The exact defect, mechanically reproduced: with no declared
        root the compiler falls back to the doctrine's own directory and
        every enforced_at path fails to resolve."""
        with tempfile.TemporaryDirectory() as d:
            stripped = Path(d) / "no_decl.yaml"
            stripped.write_text("\n".join(
                l for l in DOCTRINE.read_text().splitlines()
                if not l.startswith("workspace_root:")
            ))
            code, report = _run(stripped)
        self.assertEqual(code, 1)
        self.assertEqual(report["result"], "REFUSED")

    def test_a_wrong_declared_root_still_refuses(self):
        """The declaration is not a rubber stamp — declaring a root that
        does not contain the enforcement code must still REFUSE, or the
        mechanism would launder any claim."""
        with tempfile.TemporaryDirectory() as d:
            wrong = Path(d) / "wrong.yaml"
            wrong.write_text(DOCTRINE.read_text().replace(
                'workspace_root: "../.."', 'workspace_root: "."'))
            code, report = _run(wrong)
        self.assertEqual(code, 1)
        self.assertEqual(report["result"], "REFUSED")
        self.assertEqual(report["failed"], 5)

    def test_cli_override_still_wins(self):
        """Backwards compatibility: an explicit root argument must take
        precedence, so the tool stays testable against a fixture tree and
        a caller who knows better is never blocked by a stale
        declaration."""
        code, report = _run(DOCTRINE, REPO_ROOT)
        self.assertEqual(report["workspace_root_source"], "cli")
        self.assertEqual(report["result"], "REFUSED")

    def test_refusal_is_the_success_path_not_a_crash(self):
        """A REFUSED doctrine must exit 1 with a full JSON report, never
        raise — the report is the evidence."""
        code, report = _run(DOCTRINE, REPO_ROOT)
        self.assertEqual(code, 1)
        self.assertIn("findings", report)
        self.assertTrue(all("verdict" in f for f in report["findings"]))


class TestGeneralizationAcrossAllDoctrines(unittest.TestCase):
    """N=3 probe (2026-08-28, cycle config_generalization_001).

    The workspace_root fix was implemented for doctrine-002 alone. Probing
    the other two real doctrine files reproduced the SAME failure shape
    twice more — and revealed that all three used DIFFERENT implicit root
    conventions, none of them recorded anywhere:

      doctrine-001.yaml            titanos-obelisk/...      (parent root)
      doctrine-002.yaml            titanos_launch/...       (parent root)
      POLE_REVERSAL_DOCTRINE.yaml  cosmic-library/...       (parent root)

    Same resolved root, three different path prefixes, zero declarations.
    That is a reproduced pattern (N=3), not a one-off — but the fix stayed
    a local declaration per file, NOT a new mechanism, because the existing
    resolve_workspace_root() already carried it.
    """

    DOCTRINE_DIR = REPO_ROOT / "doctrine"

    @needs_external
    def test_pole_reversal_is_accepted_with_its_declaration(self):
        code, report = _run(self.DOCTRINE_DIR / "POLE_REVERSAL_DOCTRINE.yaml")
        self.assertEqual(report["result"], "ACCEPTED")
        self.assertEqual(report["failed"], 0)
        self.assertEqual(code, 0)

    def test_pole_reversal_refuses_without_its_declaration(self):
        """Discriminating mutation: strip the declaration, the same false
        REFUSAL returns. Proves the declaration is load-bearing here too,
        not decorative."""
        src = (self.DOCTRINE_DIR / "POLE_REVERSAL_DOCTRINE.yaml").read_text()
        with tempfile.TemporaryDirectory() as d:
            stripped = Path(d) / "pr.yaml"
            stripped.write_text("\n".join(
                l for l in src.splitlines() if not l.startswith("workspace_root:")))
            code, report = _run(stripped)
        self.assertEqual(report["result"], "REFUSED")

    @needs_external
    def test_doctrine_001_is_correctly_still_refused(self):
        """NOT a bug. doctrine-001 is SUPERSEDED and deliberately preserved
        verbatim; its one STALE_CLAIM (I-06) is the exact defect that
        doctrine-002's own amendment_record cites as the reason 002 was
        authored. Editing it would destroy the historical record. This test
        exists so a future agent does not "fix" it."""
        code, report = _run(self.DOCTRINE_DIR / "doctrine-001.yaml")
        self.assertEqual(report["result"], "REFUSED")
        self.assertEqual(report["failed"], 1)
        stale = [f for f in report["findings"] if f["verdict"] == "STALE_CLAIM"]
        self.assertEqual(len(stale), 1)
        self.assertEqual(stale[0]["invariant_id"], "I-06")

    def test_doctrine_001_declares_itself_superseded(self):
        """The two-file contradiction found this cycle: doctrine-002 said
        `supersedes: DOCTRINE-001` while doctrine-001 said `status: ACTIVE`
        and `superseded_by: null`. Nothing detected it because nothing ever
        ran the compiler against doctrine-001."""
        import yaml as _yaml
        doc = _yaml.safe_load((self.DOCTRINE_DIR / "doctrine-001.yaml").read_text())
        self.assertEqual(doc["status"], "SUPERSEDED")
        self.assertEqual(doc["superseded_by"], "DOCTRINE-002")
        d2 = _yaml.safe_load((self.DOCTRINE_DIR / "doctrine-002.yaml").read_text())
        self.assertEqual(d2["supersedes"], "DOCTRINE-001",
                         "the two files must agree on the supersession edge")


class TestEveryApplicableDoctrineIsValidated(unittest.TestCase):
    """COVERAGE ESCAPE, reproduced 2026-08-28 (cycle coverage_probe_001).

    THE DEFECT THIS CLOSES: CI runs `unittest discover -s compiler`, and
    every test above names its doctrine file explicitly
    (`doctrine-002.yaml`, `POLE_REVERSAL_DOCTRINE.yaml`, ...). Discovery
    was therefore EXPLICIT ENUMERATION INSIDE TEST CODE. Reproduced
    directly: a fourth file, `doctrine-999-ESCAPE-PROBE.yaml`, declaring
    `status: ENFORCED` against `nonexistent/path/does_not_exist.py`, was
    dropped into `doctrine/`. Pointed at directly the compiler correctly
    REFUSED it (exit 1). Run through CI's actual invocation, the full
    suite stayed GREEN — the file escaped validation entirely while
    sitting in the repository.

    "All three known files pass" was never the same claim as "a fourth
    file cannot silently exist outside the validation boundary."

    APPLICABILITY FILTER: a YAML in doctrine/ is a doctrine iff it has a
    top-level `invariants:` key. That is the compiler's own contract --
    `check_doctrine` iterates `doc.get("invariants", [])` -- so a
    non-doctrine YAML placed beside them is not forced through and cannot
    create a false failure. Reusing the compiler's existing notion of
    applicability rather than inventing a registry, manifest, or marker.
    """

    DOCTRINE_DIR = REPO_ROOT / "doctrine"

    @classmethod
    def applicable_doctrines(cls):
        """Glob discovery + the compiler's own applicability contract."""
        import yaml as _yaml
        found = []
        for path in sorted(REPO_ROOT.rglob("*.yaml")):
            if any(part in ("__pycache__", ".git", "node_modules")
                   for part in path.parts):
                continue
            try:
                doc = _yaml.safe_load(path.read_text(encoding="utf-8",
                                                     errors="replace"))
            except _yaml.YAMLError:
                continue
            if not isinstance(doc, dict):
                continue
            inv = doc.get("invariants")
            # The compiler's own contract: a list of invariants each
            # carrying `enforced_at`. Widened from doctrine/*.yaml to the
            # whole repo 2026-08-28 after magl/constitution/
            # OBELISK_INVARIANTS.yaml was found carrying this exact schema
            # OUTSIDE doctrine/ and having never been validated (11/11
            # CONSISTENT once run at the correct root -- never stale, just
            # unchecked). Directory location was never the real boundary;
            # the schema is.
            if isinstance(inv, list) and any(
                    isinstance(i, dict) and "enforced_at" in i for i in inv):
                found.append(path)
        return found

    def test_discovery_finds_at_least_the_known_doctrines(self):
        """Control: the escape hatch is glob-based, so it must actually
        find the files we already know about."""
        names = {p.name for p in self.applicable_doctrines()}
        self.assertIn("doctrine-002.yaml", names)
        self.assertIn("POLE_REVERSAL_DOCTRINE.yaml", names)
        self.assertIn("doctrine-001.yaml", names)

    def test_discovery_finds_obelisk_invariants_outside_doctrine_dir(self):
        """THE ACTUAL REGRESSION GUARANTEE for repo-wide discovery.

        REPRODUCED 2026-08-28 (cycle regression_probe_001): reverting
        `applicable_doctrines()` from `REPO_ROOT.rglob("*.yaml")` back to
        `DOCTRINE_DIR.glob("*.yaml")` left the ENTIRE compiler suite
        green -- no committed test named this file, so nothing noticed
        it silently dropped out of the validated set.
        magl/constitution/OBELISK_INVARIANTS.yaml carries the compiler's
        full schema (11 invariants with enforced_at/status/test) and
        lives OUTSIDE doctrine/ -- it is the one real file that exists
        specifically because directory location was never the true
        applicability boundary, only the schema is. This is the only
        committed assertion that discriminates repo-wide discovery from
        directory-scoped discovery."""
        names = {p.name for p in self.applicable_doctrines()}
        self.assertIn("OBELISK_INVARIANTS.yaml", names)

    def test_every_applicable_doctrine_declares_a_workspace_root(self):
        """No applicable doctrine may omit `workspace_root` — omitting it
        silently resolves to the doctrine's own directory, which produces
        a FALSE REFUSAL that reads like real drift."""
        import yaml as _yaml
        missing = [
            p.name for p in self.applicable_doctrines()
            if "workspace_root" not in (
                _yaml.safe_load(p.read_text(encoding="utf-8")) or {})
        ]
        self.assertEqual(missing, [], f"applicable doctrines with no declared "
                         f"workspace_root: {missing}")

    @needs_external
    def test_every_applicable_doctrine_is_accepted_or_knowingly_refused(self):
        """The real coverage gate. Every discovered doctrine is actually
        run through the compiler. ACCEPTED passes. REFUSED passes ONLY if
        the file is explicitly marked SUPERSEDED — a superseded doctrine
        is a preserved historical record whose stale claims must not be
        edited (doctrine-001's I-06 is exactly that). Any other REFUSAL
        fails the build."""
        import yaml as _yaml
        failures = []
        for path in self.applicable_doctrines():
            code, report = _run(path)
            if report["result"] == "ACCEPTED":
                continue
            doc = _yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            if self._supersession_is_corroborated(doc):
                continue
            failures.append((path.name, report["result"], report["failed"]))
        self.assertEqual(failures, [], f"ACTIVE doctrines refused by the "
                         f"compiler: {failures}")

    @classmethod
    def _supersession_is_corroborated(cls, doc):
        """A lifecycle exemption may not be self-authorised.

        THE DEFECT THIS CLOSES (reproduced 2026-08-28, cycle
        identity_probe_001): the first version of this gate skipped any
        doctrine declaring `status: SUPERSEDED`. That is an escape hatch
        the exempted file writes for itself. Reproduced directly: a file
        declaring SUPERSEDED, `superseded_by: null`, a valid
        `workspace_root`, and `status: ENFORCED` against
        `nonexistent/nope.py` was REFUSED by the compiler (exit 1) while
        this suite reported OK.

        Corroboration reuses the bidirectional metadata the schema
        already carries -- doctrine-001 declares
        `superseded_by: DOCTRINE-002` and doctrine-002 independently
        declares `supersedes: DOCTRINE-001`. Both halves must agree, in
        two separate files, before the exemption is honoured. No
        registry, no new field, no heuristic.
        """
        import yaml as _yaml
        if str(doc.get("status", "")).upper() != "SUPERSEDED":
            return False
        successor = doc.get("superseded_by")
        if not successor:
            return False   # orphan SUPERSEDED: names no successor
        own_id = doc.get("id")
        for other in cls.applicable_doctrines():
            odoc = _yaml.safe_load(other.read_text(encoding="utf-8")) or {}
            if odoc.get("id") == successor and odoc.get("supersedes") == own_id:
                return True
        return False   # successor absent, or does not point back


class TestDoctrineIdentityBoundary(unittest.TestCase):
    """A malformed doctrine must not be able to demote itself to
    "unrelated YAML" and escape the gate.

    REPRODUCED 2026-08-28 (cycle identity_probe_001): removing the
    `invariants:` key from a real doctrine makes it non-applicable under
    the glob+`invariants:` filter, so it silently leaves the validated
    set. The escape WAS caught, but only incidentally — by tests that
    happen to name `doctrine-002.yaml` literally. Rename or add a file
    and that accident does not repeat.

    The distinction that must hold mechanically:

        unrelated YAML          -> ignored, no false failure
        malformed doctrine      -> DETECTED, not silently ignored
        valid active doctrine   -> validated

    DOCTRINE_MARKERS below are the fields every real doctrine in this
    repository actually carries (verified against all three). A file
    carrying doctrine identity but missing `invariants:` is malformed,
    not unrelated — it is claiming to be a doctrine while omitting the
    thing that makes a doctrine checkable.
    """

    DOCTRINE_DIR = REPO_ROOT / "doctrine"
    # Identity markers, not a heuristic guess: every real doctrine here
    # declares all three. `docs/SENSOR_ATLAS.yaml` and ordinary notes
    # files declare none of them.
    DOCTRINE_MARKERS = ("id", "status", "effective_from")

    @classmethod
    def _load(cls, path):
        import yaml as _yaml
        try:
            doc = _yaml.safe_load(path.read_text(encoding="utf-8"))
        except _yaml.YAMLError:
            return None
        return doc if isinstance(doc, dict) else None

    @classmethod
    def _claims_doctrine_identity(cls, doc):
        """THRESHOLD, NOT all(). Reproduced 2026-08-28: with `all()`, 7 of
        the 8 marker subsets escaped silently -- a file with {id, status}
        and no `invariants:` was neither applicable nor malformed, so it
        fell through BOTH boundaries. Two of three markers is the measured
        threshold: every real doctrine carries all three, and a repo-wide
        scan found no YAML carrying 2+ that is not genuinely a doctrine/
        constitution artifact. Extracted to its own method (2026-08-28,
        cycle regression_probe_001) after proving no committed test would
        catch a regression back to `all()`: every real file in doctrine/
        happens to carry all 3 markers, so the real-directory sweep below
        cannot discriminate the two implementations -- only a synthetic
        fixture can. See test_threshold_flags_a_two_marker_fixture_
        without_invariants below, the actual regression guarantee."""
        present = sum(1 for m in cls.DOCTRINE_MARKERS if m in doc)
        return present >= 2

    def test_no_yaml_in_doctrine_dir_claims_identity_without_invariants(self):
        """The identity boundary. A file that looks like a doctrine by its
        own declared fields must carry `invariants:`, or it is malformed
        and must be fixed or moved — never silently ignored."""
        malformed = []
        for path in sorted(self.DOCTRINE_DIR.glob("*.yaml")):
            doc = self._load(path)
            if doc is None:
                malformed.append((path.name, "unparseable"))
                continue
            claims_identity = self._claims_doctrine_identity(doc)
            if claims_identity and "invariants" not in doc:
                malformed.append((path.name, "doctrine identity, no invariants"))
        self.assertEqual(malformed, [], f"malformed doctrines in "
                         f"{self.DOCTRINE_DIR.name}/: {malformed}")

    def test_threshold_flags_a_two_marker_fixture_without_invariants(self):
        """THE ACTUAL REGRESSION GUARANTEE for the threshold itself.

        REPRODUCED 2026-08-28 (cycle regression_probe_001): mutating
        `_claims_doctrine_identity` from `present >= 2` back to
        `all(m in doc for m in DOCTRINE_MARKERS)` left the ENTIRE compiler
        suite green, including the test directly above -- because every
        real file currently in doctrine/ carries all 3 markers, `all()`
        and `>=2` are behaviorally identical against the real directory.
        This test uses a synthetic fixture with exactly 2 markers, which
        is the only committed assertion that actually discriminates the
        two implementations. It fails before the >=2 fix and passes
        after it."""
        self.assertTrue(self._claims_doctrine_identity(
            {"id": "X", "status": "ACTIVE"}))
        self.assertTrue(self._claims_doctrine_identity(
            {"status": "ACTIVE", "effective_from": "2026-01-01"}))
        self.assertFalse(self._claims_doctrine_identity({"id": "X"}))
        self.assertFalse(self._claims_doctrine_identity({}))

    def test_all_three_known_doctrines_carry_full_identity(self):
        """Control for the marker set: if this fails, DOCTRINE_MARKERS was
        chosen wrongly and the boundary above is measuring the wrong
        thing."""
        for name in ("doctrine-001.yaml", "doctrine-002.yaml",
                     "POLE_REVERSAL_DOCTRINE.yaml"):
            doc = self._load(self.DOCTRINE_DIR / name)
            for marker in self.DOCTRINE_MARKERS:
                self.assertIn(marker, doc, f"{name} lacks marker {marker!r}")
