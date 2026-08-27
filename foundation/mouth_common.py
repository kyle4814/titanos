"""Shared shape extracted from two real mouths (`mouth_pypi.py`,
`mouth_github_releases.py`) after comparing them line-by-line, per the
Inspector Swarm directive's own replication test: `fetch_feed()`,
`compute_state_hash()`, `MouthObservation`, `_load_state()`, and
`observe()`'s control flow were byte-for-byte duplicated across both —
not "philosophically similar," not speculative future-proofing. This is
that duplication, extracted once, parameterized by the one thing that
was genuinely source-specific: how to parse the fetched bytes into a
tuple of `{"key": ..., ...}` dicts.

WHAT THIS IS NOT: not a source registry, not an agent framework, not a
scheduler — the existing `foundation/cron_pulse.py` cron entry remains
the only clock. A third mouth reuses this module only if its `observe()`
shape genuinely matches (fetch bytes -> parse to keyed items -> hash ->
compare -> receipt); if a future source needs a different shape (e.g. a
paginated API, not a single feed fetch), copy-and-adapt again rather
than bending this module to fit — same discipline this module itself
was built under.
"""
from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

__all__ = [
    "FetchError",
    "MouthObservation",
    "fetch_feed",
    "compute_state_hash",
    "observe",
    "MouthLogContinuity",
    "read_mouth_log_continuity",
]

DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_USER_AGENT = "titanos-cosmic-library-mouth/1 (+https://github.com/kyle4814/titanos)"

# Same cadence/threshold policy as foundation/sentinel.py's read_pulse_continuity —
# both clocks are hourly cron entries. Not shared code (different payload
# shapes: Finding vs MouthObservation/dependency-pressure records); same
# policy number, independently declared.
LOG_MAX_RECORDS = 20
LOG_STALE_AFTER_SECONDS = 3 * 3600


class FetchError(Exception):
    """The feed could not be retrieved or parsed this attempt. Bounded,
    expected, non-fatal — callers must treat this as UNAVAILABLE, never
    as 'zero items' or 'no change'."""


def fetch_feed(url: str, timeout: int = DEFAULT_TIMEOUT_SECONDS,
                user_agent: str = DEFAULT_USER_AGENT) -> bytes:
    """One GET request, real network I/O, no retry loop here — the
    caller's own schedule (cron) is the backoff policy."""
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise FetchError(f"could not fetch {url!r}: {exc}") from exc


def compute_state_hash(items: tuple[dict, ...]) -> str:
    """Deterministic hash over the item set — order-independent (keys
    sorted) so feed re-ordering alone never looks like a change."""
    canonical = sorted(item["key"] for item in items)
    payload = json.dumps(canonical, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class MouthObservation:
    mouth_id: str
    observed_at: str
    status: str  # FIRST_SEEN | UNCHANGED | CHANGED | UNAVAILABLE
    content_hash: Optional[str]
    item_count: int
    new_items: tuple[dict, ...]
    error: Optional[str] = None


def _load_state(state_path: Path) -> Optional[dict]:
    if not state_path.exists():
        return None
    try:
        return json.loads(state_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def observe(
    mouth_id: str,
    state_path: Path,
    fetch_fn: Callable[[], bytes],
    parse_fn: Callable[[bytes], tuple[dict, ...]],
    now: Optional[datetime] = None,
) -> MouthObservation:
    """Run one observation cycle: fetch, parse (source-specific), hash,
    compare, persist. `fetch_fn`/`parse_fn` are injectable so tests never
    need real network I/O. A failed fetch or parse leaves `state_path`
    untouched — the last known good baseline survives an outage."""
    observed_at = (now or datetime.now(timezone.utc)).isoformat()
    prior = _load_state(state_path)

    try:
        raw = fetch_fn()
        items = parse_fn(raw)
    except FetchError as exc:
        return MouthObservation(
            mouth_id=mouth_id, observed_at=observed_at, status="UNAVAILABLE",
            content_hash=None, item_count=0, new_items=(), error=str(exc),
        )

    content_hash = compute_state_hash(items)

    if prior is None:
        status = "FIRST_SEEN"
        new_items = items
    elif prior.get("content_hash") == content_hash:
        status = "UNCHANGED"
        new_items = ()
    else:
        status = "CHANGED"
        prior_keys = set(prior.get("keys", ()))
        new_items = tuple(i for i in items if i["key"] not in prior_keys)

    if status in ("FIRST_SEEN", "CHANGED"):
        state_path.write_text(json.dumps({
            "content_hash": content_hash,
            "keys": sorted(i["key"] for i in items),
            "observed_at": observed_at,
            "item_count": len(items),
        }))

    return MouthObservation(
        mouth_id=mouth_id, observed_at=observed_at, status=status,
        content_hash=content_hash, item_count=len(items), new_items=new_items,
    )


@dataclass(frozen=True)
class MouthLogContinuity:
    """Bounded, read-only view of a receipt log's tail — the same
    question `sentinel.read_pulse_continuity()` answers for
    `pulse_log.jsonl`, asked here for any jsonl receipt stream that
    records an `observed_at` (or `timestamp`) field per line: mouth
    observation logs, `dependency_pressure_log.jsonl`. `stale=True`
    means the clock that's supposed to write this log may have stopped
    — check is never automated into action, same as every other
    Finding-adjacent primitive in this repository."""

    available: bool
    latest_timestamp: Optional[str]
    latest_status: Optional[str]
    records_considered: int
    stale: bool
    warnings: tuple[str, ...]
    source: str


def read_mouth_log_continuity(
    log_path: Path,
    max_records: int = LOG_MAX_RECORDS,
    now: Optional[datetime] = None,
) -> MouthLogContinuity:
    """Read the tail of a jsonl receipt log and report its freshness.

    Read-only, bounded, fails soft: a missing file, an empty file, and
    malformed lines are all reported as `warnings`, never raised.
    """
    source = str(log_path)
    if not log_path.exists():
        return MouthLogContinuity(
            available=False, latest_timestamp=None, latest_status=None,
            records_considered=0,
            warnings=(f"{log_path.name} does not exist yet — this clock has never fired",),
            source=source, stale=False,
        )

    all_lines = [line for line in log_path.read_text().splitlines() if line.strip()]
    tail = all_lines[-max_records:] if max_records > 0 else []

    records: list[dict] = []
    warnings: list[str] = []
    for line in tail:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            warnings.append(f"skipped malformed JSON line: {exc}")

    if not records:
        return MouthLogContinuity(
            available=True, latest_timestamp=None, latest_status=None,
            records_considered=0,
            warnings=tuple(warnings) or ("no records in the bounded window",),
            source=source, stale=False,
        )

    latest = records[-1]
    latest_timestamp = latest.get("observed_at") or latest.get("timestamp")
    latest_status = latest.get("status")

    stale = False
    if latest_timestamp:
        try:
            parsed = datetime.fromisoformat(latest_timestamp)
        except (ValueError, TypeError):
            parsed = None
            warnings.append(f"latest timestamp {latest_timestamp!r} could not be parsed as ISO-8601")
        if parsed is not None:
            current = now if now is not None else datetime.now(timezone.utc)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            if current.tzinfo is None:
                current = current.replace(tzinfo=timezone.utc)
            age_seconds = (current - parsed).total_seconds()
            if age_seconds > LOG_STALE_AFTER_SECONDS:
                stale = True
                warnings.append(
                    f"log appears stale — last record {age_seconds / 3600:.1f}h ago "
                    f"(threshold {LOG_STALE_AFTER_SECONDS / 3600:.0f}h)"
                )

    return MouthLogContinuity(
        available=True, latest_timestamp=latest_timestamp, latest_status=latest_status,
        records_considered=len(records), warnings=tuple(warnings), source=source,
        stale=stale,
    )
