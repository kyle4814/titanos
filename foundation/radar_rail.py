"""The missing rail between a mouth and a ranked opportunity.

WHY THIS EXISTS, AND WHY IT IS WIRING RATHER THAN INVENTION

`foundation/tentacles.py::github_issue_demand_signal()` and
`foundation/target_mapping.py` have zero production importers. Every
sweep this repository has ever run was a human pasting an ad-hoc script
into a shell -- the chain

    mouth (fetch+dedupe) -> tentacle (item -> CanonicalSignal) -> report

has never been wired end-to-end IN THE REPOSITORY. That is a bigger gap
than any missing feature: the instruments exist, are individually
tested, and have never been connected to each other by code that lives
here and can be re-run.

This module adds no new fetching, no new classification, and no new
signal shape. It calls, in order:

  1. `foundation/mouth_github_issues.py::observe()` -- fetch, dedupe
     against prior state, hand back only new items. This is the ONLY
     fetch path; see (3) below.
  2. `foundation/tentacles.py::github_issue_demand_signal()` -- turn
     each new item into a `CanonicalSignal`, exactly as it already does.
  3. A thin, LOCAL classification of *why* a non-demand signal was
     rejected, read off fields `github_issue_demand_signal()` already
     computed and placed in `evidence` (`assignees`, `author_is_bot`,
     `demand_direction`) plus the same `_HELP_WANTED` label vocabulary
     the tentacle itself gates on. This does not re-derive the verdict
     -- `pressure_class` on the signal remains the single source of
     truth for demand/no-demand -- it only names which gate the signal
     failed, for an operator who wants to know why a target was
     dropped rather than just that it was.

WHAT THIS DOES NOT DO

- Does not auto-promote a target, contact anyone, or write to a durable
  opportunity/promotion ledger. `mouth_github_issues.observe()` does
  write its own small dedupe-state file (the same file it always
  wrote before this module existed) so the next sweep can tell what is
  new; that is change-detection state, not a decision record. Nothing
  in this module calls `opportunity.rank()`, `opportunity.handoff()`,
  or any ledger writer. A `RadarSweep` is an observation report. Acting
  on it -- ranking, promoting, contacting a target -- stays a decision
  a human or an explicit downstream kernel makes by reading the
  report, never something this function does on its own.
- Does not open a second fetch path. `fetch_fn` flows straight through
  to `mouth_github_issues.observe()`, which uses it in place of its own
  default fetcher. When `fetch_fn` is None, `observe()` falls back to
  `mouth_common.fetch_feed()`, which is the one function in this
  repository that enforces `discovery_authorization.authorize_discovery()`
  before opening a socket. This module never imports `urllib` and never
  calls `authorize_discovery()` itself -- there is exactly one gate, at
  exactly the one place a socket can open, same as every other mouth.

CANNOT

- Cannot tell a genuinely empty feed apart from a malformed payload.
  `mouth_github_issues.parse_items()` already collapses unparsable JSON
  to zero items (a caught `ValueError`, not a raised one) so this
  module inherits that: a sweep over garbage bytes reports the same
  shape as a sweep over `{"items": []}` -- zero fetched, zero signals,
  no exception. That is an existing, documented limitation of the mouth
  this module composes with, not something new introduced here.
- Cannot see demand that never gets an explicit help-wanted-shaped
  label. That limitation belongs to `tentacles.github_issue_demand_signal()`
  and is unchanged here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from foundation import mouth_github_issues, tentacles
from foundation.signal_spine import CanonicalSignal

__all__ = ["RadarSweep", "sweep"]

# The exact label vocabulary `github_issue_demand_signal()` gates
# "asked for help at all" on. Read from `tentacles`, not retyped, so
# this module's rejection reasons can never silently drift from the
# verdict that actually produced `pressure_class`.
_HELP_WANTED = tentacles._HELP_WANTED


def _reject_reason(signal: CanonicalSignal) -> Optional[str]:
    """Name the one gate a NONE-class signal failed.

    Checked in the same order `github_issue_demand_signal()` ANDs its
    four conditions (asked / unassigned / not-bot / not-recruitment),
    reading the exact fields it already placed in `evidence` rather
    than re-deriving them. Returns None for an EXPLICIT_DEMAND signal
    -- there is nothing to explain away.
    """
    if signal.pressure_class != "NONE":
        return None
    evidence = signal.evidence
    labels = [str(l).lower() for l in evidence.get("labels", ())]
    asked = any(l in _HELP_WANTED for l in labels)
    if not asked:
        return "no help label"
    if evidence.get("assignees"):
        return "assigned"
    if evidence.get("author_is_bot"):
        return "bot-authored"
    if evidence.get("demand_direction") == "WORK_OFFERED":
        return "recruitment"
    # Defensive: the four checks above mirror every way
    # `github_issue_demand_signal()`'s AND can fail. Reaching here means
    # a fifth gate was added there and not mirrored here -- report it
    # honestly rather than mislabel it as one of the four known reasons.
    return "unclassified (verdict NONE, no known gate matched)"


@dataclass(frozen=True)
class RadarSweep:
    """One observation cycle, end to end -- report only, no side effect
    beyond the mouth's own dedupe-state write. See module docstring for
    exactly what this does and does not do.
    """

    status: str                                   # mouth_common's MouthObservation.status
    fetched_count: int                             # items in the raw feed this cycle
    error: Optional[str]                            # set only when status == UNAVAILABLE
    signals: tuple[CanonicalSignal, ...]            # every signal built from new items
    explicit_demand: tuple[CanonicalSignal, ...]    # signals that cleared every gate
    rejected: tuple[tuple[CanonicalSignal, str], ...]  # (signal, reason) pairs
    targets: tuple[str, ...]                        # distinct signal.target values, sorted

    def show_the_math(self) -> str:
        """Human-readable: what was fetched, what became a signal, what
        was rejected and for exactly which reason. An operator reading
        this should never have to open `evidence` by hand to learn why
        a target was dropped."""
        lines = [
            f"RADAR SWEEP status={self.status} fetched={self.fetched_count} "
            f"signals={len(self.signals)} "
            f"explicit_demand={len(self.explicit_demand)} "
            f"rejected={len(self.rejected)}"
        ]
        if self.error:
            lines.append(f"  error: {self.error}")
        reason_counts: dict[str, int] = {}
        for _signal, reason in self.rejected:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        for reason in sorted(reason_counts):
            lines.append(f"  rejected  {reason_counts[reason]:>3}  {reason}")
        if self.explicit_demand:
            lines.append(
                "  explicit demand targets: "
                + ", ".join(sorted({s.target for s in self.explicit_demand})))
        if self.targets:
            lines.append(f"  distinct targets observed: {', '.join(self.targets)}")
        return "\n".join(lines)


def sweep(state_dir: Path, per_page: int = 5,
          fetch_fn: Optional[Callable[[], bytes]] = None,
          now: Optional[datetime] = None) -> RadarSweep:
    """Run one demand-radar cycle: observe -> signal -> report.

    `state_dir` holds the mouth's own dedupe-state file (named after
    `mouth_github_issues.MOUTH_ID`), the same file the mouth has always
    written -- this function adds no second state store.

    `fetch_fn`, when given, is handed straight to
    `mouth_github_issues.observe()` and used verbatim in place of the
    real network fetch, so every test of this function runs offline on
    fixture bytes. When `fetch_fn` is None, `observe()` reaches its
    default fetcher, which goes through `mouth_common.fetch_feed()` and
    therefore through `discovery_authorization.authorize_discovery()` --
    there is no bypass path here.

    Raises whatever `mouth_github_issues.observe()` raises (notably
    `CommunicationDenied` when the gate refuses) rather than swallowing
    it -- a refused fetch is a real refusal, not an empty sweep.
    """
    state_path = Path(state_dir) / f"{mouth_github_issues.MOUTH_ID}.json"
    observation = mouth_github_issues.observe(
        state_path=state_path, per_page=per_page, fetch_fn=fetch_fn, now=now)

    signals = tuple(
        tentacles.github_issue_demand_signal(item, now=now)
        for item in observation.new_items)

    explicit_demand = tuple(
        s for s in signals if s.pressure_class == "EXPLICIT_DEMAND")
    rejected = tuple(
        (s, _reject_reason(s)) for s in signals if s.pressure_class != "EXPLICIT_DEMAND")
    targets = tuple(sorted({s.target for s in signals}))

    return RadarSweep(
        status=observation.status,
        fetched_count=observation.item_count,
        error=observation.error,
        signals=signals,
        explicit_demand=explicit_demand,
        rejected=rejected,
        targets=targets,
    )
