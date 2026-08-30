"""The radar's artifact: where to look next, and nothing stronger.

WHY THIS IS NOT A `Receipt`

`Receipt` answers "what did this investigation establish about a target".
An opportunity answers "why is looking here next justified". Teaching
`Receipt` to carry the second would let a target search wear the clothes
of a finding, which is the precise confusion this project keeps having to
correct. So this is a separate type whose central field is a refusal:

    bug_claim() -> "NONE"    always, structurally, with no setter.

The radar lights up the map. It does not invent the treasure.

FOUR ECONOMIC FACTS THAT ARE NOT THE SAME FACT

    advertised    a number on a page. Says nothing about us.
    eligibility   whether we could claim it. Usually UNKNOWN.
    expected      what we would actually reckon on. Almost never the
                  advertised figure.
    paid          money received. Requires evidence, not optimism.

A displayed maximum reward is not revenue. `reward_advertised` is stored
as free text precisely so it cannot be arithmetic'd into a forecast.

SOURCE AUTHORITY IS NOT PROXIMITY

A search snippet claiming a bounty is a lead. An official programme page
is evidence. `VERIFIED_CURRENT` requires a PRIMARY or OFFICIAL source and
is refused otherwise — a third-party mention cannot be promoted by
enthusiasm.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

__all__ = [
    "SOURCE_TYPES",
    "AUTHORITATIVE_SOURCES",
    "REWARD_STATES",
    "ACTIVITY_CLASSES",
    "QUEUE_STATES",
    "RECOMMENDATIONS",
    "HARD_DISQUALIFIERS",
    "OpportunityIntegrityError",
    "SignalEvidence",
    "OpportunityReceipt",
    "rank",
]

SOURCE_TYPES = ("PRIMARY", "OFFICIAL", "PLATFORM", "PROJECT_MAINTAINED",
                "THIRD_PARTY", "COMMUNITY", "UNVERIFIED")

# Only these may support a VERIFIED_CURRENT reward claim.
AUTHORITATIVE_SOURCES = ("PRIMARY", "OFFICIAL")

REWARD_STATES = ("NOT_PRESENT", "POSSIBLE", "OBSERVED", "VERIFIED_CURRENT",
                 "CONDITIONAL", "ELIGIBILITY_UNKNOWN", "EXPIRED", "PAID",
                 "WITHDRAWN", "AMBIGUOUS")

ACTIVITY_CLASSES = ("DORMANT", "LOW", "ACTIVE", "HIGHLY_ACTIVE", "UNKNOWN")

QUEUE_STATES = ("DISCOVERED", "OBSERVED", "VERIFIED_CURRENT", "SCORED",
                "WATCH", "RECHECK_REQUIRED", "READY_FOR_INVESTIGATION",
                "CLAIMED", "INVESTIGATING", "DISCARDED", "WITHHELD",
                "QUALIFIED", "ROUTED", "RETIRED")

RECOMMENDATIONS = ("IGNORE", "WATCH", "RECHECK", "INVESTIGATE",
                   "HUMAN_REVIEW_REQUIRED", "WITHHOLD")

# Conditions no score may outrank. A large advertised number is not a
# reason to walk through a door that is shut.
HARD_DISQUALIFIERS = ("SECURITY_SENSITIVE", "OUT_OF_SCOPE",
                      "REQUIRES_SECRETS", "REQUIRES_LIVE_INFRA",
                      "CONTRIBUTION_FORBIDDEN")

# How long an observation stays current before it must be re-checked.
# A policy default, not a measurement: upstream moves, issues close, and
# programmes change. Short enough that a stale lead cannot stay hot.
FRESHNESS_WINDOW = timedelta(days=7)


class OpportunityIntegrityError(ValueError):
    """An opportunity claimed more than its sources support."""


@dataclass(frozen=True)
class SignalEvidence:
    """One observed fact plus where it came from.

    `detail` is what was actually seen. `source_type` decides how much
    weight it may carry, and nothing upgrades it later.
    """

    kind: str            # e.g. ACTIVITY, DEMAND, REWARD, CODE_PRESSURE
    detail: str
    source_type: str
    source_ref: str = ""

    def __post_init__(self) -> None:
        if self.source_type not in SOURCE_TYPES:
            raise OpportunityIntegrityError(
                f"unknown source type {self.source_type!r}")
        if not self.detail.strip():
            raise OpportunityIntegrityError("a signal must state what was seen")

    def is_authoritative(self) -> bool:
        return self.source_type in AUTHORITATIVE_SOURCES


@dataclass(frozen=True)
class OpportunityReceipt:
    """Why looking here next is justified. Never what is wrong there."""

    opportunity_id: str
    target: str
    discovered_at: str
    signals: tuple[SignalEvidence, ...]
    activity_class: str = "UNKNOWN"
    reward_state: str = "NOT_PRESENT"
    reward_advertised: str = ""        # free text on purpose: not arithmetic
    reward_eligibility: str = "UNKNOWN"
    locally_reproducible: str = "UNKNOWN"
    disqualifiers: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    queue_state: str = "DISCOVERED"
    observed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        if self.activity_class not in ACTIVITY_CLASSES:
            raise OpportunityIntegrityError(
                f"unknown activity class {self.activity_class!r}")
        if self.reward_state not in REWARD_STATES:
            raise OpportunityIntegrityError(
                f"unknown reward state {self.reward_state!r}")
        if self.queue_state not in QUEUE_STATES:
            raise OpportunityIntegrityError(
                f"unknown queue state {self.queue_state!r}")

        # A reward is only VERIFIED_CURRENT on an authoritative source. A
        # search snippet saying "$50,000 BOUNTY" is a lead, not a fact.
        if self.reward_state == "VERIFIED_CURRENT":
            rewards = [s for s in self.signals if s.kind == "REWARD"]
            if not rewards or not any(s.is_authoritative() for s in rewards):
                raise OpportunityIntegrityError(
                    "reward VERIFIED_CURRENT requires a PRIMARY or OFFICIAL "
                    "source; a third-party mention is a lead, not evidence")

        # An advertised figure without an eligibility answer must say so.
        if self.reward_advertised.strip() and self.reward_eligibility == "":
            raise OpportunityIntegrityError(
                "an advertised reward must carry an eligibility state, even "
                "if that state is UNKNOWN")

    def bug_claim(self) -> str:
        """Load-bearing. The radar never claims a defect."""
        return "NONE"

    def reward_expected(self) -> str:
        """Never derived from the advertised figure.

        Expected value requires eligibility, and eligibility is almost
        always UNKNOWN at discovery time. Returning the advertised number
        here is how a listing becomes a forecast.
        """
        if self.reward_state == "PAID":
            return self.reward_advertised or "PAID_AMOUNT_UNRECORDED"
        if self.reward_eligibility == "CONFIRMED":
            return "SEE_PROGRAMME_TERMS"
        return "NOT_MEASURED"

    def is_stale(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now(timezone.utc)
        try:
            seen = datetime.fromisoformat(self.observed_at)
        except (ValueError, TypeError):
            return True
        if seen.tzinfo is None:
            seen = seen.replace(tzinfo=timezone.utc)
        return (now - seen) > FRESHNESS_WINDOW

    def blocking_disqualifiers(self) -> tuple[str, ...]:
        return tuple(d for d in self.disqualifiers if d in HARD_DISQUALIFIERS)


@dataclass(frozen=True)
class Ranking:
    recommendation: str
    inputs: tuple[str, ...]      # every reason, in words
    priority: int                # queue order only, never a truth claim

    def explanation(self) -> str:
        return "\n".join(f"  - {line}" for line in self.inputs)


def rank(opportunity: OpportunityReceipt,
         now: Optional[datetime] = None) -> Ranking:
    """Explainable ranking. Every input is stated, never just a number.

    Order matters: disqualifiers and staleness are checked BEFORE any
    value signal is counted, so a large advertised reward cannot buy its
    way past a shut door.
    """
    inputs: list[str] = []

    blocking = opportunity.blocking_disqualifiers()
    if blocking:
        inputs.append(f"hard disqualifier(s): {', '.join(blocking)}")
        rec = ("HUMAN_REVIEW_REQUIRED" if "SECURITY_SENSITIVE" in blocking
               else "WITHHOLD")
        inputs.append("no score may outrank a disqualifier")
        return Ranking(rec, tuple(inputs), priority=0)

    if opportunity.is_stale(now):
        inputs.append("observation older than the freshness window")
        return Ranking("RECHECK", tuple(inputs), priority=0)

    priority = 0
    if opportunity.activity_class in ("ACTIVE", "HIGHLY_ACTIVE"):
        priority += 2
        inputs.append(f"target activity: {opportunity.activity_class}")
    elif opportunity.activity_class == "DORMANT":
        inputs.append("target dormant: a corpse with stars is not a target")
        return Ranking("IGNORE", tuple(inputs), priority=0)
    else:
        inputs.append(f"target activity: {opportunity.activity_class}")

    if any(s.kind == "DEMAND" for s in opportunity.signals):
        priority += 2
        inputs.append("explicit demand observed (maintainer or issue request)")

    if any(s.kind == "CODE_PRESSURE" for s in opportunity.signals):
        priority += 2
        inputs.append("measurable code pressure observed")

    if opportunity.reward_state in ("OBSERVED", "VERIFIED_CURRENT"):
        priority += 1
        inputs.append(
            f"reward {opportunity.reward_state}; eligibility "
            f"{opportunity.reward_eligibility}; expected "
            f"{opportunity.reward_expected()}")

    if opportunity.locally_reproducible == "YES":
        priority += 2
        inputs.append("work is locally reproducible")
    elif opportunity.locally_reproducible == "NO":
        priority -= 2
        inputs.append("not locally reproducible: investigation cost is high")

    if opportunity.unknowns:
        inputs.append(f"{len(opportunity.unknowns)} unknown(s) recorded, "
                      f"not papered over")

    rec = "INVESTIGATE" if priority >= 5 else "WATCH" if priority >= 2 else "IGNORE"
    inputs.append(f"priority {priority} -> {rec} (queue order, not a verdict)")
    return Ranking(rec, tuple(inputs), priority=priority)


def opportunity_id_for(target: str, handle: str) -> str:
    """Stable identity so the queue cannot hold the same lead twice."""
    raw = f"{target.strip().lower()}|{handle.strip().lower()}"
    return "OPP-" + hashlib.sha256(raw.encode()).hexdigest()[:16]
