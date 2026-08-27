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

import re
from pathlib import Path
from typing import Optional

from foundation.sentinel import Finding
from foundation.mouth_common import MouthObservation

__all__ = ["evaluate_dependency_pressure"]

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
