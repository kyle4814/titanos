"""
KPM — contradiction registry (§9 sibling: contradictions across claims).

WHY THIS IS A SEPARATE REGISTER FROM DISSENT

firewall/dissent.py records live disagreement between *positions held by
sources*: A says X, B says Y, and the register exists to stop that
tension from being silently averaged into "probably X". A contradiction,
as recorded here, is a stronger and more structural claim: two or more
blueprints or claims that CANNOT BOTH BE TRUE — not a difference of
opinion, but a logical collision, however it was found (a human noticing
it, or an automated scanner flagging it; this module does not care which,
it only cares that the finding is preserved once made).

Conflating the two would blur an important distinction: a dispute can be
resolved by producing better evidence for one side, and the other side
was still a reasonable position to have held. A contradiction, once
verified, means at least one of the involved claims is simply wrong — but
until it is resolved, this registry does not adjudicate which one, and it
never discards the losing side's identity once it does.

THE SAME EVIDENCE-GATING DISCIPLINE AS dissent.py

`resolve()` refuses to close a contradiction as RESOLVED without
`evidence_refs`. A contradiction "resolved" on say-so is just an assertion
wearing a status field; the whole point of tracking contradictions
structurally is that they get closed the way disputes do — by evidence a
reviewer can point to, never by a vote or a shrug. WONT_FIX is the one
status this module accepts without asserting a factual finding (someone
decided not to pursue it), but it still requires a reason and a named
resolver, because an unexplained WONT_FIX is indistinguishable from
neglect.

INVOLVED_IDS SURVIVE RESOLUTION

Resolving a contradiction does not shrink `involved_ids`. The record of
which claims were in tension is exactly as valuable after resolution as
before — it is the audit trail that lets a future reviewer ask "wait, was
this ever actually checked against Y?" and get a real answer, mirroring
dissent.py's refusal to delete minority positions once a dispute closes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Sequence

__all__ = ["ContradictionRecord", "ContradictionRegistry", "ContradictionStatus"]

ContradictionStatus = str
STATUSES = ("OPEN", "RESOLVED", "WONT_FIX")


@dataclass
class ContradictionRecord:
    contradiction_id: str
    description: str
    involved_ids: tuple[str, ...]
    status: ContradictionStatus = "OPEN"
    resolution: dict[str, Any] | None = None
    history: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ContradictionRegistry:
    """Append-only register of found contradictions.

    No delete surface — no `delete`, `purge`, `clear` or `remove` method
    exists on this class. A contradiction is closed by resolving it (with
    evidence, or an explicit WONT_FIX with a reason), never by removing
    the finding.
    """

    def __init__(self) -> None:
        self._contradictions: dict[str, ContradictionRecord] = {}

    def record(self, contradiction_id: str, description: str,
               involved_ids: Sequence[str]) -> ContradictionRecord:
        if contradiction_id in self._contradictions:
            raise ValueError(f"contradiction '{contradiction_id}' already recorded")
        if len(involved_ids) < 2:
            # Mirrors dissent.py's test_single_position_is_not_a_dispute:
            # a "contradiction" with one party isn't a contradiction, it's
            # just a claim.
            raise ValueError(
                "a contradiction requires at least two involved_ids; one "
                "claim cannot contradict itself."
            )
        if not description.strip():
            raise ValueError(
                "a contradiction requires a description. An unexplained "
                "flag cannot be reviewed."
            )
        now = datetime.now(timezone.utc).isoformat()
        rec = ContradictionRecord(
            contradiction_id=contradiction_id,
            description=description,
            involved_ids=tuple(involved_ids),
            status="OPEN",
            created_at=now,
        )
        rec.history.append({"event": "RECORDED", "status": "OPEN", "at": now,
                            "involved_ids": list(rec.involved_ids)})
        self._contradictions[contradiction_id] = rec
        return rec

    def resolve(
        self, contradiction_id: str, resolution_reason: str, *,
        evidence_refs: Sequence[str], resolved_by: str,
        final_status: ContradictionStatus = "RESOLVED",
    ) -> ContradictionRecord:
        """Close a contradiction — with evidence, never with a vote or a shrug.

        RESOLVED requires non-empty `evidence_refs`. WONT_FIX does not
        require evidence (there is no finding being asserted), but still
        requires a non-empty `resolution_reason` and a named `resolved_by`
        — an unexplained WONT_FIX is indistinguishable from neglect.
        """
        rec = self._contradictions.get(contradiction_id)
        if rec is None:
            raise KeyError(f"no contradiction '{contradiction_id}'")
        if final_status not in STATUSES or final_status == "OPEN":
            raise ValueError(f"cannot resolve to status '{final_status}'")
        if not resolution_reason.strip():
            raise ValueError("resolution requires a non-empty resolution_reason")
        if not resolved_by:
            raise ValueError("resolution requires resolved_by — a human closes a contradiction")

        if final_status == "RESOLVED" and not evidence_refs:
            raise ValueError(
                f"cannot mark '{contradiction_id}' RESOLVED without evidence. "
                f"A stated reason is not evidence; leave it OPEN or use "
                f"final_status='WONT_FIX' if it will not be pursued."
            )

        resolution = {
            "reason": resolution_reason,
            "evidence_refs": tuple(evidence_refs),
            "resolved_by": resolved_by,
        }
        rec.history.append({
            "event": "RESOLVED", "from": rec.status, "to": final_status,
            "reason": resolution_reason, "evidence_refs": list(evidence_refs),
            "resolved_by": resolved_by,
            "at": datetime.now(timezone.utc).isoformat(),
            # Explicit: involved_ids are unchanged by resolution.
            "involved_ids_preserved": list(rec.involved_ids),
        })
        rec.status = final_status
        rec.resolution = resolution
        return rec

    def get(self, contradiction_id: str) -> ContradictionRecord | None:
        return self._contradictions.get(contradiction_id)

    def open_contradictions(self) -> tuple[ContradictionRecord, ...]:
        return tuple(r for r in self._contradictions.values() if r.status == "OPEN")

    def export(self) -> str:
        return json.dumps([r.to_dict() for r in self._contradictions.values()],
                          indent=2, sort_keys=True)
