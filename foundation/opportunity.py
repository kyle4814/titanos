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
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from types import MappingProxyType
from typing import Any, Mapping, Optional

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
    "CeilingAnalysis",
    "ceiling_analysis",
    "SCORING_LEVERS",
    "INVESTIGATE_THRESHOLD",
    "PowerProfile",
    "power_profile",
    "controlling_party",
    "InvestigationMission",
    "HandoffRefused",
    "handoff",
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
    # Carried verbatim from `signal_spine.CanonicalSignal.evidence` when a
    # signal originates there (e.g. `author_login`, set by
    # `tentacles.py` for DEMAND signals). Not required, not validated for
    # shape beyond being a mapping -- this is provenance passed through,
    # not a new claim this module makes on its own authority.
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.source_type not in SOURCE_TYPES:
            raise OpportunityIntegrityError(
                f"unknown source type {self.source_type!r}")
        if not self.detail.strip():
            raise OpportunityIntegrityError("a signal must state what was seen")
        # Freeze so a caller cannot mutate evidence after construction and
        # have `controlling_party()` see something different than what
        # was reasoned about when the signal was admitted.
        object.__setattr__(self, "evidence",
                           MappingProxyType(dict(self.evidence)))

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

    rec = ("INVESTIGATE" if priority >= INVESTIGATE_THRESHOLD
           else "WATCH" if priority >= 2 else "IGNORE")
    inputs.append(f"priority {priority} -> {rec} (queue order, not a verdict)")

    # Diagnosis, not tuning: no weight and no threshold changes here. If the
    # only levers left are ones no instrument can supply, say so, because
    # "WATCH because weak" and "WATCH because impossible" are opposite facts
    # that previously looked identical.
    if rec != "INVESTIGATE":
        unavailable = []
        if not any(s.kind == "CODE_PRESSURE" for s in opportunity.signals):
            unavailable.append("CODE_PRESSURE (no instrument emits it)")
        if opportunity.locally_reproducible == "UNKNOWN":
            unavailable.append("local reproducibility (never measured)")
        if opportunity.reward_state not in ("OBSERVED", "VERIFIED_CURRENT",
                                            "PAID"):
            unavailable.append("reward (no money instrument)")
        headroom = INVESTIGATE_THRESHOLD - priority
        if unavailable and headroom > 0:
            inputs.append(
                f"needs {headroom} more point(s); the only remaining levers "
                f"are unavailable to this system: {'; '.join(unavailable)}")

    return Ranking(rec, tuple(inputs), priority=priority)


# What each remaining scoring lever needs, and what would have to exist to
# supply it. Written down because a target that cannot reach INVESTIGATE
# should say WHY, rather than reading as merely weak.
SCORING_LEVERS = {
    "CODE_PRESSURE": (
        2, "a signal of kind CODE_PRESSURE",
        "no live instrument emits this kind; the mouths emit DEMAND, "
        "ACTIVITY and RELEASE"),
    "LOCAL_REPRODUCIBILITY": (
        2, "locally_reproducible == 'YES'",
        "nothing measures reproducibility; the radar always sets UNKNOWN"),
    "REWARD": (
        1, "reward_state OBSERVED or VERIFIED_CURRENT",
        "no money instrument exists, deliberately"),
}

INVESTIGATE_THRESHOLD = 5


@dataclass(frozen=True)
class CeilingAnalysis:
    """Whether this target could reach INVESTIGATE at all, and what stops it.

    A ranking of WATCH is ambiguous: it can mean "weak target" or it can
    mean "no combination of available evidence could ever score higher".
    Those are opposite facts and were previously indistinguishable.
    """

    achieved: int
    reachable_ceiling: int
    threshold: int
    blocked_by: tuple[tuple[str, str], ...]   # (lever, why it is unavailable)

    def is_structurally_capped(self) -> bool:
        """True when the threshold cannot be reached by any evidence the
        system can currently produce -- not merely not reached yet."""
        return self.reachable_ceiling < self.threshold

    def explain(self) -> str:
        if not self.is_structurally_capped():
            return (f"ceiling {self.reachable_ceiling} >= threshold "
                    f"{self.threshold}: INVESTIGATE is reachable")
        lines = [f"STRUCTURAL CEILING: max achievable priority is "
                 f"{self.reachable_ceiling}, threshold is {self.threshold}. "
                 f"No evidence this system can currently produce would "
                 f"change the recommendation."]
        for lever, why in self.blocked_by:
            lines.append(f"  unavailable: {lever} -- {why}")
        return "\n".join(lines)


def ceiling_analysis(opportunity: "OpportunityReceipt") -> CeilingAnalysis:
    """How high this target could score if every AVAILABLE lever were pulled.

    Does not change any weight or threshold. It asks a different question
    from `rank()`: not "what did this score" but "what could it ever score".
    """
    achieved = rank(opportunity).priority
    ceiling = achieved
    blocked = []

    if not any(s.kind == "CODE_PRESSURE" for s in opportunity.signals):
        pts, _, why = SCORING_LEVERS["CODE_PRESSURE"]
        blocked.append(("CODE_PRESSURE", why))
    if opportunity.locally_reproducible != "YES":
        pts, _, why = SCORING_LEVERS["LOCAL_REPRODUCIBILITY"]
        if opportunity.locally_reproducible == "UNKNOWN":
            blocked.append(("LOCAL_REPRODUCIBILITY", why))
        else:
            ceiling += pts + 2      # NO -> YES recovers the penalty too
    if opportunity.reward_state not in ("OBSERVED", "VERIFIED_CURRENT", "PAID"):
        pts, _, why = SCORING_LEVERS["REWARD"]
        blocked.append(("REWARD", why))

    return CeilingAnalysis(achieved=achieved, reachable_ceiling=ceiling,
                           threshold=INVESTIGATE_THRESHOLD,
                           blocked_by=tuple(blocked))


def opportunity_id_for(target: str, handle: str) -> str:
    """Stable identity so the queue cannot hold the same lead twice."""
    raw = f"{target.strip().lower()}|{handle.strip().lower()}"
    return "OPP-" + hashlib.sha256(raw.encode()).hexdigest()[:16]


# ── THE SCOUTER ──────────────────────────────────────────────────────────
#
# A power level is a decision aid, not a fact and never money. It exists so
# a queue can be skimmed; it must always be able to answer "why?".
#
# Power and confidence are reported SEPARATELY and never multiplied into
# one figure. A 9,000 at 0.2 confidence and a 6,500 at 0.9 are different
# kinds of target -- one is a speculation, the other is work -- and
# collapsing them hides the only distinction that matters when choosing
# what to actually do next.

_BANDS = ((9000, "EXTREME"), (7000, "HOT"), (4000, "PROMISING"),
          (2000, "WATCH"), (0, "LOW"))


def controlling_party(target: str, signal: SignalEvidence) -> str:
    """Who actually stands behind one signal -- not which API served it.

    THE ATTACK THIS CLOSES

    An attacker who owns a public GitHub repo simultaneously controls the
    repo's issues (becomes a DEMAND signal, +1800 EXPLICIT_DEMAND), the
    repo's commits (becomes ACTIVITY, +900/+1200 TARGET_ACTIVITY) and the
    commit subject text (becomes CODE_PRESSURE, +1500). Before this
    function existed, `power_profile()` computed diversity as
    `len({s.source_type for s in signals}) > 1` -- three signals arriving
    through three different fetchers read as three witnesses and earned
    SOURCE_DIVERSITY (+400) on top. They are not three witnesses. They
    are one party talking to itself through three doors. Self-dealt
    total before this fix: 1800 + 1200 (HIGHLY_ACTIVE) + 1500 + 400 =
    4900, or 1800 + 900 (ACTIVE) + 1500 + 400 = 4600, entirely sourced
    from one repository's own owner.

    THE PRINCIPLE, MOVED ONE LEVEL UP

    `signal_spine.py`'s `source_lineage` already established that two
    FEEDS reporting one event are one fact, not two -- see `relate()`,
    which treats matching `source_lineage` as one fact observed twice,
    not two facts. That rule was never applied to the CONTROLLING
    PARTY, only to the feed. This function
    applies the identical idea one layer up: diversity of API endpoint
    (issues vs. commits) is not diversity of witness when both endpoints
    are doors into a repository the same account owns.

    THE NUANCE THAT MUST SURVIVE

    A `help wanted` issue filed by someone OTHER than the repo owner is
    genuinely independent third-party evidence -- a stranger asking for
    something is not the owner talking to itself, even though the
    signal still arrives via the repo's own issues API. `tentacles.py`
    already captures who wrote it as `evidence["author_login"]` for
    DEMAND signals. When that name differs from the target's owner, the
    author -- not the repo -- is this signal's controlling party. Losing
    this distinction would collapse a genuine contributor-demand signal
    into a self-dealt one, which is the over-correction this function
    exists to avoid: the fix is to stop self-dealt signals from
    corroborating each other, not to stop counting real ones.

    WHAT THIS DOES NOT COVER

    - Sock puppets: an `author_login` the same attacker also controls
      (an alt account, a bot they run) still reads as a second party.
      This function has no identity-linking capability and does not
      pretend to -- it answers "does GitHub's own record name a
      different account", not "is that account really independent".
    - Non-GitHub targets: "the first path segment is the owner" is a
      GitHub convention. A target with no "/" is treated as its own
      single party rather than raising, but this has not been validated
      against any non-GitHub identity model.
    - Signals with no `author_login` (ACTIVITY, CODE_PRESSURE, RELEASE --
      these describe the repo as a whole, not one person's post) are
      conservatively attributed to the repo owner. That is the same
      assumption the attack exploits; refusing to make it here would
      silently reopen the hole for exactly the signal kinds that carry
      it, so it is made deliberately, not by oversight.

    TWO DEFECTS CLOSED 2026-09-01 (blue-team pass 008, findings 3 and 4)

    Both concern how the OWNER half of identity is derived, and both are
    fixed together because they are the same underlying mistake:
    treating a DISPLAY string as if it were an IDENTITY string.

    Finding 3 -- truncation collision. `target` here is frequently
    `describe(raw_name).safe`: a value already truncated (at
    `untrusted_text.DEFAULT_MAX_LEN`, 300 chars) for safe display. Two
    different organisations whose names share a ~290-character prefix
    and have equal total length truncate to the SAME `.safe` string, so
    deriving identity from `target` directly collapses two real buyers
    into one controlling party -- confirmed live (two constructed
    290+-char names, byte-identical `.safe` output). Truncating less is
    not the fix: the display cap exists to bound what reaches the
    durable ledger, and widening or removing it reintroduces the
    unbounded-write defect an earlier cycle already closed (see
    `mouth_ted.py`'s own `target`-bounding comment). The fix instead
    gives identity a second, FULL-length-derived input that never
    itself reaches the ledger unbounded: if the signal's `evidence`
    carries `identity_hash` (a fixed-length, e.g. sha256 hex digest,
    computed by the signal's producer from the FULL untruncated name
    before any truncation happened -- see `mouth_ted.ted_signal()`),
    that hash IS the owner identity, not the truncated `target` string.
    A hash collision on two genuinely different full names is
    astronomically unlikely; a truncation collision on two genuinely
    different 300-char-bounded prefixes is not. Signals with no
    `identity_hash` in evidence (e.g. GitHub `owner/repo` targets, which
    have no truncation-collision exposure in the first place because
    repo slugs are short) fall back to the previous `target`-derived
    behaviour unchanged.

    Finding 4 -- no Unicode normalisation. NFC and NFD encodings of the
    identical name are visually and semantically identical but
    byte-different, so the old `.strip().lower()` alone produced two
    different controlling parties for one real buyer -- confirmed live
    with "Ministère de la Santé" in both forms. Fixed by running
    `unicodedata.normalize("NFKC", ...)` before lowering, on both the
    owner and the author. NFKC (not NFC) is chosen deliberately: this is
    EU procurement data (`mouth_ted.py`), where the same organisation
    name can also arrive using compatibility-equivalent characters
    (full-width forms, certain typographic ligatures) that NFC alone
    does not fold together but NFKC does -- the identity question here
    is "is this the same organisation", which tolerates the lossier
    compatibility folding NFKC performs; a case using this function to
    answer "is this byte-for-byte the same canonical string" would want
    NFC instead, but no caller of `controlling_party()` currently needs
    that distinction.
    """
    identity_hash = signal.evidence.get("identity_hash", "")
    if isinstance(identity_hash, str) and identity_hash.strip():
        # A fixed-length digest computed by the producer from the FULL,
        # untruncated name -- see the docstring section above. Using it
        # directly as the owner sidesteps the truncation-collision
        # defect entirely, because it was never derived from the
        # truncated display string in the first place.
        owner = identity_hash.strip().lower()
    else:
        raw_owner = target.split("/", 1)[0] if "/" in target else target
        owner = unicodedata.normalize("NFKC", raw_owner).strip().lower()
    raw_author = str(signal.evidence.get("author_login", "")).strip()
    author = unicodedata.normalize("NFKC", raw_author).lower() if raw_author else ""
    return author if author and author != owner else owner


@dataclass(frozen=True)
class PowerProfile:
    power_level: int
    breakdown: tuple[tuple[str, int], ...]
    confidence: float
    confidence_inputs: tuple[str, ...]
    # One controlling party per signal, same order as the signals that
    # were scored. Carried through so `show_the_math()` can name the
    # finding in words rather than leaving it invisible inside a number.
    controlling_parties: tuple[str, ...] = ()

    def band(self) -> str:
        for floor, name in _BANDS:
            if self.power_level >= floor:
                return name
        return "LOW"

    def classification(self) -> str:
        """Power and confidence together, never averaged."""
        if self.power_level >= 7000 and self.confidence < 0.4:
            return "HIGH_UPSIDE_UNCERTAIN"
        if self.power_level >= 4000 and self.confidence >= 0.7:
            return "STRONG_EXECUTION_TARGET"
        return f"{self.band()}_CONFIDENCE_{self.confidence:.2f}"

    def show_the_math(self) -> str:
        lines = [f"POWER {self.power_level}  ({self.band()})"]
        lines += [f"  {'+' if v >= 0 else '-'} {k}={abs(v)}"
                  for k, v in self.breakdown]
        lines.append(f"CONFIDENCE {self.confidence:.2f}")
        lines += [f"  - {c}" for c in self.confidence_inputs]
        distinct = sorted(set(self.controlling_parties))
        if len(distinct) <= 1:
            who = distinct[0] if distinct else "unknown"
            lines.append(
                f"SOURCE CONTROL: all {len(self.controlling_parties)} "
                f"signal(s) traced to one controlling party ({who}) -- "
                f"SOURCE_DIVERSITY withheld; source multiplicity is not "
                f"independence")
        else:
            lines.append(
                f"SOURCE CONTROL: {len(distinct)} distinct controlling "
                f"parties ({', '.join(distinct)}) -- SOURCE_DIVERSITY "
                f"earned")
        return "\n".join(lines)


def power_profile(opportunity: OpportunityReceipt,
                  now: Optional[datetime] = None) -> PowerProfile:
    """Explainable power level. Every term is traceable to an observation.

    Money is only counted when money was actually OBSERVED. An unknown
    reward contributes nothing -- it is not scored as zero for
    convenience, it simply does not appear in the breakdown, and the
    absence is visible.
    """
    parts: list[tuple[str, int]] = []

    if opportunity.reward_state == "VERIFIED_CURRENT":
        parts.append(("VERIFIED_REWARD_OBSERVED", 2500))
    elif opportunity.reward_state == "OBSERVED":
        parts.append(("REWARD_OBSERVED_UNVERIFIED", 1200))
    # UNKNOWN / NOT_PRESENT contribute nothing and are not scored as zero.

    if any(s.kind == "DEMAND" for s in opportunity.signals):
        parts.append(("EXPLICIT_DEMAND", 1800))
    if any(s.kind == "CODE_PRESSURE" for s in opportunity.signals):
        parts.append(("CODE_PRESSURE", 1500))
    if opportunity.activity_class == "HIGHLY_ACTIVE":
        parts.append(("TARGET_ACTIVITY", 1200))
    elif opportunity.activity_class == "ACTIVE":
        parts.append(("TARGET_ACTIVITY", 900))

    if opportunity.locally_reproducible == "YES":
        parts.append(("LOCAL_REPRODUCIBILITY", 1600))
    elif opportunity.locally_reproducible == "NO":
        parts.append(("NOT_LOCALLY_REPRODUCIBLE", -1200))

    if not opportunity.is_stale(now):
        parts.append(("EVIDENCE_FRESH", 700))
    else:
        parts.append(("EVIDENCE_STALE", -1500))

    # SOURCE_DIVERSITY rewards independent corroboration, not endpoint
    # variety. Grouping by `source_type` alone let one party earn it by
    # self-publishing through several API shapes (issues + commits +
    # releases) it fully controls -- see `controlling_party()`'s
    # docstring for the concrete attack this closed. Grouping by
    # controlling party instead means the bonus fires only when the
    # evidence traces to more than one real party, which for a GitHub
    # target means: the repo owner plus at least one third-party
    # `author_login` (e.g. a genuine community-filed issue).
    parties = tuple(controlling_party(opportunity.target, s)
                    for s in opportunity.signals)
    if len(set(parties)) > 1:
        parts.append(("SOURCE_DIVERSITY", 400))

    if opportunity.unknowns:
        parts.append(("EVIDENCE_UNCERTAINTY", -150 * len(opportunity.unknowns)))
    if opportunity.disqualifiers:
        parts.append(("DISQUALIFIER_FRICTION", -2000 * len(opportunity.disqualifiers)))

    power = max(0, sum(v for _, v in parts))

    # Confidence is about how well we KNOW, not how much it is worth.
    conf_inputs: list[str] = []
    confidence = 0.5
    if any(s.is_authoritative() for s in opportunity.signals):
        confidence += 0.2
        conf_inputs.append("at least one PRIMARY/OFFICIAL source")
    else:
        conf_inputs.append("no authoritative source: platform/third-party only")
    if opportunity.is_stale(now):
        confidence -= 0.3
        conf_inputs.append("evidence is stale")
    if opportunity.unknowns:
        confidence -= min(0.1 * len(opportunity.unknowns), 0.3)
        conf_inputs.append(f"{len(opportunity.unknowns)} recorded unknown(s)")
    if opportunity.locally_reproducible == "UNKNOWN":
        confidence -= 0.1
        conf_inputs.append("local reproducibility unverified")
    confidence = round(min(max(confidence, 0.0), 1.0), 2)

    return PowerProfile(power, tuple(parts), confidence, tuple(conf_inputs),
                        controlling_parties=parties)


class HandoffRefused(OpportunityIntegrityError):
    """The opportunity was not in a state that justifies a mission."""


@dataclass(frozen=True)
class InvestigationMission:
    """A bounded question, carrying the evidence that justified asking it.

    Deliberately has no verdict, no claim, and no route to a Receipt or a
    GoldBrick. Those require an investigation to actually happen. The
    mission says why to look, never what will be found.
    """

    opportunity_id: str
    target: str
    why_this_target_now: tuple[str, ...]
    source_observations: tuple[SignalEvidence, ...]
    power_level: int
    confidence: float
    classification: str
    unknowns: tuple[str, ...]
    disqualifiers: tuple[str, ...]
    next_cheapest_experiment: str
    what_would_disprove_value: str
    stop_conditions: tuple[str, ...]

    def bug_claim(self) -> str:
        return "NONE"

    def value_claim(self) -> str:
        return "NOT_MEASURED"


def handoff(opportunity: OpportunityReceipt,
            next_cheapest_experiment: str,
            what_would_disprove_value: str,
            now: Optional[datetime] = None) -> InvestigationMission:
    """Turn a ranked opportunity into a bounded mission, or refuse.

    Refuses rather than degrades. A stale, disqualified or un-ranked
    target must not become a mission just because someone called this
    function -- that would be the radar authorising its own hunt.

    Provenance and unknowns are carried through by construction, because
    a mission that loses them sends the investigator out believing the
    evidence is better than it is.
    """
    ranking = rank(opportunity, now)
    if ranking.recommendation != "INVESTIGATE":
        raise HandoffRefused(
            f"ranking says {ranking.recommendation}, not INVESTIGATE; the "
            f"radar does not authorise its own hunt")
    if opportunity.blocking_disqualifiers():
        raise HandoffRefused(
            f"blocking disqualifier(s): "
            f"{', '.join(opportunity.blocking_disqualifiers())}")
    if not next_cheapest_experiment.strip():
        raise HandoffRefused(
            "a mission must name the cheapest experiment that could kill it")

    profile = power_profile(opportunity, now)
    return InvestigationMission(
        opportunity_id=opportunity.opportunity_id,
        target=opportunity.target,
        why_this_target_now=ranking.inputs,
        source_observations=opportunity.signals,
        power_level=profile.power_level,
        confidence=profile.confidence,
        classification=profile.classification(),
        unknowns=opportunity.unknowns,
        disqualifiers=opportunity.disqualifiers,
        next_cheapest_experiment=next_cheapest_experiment.strip(),
        what_would_disprove_value=what_would_disprove_value.strip(),
        stop_conditions=(
            "stop at any external action requiring owner authority",
            "stop if the evidence proves stale at current upstream",
            "stop if a security-sensitive finding appears: private route only",
        ),
    )
