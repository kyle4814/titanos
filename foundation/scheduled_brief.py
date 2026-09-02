"""foundation/scheduled_brief.py -- the thing that makes the hunt run
on a schedule with nobody typing anything, and puts the result where
the operator will actually see it.

WHY THIS EXISTS

`foundation/hunt_loop.py` already runs the hunt, computes the diff
against the durable log, and writes a receipt for every cycle -- but it
is a Python function. Making it run "on a schedule" means cron, and cron
needs a script it can invoke unattended: one that cannot double-write if
two invocations overlap, that never crashes silently, that leaves a
readable result at a fixed path, and that does not grow `briefs/`
without bound over a year of daily runs. This module is that script's
logic (`foundation/tests/test_scheduled_brief.py` exercises it directly;
a thin `if __name__ == "__main__":` block below is the actual cron
entry point).

WHAT THIS REUSES RATHER THAN DUPLICATES

- `foundation.hunt_loop.run_one_hunt_cycle()` runs the actual hunt and
  computes the diff against the durable `hunt_loop_log.jsonl` -- this
  module never re-implements fetch, assessment, or diffing. It only
  decides WHERE the resulting text lands and HOW OFTEN the whole thing
  may run.
- `foundation.hunt_loop.render_hunt_cycle()` is the diff-led renderer
  ("what's NEW", not a full re-dump) -- reused verbatim as the body of
  every dated brief file, which is exactly requirement 2 (diffed
  output) for free.
- `foundation.hunt_loop.HUNT_STOP_FILENAME` (`.hunt_stop`) is the same
  kill switch `hunt_loop.py` already checks -- this module does not
  invent a second one. Dropping `.hunt_stop` in the repo root silences
  both `operator_cli.py loop` and this scheduled runner.
- `foundation.operator_cli.load_operator_profile()` -- the real operator
  profile, same fallback-to-example-with-loud-notice behaviour as every
  other entry point. Not re-read or re-parsed here.
- `foundation.discovery_authorization.DiscoveryPolicy` -- the same
  budget/objective object every other network-touching entry point in
  this repository must build before a socket opens.

WHAT THIS DOES NOT DO

No email, no webhook, no application, no account creation, no outward
contact of any kind, ever. This module's entire public surface is: take
a lock, run one hunt cycle, write a file, copy it to a stable path,
delete old files it itself created, append one receipt line. See
`TestNoOutwardAction` in the test file, which enumerates every public
callable here and fails on an outbound-action verb -- the same
structural check `hunt_loop.py` already applies to itself.

CRON SAFETY, NAMED EXPLICITLY

- SINGLE-INSTANCE: `acquire_lock()` uses `os.O_CREAT | os.O_EXCL`, which
  is atomic at the OS level -- two processes racing to create the same
  lock file cannot both succeed. A second overlapping run sees
  `LockHeld`, writes no brief, and exits cleanly (still receipted).
- LOCK RELEASE ON FAILURE: `run_scheduled_brief_cycle()`'s lock-holding
  section is a single `try/finally` -- `release_lock()` runs whether the
  cycle succeeded, returned a stop result, or raised. A crash that did
  not release the lock would make every future scheduled run silently
  do nothing forever, which is worse than the crash itself.
- A RUN THAT FINDS NOTHING STILL WRITES A BRIEF: `render_hunt_cycle()`
  always produces text, even for `RAN_CLEAN`/`RAN_NO_CHANGE` -- this
  module writes that text to disk unconditionally on every completed
  cycle. Silence is indistinguishable from breakage, so this module
  never goes silent.
- A RECEIPT IS WRITTEN EVERY RUN: `_append_receipt()` runs at every
  return point in `run_scheduled_brief_cycle()` -- locked-out, killed,
  profile-load failure, hunt error, clean success. Never fabricated:
  every field traces back to a real `HuntCycleResult` or a real
  exception, never a guess.
- RETENTION IS SELF-SCOPED: `enforce_retention()` only ever deletes
  files in `briefs/` whose name matches `BRIEF_FILENAME_RE`
  (`brief_YYYYMMDDTHHMMSSZ.md`) -- the exact pattern
  `write_brief_file()` itself produces. It never touches `LATEST.md`,
  never touches a file this runner did not create, and is not a general
  cleanup routine.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List, Mapping, Optional, Sequence

from foundation.discovery_authorization import (
    DEFAULT_MAX_QUERIES,
    DEFAULT_MAX_RESULTS,
    DEFAULT_MAX_WALL_CLOCK_SECONDS,
    DiscoveryPolicy,
)
from foundation.hunt_loop import (
    HUNT_STOP_FILENAME,
    HuntCycleResult,
    render_hunt_cycle,
    run_one_hunt_cycle,
)
from foundation.operator_cli import ProfileLoadError, load_operator_profile
from foundation.qualification import OperatorProfile
from foundation.relevance import CapabilityProfile

__all__ = [
    "BRIEFS_DIRNAME",
    "LOCK_FILENAME",
    "RECEIPT_LOG_NAME",
    "LATEST_FILENAME",
    "DEFAULT_RETAIN_COUNT",
    "DEFAULT_KEYWORD",
    "BRIEF_FILENAME_RE",
    "SCHEDULED_ACTIONS",
    "ScheduledBriefIntegrityError",
    "LockHeld",
    "ScheduledBriefResult",
    "acquire_lock",
    "release_lock",
    "default_capability_profile",
    "default_policy",
    "brief_filename",
    "write_brief_file",
    "update_latest",
    "enforce_retention",
    "run_scheduled_brief_cycle",
]

BRIEFS_DIRNAME = "briefs"
LOCK_FILENAME = ".scheduled_brief.lock"
RECEIPT_LOG_NAME = "scheduled_brief_log.jsonl"
LATEST_FILENAME = "LATEST.md"
DEFAULT_RETAIN_COUNT = 30
DEFAULT_KEYWORD = "cyber security"

_DEFAULT_EXCLUSIONS = (
    "construction", "catering", "cleaning", "vehicles", "medical supplies",
)

# The exact filename shape `write_brief_file()` produces. Retention
# deletes ONLY files matching this pattern in this runner's own
# `briefs/` directory -- never a broader glob.
BRIEF_FILENAME_RE = re.compile(r"^brief_(\d{8}T\d{6}Z)\.md$")

SCHEDULED_ACTIONS = frozenset({
    "WROTE_RAN_CLEAN",
    "WROTE_RAN_NO_CHANGE",
    "WROTE_RAN_WITH_CHANGES",
    "STOPPED_KILL_SWITCH",
    "STOPPED_HUNT_ERROR",
    "SKIPPED_LOCKED",
    "FAILED_PROFILE",
    "FAILED_SETUP",
    "FAILED_UNEXPECTED",
})


class ScheduledBriefIntegrityError(ValueError):
    """Raised on a caller error this module refuses to silently paper
    over -- e.g. a `retain_count` low enough to delete the brief this
    very run just wrote."""


class LockHeld(RuntimeError):
    """Raised by `acquire_lock()` when another run currently holds the
    lock. A caller should treat this as a clean, receipted no-op, not a
    crash -- overlap is an expected condition on any real cron
    schedule, not a bug."""


@dataclass(frozen=True)
class ScheduledBriefResult:
    """One scheduled run's outcome -- the receipt shape, written
    verbatim by every return path in `run_scheduled_brief_cycle()`."""

    action: str
    occurred_at: str
    detail: str
    brief_path: Optional[str] = None
    deleted_count: int = 0

    def __post_init__(self) -> None:
        if self.action not in SCHEDULED_ACTIONS:
            raise ScheduledBriefIntegrityError(
                f"unknown ScheduledBriefResult action {self.action!r}")


def acquire_lock(lock_path: Path) -> None:
    """Atomically create `lock_path`. Raises `LockHeld` if it already
    exists -- `O_CREAT | O_EXCL` is the OS-level atomic primitive this
    relies on, so two processes racing to acquire the same lock cannot
    both succeed."""
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise LockHeld(
            f"lock file {lock_path} already exists -- another run is "
            f"in progress or a prior run crashed without releasing it"
        ) from exc
    try:
        payload = f"{os.getpid()} {datetime.now(timezone.utc).isoformat()}\n"
        os.write(fd, payload.encode("utf-8"))
    finally:
        os.close(fd)


def release_lock(lock_path: Path) -> None:
    """Remove `lock_path`. Never raises -- this is always called from a
    `finally` block, and a release failure must not mask or replace
    whatever the cycle itself already decided to report."""
    try:
        lock_path.unlink()
    except OSError:
        pass


def default_capability_profile(keyword: str) -> CapabilityProfile:
    """The same shape `operator_cli.py`'s own default capability profile
    uses (keyword-derived, generic CPV, the standard exclusion list) --
    not imported from there because it is a private helper, but kept
    identical in substance so a scheduled run and a manual `--live` run
    of the same keyword classify notices the same way."""
    return CapabilityProfile(
        name="scheduled-brief-default",
        declared_by="cron",
        keywords=frozenset({keyword.lower()}),
        cpv_codes=frozenset({"72000000"}),
        exclusions=frozenset(_DEFAULT_EXCLUSIONS),
    )


def default_policy(keyword: str, *, objective: Optional[str] = None) -> DiscoveryPolicy:
    """A real, bounded `DiscoveryPolicy` for a live scheduled run.
    Never built when `fetch_notices_fn` is supplied -- see
    `run_scheduled_brief_cycle()` -- because an offline/test run has
    not earned a socket and should not need one authorized."""
    return DiscoveryPolicy(
        objective=objective or (
            f"scheduled unattended hunt for keyword {keyword!r} against TED"),
        requested_scope="READ_API",
        max_queries=DEFAULT_MAX_QUERIES,
        max_wall_clock_seconds=DEFAULT_MAX_WALL_CLOCK_SECONDS,
        max_results=DEFAULT_MAX_RESULTS,
    )


def brief_filename(now: datetime) -> str:
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    stamp = now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"brief_{stamp}.md"


def write_brief_file(briefs_dir: Path, now: datetime, text: str) -> Path:
    """Write `text` to a new dated file under `briefs_dir`, returning
    its path. Never overwrites an existing file -- a same-second
    collision (two cycles in the same wall-clock second, realistic only
    under test) gets a numeric suffix rather than clobbering the
    earlier run's record."""
    briefs_dir.mkdir(parents=True, exist_ok=True)
    base = brief_filename(now)
    path = briefs_dir / base
    if path.exists():
        stem, suffix = base[:-3], base[-3:]
        n = 2
        while (briefs_dir / f"{stem}-{n}{suffix}").exists():
            n += 1
        path = briefs_dir / f"{stem}-{n}{suffix}"
    path.write_text(text, encoding="utf-8")
    return path


def update_latest(briefs_dir: Path, text: str) -> Path:
    """Write `text` to `briefs_dir/LATEST.md` -- the one stable path an
    operator (or a second script) can always read without knowing
    today's timestamp. A plain copy, not a symlink: portable across the
    filesystems and platforms this repository already runs its tests
    on, and just as replaceable every cycle."""
    briefs_dir.mkdir(parents=True, exist_ok=True)
    latest = briefs_dir / LATEST_FILENAME
    latest.write_text(text, encoding="utf-8")
    return latest


def enforce_retention(briefs_dir: Path, retain_count: int) -> List[Path]:
    """Keep only the `retain_count` most recent dated brief files this
    runner itself created; delete the rest. Matches ONLY
    `BRIEF_FILENAME_RE` -- `LATEST.md`, `.gitkeep`, or any other file a
    human left in `briefs/` is never touched, matched, or counted.
    Returns the list of paths actually deleted (best-effort: an
    individual delete failure is skipped, never raised, so one locked
    file cannot abort the rest of the sweep)."""
    if retain_count < 1:
        raise ScheduledBriefIntegrityError(
            f"retain_count must be at least 1 (a value below 1 could "
            f"delete the brief this very run just wrote), got {retain_count}")
    if not briefs_dir.exists():
        return []
    dated = sorted(
        p for p in briefs_dir.iterdir()
        if p.is_file() and BRIEF_FILENAME_RE.match(p.name)
    )
    if len(dated) <= retain_count:
        return []
    to_delete = dated[: len(dated) - retain_count]
    deleted: List[Path] = []
    for p in to_delete:
        try:
            p.unlink()
            deleted.append(p)
        except OSError:
            continue
    return deleted


def _append_receipt(log_path: Path, result: ScheduledBriefResult) -> None:
    """Append one receipt line. Never raises -- a logging failure must
    not crash the runner or silently misreport the cycle it is
    recording, same discipline `cron_pulse.py::_append_jsonl` already
    applies to its own writes."""
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "kind": "SCHEDULED_BRIEF_RUN",
            "action": result.action,
            "occurred_at": result.occurred_at,
            "detail": result.detail,
            "brief_path": result.brief_path,
            "deleted_count": result.deleted_count,
        }
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
    except OSError as exc:  # noqa: BLE001 -- see docstring above
        print(f"could not append receipt to {log_path}: {exc}", file=sys.stderr)


def _error_brief_text(occurred_at: str, message: str) -> str:
    """The brief this module writes when the cycle itself could not run
    at all (no operator profile, an unexpected exception). Still a real
    brief, not a blank file -- `LATEST.md` must never go silently
    stale or missing just because something upstream broke."""
    return (
        "=" * 72 + "\n"
        "SCHEDULED BRIEF -- RUN DID NOT COMPLETE\n"
        + "=" * 72 + "\n"
        f"occurred_at : {occurred_at}\n"
        f"reason      : {message}\n"
        "\n"
        "This run could not produce a hunt result. This file exists so "
        "that a missing or stale LATEST.md is never mistaken for 'ran "
        "clean' -- an unreadable outcome is reported honestly, not left "
        "silent.\n"
    )


def run_scheduled_brief_cycle(
    repo_root: Path,
    *,
    keyword: str = DEFAULT_KEYWORD,
    ted_query: Optional[str] = None,
    operator: Optional[OperatorProfile] = None,
    capability: Optional[CapabilityProfile] = None,
    policy: Optional[DiscoveryPolicy] = None,
    fetch_notices_fn: Optional[Callable[[], Sequence[Mapping]]] = None,
    limit: int = 50,
    retain_count: int = DEFAULT_RETAIN_COUNT,
    now: Optional[datetime] = None,
    briefs_dir: Optional[Path] = None,
    lock_path: Optional[Path] = None,
    receipt_log_path: Optional[Path] = None,
    hunt_log_path: Optional[Path] = None,
) -> ScheduledBriefResult:
    """Run exactly one scheduled cycle: acquire the lock, run one hunt
    cycle (via `hunt_loop.run_one_hunt_cycle`, diff included), write a
    dated brief, update `LATEST.md`, enforce retention, append a
    receipt, release the lock. Safe to invoke from cron once per
    schedule tick -- an overlapping second invocation exits cleanly as
    `SKIPPED_LOCKED` rather than racing the first.

    `operator` / `fetch_notices_fn` are the offline-test injection
    points -- when both are supplied this function never reads
    `operator_profile.json` and never touches the network, exactly like
    `hunt_loop.run_one_hunt_cycle()`'s own contract.
    """
    repo_root = Path(repo_root)
    now = now or datetime.now(timezone.utc)
    occurred_at = now.isoformat()
    briefs_dir = briefs_dir or (repo_root / BRIEFS_DIRNAME)
    lock_path = lock_path or (repo_root / LOCK_FILENAME)
    receipt_log_path = receipt_log_path or (repo_root / "foundation" / RECEIPT_LOG_NAME)

    try:
        acquire_lock(lock_path)
    except LockHeld as exc:
        result = ScheduledBriefResult(
            action="SKIPPED_LOCKED", occurred_at=occurred_at, detail=str(exc))
        _append_receipt(receipt_log_path, result)
        return result

    try:
        if (repo_root / HUNT_STOP_FILENAME).exists():
            result = ScheduledBriefResult(
                action="STOPPED_KILL_SWITCH", occurred_at=occurred_at,
                detail=f"{repo_root / HUNT_STOP_FILENAME} present -- no cycle run")
            _append_receipt(receipt_log_path, result)
            return result

        resolved_operator = operator
        if resolved_operator is None:
            try:
                loaded = load_operator_profile()
                resolved_operator = loaded.operator
            except ProfileLoadError as exc:
                text = _error_brief_text(occurred_at, f"could not load operator profile: {exc}")
                path = write_brief_file(briefs_dir, now, text)
                update_latest(briefs_dir, text)
                result = ScheduledBriefResult(
                    action="FAILED_PROFILE", occurred_at=occurred_at,
                    detail=str(exc), brief_path=str(path))
                _append_receipt(receipt_log_path, result)
                return result

        resolved_capability = capability or default_capability_profile(keyword)
        resolved_policy = policy
        if resolved_policy is None and fetch_notices_fn is None:
            resolved_policy = default_policy(keyword)
        query = ted_query or f'FT ~ ("{keyword}")'

        cycle: HuntCycleResult = run_one_hunt_cycle(
            repo_root, query, resolved_operator,
            policy=resolved_policy, capability=resolved_capability, limit=limit,
            fetch_notices_fn=fetch_notices_fn, now=now,
            log_path=hunt_log_path,
        )

        text = render_hunt_cycle(cycle)
        path = write_brief_file(briefs_dir, now, text)
        update_latest(briefs_dir, text)
        deleted = enforce_retention(briefs_dir, retain_count)

        action = cycle.action if cycle.is_stop() else f"WROTE_{cycle.action}"
        result = ScheduledBriefResult(
            action=action, occurred_at=occurred_at, detail=cycle.detail,
            brief_path=str(path), deleted_count=len(deleted),
        )
        _append_receipt(receipt_log_path, result)
        return result

    except Exception as exc:  # noqa: BLE001 -- a scheduled run must never
        # crash the cron job or leave the lock held; it becomes a
        # receipted failure with the real exception named, and a brief
        # that says so, rather than an uncaught traceback in cron's mail.
        detail = f"{type(exc).__name__}: {exc}"
        brief_path: Optional[str] = None
        try:
            text = _error_brief_text(occurred_at, detail)
            path = write_brief_file(briefs_dir, now, text)
            update_latest(briefs_dir, text)
            brief_path = str(path)
        except OSError:
            pass
        result = ScheduledBriefResult(
            action="FAILED_UNEXPECTED", occurred_at=occurred_at,
            detail=detail, brief_path=brief_path)
        _append_receipt(receipt_log_path, result)
        return result

    finally:
        # Runs on every path above, including the two explicit `return`s
        # inside the try-block and an uncaught exception the except-
        # clause above did not itself raise further -- the lock is
        # released regardless of how this cycle ended.
        release_lock(lock_path)


def _main(argv: Optional[list] = None) -> int:  # pragma: no cover -- cron entry point
    """The actual cron entry point: `python3 -m foundation.scheduled_brief`.
    No arguments, no flags -- a scheduled job should not require anyone
    to remember an invocation beyond the one line in HOW_TO_RUN.md."""
    repo_root = Path(__file__).resolve().parent.parent
    result = run_scheduled_brief_cycle(repo_root)
    print(f"[{result.occurred_at}] {result.action} -- {result.detail}")
    if result.brief_path:
        print(f"brief: {result.brief_path}")
    return 1 if result.action in ("STOPPED_HUNT_ERROR", "FAILED_UNEXPECTED") else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main())
