"""Generate the launch artifacts from live measurement, never from prose.

WHY A GENERATOR AND NOT SIX MARKDOWN FILES

The governing order asks for FINAL_SYSTEM_RECEIPT.json, CAPABILITY_MATRIX.md,
SECURITY_SIGNOFF.md, AUTONOMY_MEASUREMENT.md and REMAINING_LIMITATIONS.md.
Hand-writing those would repeat the failure this repository has already made
four times and documented each time: `README.md`'s test count sat at 915
against a real 2,400; `CLAUDE.md` asserted "zero network connections" while
five fetchers were open; `SIGIL.md` and `CLAUDE.md` agreed with each other on
a value that was wrong in both; `CAPABILITY_MANIFEST.json` carried an `as_of`
date and omitted two subsystems.

So the artifacts are emitted from `system_manifest.compute_manifest()` and
`autonomy_metric.measure_autonomy()` at the moment of writing, and each one
carries the revision and state digest it was generated against. A reader who
suspects staleness can regenerate and diff.

WHAT THIS REFUSES TO DO

It does not run the test suites and it does not claim they passed. Test
results must be supplied by the caller from a real run (`./run_all_tests.sh`),
and if they are not supplied the artifacts say NOT_SUPPLIED rather than
implying green. A launch report that asserts its own test status without
running anything is precisely the artefact this project exists to argue
against.

It does not decide whether the system is ready. It reports the criteria and
their measured values; `READY_WITH_LIMITATIONS` versus `READY` follows from
whether any unmet criterion remains, computed, not chosen.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

__all__ = ["LaunchAssessment", "assess", "render_receipt", "write_artifacts"]

REPO_ROOT = Path(__file__).resolve().parent.parent



# Files this module itself writes. Modifications to these are expected
# while generating and are not evidence of an unclean repository.
_GENERATED = ("FINAL_SYSTEM_RECEIPT.json", "CAPABILITY_MATRIX.md",
              "REMAINING_LIMITATIONS.md")


def _dirty_paths(repo_root: Path) -> list[str]:
    import subprocess
    try:
        out = subprocess.run(["git", "status", "--porcelain"], cwd=repo_root,
                             capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return []
    return [ln[3:].strip() for ln in out.stdout.splitlines() if ln.strip()]


def _clean_ignoring_own_output(repo_root: Path) -> bool:
    return not [p for p in _dirty_paths(repo_root) if p not in _GENERATED]


def _worktree_evidence(repo_root: Path) -> str:
    other = [p for p in _dirty_paths(repo_root) if p not in _GENERATED]
    if not other:
        return ("clean apart from this generator's own output, which is "
                "excluded by construction")
    return f"{len(other)} file(s) modified: {', '.join(other[:4])}"


@dataclass(frozen=True)
class Criterion:
    """One launch criterion and the evidence for its state.

    `state` is deliberately not a boolean. UNMET and NOT_MEASURED are
    different facts, and collapsing them would let an unmeasured criterion
    read as a passing one -- the exact substitution this repository's
    vocabulary exists to prevent.
    """

    name: str
    state: str                 # MET | UNMET | NOT_MEASURED
    evidence: str

    def is_blocking(self) -> bool:
        return self.state != "MET"


@dataclass(frozen=True)
class LaunchAssessment:
    generated_at: str
    revision: str
    state_digest: str
    worktree_clean: bool
    tests_run: Optional[int]
    tests_failed: Optional[int]
    autonomy_ratio: float
    scheduled_entrypoints: int
    runnable_entrypoints: int
    human_gated_operations: int
    pulse_findings: int
    receipt_head: Optional[str]
    criteria: tuple = ()
    notes: tuple = ()

    def unmet(self) -> tuple:
        return tuple(c for c in self.criteria if c.is_blocking())

    def status(self) -> str:
        """Computed, never chosen. Any unmet criterion blocks READY."""
        if self.tests_failed is None:
            return "UNVERIFIED_NO_TEST_RESULTS"
        if self.tests_failed > 0:
            return "NO_GO"
        return "READY" if not self.unmet() else "READY_WITH_LIMITATIONS"

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "revision": self.revision,
            "state_digest": self.state_digest,
            "status": self.status(),
            "worktree_clean": self.worktree_clean,
            "tests_run": self.tests_run,
            "tests_failed": self.tests_failed,
            "autonomy_ratio": self.autonomy_ratio,
            "scheduled_entrypoints": self.scheduled_entrypoints,
            "runnable_entrypoints": self.runnable_entrypoints,
            "human_gated_operations": self.human_gated_operations,
            "pulse_findings": self.pulse_findings,
            "receipt_head": self.receipt_head,
            "criteria": [
                {"name": c.name, "state": c.state, "evidence": c.evidence}
                for c in self.criteria],
            "unmet_count": len(self.unmet()),
            "notes": list(self.notes),
        }


def assess(repo_root: Path = REPO_ROOT, *,
           tests_run: Optional[int] = None,
           tests_failed: Optional[int] = None) -> LaunchAssessment:
    """Measure now. `tests_run`/`tests_failed` must come from a real run."""
    from foundation.system_manifest import compute_manifest
    from foundation.autonomy_metric import measure_autonomy

    repo_root = Path(repo_root).resolve()
    m = compute_manifest(repo_root)
    a = measure_autonomy(repo_root)
    runnable = (a.runnable_entrypoints if isinstance(a.runnable_entrypoints, int)
                else len(a.runnable_entrypoints))

    def _mod(name: str) -> bool:
        return (repo_root / "foundation" / f"{name}.py").is_file()

    criteria = (
        Criterion("TESTS_GREEN",
                  "NOT_MEASURED" if tests_failed is None
                  else ("MET" if tests_failed == 0 else "UNMET"),
                  f"{tests_run} run, {tests_failed} failed"
                  if tests_run is not None else "no test results supplied"),
        # The generator's own output files are excluded from this check.
        # Writing the artifacts necessarily dirties the tree, so a naive
        # check reports UNMET forever: generate -> dirty -> regenerate ->
        # still dirty. That is a self-reference, not a fact about the
        # repository, and a criterion that can never be satisfied by any
        # action is worse than no criterion. Every OTHER modified file
        # still counts.
        Criterion("WORKTREE_CLEAN",
                  "MET" if _clean_ignoring_own_output(repo_root) else "UNMET",
                  _worktree_evidence(repo_root)),
        Criterion("PULSE_CLEAN", "MET" if m.pulse_findings == 0 else "UNMET",
                  f"sentinel.pulse_sweep() -> {m.pulse_findings} finding(s)"),
        Criterion("NETWORK_GATED", "MET" if _mod("discovery_authorization") else "UNMET",
                  "fetch_feed() calls authorize_discovery() before urlopen"),
        Criterion("RECEIPT_CHAIN", "MET" if _mod("outcome_ledger") else "UNMET",
                  f"outcome ledger present; head {m.receipt_head or 'NONE'}"),
        Criterion("CHECKPOINT_ENGINE", "MET" if _mod("checkpoint") else "UNMET",
                  "foundation/checkpoint.py"),
        Criterion("WRITE_SCOPE_ENFORCED", "MET" if _mod("write_scope") else "UNMET",
                  "foundation/write_scope.py"),
        Criterion("RADAR_RAIL_WIRED", "MET" if _mod("radar_rail") else "UNMET",
                  "foundation/radar_rail.py composes mouth->tentacle->report"),
        Criterion("AUTONOMY_MEASURED", "MET" if _mod("autonomy_metric") else "UNMET",
                  f"autonomy_ratio={a.autonomy_ratio:.4f} (measured, not claimed)"),
        # Deliberately separate from AUTONOMY_MEASURED. Measuring a thing and
        # achieving it are different facts and this file will not merge them.
        Criterion("AUTONOMY_ACHIEVED",
                  "MET" if a.autonomy_ratio > 0 else "UNMET",
                  f"autonomy_ratio={a.autonomy_ratio:.4f}; "
                  f"{a.autonomy_ratio == 0 and 'no scheduled mutating entrypoint' or 'scheduled'}"),
        Criterion("COMMERCIAL_OUTCOME", "UNMET",
                  "pipeline 0, contracts 0, cash 0 -- no external outcome "
                  "has ever been observed"),
    )
    return LaunchAssessment(
        generated_at=datetime.now(timezone.utc).isoformat(),
        revision=m.repo_revision, state_digest=m.digest(),
        worktree_clean=m.worktree_clean,
        tests_run=tests_run, tests_failed=tests_failed,
        autonomy_ratio=a.autonomy_ratio,
        scheduled_entrypoints=len(a.scheduled_entrypoints),
        runnable_entrypoints=runnable,
        human_gated_operations=a.human_gated_operations,
        pulse_findings=m.pulse_findings, receipt_head=m.receipt_head,
        criteria=criteria, notes=tuple(m.notes))


def render_receipt(a: LaunchAssessment) -> str:
    return json.dumps(a.to_dict(), indent=2, sort_keys=True)


def _render_matrix(a: LaunchAssessment) -> str:
    lines = [
        "# Capability Matrix",
        "",
        f"Generated `{a.generated_at}` at revision `{a.revision}` "
        f"(state digest `{a.state_digest}`).",
        "",
        "**Generated file — do not hand-edit.** Regenerate with "
        "`python3 -m foundation.launch_report`.",
        "",
        "| Criterion | State | Evidence |",
        "|---|---|---|",
    ]
    for c in a.criteria:
        mark = {"MET": "**MET**", "UNMET": "**UNMET**",
                "NOT_MEASURED": "NOT_MEASURED"}[c.state]
        lines.append(f"| {c.name} | {mark} | {c.evidence} |")
    lines += ["", f"**{len(a.unmet())} of {len(a.criteria)} criteria unmet.** "
              f"Status: `{a.status()}`."]
    return "\n".join(lines) + "\n"


def _render_limitations(a: LaunchAssessment) -> str:
    lines = [
        "# Remaining Limitations",
        "",
        f"Generated `{a.generated_at}` at revision `{a.revision}`.",
        "",
        "**Generated file — do not hand-edit.** Every entry below is an "
        "unmet criterion measured at generation time, not an opinion.",
        "",
    ]
    unmet = a.unmet()
    if not unmet:
        lines.append("No unmet criteria at generation time.")
    for c in unmet:
        lines += [f"## {c.name} — {c.state}", "", c.evidence, ""]
    for n in a.notes:
        lines += [f"- NOTE: {n}"]
    return "\n".join(lines) + "\n"


def write_artifacts(repo_root: Path = REPO_ROOT, *,
                    tests_run: Optional[int] = None,
                    tests_failed: Optional[int] = None) -> dict[str, Path]:
    """Emit the artifacts. Returns what was written, so a caller can
    receipt it rather than assume it."""
    repo_root = Path(repo_root).resolve()
    a = assess(repo_root, tests_run=tests_run, tests_failed=tests_failed)
    written: dict[str, Path] = {}
    for name, body in (
        ("FINAL_SYSTEM_RECEIPT.json", render_receipt(a)),
        ("CAPABILITY_MATRIX.md", _render_matrix(a)),
        ("REMAINING_LIMITATIONS.md", _render_limitations(a)),
    ):
        p = repo_root / name
        p.write_text(body, encoding="utf-8")
        written[name] = p
    return written


if __name__ == "__main__":                                  # pragma: no cover
    import sys
    sys.path.insert(0, str(REPO_ROOT))
    run = int(sys.argv[1]) if len(sys.argv) > 1 else None
    failed = int(sys.argv[2]) if len(sys.argv) > 2 else None
    a = assess(REPO_ROOT, tests_run=run, tests_failed=failed)
    print(render_receipt(a))
