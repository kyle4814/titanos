"""Answer the two questions an operator actually has: what is NEW, and
what is CLOSING SOON. Not a lead generator, not a ranking engine.

WHY THIS EXISTS

`foundation/shortlist.py` renders the top signals by relevance band.
That answers "what matches me" -- it does not answer "what changed since
I last looked" or "what closes soonest." An operator who ran the digest
yesterday does not want to re-read yesterday's list, and a STRONG_MATCH
closing in four days matters more than a STRONG_MATCH closing in 2031 --
the corpus genuinely contains both, because TED framework agreements run
for years (see `mouth_ted.py`'s own notes on multi-year deadlines). This
module is the thin layer that turns "a merged pile of signals" into
"what actually needs my attention today."

WHAT THIS MODULE DOES NOT DO

- Does not score or rank by relevance. That is `relevance.py`'s job.
- Does not render a shortlist. That is `shortlist.py`'s job.
- Does not write to `foundation/outcome_ledger.py` or any other ledger.
  Nothing here is a lead, an assessed opportunity, or revenue -- see
  `_REPORT_HEADER` below, present on every render, same discipline as
  `shortlist.py::render_digest()`.
- Does not invent a second "seen" mechanism. The atomic-write discipline
  below is `foundation/checkpoint.py`'s (`CheckpointStore.save()`):
  temp file in the same directory, fsync, `os.replace`. `foundation/
  mouth_common.py::observe()`'s "leave prior state untouched on failure"
  posture is the same idea applied to a different payload shape
  (mouth state is a single hash+key-list; this module's state is a set
  of previously-seen signal ids). Neither is duplicated here as new
  design -- both are the same one atomic-publish primitive, re-applied.

CRASH SAFETY

`new_since()` computes the full "new" answer BEFORE touching disk, then
publishes the updated seen-set in one atomic `os.replace`. There is no
window in which a reader can observe a half-written state file, for the
same reason `checkpoint.py` has none: the path a reader opens is never
the path being written to. A process killed at any point before the
`os.replace` call leaves the previous state file completely untouched --
the next run recomputes "new" against the same prior baseline and
reaches the same answer, so nothing is silently marked seen without
having actually been durably recorded as seen. A process killed AFTER
`os.replace` completes is a normal successful run, not a crash in this
module's sense. Corrupt or unreadable state (truncated write from a
still-older crash, hand-edited file) is treated as "no prior state,"
never a fatal error -- same posture as `checkpoint.py::CheckpointStore.
_replay()` skipping an unparseable line and `mouth_common.py::_load_state()`
returning `None` on a decode error.

DEADLINE PARSING AND TIMEZONES

TED emits deadlines with explicit UTC offsets (`"2026-09-09T12:00:00+03:00"`,
`"2026-10-01T00:00:00Z"`); Contracts Finder (OCDS) emits similar ISO-8601
shapes. A deadline can also be absent entirely (framework agreements,
malformed source data) or already in the past (an expired notice still
present in the corpus). All four shapes are handled EXPLICITLY, never
collapsed into one bucket:

- present + parses + timezone-aware + in the future  -> FUTURE
- present + parses + naive (no offset)                -> treated as UTC,
  same assumption `mouth_common.py::read_mouth_log_continuity()` already
  makes for a naive timestamp, not a new policy invented here
- present + parses + in the past                      -> EXPIRED, never
  silently dropped and never counted as urgent
- present + does not parse (malformed)                 -> UNKNOWN
- absent entirely                                       -> UNKNOWN

UNKNOWN is never treated as urgent (it cannot be sorted against a real
deadline) and never silently dropped (an entry with no deadline is still
visible in its own section) -- "we don't know when this closes" is not
the same claim as "this doesn't close." All comparisons happen on
timezone-AWARE datetimes: every parsed deadline and every `now` value is
normalised to carry `tzinfo` before any `<`/`>` comparison, so a naive/
aware mix (which raises `TypeError` in Python, or worse, silently
compares wrong if one side were pre-converted incorrectly) cannot occur.
"""

from __future__ import annotations

import json
import os
import tempfile
import textwrap
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Mapping, Optional, Sequence, Tuple

from foundation.signal_spine import CanonicalSignal
from foundation.untrusted_text import neutralise

__all__ = [
    "UNKNOWN",
    "DEADLINE_STATUSES",
    "DeadlineInfo",
    "classify_deadline",
    "NewSinceResult",
    "new_since",
    "ClosingEntry",
    "closing_within",
    "WatchReport",
    "watch_report",
    "render_watch",
]

# Same literal `shortlist.py` uses for "the underlying data did not carry
# this fact" -- never a blank, never a guess. Not imported from
# `shortlist.py` (this module owns no dependency on it) -- redeclared
# identically, the same way `shortlist.py` itself redeclares constants
# `relevance.py` already defines when reuse would create a cross-module
# coupling neither module needs.
UNKNOWN = "UNKNOWN"

_SHORT_MAX_LEN = 80
_DISPLAY_MAX_LEN = 200
_REFERENCE_MAX_LEN = 320

_REPORT_HEADER = (
    "=" * 72,
    "OPPORTUNITY WATCH -- NOT LEADS. NOT OPPORTUNITIES. NOT REVENUE.",
    "=" * 72,
    "This report answers two questions only: what changed since the last",
    "run, and what closes soonest. It re-states nothing about fitness or",
    "relevance -- see shortlist.py for that. Nothing below has been",
    "reviewed by a human or checked against eligibility. Every entry is",
    "unverified until a human independently checks it.",
    "",
    "A deadline showing UNKNOWN means the underlying notice did not carry",
    "a parseable deadline -- it is not \"no deadline pressure,\" it is",
    "\"we do not know.\" An EXPIRED deadline is shown, not hidden, so an",
    "operator can see the system noticed rather than silently dropped it.",
    "=" * 72,
)


def _clean(value: object, max_len: int = _DISPLAY_MAX_LEN) -> str:
    text = neutralise(str(value) if value is not None else "", max_len=max_len)
    return text if text.strip() else UNKNOWN


def _deadline_raw(signal: CanonicalSignal) -> str:
    """Same field-priority `shortlist.py::_entry_from_assessment` uses:
    `facts["deadline"]` first (the normalised fact a tentacle promoted),
    falling back to `evidence["deadline"]` (the raw field some tentacles
    only ever populate there). Not imported from `shortlist.py` -- that
    function is private to this module's caller, so the two-line
    priority rule is restated here rather than reaching into another
    module's internals.
    """
    raw = signal.facts.get("deadline") or signal.evidence.get("deadline") or ""
    return str(raw).strip()


def _notice_reference(signal: CanonicalSignal) -> str:
    for key in ("publication_number", "tender_id", "ocid"):
        value = signal.evidence.get(key)
        if value:
            return str(value)
    return ""


def _ensure_aware(dt: datetime) -> datetime:
    """Normalise a naive datetime to UTC-aware. This is the ONE place a
    naive/aware mix could otherwise be introduced -- every comparison in
    this module goes through parsed values that have passed through here
    (or through `_current_now`, which applies the identical rule to
    `now`), so a raw `<`/`>` between an aware and a naive datetime can
    never reach a comparison anywhere else in this module.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _current_now(now: Optional[datetime]) -> datetime:
    return _ensure_aware(now if now is not None else datetime.now(timezone.utc))


def _parse_deadline(raw: str) -> Optional[datetime]:
    """Parse the deadline shapes TED and Contracts Finder actually emit.
    Returns `None` for absent or malformed input -- callers turn that
    into UNKNOWN, never into a crash and never into a guessed date.
    """
    text = raw.strip()
    if not text:
        return None
    # `datetime.fromisoformat` (3.11+) already accepts a trailing "Z",
    # but this repository's own tests and CI matrix are not guaranteed
    # to run on 3.11+ everywhere the code might execute -- the explicit
    # substitution costs nothing and removes that assumption entirely.
    candidate = text
    if candidate.endswith("Z") or candidate.endswith("z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except (ValueError, TypeError):
        return None
    return _ensure_aware(parsed)


DEADLINE_STATUSES = ("FUTURE", "EXPIRED", "UNKNOWN")


@dataclass(frozen=True)
class DeadlineInfo:
    """What this module knows about one signal's deadline -- the raw
    string exactly as observed (never re-formatted, so a human can
    cross-check it against the source notice), whether it parsed, and
    the three-way classification `DEADLINE_STATUSES` names. `parsed` is
    always timezone-aware when not `None` -- see `_ensure_aware`.
    """

    raw: str
    parsed: Optional[datetime]
    status: str

    def __post_init__(self) -> None:
        if self.status not in DEADLINE_STATUSES:
            raise ValueError(f"unknown deadline status {self.status!r}")
        if self.parsed is not None and self.parsed.tzinfo is None:
            raise ValueError("DeadlineInfo.parsed must be timezone-aware")


def classify_deadline(signal: CanonicalSignal, now: Optional[datetime] = None) -> DeadlineInfo:
    """Classify one signal's deadline against `now` (defaults to the
    real current time, UTC). Three, and only three, outcomes -- see
    module docstring: FUTURE, EXPIRED, UNKNOWN. Never raises on bad
    input; a malformed or absent deadline is UNKNOWN, not an error.
    """
    raw = _deadline_raw(signal)
    parsed = _parse_deadline(raw)
    if parsed is None:
        return DeadlineInfo(raw=raw, parsed=None, status="UNKNOWN")
    current = _current_now(now)
    status = "FUTURE" if parsed >= current else "EXPIRED"
    return DeadlineInfo(raw=raw, parsed=parsed, status=status)


# ── new_since ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class NewSinceResult:
    """`new` is every signal not present in the state file BEFORE this
    call -- the state file is then atomically updated to include every
    signal id seen this run (new and previously-seen alike), so the
    NEXT call's `new` reflects only what changed after this one. An
    empty `signals` sequence is a valid input and produces an empty
    `new` with no error -- a run over zero signals is an honest outcome,
    same posture `shortlist.py::build_shortlist()` already takes for an
    empty pipeline sweep.
    """

    new: Tuple[CanonicalSignal, ...]
    previously_seen_ids: Tuple[str, ...]
    total_seen_after: int
    checked_at: str


def _load_seen_ids(state_path: Path) -> frozenset:
    """Read-only. Missing file -> empty set (first run, not an error).
    Corrupt/unreadable file -> empty set, same "truncated write from a
    killed process is not fatal" posture `checkpoint.py::_replay()` and
    `mouth_common.py::_load_state()` both already take -- worst case a
    prior run's crash costs one duplicate "new" notification on the
    next run, never a silent loss of "this is genuinely new."
    """
    if not state_path.exists():
        return frozenset()
    try:
        obj = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return frozenset()
    if not isinstance(obj, Mapping):
        return frozenset()
    ids = obj.get("seen_ids", [])
    if not isinstance(ids, list):
        return frozenset()
    return frozenset(str(i) for i in ids)


def _atomic_write_seen_ids(state_path: Path, seen_ids: frozenset, checked_at: str) -> None:
    """Publish the full updated seen-set in one filesystem rename -- the
    exact discipline `foundation/checkpoint.py::CheckpointStore.save()`
    uses (temp file in the SAME directory, flush, fsync, `os.replace`).
    A crash at any point before `os.replace` completes leaves whatever
    was durably published by the PREVIOUS call untouched; there is no
    partially-written file a reader can ever open, because the path
    readers open (`state_path`) is never the path being written.
    """
    state_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({
        "seen_ids": sorted(seen_ids),
        "updated_at": checked_at,
    }, sort_keys=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(state_path.parent), prefix=".tmp-opportunity-watch-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            tmp.write(payload)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_name, state_path)
    except Exception:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
        raise


def new_since(
    signals: Sequence[CanonicalSignal],
    state_path: Path,
    now: Optional[datetime] = None,
) -> NewSinceResult:
    """Which of `signals` were not seen on any previous call against
    `state_path`, then durably record every signal id seen this run.

    Crash-safe: everything is computed in memory FIRST (the read of the
    prior state, the diff, the new merged set); the only disk write is
    the single atomic publish at the very end. If the process dies
    before that publish completes, `state_path` still reflects exactly
    what the previous successful call wrote -- the next call computes
    "new" against that same baseline and reaches the same, correct
    answer. Nothing is ever marked seen without the write that records
    it having actually completed.
    """
    checked_at = _current_now(now).isoformat()
    prior_ids = _load_seen_ids(state_path)

    new_signals = tuple(s for s in signals if s.signal_id not in prior_ids)
    all_ids = set(prior_ids) | {s.signal_id for s in signals}

    _atomic_write_seen_ids(state_path, frozenset(all_ids), checked_at)

    return NewSinceResult(
        new=new_signals,
        previously_seen_ids=tuple(sorted(prior_ids)),
        total_seen_after=len(all_ids),
        checked_at=checked_at,
    )


# ── closing_within ──────────────────────────────────────────────────

@dataclass(frozen=True)
class ClosingEntry:
    """One signal with a real, future, in-window deadline -- everything
    an operator needs to see without opening the source. Text fields are
    already `neutralise()`d, same discipline as `shortlist.ShortlistEntry`.
    """

    signal_id: str
    buyer: str
    title: str
    deadline_raw: str
    deadline: datetime
    days_remaining: int
    source_id: str
    reference: str


def closing_within(
    signals: Sequence[CanonicalSignal],
    days: int,
    now: Optional[datetime] = None,
) -> Tuple[ClosingEntry, ...]:
    """Signals whose deadline falls in `[now, now + days]`, inclusive at
    both ends, soonest first. A signal with an EXPIRED or UNKNOWN
    deadline is never included here -- a past deadline is not "closing
    soon," it is expired (see `render_watch()`'s EXPIRED section for
    where it IS shown), and an unknown deadline cannot be sorted against
    a real one at all.
    """
    if days < 0:
        raise ValueError("days must be >= 0")
    current = _current_now(now)
    window_end = current + timedelta(days=days)

    entries = []
    for signal in signals:
        info = classify_deadline(signal, now=current)
        if info.status != "FUTURE":
            continue
        if not (current <= info.parsed <= window_end):
            continue
        remaining = (info.parsed - current)
        entries.append(ClosingEntry(
            signal_id=signal.signal_id,
            buyer=_clean(signal.evidence.get("buyer_name_safe", "")),
            title=_clean(signal.evidence.get("title_safe", "")),
            deadline_raw=_clean(info.raw, max_len=_SHORT_MAX_LEN),
            deadline=info.parsed,
            days_remaining=remaining.days,
            source_id=_clean(signal.source_id, max_len=_SHORT_MAX_LEN),
            reference=_clean(signal.source_ref, max_len=_REFERENCE_MAX_LEN),
        ))

    entries.sort(key=lambda e: (e.deadline, e.signal_id))
    return tuple(entries)


# ── combined report ────────────────────────────────────────────────

@dataclass(frozen=True)
class WatchEntry:
    """A lighter-weight display row than `ClosingEntry` -- used for the
    NEW / EXPIRED / UNKNOWN sections, which don't carry a sortable
    deadline the way the CLOSING SOON section does.
    """

    signal_id: str
    buyer: str
    title: str
    deadline_raw: str
    source_id: str
    reference: str


def _watch_entry(signal: CanonicalSignal, deadline_raw: str) -> WatchEntry:
    return WatchEntry(
        signal_id=signal.signal_id,
        buyer=_clean(signal.evidence.get("buyer_name_safe", "")),
        title=_clean(signal.evidence.get("title_safe", "")),
        deadline_raw=_clean(deadline_raw, max_len=_SHORT_MAX_LEN),
        source_id=_clean(signal.source_id, max_len=_SHORT_MAX_LEN),
        reference=_clean(signal.source_ref, max_len=_REFERENCE_MAX_LEN),
    )


@dataclass(frozen=True)
class WatchReport:
    """The fifteen-second answer. `new` is every signal not seen on a
    prior run (any deadline status). `closing_soon` is every FUTURE
    deadline inside the window (new or previously seen). `new_and_closing`
    is the intersection -- the highest-priority row an operator has.
    `expired`/`unknown_deadline` exist purely for visibility, per the
    hard rule that an unknown or expired deadline must never be silently
    dropped.
    """

    new: Tuple[WatchEntry, ...]
    closing_soon: Tuple[ClosingEntry, ...]
    new_and_closing: Tuple[ClosingEntry, ...]
    expired: Tuple[WatchEntry, ...]
    unknown_deadline: Tuple[WatchEntry, ...]
    window_days: int
    generated_at: str
    total_signals: int


def watch_report(
    signals: Sequence[CanonicalSignal],
    state_path: Path,
    days: int = 30,
    now: Optional[datetime] = None,
) -> WatchReport:
    """Run `new_since()` and `closing_within()` against the same
    `signals`/`now`, and assemble the combined view. This is the one
    call site most callers want; `new_since()`/`closing_within()` remain
    independently callable for anyone who only needs one half.
    """
    current = _current_now(now)
    new_result = new_since(signals, state_path, now=current)
    new_ids = {s.signal_id for s in new_result.new}

    closing = closing_within(signals, days, now=current)
    closing_ids = {e.signal_id for e in closing}

    new_entries = tuple(
        _watch_entry(s, _deadline_raw(s)) for s in new_result.new)
    new_and_closing = tuple(e for e in closing if e.signal_id in new_ids)

    expired_entries = []
    unknown_entries = []
    for signal in signals:
        info = classify_deadline(signal, now=current)
        if info.status == "EXPIRED":
            expired_entries.append(_watch_entry(signal, info.raw))
        elif info.status == "UNKNOWN":
            unknown_entries.append(_watch_entry(signal, info.raw))

    return WatchReport(
        new=new_entries,
        closing_soon=closing,
        new_and_closing=new_and_closing,
        expired=tuple(expired_entries),
        unknown_deadline=tuple(unknown_entries),
        window_days=days,
        generated_at=current.isoformat(),
        total_signals=len(signals),
    )


_WRAP_WIDTH = 56
_CONTINUATION_GUTTER = "        | "


def _wrap_line(line: str) -> Tuple[str, ...]:
    """Same hard-wrap discipline as `shortlist.py::_wrap_line` -- a
    line-wrap boundary is never left to the terminal, for the identical
    forged-entry reason documented there (FINDING A, BLUE_TEAM_009).
    Redeclared rather than imported: this module owns no dependency on
    `shortlist.py`'s private helpers.
    """
    wrapped = textwrap.wrap(
        line, width=_WRAP_WIDTH, subsequent_indent=_CONTINUATION_GUTTER,
        break_long_words=True, break_on_hyphens=False)
    return tuple(wrapped) if wrapped else ("",)


def _render_rows(rows: Sequence, formatter) -> Tuple[str, ...]:
    lines: list = []
    for position, row in enumerate(rows, start=1):
        for line in formatter(position, row):
            lines.extend(_wrap_line(line))
    return tuple(lines)


def _fmt_watch_entry(position: int, e: WatchEntry) -> Tuple[str, ...]:
    return (
        f"{position}. {e.buyer} -- {e.title}",
        f"   deadline: {e.deadline_raw}    source: {e.source_id}",
        f"   reference: {e.reference}",
    )


def _fmt_closing_entry(position: int, e: ClosingEntry) -> Tuple[str, ...]:
    return (
        f"{position}. [{e.days_remaining}d] {e.buyer} -- {e.title}",
        f"   deadline: {e.deadline_raw}    source: {e.source_id}",
        f"   reference: {e.reference}",
    )


def render_watch(report: WatchReport) -> str:
    """Render `report` as plain text a human reads in fifteen seconds.
    The header is present on every call, unconditionally -- same
    discipline as `shortlist.py::render_digest()`. Every section renders
    even when empty, with one honest "none" line -- never an omitted
    section, which would look identical to "not checked."
    """
    lines = list(_REPORT_HEADER)
    lines.append("")
    lines.append(f"generated_at: {report.generated_at}    "
                 f"window: {report.window_days}d    "
                 f"total signals this run: {report.total_signals}")
    lines.append("")

    lines.append(f"-- NEW AND CLOSING SOON ({len(report.new_and_closing)}) --")
    if report.new_and_closing:
        lines.extend(_render_rows(report.new_and_closing, _fmt_closing_entry))
    else:
        lines.append("(none)")
    lines.append("")

    lines.append(f"-- CLOSING WITHIN {report.window_days} DAYS ({len(report.closing_soon)}) --")
    if report.closing_soon:
        lines.extend(_render_rows(report.closing_soon, _fmt_closing_entry))
    else:
        lines.append("(none)")
    lines.append("")

    lines.append(f"-- NEW SINCE LAST RUN ({len(report.new)}) --")
    if report.new:
        lines.extend(_render_rows(report.new, _fmt_watch_entry))
    else:
        lines.append("(none)")
    lines.append("")

    lines.append(f"-- EXPIRED, STILL IN CORPUS ({len(report.expired)}) --")
    if report.expired:
        lines.extend(_render_rows(report.expired, _fmt_watch_entry))
    else:
        lines.append("(none)")
    lines.append("")

    lines.append(f"-- UNKNOWN DEADLINE ({len(report.unknown_deadline)}) --")
    if report.unknown_deadline:
        lines.extend(_render_rows(report.unknown_deadline, _fmt_watch_entry))
    else:
        lines.append("(none)")

    return "\n".join(lines).rstrip("\n") + "\n"
