"""
TAAL — quarantine terminology mapping (directive §9/§15 vocabulary).

WHAT THIS FILE IS, AND WHAT IT IS NOT

The governing directive for this session describes a "quarantine
mechanism contract" using the state names QUARANTINED, REVIEWED,
RECOVERED, CONFIRMED_POLICY_VIOLATION, and CONTAINED.

This codebase already has a complete, tested, append-only quarantine
mechanism: `firewall.quarantine.QuarantineStore`, with its own explicit
`ContaminationState` vocabulary and `TRANSITIONS` table (CLEAN,
UNVERIFIED, DISPUTED, SUSPICIOUS, CONTAMINATED, QUARANTINED, VERIFIED,
AUTHORIZED, REJECTED, ARCHIVED). This file does NOT build a second store,
a second state machine, or a second set of transition rules. It is a
MAPPING — TAAL's requested vocabulary translated into the real store's
real states and real transitions — plus a thin set of named convenience
wrappers around `QuarantineStore` for callers who think in TAAL's terms.

Every correspondence below was driven through a real `QuarantineStore`
instance in taal/gate/tests/test_quarantine_mapping.py and verified
against the actual `TRANSITIONS` table, not merely asserted in a comment.

THE MAPPING

  TAAL "QUARANTINED"
      == firewall.quarantine state "QUARANTINED", same value, same store.
      Reached via `QuarantineStore.quarantine(...)`.

  TAAL "REVIEWED"
      corresponds to the QUARANTINED -> VERIFIED transition. A human
      looked at the held artifact and it checked out. In the real store
      this transition REQUIRES `reviewed_by` (see
      `QuarantineStore.transition`'s explicit check) — which is exactly
      what "reviewed" means in TAAL's vocabulary. There is no separate
      "REVIEWED" state in the real store; VERIFIED *is* TAAL's REVIEWED,
      reached specifically from QUARANTINED.

  TAAL "RECOVERED"
      corresponds to a VERIFIED record subsequently reaching AUTHORIZED,
      i.e. the VERIFIED -> AUTHORIZED edge in the real TRANSITIONS table.
      IMPORTANT: the real store's VERIFIED row is
      `{AUTHORIZED, DISPUTED, SUSPICIOUS, ARCHIVED}` — AUTHORIZED is only
      one of four legal next states from VERIFIED, not automatic. "TAAL
      recovered" therefore means "the record actually reached AUTHORIZED
      via the real store's real transition rules", not a new state this
      file invents. A VERIFIED record that instead moves to DISPUTED,
      SUSPICIOUS, or ARCHIVED has NOT been "recovered" in TAAL's sense,
      even though it passed through REVIEWED.

  TAAL "CONFIRMED_POLICY_VIOLATION"
      corresponds to the QUARANTINED -> REJECTED transition. A human
      reviewed the held artifact and it did NOT check out.

  TAAL "CONTAINED"
      corresponds to the REJECTED -> ARCHIVED transition (terminal — the
      real store's ARCHIVED row is the empty frozenset, so nothing moves
      out of CONTAINED once reached).

WHY NO "RECOVERED" OR "REVIEWED" STATE STRING APPEARS IN THE REAL STORE

Because they don't need to. The real store's states are ALREADY the
mechanism; TAAL's five names are a caller-facing gloss over four of the
real store's edges (QUARANTINED->VERIFIED, VERIFIED->AUTHORIZED,
QUARANTINED->REJECTED, REJECTED->ARCHIVED). Introducing a parallel state
string for each would be exactly the duplication this session's brief
warns against (see magl/BUILD_REPORT.md, rpa/BUILD_REPORT.md for prior
instances of this discipline in this repo).
"""

from __future__ import annotations

from typing import Mapping

from firewall.quarantine import QuarantineRecord, QuarantineStore

__all__ = [
    "TAAL_TO_REAL_TRANSITION",
    "taal_quarantine",
    "taal_mark_reviewed",
    "taal_mark_recovered",
    "taal_mark_confirmed_policy_violation",
    "taal_mark_contained",
]

# TAAL vocabulary -> (from_state, to_state) in the REAL TRANSITIONS table.
# Documentation-as-data: every pair here is exercised against the real
# store in taal/gate/tests/test_quarantine_mapping.py.
TAAL_TO_REAL_TRANSITION: Mapping[str, tuple[str, str]] = {
    "REVIEWED": ("QUARANTINED", "VERIFIED"),
    "RECOVERED": ("VERIFIED", "AUTHORIZED"),
    "CONFIRMED_POLICY_VIOLATION": ("QUARANTINED", "REJECTED"),
    "CONTAINED": ("REJECTED", "ARCHIVED"),
}


def taal_quarantine(
    store: QuarantineStore, *, artifact_id: str, content: str, reason: str,
    provenance: Mapping[str, object] | None = None,
) -> QuarantineRecord:
    """TAAL "QUARANTINED" — thin passthrough, same store, same state."""
    return store.quarantine(
        artifact_id=artifact_id, content=content, reason=reason,
        provenance=provenance,
    )


def taal_mark_reviewed(
    store: QuarantineStore, artifact_id: str, *, reason: str, reviewed_by: str,
) -> QuarantineRecord:
    """TAAL "REVIEWED" == real QUARANTINED -> VERIFIED, human-reviewed."""
    return store.transition(
        artifact_id, "VERIFIED", reason=reason, reviewed_by=reviewed_by,
    )


def taal_mark_recovered(
    store: QuarantineStore, artifact_id: str, *, reason: str, reviewed_by: str | None = None,
) -> QuarantineRecord:
    """TAAL "RECOVERED" == real VERIFIED -> AUTHORIZED.

    Requires the record to already be VERIFIED (i.e. already REVIEWED in
    TAAL's terms) — the real store enforces this by refusing any other
    source state via `can_transition`; this wrapper does not add a
    separate check because the real store's check is the enforcement.
    """
    return store.transition(
        artifact_id, "AUTHORIZED", reason=reason, reviewed_by=reviewed_by,
    )


def taal_mark_confirmed_policy_violation(
    store: QuarantineStore, artifact_id: str, *, reason: str, reviewed_by: str,
) -> QuarantineRecord:
    """TAAL "CONFIRMED_POLICY_VIOLATION" == real QUARANTINED -> REJECTED."""
    return store.transition(
        artifact_id, "REJECTED", reason=reason, reviewed_by=reviewed_by,
    )


def taal_mark_contained(
    store: QuarantineStore, artifact_id: str, *, reason: str, reviewed_by: str | None = None,
) -> QuarantineRecord:
    """TAAL "CONTAINED" == real REJECTED -> ARCHIVED (terminal)."""
    return store.transition(
        artifact_id, "ARCHIVED", reason=reason, reviewed_by=reviewed_by,
    )
