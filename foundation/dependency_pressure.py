"""Convert a real mouth's CHANGED observation into a bounded, evidenced
dependency-pressure finding for this repository's own requirements.txt.

THE REAL GAP THIS CLOSES

`foundation/tests/test_requirements_manifest.py` already proves
`requirements.txt`'s pin matches what's actually installed
(`yaml.__version__`). Two real mouths (`mouth_pypi.py`,
`mouth_github_releases.py`) already detect when PyYAML ships a new
release, external to this repository. Neither is connected to the
other: a CHANGED observation is logged to a receipt file and nothing
compares it against what this repository has actually pinned. Whoever
reads the mouth log has to manually re-derive "does this matter to us"
every time — that's the concrete missing information this module
supplies, nothing more.

WHAT THIS DOES NOT DO

No vulnerability database, no CVE lookup, no risk scoring, no
auto-update, no PR generation, no network call of its own (it consumes
an already-fetched `MouthObservation`, never fetches). It answers
exactly one bounded question: is the pinned version behind, equal to,
or ahead of the newest version a real mouth just observed — and if the
comparison can't be made honestly, it says so instead of guessing.

Reuses `foundation.sentinel.Finding` (finding != authorization, same
rule as every other Sentinel finding) rather than inventing a second
finding type — `evaluate_dependency_pressure()` is READ-ONLY, touches
no files, and the returned `Finding.recommended_next_action` is always
advisory (`HUMAN_REVIEW_REQUIRED` or `NONE_REQUIRED`), never an action
verb — same discipline `TestSentinelCannotExecute` already enforces on
`sentinel.py` itself.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from foundation.sentinel import Finding, consolidate
from foundation.mouth_common import (
    LOG_MAX_RECORDS,
    LOG_STALE_AFTER_SECONDS,
    MouthObservation,
)

__all__ = [
    "evaluate_dependency_pressure",
    "DependencyPressureContinuity",
    "read_dependency_pressure_log",
]

# Same shape as foundation/tests/test_requirements_manifest.py's own
# _PIN_PATTERN — reused, not reinvented.
_PIN_PATTERN = re.compile(r"^([A-Za-z0-9_.-]+)==([A-Za-z0-9_.-]+)$")


def _read_pinned_version(requirements_path: Path, package_name: str) -> Optional[str]:
    if not requirements_path.exists():
        return None
    for line in requirements_path.read_text().splitlines():
        line = line.strip()
        match = _PIN_PATTERN.match(line)
        if match and match.group(1).lower() == package_name.lower():
            return match.group(2)
    return None


def _parse_dotted_version(version: str) -> Optional[tuple[int, ...]]:
    """Parse a leading dotted-numeric prefix (e.g. '6.0.3' out of
    '6.0.3' or '6.0.3rc1'). Returns None for anything that doesn't start
    with a numeric dotted sequence — fail closed, never guess."""
    match = re.match(r"^(\d+(?:\.\d+)*)", version.strip())
    if not match:
        return None
    return tuple(int(part) for part in match.group(1).split("."))


def evaluate_dependency_pressure(
    observation: MouthObservation,
    requirements_path: Path,
    package_name: str,
) -> Optional[Finding]:
    """Return a Finding iff `observation` is a real CHANGED event with at
    least one new item — UNCHANGED/FIRST_SEEN/UNAVAILABLE carry no new
    evidence, so they return None (no finding, not a suppressed one)."""
    if observation.status != "CHANGED" or not observation.new_items:
        return None

    pinned = _read_pinned_version(requirements_path, package_name)
    newest_title = observation.new_items[0].get("title", "")

    if pinned is None:
        return Finding(
            observation=(
                f"{package_name} is not pinned in {requirements_path.name}, "
                f"but mouth {observation.mouth_id!r} observed a real release "
                f"change ({newest_title!r})"
            ),
            evidence_location=str(requirements_path),
            confidence="HIGH",
            interpretation="dependency pressure cannot be evaluated against an undeclared package",
            reversibility="reversible — informational finding only, nothing executed",
            recommended_next_action="HUMAN_REVIEW_REQUIRED: confirm whether this package should be declared",
        )

    pinned_tuple = _parse_dotted_version(pinned)
    newest_tuple = _parse_dotted_version(newest_title)

    if pinned_tuple is None or newest_tuple is None:
        return Finding(
            observation=f"{package_name}: pinned={pinned!r}, newest observed={newest_title!r}",
            evidence_location=str(requirements_path),
            confidence="LOW",
            interpretation="one or both versions are not a plain dotted-numeric string — comparison is ambiguous, not guessed",
            reversibility="reversible — informational finding only, nothing executed",
            recommended_next_action="HUMAN_REVIEW_REQUIRED: manually compare the two version strings",
        )

    if newest_tuple > pinned_tuple:
        return Finding(
            observation=f"{package_name} {newest_title} is newer than the pinned {pinned}",
            evidence_location=str(requirements_path),
            confidence="HIGH",
            interpretation=(
                f"mouth {observation.mouth_id!r} observed a real release not yet "
                f"reflected in {requirements_path.name}"
            ),
            reversibility="reversible — informational finding only, nothing executed",
            recommended_next_action="HUMAN_REVIEW_REQUIRED: decide whether to update the pin",
        )
    if newest_tuple == pinned_tuple:
        return Finding(
            observation=f"{package_name} is already pinned to the newest observed release ({pinned})",
            evidence_location=str(requirements_path),
            confidence="HIGH",
            interpretation="no dependency pressure — the mouth's change was a metadata update, not a version we're behind on",
            reversibility="reversible — informational finding only, nothing executed",
            recommended_next_action="NONE_REQUIRED",
        )
    return Finding(
        observation=f"{package_name}: observed {newest_title} is older than the pinned {pinned}",
        evidence_location=str(requirements_path),
        confidence="MEDIUM",
        interpretation=(
            "unexpected: the mouth reported CHANGED with a new item, but the "
            "observed version is not newer than what's pinned — possibly a "
            "yanked/re-published release or a feed ordering quirk, not "
            "silently treated as pressure"
        ),
        reversibility="reversible — informational finding only, nothing executed",
        recommended_next_action="HUMAN_REVIEW_REQUIRED: investigate why an older-looking release triggered CHANGED",
    )


# --------------------------------------------------------------------------
# READING BACK WHAT THIS MODULE WROTE
#
# THE EXACT OPEN EDGE THIS CLOSES (traced 2026-08-28, reproduced before
# being closed): `foundation/cron_pulse.py` appends every Finding this
# module returns to `foundation/dependency_pressure_log.jsonl` -- a real,
# live, hourly producer. `.claude/commands/boot.md` step 4c names that
# exact file as something a session must check every boot, via
# `mouth_common.read_mouth_log_continuity()`. But a dependency-pressure
# record is a `Finding` payload, not a `MouthObservation`: it has no
# `status` field, so that reader returns `latest_status=None` for every
# record it will ever see. Directly reproduced against a real-shaped
# record: available=True, latest_timestamp correct, latest_status=None --
# the clock is legibly alive, and the finding it wrote is invisible.
#
# So the one actionable output this whole mouth -> pressure pipeline
# exists to produce had no reader that could hand it back. This module's
# own opening docstring says the gap it closes is that "whoever reads the
# mouth log has to manually re-derive 'does this matter to us' every
# time" -- and then the answer could only be reached by hand-reading a
# jsonl file, which is the same manual step one layer down.
#
# `read_mouth_log_continuity()` is not wrong and is not replaced: it
# answers "is this clock still writing," correctly, for any receipt log.
# This answers the separate question "and what did it say," for this log
# only. Same split, and the same deliberate not-shared-code decision,
# already made once between `sentinel.read_pulse_continuity()` and
# `mouth_common.read_mouth_log_continuity()`.
#
# Read-only, bounded, fail-soft -- identical discipline to both existing
# readers. Reuses `Finding` (the literal payload written) and
# `sentinel.consolidate()` (the existing dedup: same observation at same
# location collapses to one) rather than inventing either.
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class DependencyPressureContinuity:
    """Bounded, read-only view of `dependency_pressure_log.jsonl`'s tail.

    A non-empty `findings` is evidence to look at, never authorization --
    the same `finding != authorization` rule every other Finding in this
    repository carries. `actionable` is a convenience derived from the
    findings themselves, not a second source of truth: it is True iff at
    least one retained finding's `recommended_next_action` is anything
    other than `NONE_REQUIRED`.

    `available=False` means the log has never been written -- no
    dependency pressure has ever fired, which is the normal state, not a
    fault. `stale=True` only ever means the log exists and its newest
    record is older than `LOG_STALE_AFTER_SECONDS`; because this log is
    written only on a CHANGED observation (not every tick), staleness
    here is far weaker evidence of a stopped clock than it is for
    `pulse_log.jsonl` -- check the mouth logs for that.
    """

    available: bool
    latest_timestamp: Optional[str]
    records_considered: int
    findings: tuple[Finding, ...]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    source: str
    stale: bool = False

    @property
    def actionable(self) -> bool:
        return any(f.recommended_next_action != "NONE_REQUIRED" for f in self.findings)


def read_dependency_pressure_log(
    log_path: Path,
    max_records: int = LOG_MAX_RECORDS,
    now: Optional[datetime] = None,
) -> DependencyPressureContinuity:
    """Reconstruct the Findings `cron_pulse.py` wrote to this log.

    Never writes, truncates, or rotates. Bounded to the trailing
    `max_records` lines regardless of file size. Fails soft at every
    layer: a missing file, an empty file, a malformed JSON line, and a
    record whose payload is not a valid Finding are all reported, never
    raised -- a boot sequence must not fail because a receipt line got
    truncated mid-write.

    `cron_pulse.py` writes two distinct record shapes to this same log:
    a Finding payload, and an `{"error": ...}` record when
    `evaluate_dependency_pressure()` itself raised. The second shape is
    surfaced separately as `errors` rather than being silently dropped
    or mistaken for a finding -- an evaluation that crashed is not the
    same state as an evaluation that found nothing.
    """
    source = str(log_path)
    if not log_path.exists():
        return DependencyPressureContinuity(
            available=False, latest_timestamp=None, records_considered=0,
            findings=(), errors=(),
            warnings=(
                f"{log_path.name} does not exist yet -- no dependency "
                f"pressure has ever fired (the normal state, not a fault)",
            ),
            source=source,
        )

    all_lines = [line for line in log_path.read_text().splitlines() if line.strip()]
    tail = all_lines[-max_records:] if max_records > 0 else []

    records: list[dict] = []
    warnings: list[str] = []
    for line in tail:
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            warnings.append(f"skipped malformed JSON line: {exc}")
            continue
        # Same fix as sentinel.py::read_pulse_continuity() and
        # mouth_common.py::read_mouth_log_continuity() -- a valid-JSON
        # non-dict line crashed the "error" in rec / rec.items() logic
        # below with TypeError. Found by systemic hunt 2026-08-28.
        if not isinstance(obj, dict):
            warnings.append(f"skipped non-record JSON line (not an object): {obj!r}"[:200])
            continue
        records.append(obj)

    if not records:
        return DependencyPressureContinuity(
            available=True, latest_timestamp=None, records_considered=0,
            findings=(), errors=(),
            warnings=tuple(warnings) or ("no records in the bounded window",),
            source=source,
        )

    findings: list[Finding] = []
    errors: list[str] = []
    for rec in records:
        if "error" in rec:
            errors.append(
                f"{rec.get('observed_at', 'unknown time')} "
                f"[{rec.get('mouth_id', 'unknown mouth')}]: {rec['error']}"
            )
            continue
        payload = {k: v for k, v in rec.items() if k not in ("mouth_id", "observed_at")}
        try:
            findings.append(Finding(**payload))
        except (TypeError, ValueError) as exc:
            warnings.append(f"skipped malformed finding payload: {exc}")

    latest_timestamp = records[-1].get("observed_at") or records[-1].get("timestamp")

    stale = False
    if latest_timestamp:
        try:
            parsed = datetime.fromisoformat(latest_timestamp)
        except (ValueError, TypeError):
            parsed = None
            warnings.append(
                f"latest timestamp {latest_timestamp!r} could not be parsed as ISO-8601"
            )
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
                    f"newest dependency-pressure record is {age_seconds / 3600:.1f}h "
                    f"old (threshold {LOG_STALE_AFTER_SECONDS / 3600:.0f}h) -- note "
                    f"this log is written only on a CHANGED observation, so age "
                    f"here is weak evidence about the clock; check the mouth logs"
                )

    return DependencyPressureContinuity(
        available=True,
        latest_timestamp=latest_timestamp,
        records_considered=len(records),
        findings=consolidate(findings),
        errors=tuple(errors),
        warnings=tuple(warnings),
        source=source,
        stale=stale,
    )
