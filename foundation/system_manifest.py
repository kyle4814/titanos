"""One computed answer to "what state is this system in right now?"

WHY THIS IS COMPUTED AND NEVER HAND-MAINTAINED

Every hand-maintained snapshot in this repository has gone stale and
then actively misled somebody:

- `README.md`'s test count sat at 915 while reality passed 2,400, and
  broke the build three times in two work cells.
- `CLAUDE.md` asserted "this repository still makes zero network
  connections" for several cycles after the mouths were built -- and
  that sentence is the reason an unwired network gate went unnoticed,
  because the document guarding the door insisted there was no door.
- `SIGIL.md` and `CLAUDE.md` both recorded `LATTICE:6` against a real
  value of 7, and AGREED with each other, so the check that compares
  snapshots stayed silent.
- `CAPABILITY_MANIFEST.json` carried `as_of: 2026-08-27` and omitted two
  whole subsystems.

The pattern is not carelessness. A snapshot is a copy of a fact, and a
copy drifts. So this module writes nothing by default and holds no
`as_of` field it could lie with: it recomputes from disk every call.

WHAT IT DELIBERATELY DOES NOT DO

It does not run the test suites. `sigil.py::compute_sigil()` genuinely
does (~18s of subprocess time), and that cost is why it cannot be in a
frequently-called path. This module reports the test INVENTORY -- how
many test functions exist and where -- which is a different and cheaper
fact, and it says so rather than implying the suite is green.

It also does not decide what to do next. It reports where the answer is
recorded (`NEXT_MOVE.md`), because a manifest that invented a priority
would be competing with the Pareto frontier rather than describing it.

THE POINT

A fresh worker with no conversation history should be able to run this
and learn what is true. That is the whole test.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

__all__ = ["SystemManifest", "compute_manifest", "format_manifest"]

REPO_ROOT = Path(__file__).resolve().parent.parent

# Files whose content defines the active configuration. A change to any
# of them changes what an agent is told to do at boot, so they are what
# `config_digest` commits to.
_CONFIG_FILES = ("CLAUDE.md",)
_DOCTRINE_GLOB = "TITANOS_*.md"

_DURABLE_LEDGERS = (
    "foundation/outcome_ledger.jsonl",
    "foundation/autonomy_loop_log.jsonl",
    "foundation/pulse_log.jsonl",
    "foundation/authority_ledger.jsonl",
    "kpm/source-vault/registry.jsonl",
)


def _git(root: Path, *args: str) -> str:
    try:
        r = subprocess.run(["git", *args], cwd=root, capture_output=True,
                           text=True, timeout=15)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def _digest(parts) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p if isinstance(p, bytes) else str(p).encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()[:16]


@dataclass(frozen=True)
class SystemManifest:
    """A computed snapshot. Every field is derived, none is declared."""

    computed_at: str
    repo_revision: str
    worktree_clean: bool
    config_digest: str
    doctrine_files: int
    tracked_files: int
    python_modules: int
    test_modules: int
    test_functions: int
    durable_ledgers: dict = field(default_factory=dict)
    receipt_head: Optional[str] = None
    pulse_findings: int = -1
    pulse_detail: tuple = ()
    next_move_recorded_in: str = ""
    next_move_stale: Optional[bool] = None
    open_human_decisions: int = -1
    resolved_human_decisions: int = 0
    notes: tuple = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def digest(self) -> str:
        """Identity of this system state. Excludes `computed_at` so two
        runs against an unchanged repository agree -- a digest that
        changed every second would be useless for detecting drift."""
        d = self.to_dict()
        d.pop("computed_at", None)
        return _digest([json.dumps(d, sort_keys=True, default=str)])


def compute_manifest(repo_root: Path = REPO_ROOT) -> SystemManifest:
    """Recompute from disk. Reads only; writes nothing, anywhere."""
    repo_root = Path(repo_root)
    notes: list[str] = []

    revision = _git(repo_root, "rev-parse", "--short", "HEAD") or "UNKNOWN"
    status = _git(repo_root, "status", "--porcelain")
    clean = status == ""

    config_parts = []
    for name in _CONFIG_FILES:
        p = repo_root / name
        if p.is_file():
            config_parts.append(p.read_bytes())
    doctrine = sorted(repo_root.glob(_DOCTRINE_GLOB))
    for p in doctrine:
        config_parts.append(p.read_bytes())

    tracked = _git(repo_root, "ls-files")
    tracked_count = len(tracked.splitlines()) if tracked else -1

    # The test count is DELEGATED, never recounted here. An earlier draft
    # of this module counted `def test_` itself and was immediately
    # convicted by `foundation/tests/test_single_readme_fixer.py`, which
    # exists to forbid exactly that -- a second counter that disagrees
    # with the sensor leaves a drift finding permanently open, and this
    # repository has already lived through that once. The sensor defines
    # the quantity; this module only reports it.
    from foundation.sentinel import count_real_tests
    py, test_mods = 0, 0
    for p in repo_root.rglob("*.py"):
        rel = p.relative_to(repo_root).as_posix()
        if rel.startswith(".git/"):
            continue
        py += 1
        if "/tests/" in f"/{rel}":
            test_mods += 1
    try:
        test_fns = count_real_tests(repo_root)
    except Exception:                                         # noqa: BLE001
        test_fns = -1
        notes.append("test inventory unavailable: sentinel.count_real_tests failed")

    ledgers: dict[str, Any] = {}
    receipt_head = None
    for rel in _DURABLE_LEDGERS:
        p = repo_root / rel
        if not p.is_file():
            ledgers[rel] = {"present": False}
            continue
        try:
            lines = [x for x in p.read_text(errors="ignore").splitlines() if x.strip()]
        except OSError:
            ledgers[rel] = {"present": True, "readable": False}
            continue
        ledgers[rel] = {"present": True, "records": len(lines),
                        "bytes": p.stat().st_size}
        if rel.endswith("outcome_ledger.jsonl") and lines:
            try:
                last = json.loads(lines[-1])
                receipt_head = last.get("record_hash") or last.get(
                    "outcome_id") or last.get("context_id")
                if not last.get("record_hash"):
                    notes.append(
                        "outcome ledger head predates hash chaining; it is "
                        "CHAIN_UNVERIFIED_LEGACY, not verified")
            except ValueError:
                notes.append("outcome ledger tail is unparseable "
                             "(consistent with an interrupted append)")

    pulse_n, pulse_detail = -1, ()
    try:
        from foundation.sentinel import pulse_sweep
        findings = pulse_sweep(repo_root).findings
        pulse_n = len(findings)
        pulse_detail = tuple(f.observation for f in findings)
    except Exception as exc:                                  # noqa: BLE001
        notes.append(f"pulse_sweep unavailable: {type(exc).__name__}")

    # HUMAN_DECISIONS.md numbers its items `N. **Title**` under prose
    # section headings; an earlier version of this counted `###` headings
    # and reported 1 against a real 13. A manifest that miscounts is the
    # exact failure this module exists to prevent, so the pattern matches
    # the file's real shape and RESOLVED items (struck through) are
    # excluded -- "open decisions" must mean open.
    decisions, resolved = -1, 0
    hd = repo_root / "HUMAN_DECISIONS.md"
    if hd.is_file():
        try:
            text = hd.read_text(errors="ignore")
            items = re.findall(r"^(\d+)\. (.*)$", text, re.M)
            resolved = sum(1 for _, body in items if body.lstrip().startswith("~~"))
            decisions = len(items) - resolved
        except OSError:
            pass

    # NEXT_MOVE.md is hand-written prose that documents its own repeated
    # staleness at length. A cleanroom test found its asserted git state
    # ("0 ahead, 0 behind") contradicting reality (37 ahead) -- exactly
    # the drift the file warns about, unnoticed because nothing checked.
    # Any short commit hash it cites is compared against real history:
    # a hash git does not know, or one that is no longer HEAD, means the
    # prose was written against a different repository than this one.
    next_move = "NEXT_MOVE.md" if (repo_root / "NEXT_MOVE.md").is_file() else ""
    next_move_stale = None
    if next_move:
        try:
            nm = (repo_root / "NEXT_MOVE.md").read_text(errors="ignore")
            cited = set(re.findall(r"\b([0-9a-f]{7,40})\b", nm))
            head = _git(repo_root, "rev-parse", "HEAD")
            known = {c for c in cited
                     if _git(repo_root, "cat-file", "-t", c) == "commit"}
            if known:
                next_move_stale = not any(head.startswith(c) for c in known)
                if next_move_stale:
                    notes.append(
                        f"NEXT_MOVE.md cites commit(s) "
                        f"{sorted(known)} but HEAD is {head[:8]}; its prose "
                        f"describes an earlier repository state")
        except OSError:
            pass

    return SystemManifest(
        computed_at=datetime.now(timezone.utc).isoformat(),
        repo_revision=revision,
        worktree_clean=clean,
        config_digest=_digest(config_parts),
        doctrine_files=len(doctrine),
        tracked_files=tracked_count,
        python_modules=py,
        test_modules=test_mods,
        test_functions=test_fns,
        durable_ledgers=ledgers,
        receipt_head=receipt_head,
        pulse_findings=pulse_n,
        pulse_detail=pulse_detail,
        next_move_recorded_in=next_move,
        next_move_stale=next_move_stale,
        open_human_decisions=decisions,
        resolved_human_decisions=resolved,
        notes=tuple(notes),
    )


def format_manifest(m: SystemManifest) -> str:
    """Human-readable. Every line traceable to a computed field."""
    lines = [
        "TITANOS SYSTEM MANIFEST (computed, not stored)",
        f"  computed_at      {m.computed_at}",
        f"  repo_revision    {m.repo_revision}"
        f"{'' if m.worktree_clean else '  (WORKTREE DIRTY)'}",
        f"  config_digest    {m.config_digest}  "
        f"({m.doctrine_files} doctrine files + CLAUDE.md)",
        f"  state_digest     {m.digest()}",
        f"  tracked_files    {m.tracked_files}",
        f"  python_modules   {m.python_modules}  "
        f"({m.test_modules} test modules, {m.test_functions} test functions)",
        "  NOTE: test_functions is an INVENTORY, not a pass count. This "
        "module never runs the suites.",
        "  durable ledgers:",
    ]
    for rel, info in m.durable_ledgers.items():
        if not info.get("present"):
            lines.append(f"    {rel:<44} ABSENT")
        else:
            lines.append(f"    {rel:<44} {info.get('records','?')} records")
    lines += [
        f"  receipt_head     {m.receipt_head or 'NONE'}",
        f"  pulse_findings   {m.pulse_findings}",
    ]
    for d in m.pulse_detail:
        lines.append(f"    - {d}")
    lines += [
        f"  human_decisions  {m.open_human_decisions} OPEN "
        f"({m.resolved_human_decisions} resolved) in HUMAN_DECISIONS.md",
        f"  next_move        see {m.next_move_recorded_in or 'NOWHERE'}"
        f"  (reports where it is recorded; does not decide)"
        + ("  [STALE: cites an older commit]" if m.next_move_stale else ""),
    ]
    for n in m.notes:
        lines.append(f"  NOTE: {n}")
    return "\n".join(lines)


if __name__ == "__main__":                                  # pragma: no cover
    import sys
    sys.path.insert(0, str(REPO_ROOT))
    print(format_manifest(compute_manifest()))
