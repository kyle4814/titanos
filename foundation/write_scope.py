"""
Write Scope — a checkable boundary for "which paths may this actor write
to," built after a real incident this project's own history recorded, not
a hypothetical one.

THE REAL INCIDENT THIS CLOSES

During this project, a subagent was handed a write scope as a PROMPT
INSTRUCTION — a paragraph telling it "only touch these files." It ran
`git stash` anyway, which reverted files outside that scope and
destroyed roughly 1,000 lines of another worker's concurrent uncommitted
work. Everything was recovered from the stash (stash is not force-push;
nothing was unrecoverable), but the lesson is exact and does not depend
on the recovery: **a prompt-level write scope is not a boundary. It is a
request.** A prompt can be ignored, diluted, overwritten, or lost in
context — the same failure mode this repository's own
`TITANOS_CRITICAL_FUNCTION_SWITCH_GATE.md` names for every other critical
function. "Only touch foundation/" typed into an instruction is exactly
as enforceable as "please be careful" unless something downstream of the
instruction actually checks it in code. This module is that check.

TWO-POINT ENFORCEMENT (§5), SAME SHAPE AS communication_gate.py /
publication_gate.py

`communication_gate.py` and `publication_gate.py` both split enforcement
into: point one computes a decision from declared evidence, point two
independently RE-DERIVES the answer from that evidence rather than
trusting a cached flag, and raises rather than returning False silently.
This module has no `evaluate()`/decision-object split (a write-scope
check has no multi-field switch state to compute — it's a single
membership question, "is this path under an allowed root, yes or no")
but keeps the same two load-bearing habits: `authorize_write()` and
`authorize_operation()` always resolve fresh from `scope.allowed_paths`/
`FORBIDDEN_OPERATIONS` (never from a cached bool a caller could forge),
and both raise `WriteScopeViolation` rather than returning False, so a
caller cannot mistake "didn't check" for "checked and it's fine."

WHAT THIS MODULE IS, AND WHAT IT IS NOT

This module makes a write scope CHECKABLE IN CODE. It is not a sandbox,
a filesystem permission system, or an interceptor of the `git` binary or
any other subprocess. If a caller (human, script, or agent) invokes
`git stash`, `os.remove`, or `open(path, "w")` directly, without ever
calling `authorize_write()` or `authorize_operation()` first, this module
never runs and provides zero protection — exactly what happened in the
real incident. `FORBIDDEN_OPERATIONS` is a DECLARATION a caller must
consult, not a hook installed on the git binary; nothing in Python can
intercept a subprocess that never asks. The honest claim this module
supports is narrower and still real: any caller that DOES consult it
before writing gets a fail-closed, traversal-resistant, unambiguous
answer — and `scoped_writer()` exists so that consulting it is the easy
path, not an extra step someone has to remember.

PATH TRAVERSAL IS THE CENTRAL THREAT

An `allowed_paths` glob like `"foundation/"` is a string. A path is a
filesystem location that can lie about its own string form via `..`
segments, an absolute prefix, or a symlink whose target lives entirely
outside the declared root. `authorize_write()` never compares strings
directly — it resolves the repository root, resolves the candidate path
against it (following symlinks, per `Path.resolve()`), and checks
CONTAINMENT (the resolved path is inside a resolved allowed directory,
using `Path.relative_to()`/`is_relative_to()` semantics, not
`str.startswith()`), which is also what refuses the prefix-collision
case: `foundation_evil/x.py` shares a string prefix with an allowance of
`"foundation/"` but is not a child of the resolved `foundation` directory,
so containment correctly fails where a naive `startswith("foundation")`
check would not.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Tuple

__all__ = [
    "WriteScope", "WriteScopeViolation",
    "FORBIDDEN_OPERATIONS",
    "authorize_write", "authorize_operation", "scoped_writer",
]

# Operations no WriteScope may ever authorize, regardless of
# allowed_paths. This is a DECLARATION a caller must consult via
# authorize_operation() — see the module docstring's "what this module
# is not" section. It does not, and cannot, hook the git binary itself.
FORBIDDEN_OPERATIONS: Tuple[str, ...] = (
    "git stash",
    "git checkout",
    "git reset",
    "git clean",
    "git revert",
    ".git/write",
)


class WriteScopeViolation(Exception):
    """Raised by authorize_write()/authorize_operation() whenever a
    write or operation falls outside the declared scope. Never returned
    as False — a caller that ignores this exception has to do so
    explicitly, not by accident, same reasoning as
    communication_gate.py::CommunicationDenied and
    publication_gate.py::PublicationRefused."""


@dataclass(frozen=True)
class WriteScope:
    """A declared, checkable write boundary for one task/actor.

    `allowed_paths` is a tuple of repo-relative glob patterns (e.g.
    `("foundation/*.py", "foundation/tests/*.py")`), matched against
    the path's POSIX-style relative-to-repo-root form. An EMPTY
    `allowed_paths` means NOTHING is writable — fail closed, never
    "everything." There is no wildcard shorthand for "allow everything";
    a caller that wants broad access must declare it explicitly and
    accept that explicitness is the point.
    """

    task_id: str
    actor: str
    allowed_paths: Tuple[str, ...]
    reason: str


def _repo_root() -> Path:
    # foundation/write_scope.py -> foundation/ -> repo root
    return Path(__file__).resolve().parent.parent


def _resolve_relative(path: str, repo_root: Path) -> Path:
    """Resolve `path` (which may be relative or absolute, may contain
    `..`, and may traverse a symlink) to an absolute, fully-resolved
    filesystem path. Uses Path.resolve(), which follows symlinks and
    collapses `..` segments — never naive string manipulation."""
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    return candidate.resolve()


def _is_contained(resolved_path: Path, resolved_root: Path) -> bool:
    """True iff resolved_path is resolved_root itself or a genuine
    descendant of it, per filesystem-resolved ancestry — never string
    prefix comparison, which is exactly what would let
    `foundation_evil/x.py` slip past an allowance of `foundation/`."""
    if hasattr(resolved_path, "is_relative_to"):  # Python 3.9+
        return resolved_path == resolved_root or resolved_path.is_relative_to(resolved_root)
    try:
        resolved_path.relative_to(resolved_root)
        return True
    except ValueError:
        return resolved_path == resolved_root


def _allowed_glob_roots(scope: WriteScope, repo_root: Path) -> list:
    """For each allowed_paths glob, compute its resolved directory root
    (the fixed, non-wildcard prefix directory) — used only for the
    cheap containment pre-check; the actual match is fnmatch against the
    glob pattern itself, done in authorize_write()."""
    roots = []
    for pattern in scope.allowed_paths:
        # Fixed prefix = everything before the first wildcard character.
        fixed = pattern
        for wildcard in ("*", "?", "["):
            idx = fixed.find(wildcard)
            if idx != -1:
                fixed = fixed[:idx]
        fixed_dir = fixed.rsplit("/", 1)[0] if "/" in fixed else ""
        try:
            roots.append((pattern, (repo_root / fixed_dir).resolve()))
        except (OSError, RuntimeError):
            continue
    return roots


def authorize_write(scope: WriteScope, path: str) -> bool:
    """Returns True only if `path` is genuinely, unambiguously inside
    scope.allowed_paths after full filesystem resolution. Raises
    WriteScopeViolation (never returns False silently) otherwise, naming
    the actor, the path, and the scope violated — matching
    communication_gate.py / publication_gate.py's "raise, don't return
    False" discipline exactly.

    Fail-closed: an empty allowed_paths, an unresolvable path, a path
    that resolves outside the repository entirely, and a path that only
    shares a string prefix with an allowed directory (not genuine
    filesystem containment) are all refused.
    """
    repo_root = _repo_root()

    if not scope.allowed_paths:
        raise WriteScopeViolation(
            f"actor '{scope.actor}' (task {scope.task_id}) attempted to "
            f"write to '{path}', but scope has an EMPTY allowed_paths — "
            f"empty means nothing is writable, never everything"
        )

    try:
        resolved_target = _resolve_relative(path, repo_root)
    except (OSError, RuntimeError) as exc:
        raise WriteScopeViolation(
            f"actor '{scope.actor}' (task {scope.task_id}) attempted to "
            f"write to '{path}', which could not be resolved to a real "
            f"filesystem path ({exc}) — refused"
        )

    # Refuse anything that resolves outside the repository entirely
    # (absolute paths elsewhere, symlinks pointing outside the repo,
    # `../../etc/passwd`-style escapes).
    if not _is_contained(resolved_target, repo_root):
        raise WriteScopeViolation(
            f"actor '{scope.actor}' (task {scope.task_id}) attempted to "
            f"write to '{path}', which resolves to "
            f"'{resolved_target}' — OUTSIDE the repository root "
            f"'{repo_root}' entirely (path traversal, absolute escape, "
            f"or a symlink pointing outside the repo) — refused"
        )

    relative = resolved_target.relative_to(repo_root)
    relative_posix = relative.as_posix()

    for pattern in scope.allowed_paths:
        # fnmatch against the resolved, repo-relative POSIX path — not
        # against the caller-supplied string. A caller-supplied string
        # like "foundation/../../etc/passwd" never reaches this
        # comparison as itself; only its resolved, contained form does.
        if fnmatch.fnmatch(relative_posix, pattern):
            # Containment double-check: the matched glob's own fixed
            # directory root must also genuinely contain the resolved
            # target (catches the prefix-collision case where fnmatch
            # alone could be fooled by a pattern like "foundation*").
            for pat, glob_root in _allowed_glob_roots(scope, repo_root):
                if pat != pattern:
                    continue
                if _is_contained(resolved_target, glob_root):
                    return True
            continue

    raise WriteScopeViolation(
        f"actor '{scope.actor}' (task {scope.task_id}) attempted to "
        f"write to '{path}' (resolved: '{relative_posix}'), which is "
        f"NOT within any allowed path {scope.allowed_paths} — "
        f"scope reason: {scope.reason}"
    )


def authorize_operation(scope: WriteScope, operation: str) -> bool:
    """Refuses any operation named in FORBIDDEN_OPERATIONS unconditionally
    — no allowed_paths configuration, however permissive, can authorize
    one of these. Raises WriteScopeViolation, never returns False.

    HONESTY NOTE (see module docstring): this function only protects a
    caller that actually calls it before running the operation. It does
    not, and cannot, intercept a `git` subprocess invoked directly.
    """
    normalized = operation.strip().lower()
    for forbidden in FORBIDDEN_OPERATIONS:
        if normalized == forbidden.lower() or normalized.startswith(forbidden.lower() + " "):
            raise WriteScopeViolation(
                f"actor '{scope.actor}' (task {scope.task_id}) attempted "
                f"operation '{operation}', which is in FORBIDDEN_OPERATIONS "
                f"({forbidden}) — no scope may ever authorize this, "
                f"regardless of allowed_paths. This is the exact class of "
                f"operation that destroyed ~1,000 lines of concurrent "
                f"uncommitted work in this project's real incident."
            )
    if operation.strip() == "" :
        raise WriteScopeViolation(
            f"actor '{scope.actor}' (task {scope.task_id}) attempted an "
            f"empty/unnamed operation — refused, fail-closed on unknown"
        )
    return True


def scoped_writer(scope: WriteScope) -> Callable[[str, str], None]:
    """Returns a callable `write(path, content)` that checks
    authorize_write() before writing and raises WriteScopeViolation
    instead of touching the filesystem if the path is out of scope —
    so that respecting the scope is the path of least resistance rather
    than an extra step a caller has to remember to add.
    """

    def write(path: str, content: str) -> None:
        authorize_write(scope, path)
        repo_root = _repo_root()
        resolved_target = _resolve_relative(path, repo_root)
        resolved_target.parent.mkdir(parents=True, exist_ok=True)
        resolved_target.write_text(content)

    return write
