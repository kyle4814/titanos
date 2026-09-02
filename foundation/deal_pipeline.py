"""A deal is a position with a next action, not a note in a file.

WHY THIS EXISTS
---------------
Eight autonomous cycles produced a board of researched opportunities and
zero tracked positions. Every finding landed in Markdown, which is the
right place to read them and the wrong place to work them: a document
cannot tell you that a deal has been sitting untouched for eleven days,
or that the thing you are waiting on is a reply that never came.

`opportunity.py` ranks signals. `qualification.py` decides eligibility.
`brief.py` tells you what closes soon. None of them track a deal once it
becomes real, and "becomes real" is exactly the moment the interesting
failures start.

WHAT A DEAL IS HERE
-------------------
Something with a counterparty and a next action. A tender you cannot bid
is not a deal, it is a closed question. A firm you intend to approach IS
a deal, from the moment you intend it -- because the failure mode this
module exists to catch is the approach that was never sent.

THE STAGES
----------
`IDENTIFIED`   found, not yet acted on
`APPROACHED`   contact made, awaiting response
`IN_DIALOGUE`  they replied and the conversation is live
`PROPOSED`     a specific offer with a number is on the table
`WON` / `LOST` / `PARKED`

Movement is forward-only except to LOST or PARKED. A deal cannot go from
PROPOSED back to IDENTIFIED to make a pipeline look tidier -- that is
the same class of self-deception as an unevidenced promotion in
`kpm/promotion/state_machine.py`, and it is refused for the same reason.

WHAT THIS MODULE REFUSES TO DO
------------------------------
It never invents a counterparty, a value, a date or a stage. It has no
network path and no send verb: it cannot contact anyone, and a structural
test asserts no public callable is named for an outbound action -- the
same check `sentinel.py` and `hunt_loop.py` run on themselves.

Money is `NOT_OBSERVED` until an actual number is agreed with an actual
counterparty. A quoted price is not revenue, a proposal is not revenue,
and a verbal yes is not revenue. This repository has never recorded a
dollar of income and will not start by recording an optimistic one --
`MODELLED != OBSERVED != VERIFIED != REALIZED` is enforced here rather
than restated.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple

__all__ = [
    "DealError",
    "STAGES",
    "TERMINAL_STAGES",
    "Deal",
    "DealBoard",
    "load_deals",
    "append_deal_event",
    "render_pipeline",
]


class DealError(ValueError):
    """Raised when a caller asks this module to record something it
    cannot support -- an unknown stage, a backwards transition, a deal
    with no counterparty, or revenue with no agreed number behind it."""


# Forward order. Index in this tuple IS the ordering used to refuse a
# backwards move, so the sequence is load-bearing, not documentation.
STAGES = (
    "IDENTIFIED",
    "APPROACHED",
    "IN_DIALOGUE",
    "PROPOSED",
    "WON",
)

TERMINAL_STAGES = ("WON", "LOST", "PARKED")

_ALL_STAGES = STAGES + ("LOST", "PARKED")

# The only value a deal's money field may hold before a real number is
# agreed with a real counterparty. Never 0, never "", never None -- each
# of those reads as a measured zero somewhere downstream, and this
# repository's founding rule is that UNKNOWN is not ZERO.
NOT_OBSERVED = "NOT_OBSERVED"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Deal:
    """One position. `next_action` is mandatory and non-empty for every
    non-terminal stage: a deal with no next action is not a deal being
    worked, it is a deal being forgotten, and this module's whole reason
    for existing is to make that state impossible to hold silently."""

    deal_id: str
    counterparty: str
    lane: str
    stage: str
    next_action: str
    opened_at: str
    updated_at: str
    money_observed: str = NOT_OBSERVED
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.deal_id.strip():
            raise DealError("a deal must have an id")
        if not self.counterparty.strip():
            raise DealError(
                "a deal must name its counterparty -- a position with "
                "nobody on the other side is a note, not a deal")
        if self.stage not in _ALL_STAGES:
            raise DealError(
                f"stage must be one of {_ALL_STAGES}, got {self.stage!r}")
        if self.stage not in TERMINAL_STAGES and not self.next_action.strip():
            raise DealError(
                f"a deal at stage {self.stage!r} must carry a next action -- "
                "a deal with no next action is not being worked, it is "
                "being forgotten")
        if self.money_observed != NOT_OBSERVED:
            try:
                amount = float(str(self.money_observed).split()[0])
            except (ValueError, IndexError) as exc:
                raise DealError(
                    f"money_observed must be {NOT_OBSERVED!r} or a real "
                    f"'<amount> <CURRENCY>' string, got "
                    f"{self.money_observed!r}") from exc
            if amount <= 0:
                raise DealError(
                    "observed money must be a positive agreed amount; use "
                    f"{NOT_OBSERVED!r} for anything not yet agreed")
            if self.stage != "WON":
                raise DealError(
                    f"money is only observed on a WON deal, not at stage "
                    f"{self.stage!r} -- a quote is not revenue, a proposal "
                    "is not revenue, and a verbal yes is not revenue")

    @property
    def is_terminal(self) -> bool:
        return self.stage in TERMINAL_STAGES

    def days_since_update(self, now: Optional[datetime] = None) -> Optional[int]:
        """Whole days since this deal last moved, or None if its
        timestamp cannot be read. None is honest: a deal whose age is
        unknown must not silently sort as fresh."""
        try:
            then = datetime.fromisoformat(self.updated_at)
        except (ValueError, TypeError):
            return None
        if then.tzinfo is None:
            then = then.replace(tzinfo=timezone.utc)
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        return (current.date() - then.date()).days


def _check_transition(old: str, new: str) -> None:
    if new not in _ALL_STAGES:
        raise DealError(f"unknown stage {new!r}")
    if old in TERMINAL_STAGES:
        raise DealError(
            f"a {old} deal is closed; reopening it would rewrite history. "
            "Open a new deal instead.")
    if new in ("LOST", "PARKED"):
        return
    if old not in STAGES or new not in STAGES:
        raise DealError(f"cannot move from {old!r} to {new!r}")
    if STAGES.index(new) < STAGES.index(old):
        raise DealError(
            f"cannot move a deal backwards from {old!r} to {new!r} -- "
            "a pipeline that can be walked back is a pipeline that can be "
            "made to look better than it is")


def append_deal_event(
    log_path: Path,
    *,
    deal_id: str,
    counterparty: str,
    lane: str,
    stage: str,
    next_action: str,
    money_observed: str = NOT_OBSERVED,
    notes: str = "",
    now: Optional[str] = None,
    existing: Optional[Dict[str, Deal]] = None,
) -> Deal:
    """Append one event to the durable JSONL log and return the deal.

    Durable on disk, read back fresh -- this repository documents six
    stores that call themselves append-only ledgers while holding a dict
    that dies on process exit. This is not a seventh.
    """
    log_path = Path(log_path)
    known = existing if existing is not None else load_deals(log_path)
    prior = known.get(deal_id)
    if prior is not None:
        _check_transition(prior.stage, stage)
    stamp = now or _now_iso()
    deal = Deal(
        deal_id=deal_id,
        counterparty=counterparty,
        lane=lane,
        stage=stage,
        next_action=next_action,
        opened_at=prior.opened_at if prior else stamp,
        updated_at=stamp,
        money_observed=money_observed,
        notes=notes,
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "deal_id": deal.deal_id,
            "counterparty": deal.counterparty,
            "lane": deal.lane,
            "stage": deal.stage,
            "next_action": deal.next_action,
            "opened_at": deal.opened_at,
            "updated_at": deal.updated_at,
            "money_observed": deal.money_observed,
            "notes": deal.notes,
        }, sort_keys=True) + "\n")
    return deal


def load_deals(log_path: Path) -> Dict[str, Deal]:
    """Rebuild current deal state by replaying the log from disk. Later
    events supersede earlier ones for the same id. A malformed line is
    skipped rather than raising -- one bad record must not make the whole
    pipeline unreadable -- but it is never silently treated as a deal."""
    log_path = Path(log_path)
    if not log_path.exists():
        return {}
    deals: Dict[str, Deal] = {}
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            deals[rec["deal_id"]] = Deal(
                deal_id=rec["deal_id"],
                counterparty=rec["counterparty"],
                lane=rec["lane"],
                stage=rec["stage"],
                next_action=rec["next_action"],
                opened_at=rec["opened_at"],
                updated_at=rec["updated_at"],
                money_observed=rec.get("money_observed", NOT_OBSERVED),
                notes=rec.get("notes", ""),
            )
        except (json.JSONDecodeError, KeyError, DealError):
            continue
    return deals


@dataclass(frozen=True)
class DealBoard:
    """A read-only view over current deals."""

    deals: Tuple[Deal, ...] = field(default_factory=tuple)

    @property
    def live(self) -> Tuple[Deal, ...]:
        return tuple(d for d in self.deals if not d.is_terminal)

    @property
    def won(self) -> Tuple[Deal, ...]:
        return tuple(d for d in self.deals if d.stage == "WON")

    def stale(self, days: int, now: Optional[datetime] = None) -> Tuple[Deal, ...]:
        """Live deals untouched for `days` or more, PLUS any live deal
        whose age cannot be determined. Unknown age sorts as stale, not
        as fresh -- being wrong in the direction of looking at something
        again is cheap; being wrong the other way is how a deal dies of
        silence."""
        out = []
        for d in self.live:
            age = d.days_since_update(now)
            if age is None or age >= days:
                out.append(d)
        return tuple(out)


_HEADER = (
    "=" * 72,
    "DEAL PIPELINE -- positions with a counterparty and a next action",
    "=" * 72,
    "A stage is where a conversation actually is, not where it might go.",
    "Money reads NOT_OBSERVED until a real number is agreed with a real",
    "counterparty: a quote is not revenue, a proposal is not revenue, and",
    "a verbal yes is not revenue.",
    "",
)


def render_pipeline(board: DealBoard, *, stale_after_days: int = 7,
                    now: Optional[datetime] = None) -> str:
    """Render the board, stalest first, because the deal most likely to
    die is the one nobody has touched."""
    if not isinstance(board, DealBoard):
        raise DealError(f"expected a DealBoard, got {type(board).__name__}")
    lines = list(_HEADER)
    live = board.live
    if not live:
        lines.append("No live deals. That is a real state, not an error --")
        lines.append("but it is also the one this pipeline exists to change.")
        return "\n".join(lines)

    stale = set(d.deal_id for d in board.stale(stale_after_days, now))
    ordered = sorted(
        live,
        key=lambda d: (
            0 if d.deal_id in stale else 1,
            -(d.days_since_update(now) if d.days_since_update(now) is not None
              else 10 ** 6),
            d.deal_id,
        ),
    )
    for d in ordered:
        age = d.days_since_update(now)
        age_text = "UNKNOWN" if age is None else f"{age}d"
        flag = "  <-- STALE" if d.deal_id in stale else ""
        lines.append("-" * 72)
        lines.append(f"[{d.stage}] {d.counterparty}{flag}")
        lines.append(f"  lane        : {d.lane}")
        lines.append(f"  last moved  : {age_text} ago")
        lines.append(f"  NEXT ACTION : {d.next_action}")
        if d.notes:
            lines.append(f"  notes       : {d.notes[:150]}")
    won = board.won
    lines.append("-" * 72)
    lines.append(f"live: {len(live)}   won: {len(won)}   "
                 f"stale (>= {stale_after_days}d): {len(stale)}")
    if not won:
        lines.append("No deal has been won. Recorded plainly rather than "
                     "omitted.")
    return "\n".join(lines)
