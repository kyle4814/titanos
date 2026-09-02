"""The automation loop around `foundation/hunt.py` -- the thing that makes
the hunt run without a human typing `hunt()` themselves each morning.

WHY THIS EXISTS

`hunt()` is a single bounded pass: fetch, assess, band, return. Running it
by hand every day and eyeballing the diff against yesterday's run is a
throwaway habit, and a diff that only exists in someone's memory is a diff
that gets missed. This module is that loop, structured the same way
`foundation/autonomy_loop.py` already proved out for its own actuator:
`run_one_*_cycle()` / `run_*_loop()` split, a `.hunt_stop` kill switch
checked before every cycle AND during every sleep slice, and a receipt
written for every cycle including a no-op one.

WHAT THIS REUSES RATHER THAN DUPLICATES

- `foundation/hunt.py::hunt()` is the only place notices are fetched and
  banded. This module never re-implements eligibility, qualification, or
  relevance -- it consumes `HuntReport`/`HuntEntry` exactly as `hunt.py`
  produces them.
- The kill-switch-checked-before-and-during-sleep shape is copied
  verbatim from `foundation/autonomy_loop.py::run_loop()`, not
  reinvented, per this module's own build instruction: "do not invent a
  new one."
- The durable-JSONL-with-replay-on-read pattern is the same discipline
  `foundation/outcome_ledger.py` and `foundation/autonomy_loop.py`'s own
  receipt log already use: state lives on disk, a fresh process rebuilds
  it by reading the file, never by trusting an in-memory dict that dies
  at process exit. `CLAUDE.md` names six existing stores that call
  themselves "append-only ledgers" while holding nothing but a Python
  list -- this is deliberately not a seventh.

WHAT THIS DOES NOT DO

It never fetches on its own -- every fetch happens inside `hunt()`,
through `hunt()`'s own `policy`/`fetch_notices_fn` contract, so this
module inherits `fetch_feed()`'s existing discovery-authorization gate
for free rather than adding a second one.

It takes NO outward action. No email, no application, no account
creation, no contact, ever -- observing, ranking and recording is the
entire public surface. `foundation/tests/test_hunt_loop.py` enumerates
every public callable in this module and asserts none of them is named
with an outbound-action verb (send/apply/contact/email/submit/notify/
publish/register/subscribe/post/create_account), the same structural
check `foundation/sentinel.py`'s own test file already applies to
itself.

DEADLINE HONESTY

A notice's closing date is read from `HuntEntry.signal.facts["deadline"]`
when a `CanonicalSignal` was built (i.e. when a `capability` profile was
supplied to `run_one_hunt_cycle()`/`run_hunt_loop()`). Absent or
unparseable text becomes `UNKNOWN`, never `NOT_CLOSING_SOON` -- treating
an unreadable date as safely distant is exactly the wrong direction to be
wrong in for a deadline. A date already in the past becomes `CLOSED`,
kept distinct from both `UNKNOWN` and `NOT_CLOSING_SOON` so a stale entry
is never silently read as still-open.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Mapping, Optional, Sequence

from foundation.hunt import HuntEntry, HuntReport, hunt, hunt_multi
from foundation.qualification import OperatorProfile
from foundation.relevance import CapabilityProfile
from foundation.discovery_authorization import DiscoveryPolicy

__all__ = [
    "HUNT_STOP_FILENAME",
    "HUNT_LOG_NAME",
    "DEADLINE_STATUSES",
    "HUNT_ACTIONS",
    "DEFAULT_DEADLINE_WINDOW_DAYS",
    "HuntEntrySnapshot",
    "HuntCycleResult",
    "run_one_hunt_cycle",
    "run_hunt_loop",
    "load_hunt_state",
    "render_hunt_cycle",
]

HUNT_STOP_FILENAME = ".hunt_stop"
HUNT_LOG_NAME = "hunt_loop_log.jsonl"

DEFAULT_DEADLINE_WINDOW_DAYS = 7

# UNKNOWN and CLOSED are both deliberately NOT "not closing soon" -- see
# module docstring's DEADLINE HONESTY section. Absent/unparseable data
# stays UNKNOWN forever; it is never inferred to be safely distant.
DEADLINE_STATUSES = ("CLOSING_SOON", "NOT_CLOSING_SOON", "CLOSED", "UNKNOWN")

HUNT_ACTIONS = frozenset({
    "RAN_CLEAN",         # ran; hunt() assessed zero notices
    "RAN_NO_CHANGE",     # ran; notices assessed, nothing new, nothing newly closing
    "RAN_WITH_CHANGES",  # ran; at least one new notice or newly-closing deadline
    "STOPPED_KILL_SWITCH",
    "STOPPED_HUNT_ERROR",
})


def _now_iso(now: Optional[datetime] = None) -> str:
    return (now or datetime.now(timezone.utc)).isoformat()


def _parse_deadline(raw: str) -> Optional[datetime]:
    """Best-effort ISO-8601 parse. Returns None on anything it cannot
    confidently read -- callers must treat None the same as UNKNOWN, never
    guess a value for it."""
    text = str(raw).strip()
    if not text:
        return None
    candidate = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        # A bare date ("2026-09-30") is the other real shape TED and
        # sibling sources emit for a receipt deadline.
        try:
            parsed = datetime.strptime(text[:10], "%Y-%m-%d")
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _deadline_status(raw: str, now: datetime, window_days: int) -> str:
    parsed = _parse_deadline(raw)
    if parsed is None:
        return "UNKNOWN"
    delta_days = (parsed - now).total_seconds() / 86400.0
    if delta_days < 0:
        return "CLOSED"
    if delta_days <= window_days:
        return "CLOSING_SOON"
    return "NOT_CLOSING_SOON"



# Closing-date fact keys, in priority order. Kept identical to
# `brief.py`'s `_DEADLINE_FACT_KEYS` -- see `from_entry` below for why
# a single key is not enough. If a new source uses a third key name,
# both lists must gain it; a divergence between them means the loop and
# the brief disagree about when something closes.
_DEADLINE_FACT_KEYS = ("deadline", "close_date")


def _raw_deadline(entry: HuntEntry) -> str:
    """The closing date an entry's signal carries, whichever key its
    source uses. "" when there genuinely is none -- which stays UNKNOWN,
    and UNKNOWN stays urgent."""
    if entry.signal is None:
        return ""
    facts = entry.signal.facts
    for key in _DEADLINE_FACT_KEYS:
        value = str(facts.get(key) or "").strip()
        if value:
            return value
    return ""


@dataclass(frozen=True)
class HuntEntrySnapshot:
    """One notice as recorded in one cycle -- the minimum needed to diff
    against a future cycle and to explain a deadline verdict later."""

    publication_number: str
    band: str
    deadline_raw: str
    deadline_status: str

    def __post_init__(self) -> None:
        if not self.publication_number.strip():
            raise ValueError("a snapshot must name the notice it is about")
        if self.deadline_status not in DEADLINE_STATUSES:
            raise ValueError(
                f"unknown deadline_status {self.deadline_status!r}")

    @classmethod
    def from_entry(cls, entry: HuntEntry, now: datetime,
                    window_days: int) -> "HuntEntrySnapshot":
        # Reads the SAME priority-ordered key set brief.py reads, and
        # for the same reason. NZ GETS publishes a real closing date on
        # every notice under `close_date`; TED uses `deadline`. brief.py
        # once read only `deadline` and consequently reported all 30 NZ
        # notices as "closes: UNKNOWN -- treat as urgent", filling its
        # most important section with noise while looking correct.
        #
        # This module was not affected then, only because the loop was
        # silently TED-only. It is multi-source now, so reading one key
        # here would reintroduce a bug this project already fixed once
        # today. Flagged by the 2026-09-02 audit as a landmine before it
        # ever fired -- which is the cheapest possible moment to fix a
        # defect.
        deadline_raw = _raw_deadline(entry)
        return cls(
            publication_number=entry.publication_number,
            band=entry.band,
            deadline_raw=deadline_raw,
            deadline_status=_deadline_status(deadline_raw, now, window_days),
        )

    def to_json(self) -> dict:
        return {
            "publication_number": self.publication_number,
            "band": self.band,
            "deadline_raw": self.deadline_raw,
            "deadline_status": self.deadline_status,
        }


@dataclass(frozen=True)
class HuntCycleResult:
    """One bounded cycle's outcome. Every field here is what
    `_append_cycle_record()` writes verbatim -- this dataclass IS the
    receipt shape, same discipline as `autonomy_loop.CycleResult`."""

    action: str
    occurred_at: str
    query: str
    detail: str
    fetched: int = 0
    assessed: int = 0
    entries: tuple[HuntEntrySnapshot, ...] = ()
    new_entries: tuple[HuntEntrySnapshot, ...] = ()
    closing_soon_entries: tuple[HuntEntrySnapshot, ...] = ()
    newly_closing_entries: tuple[HuntEntrySnapshot, ...] = ()
    unknown_deadline_entries: tuple[HuntEntrySnapshot, ...] = ()
    skipped: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.action not in HUNT_ACTIONS:
            raise ValueError(f"unknown HuntCycleResult action {self.action!r}")

    def is_stop(self) -> bool:
        return self.action.startswith("STOPPED_")

    @property
    def new_count(self) -> int:
        return len(self.new_entries)

    @property
    def closing_soon_count(self) -> int:
        return len(self.closing_soon_entries)

    @property
    def newly_closing_count(self) -> int:
        return len(self.newly_closing_entries)

    @property
    def unknown_deadline_count(self) -> int:
        return len(self.unknown_deadline_entries)


def _default_log_path(repo_root: Path) -> Path:
    return repo_root / "foundation" / HUNT_LOG_NAME


def load_hunt_state(log_path: Path) -> tuple[set, dict]:
    """Replay the durable log into `(ever_seen_publication_numbers,
    last_known_deadline_status_by_publication_number)`.

    Called fresh on every cycle -- there is no module-level cache -- so a
    brand-new process reading the same file sees exactly the same state
    a long-running one would. This IS the "durable, not in-memory" proof:
    nothing survives except what is actually on disk.

    Fails soft: a missing file, an unreadable file, a malformed line, or
    a non-CYCLE record are all skipped rather than raised -- the loop
    must not crash at startup because one historical line was cut mid-
    write, the same discipline `outcome_ledger.py`'s replay already
    uses for its own truncated-trailing-line case.
    """
    ever_seen: set = set()
    last_status: dict = {}
    if not log_path.exists():
        return ever_seen, last_status
    try:
        raw = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ever_seen, last_status
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict) or obj.get("kind") != "CYCLE":
            continue
        for e in obj.get("entries", ()):
            if not isinstance(e, dict):
                continue
            pub = e.get("publication_number")
            if not pub:
                continue
            ever_seen.add(pub)
            status = e.get("deadline_status")
            if status in DEADLINE_STATUSES:
                # Later lines are later cycles -- last write wins, which
                # is exactly "as of the most recent time we saw it".
                last_status[pub] = status
    return ever_seen, last_status


def _append_cycle_record(log_path: Path, result: HuntCycleResult) -> None:
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "kind": "CYCLE",
            "action": result.action,
            "occurred_at": result.occurred_at,
            "query": result.query,
            "detail": result.detail,
            "fetched": result.fetched,
            "assessed": result.assessed,
            "new_count": result.new_count,
            "closing_soon_count": result.closing_soon_count,
            "newly_closing_count": result.newly_closing_count,
            "unknown_deadline_count": result.unknown_deadline_count,
            "skipped": list(result.skipped),
            "entries": [e.to_json() for e in result.entries],
        }
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
    except OSError:
        pass  # a logging failure must never crash or silently misreport the loop


def _summarize(new_n: int, newly_closing_n: int, window_days: int,
               assessed: int) -> str:
    if assessed == 0:
        return "0 notices assessed; nothing to report"
    parts = [f"{assessed} notice(s) assessed"]
    parts.append(f"{new_n} new since last run" if new_n else "0 new since last run")
    parts.append(
        f"{newly_closing_n} newly closing within {window_days} day(s)"
        if newly_closing_n else
        f"0 newly closing within {window_days} day(s)")
    return "; ".join(parts)


def run_one_hunt_cycle(
    repo_root: Path,
    query: str,
    operator: OperatorProfile,
    *,
    policy: Optional[DiscoveryPolicy] = None,
    capability: Optional[CapabilityProfile] = None,
    limit: int = 50,
    fetch_notices_fn: Optional[Callable[[], Sequence[Mapping]]] = None,
    sources: Optional[Sequence] = None,
    deadline_window_days: int = DEFAULT_DEADLINE_WINDOW_DAYS,
    now: Optional[datetime] = None,
    log_path: Optional[Path] = None,
) -> HuntCycleResult:
    """One bounded cycle: run `hunt()`, diff against the durable log,
    flag deadlines, write exactly one receipt, return the result.

    Never raises on ordinary conditions -- a kill switch or a `hunt()`
    failure is a `HuntCycleResult`, not an exception, so `run_hunt_loop()`
    needs no except-clause of its own to stay receipted. EVERY outcome is
    receipted here, by the function that produces it, including a cycle
    that finds nothing.
    """
    now = now or datetime.now(timezone.utc)
    occurred_at = _now_iso(now)
    stop_file = repo_root / HUNT_STOP_FILENAME
    log_path = log_path or _default_log_path(repo_root)

    if stop_file.exists():
        result = HuntCycleResult(
            action="STOPPED_KILL_SWITCH", occurred_at=occurred_at, query=query,
            detail=f"{stop_file} present",
        )
        _append_cycle_record(log_path, result)
        return result

    ever_seen, last_status = load_hunt_state(log_path)

    try:
        if sources is not None and fetch_notices_fn is None:
            # MULTI-SOURCE. The 2026-09-02 audit found this loop was
            # silently TED-only while `hunt`/`brief` were three-source --
            # an operator running the unattended loop was watching a
            # narrower world than the same operator running `brief`, and
            # nothing said so. `sources` stays optional and defaulted to
            # None so every existing single-source caller and every
            # injected-fetch test keeps working unchanged.
            report: HuntReport = hunt_multi(
                query, operator, sources, capability=capability, now=now,
            )
        else:
            report = hunt(
                query, operator, policy=policy, capability=capability,
                limit=limit, fetch_notices_fn=fetch_notices_fn, now=now,
            )
    except Exception as exc:  # noqa: BLE001 - a fetch/assess failure must
        # never crash the loop or go unreceipted; it becomes a stop with
        # the real exception named, so a human can see exactly what broke.
        result = HuntCycleResult(
            action="STOPPED_HUNT_ERROR", occurred_at=occurred_at, query=query,
            detail=f"{type(exc).__name__}: {exc}",
        )
        _append_cycle_record(log_path, result)
        return result

    snapshots = tuple(
        HuntEntrySnapshot.from_entry(e, now, deadline_window_days)
        for e in report.entries
    )

    new_entries = tuple(s for s in snapshots if s.publication_number not in ever_seen)
    closing_soon = tuple(s for s in snapshots if s.deadline_status == "CLOSING_SOON")
    newly_closing = tuple(
        s for s in closing_soon
        if last_status.get(s.publication_number) != "CLOSING_SOON"
    )
    unknown_deadline = tuple(s for s in snapshots if s.deadline_status == "UNKNOWN")

    if not snapshots:
        action = "RAN_CLEAN"
    elif new_entries or newly_closing:
        action = "RAN_WITH_CHANGES"
    else:
        action = "RAN_NO_CHANGE"

    detail = _summarize(len(new_entries), len(newly_closing),
                        deadline_window_days, len(snapshots))

    result = HuntCycleResult(
        action=action, occurred_at=occurred_at, query=query, detail=detail,
        fetched=report.fetched, assessed=report.assessed, entries=snapshots,
        new_entries=new_entries, closing_soon_entries=closing_soon,
        newly_closing_entries=newly_closing,
        unknown_deadline_entries=unknown_deadline, skipped=report.skipped,
    )
    _append_cycle_record(log_path, result)
    return result


def run_hunt_loop(
    repo_root: Path,
    query: str,
    operator: OperatorProfile,
    *,
    policy: Optional[DiscoveryPolicy] = None,
    capability: Optional[CapabilityProfile] = None,
    limit: int = 50,
    fetch_notices_fn: Optional[Callable[[], Sequence[Mapping]]] = None,
    deadline_window_days: int = DEFAULT_DEADLINE_WINDOW_DAYS,
    sleep_seconds: int = 3600,
    sleep_slice_seconds: int = 5,
    max_cycles: Optional[int] = None,
    log_path: Optional[Path] = None,
) -> list[HuntCycleResult]:
    """Runs cycles until a `STOPPED_*` result, the kill switch fires
    (including mid-sleep), or `max_cycles` is reached. `max_cycles` is a
    TEST HOOK ONLY -- omit it for a real run.

    Copies `autonomy_loop.run_loop()`'s proven shape exactly: sleep in
    short slices between cycles, checking the kill switch every slice, so
    a dropped `.hunt_stop` file stops the loop within one slice even while
    backgrounded. A `STOPPED_HUNT_ERROR` halts the loop the same way a
    `STOPPED_*` result halts `autonomy_loop` -- this module never guesses
    past a failure it cannot explain.
    """
    stop_file = repo_root / HUNT_STOP_FILENAME
    resolved_log_path = log_path or _default_log_path(repo_root)
    results: list[HuntCycleResult] = []
    cycles = 0

    while max_cycles is None or cycles < max_cycles:
        result = run_one_hunt_cycle(
            repo_root, query, operator, policy=policy, capability=capability,
            limit=limit, fetch_notices_fn=fetch_notices_fn,
            deadline_window_days=deadline_window_days,
            log_path=resolved_log_path,
        )
        results.append(result)
        cycles += 1

        if result.is_stop():
            break

        elapsed = 0
        while elapsed < sleep_seconds:
            if stop_file.exists():
                kill = HuntCycleResult(
                    action="STOPPED_KILL_SWITCH",
                    occurred_at=_now_iso(),
                    query=query,
                    detail=f"{stop_file} present (during sleep)",
                )
                results.append(kill)
                _append_cycle_record(resolved_log_path, kill)
                return results
            slice_len = min(sleep_slice_seconds, sleep_seconds - elapsed)
            if slice_len > 0:
                time.sleep(slice_len)
            elapsed += sleep_slice_seconds

    return results


def render_hunt_cycle(result: HuntCycleResult) -> str:
    """Human-readable rendering of one cycle's receipt. The diff is the
    product -- this deliberately leads with what's NEW, not a re-dump of
    every assessed notice."""
    lines = [
        f"[{result.occurred_at}] {result.action} -- {result.detail}",
    ]
    if result.new_entries:
        lines.append("NEW:")
        for s in result.new_entries:
            lines.append(f"  {s.publication_number}  {s.band}  deadline={s.deadline_status}")
    if result.newly_closing_entries:
        lines.append("NEWLY CLOSING:")
        for s in result.newly_closing_entries:
            lines.append(f"  {s.publication_number}  {s.band}  deadline_raw={s.deadline_raw!r}")
    if result.unknown_deadline_entries:
        lines.append(
            f"UNKNOWN DEADLINE: {len(result.unknown_deadline_entries)} "
            f"notice(s) -- open the notice to check manually, do not assume safe"
        )
    if result.skipped:
        lines.append(f"skipped: {len(result.skipped)}")
    return "\n".join(lines)
