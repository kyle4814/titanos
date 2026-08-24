"""
TitanOS Epistemic Firewall — dissent preservation (§9).

WHY THIS IS PART OF THE FIREWALL AND NOT AN AFTERTHOUGHT

A contamination filter without dissent preservation degrades into a
censor. The two failure modes are mirror images:

  - too permissive: narrative acquires authority
  - too aggressive: disagreement is labelled contamination

§8 forbids the second explicitly. This module is the mechanism behind that
prohibition, because a rule with no enforcement is the F-006 shape again.

THE CORE RULE

When sources disagree, the status is DISPUTED. Not FALSE. Not RESOLVED.
Not an average.

Collapsing "A says X, B says Y" into "probably X" destroys the single most
useful record a system can keep: why it might be wrong. A system that
cannot reconstruct its own live disagreements has no defence against
intellectual capture, because capture looks exactly like consensus from
the inside.

MINORITY POSITIONS ARE NOT DELETED WHEN OUTVOTED

Resolution requires EVIDENCE, never a count. `resolve()` refuses to accept
vote tallies as grounds. A 9-1 split with no independent evidence stays
DISPUTED — nine agents restating one contaminated spec is one origin, and
counting them would reintroduce the memetic escalation the gate exists to
prevent.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Sequence

__all__ = ["Position", "DisputeRecord", "DissentRegister", "EpistemicStatus"]

EpistemicStatus = str
# DISPUTED is a legitimate terminal state, not a problem awaiting cleanup.
STATUSES = ("SUPPORTED", "DISPUTED", "REFUTED", "UNRESOLVED", "INSUFFICIENT_EVIDENCE")


@dataclass
class Position:
    """One stance in a dispute, with its own provenance."""
    position_id: str
    claim: str
    held_by: str
    root_origin: str | None = None
    evidence_refs: tuple[str, ...] = ()
    is_minority: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DisputeRecord:
    dispute_id: str
    subject: str
    status: EpistemicStatus
    positions: list[Position] = field(default_factory=list)
    resolution_evidence: tuple[str, ...] = ()
    history: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["positions"] = [p.to_dict() for p in self.positions]
        return d


class DissentRegister:
    """Append-only register of live disagreements.

    No delete surface. A dispute is closed by RESOLVING it with evidence,
    which preserves every original position — never by removing the losing
    side. The record of having been wrong is the point.
    """

    def __init__(self) -> None:
        self._disputes: dict[str, DisputeRecord] = {}

    def record(self, dispute_id: str, subject: str,
               positions: Sequence[Position]) -> DisputeRecord:
        if len(positions) < 2:
            raise ValueError(
                "a dispute requires at least two positions; one position is a "
                "claim, not a disagreement."
            )
        rec = DisputeRecord(
            dispute_id=dispute_id, subject=subject,
            status="DISPUTED", positions=list(positions),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        rec.history.append({"event": "RECORDED", "status": "DISPUTED",
                            "at": rec.created_at,
                            "position_count": len(positions)})
        self._disputes[dispute_id] = rec
        return rec

    @staticmethod
    def _distinct_origins(positions: Sequence[Position]) -> int:
        """Independence by root origin, never by headcount."""
        return len({p.root_origin or p.position_id for p in positions})

    def resolve(self, dispute_id: str, *, status: EpistemicStatus,
                evidence_refs: Sequence[str], reviewed_by: str) -> DisputeRecord:
        """Resolve a dispute — with evidence, never with a vote.

        Refuses to record SUPPORTED or REFUTED without independent
        evidence. That refusal is the whole safeguard: without it, "the
        majority of our agents agreed" silently becomes a finding.
        """
        rec = self._disputes.get(dispute_id)
        if rec is None:
            raise KeyError(f"no dispute '{dispute_id}'")
        if status not in STATUSES:
            raise ValueError(f"unknown epistemic status '{status}'")

        if status in ("SUPPORTED", "REFUTED"):
            if not evidence_refs:
                raise ValueError(
                    f"cannot mark '{dispute_id}' {status} without evidence. "
                    f"Agreement is not evidence; a count is not a finding. "
                    f"Leave it DISPUTED."
                )
            if self._distinct_origins(rec.positions) < 2:
                raise ValueError(
                    f"cannot resolve '{dispute_id}': all positions collapse to a "
                    f"single root origin. Shared ancestry cannot adjudicate itself."
                )
        if not reviewed_by:
            raise ValueError("resolution requires reviewed_by — a human closes a dispute.")

        rec.history.append({
            "event": "RESOLVED", "from": rec.status, "to": status,
            "evidence_refs": list(evidence_refs), "reviewed_by": reviewed_by,
            "at": datetime.now(timezone.utc).isoformat(),
            # Explicit: the losing positions remain in `positions`.
            "positions_preserved": len(rec.positions),
        })
        rec.status = status
        rec.resolution_evidence = tuple(evidence_refs)
        return rec

    def get(self, dispute_id: str) -> DisputeRecord | None:
        return self._disputes.get(dispute_id)

    def open_disputes(self) -> tuple[DisputeRecord, ...]:
        return tuple(r for r in self._disputes.values()
                     if r.status in ("DISPUTED", "UNRESOLVED", "INSUFFICIENT_EVIDENCE"))

    def minority_positions(self) -> tuple[Position, ...]:
        """Every minority position ever recorded, including in resolved disputes.

        Deliberately survives resolution. "We decided X and here is who
        said otherwise, and why" is a stronger record than "X".
        """
        return tuple(p for r in self._disputes.values()
                     for p in r.positions if p.is_minority)

    def export(self) -> str:
        return json.dumps([r.to_dict() for r in self._disputes.values()],
                          indent=2, sort_keys=True)
