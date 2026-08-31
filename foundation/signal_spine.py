"""The canonical signal shape, and the fusion that refuses to double-count.

WHAT THIS REUSES RATHER THAN DUPLICATES

- `foundation/opportunity.py` -- `SOURCE_TYPES`, `AUTHORITATIVE_SOURCES`
  and the whole power/confidence separation. This module does NOT define a
  second source vocabulary and does NOT define a second scorer. A fused
  target that earns investigation is handed to `opportunity.handoff()`,
  the existing hunter. There is no mission_v2.
- `foundation/mouth_common.py` -- the read-only observation primitive the
  real tentacles already use. This module never fetches anything itself.
- `kpm/source-vault/registry.py` -- content-addressed provenance for raw
  artifacts. A `CanonicalSignal` cites a source ref; it does not become a
  second archive.

THE PROBLEM THIS EXISTS TO SOLVE

Two tentacles observe the world. Both report that PyYAML 6.0.2 was
released -- one reading GitHub's release atom feed, one reading PyPI's
RSS. Naively fused, that is two signals and looks like corroboration.

It is one fact, observed twice, downstream of one upstream event.

Source multiplicity is not independence. The fusion layer's entire job is
to keep those two things apart, so that five copies of one blog post
never become five reasons to believe something.

WHAT IS NORMALISED AND WHAT IS NOT

`facts` is the ONLY normalised surface: a small mapping of key -> value
assertions that any tentacle can emit, so two sources can be compared at
all. Everything a source knows that does not fit there stays in
`evidence`, preserved verbatim and never flattened. A GitHub issue has
labels; a package index has download counts; a bounty program has scope
terms. Forcing those into one shape would destroy the difference that
makes a second source worth having.

Time survives per-signal, not per-target: `observed_at` (when the system
saw it) and `event_at` (when the world event happened, possibly UNKNOWN)
are separate, because a fresh observation of an ancient fact is not a
fresh fact.

Money never enters gravity. Observed money and possible money are
different fields, and neither is a force pulling the system anywhere --
only evidence is.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Optional

from foundation.opportunity import (
    AUTHORITATIVE_SOURCES,
    OpportunityReceipt,
    SOURCE_TYPES,
    SignalEvidence,
    opportunity_id_for,
)

def _neutralise(value) -> str:
    """Render-time only. Imported lazily so signal_spine keeps no import
    dependency on the defence module at construction time."""
    from foundation.untrusted_text import neutralise
    return neutralise(str(value))


__all__ = [
    "SignalIntegrityError",
    "RELATIONS",
    "MONEY_STATES",
    "PRESSURE_CLASSES",
    "TARGET_PROVENANCE",
    "TRUSTED_TARGET_PROVENANCE",
    "STALE_AFTER_DAYS",
    "CanonicalSignal",
    "Relation",
    "relate",
    "FusedTarget",
    "fuse",
    "RawValueMapEntry",
    "raw_value_map_entry",
    "GravityProfile",
    "gravity",
    "TARGET_LOCK_STATES",
    "target_lock",
    "LockNotEarned",
    "to_opportunity",
]


class SignalIntegrityError(ValueError):
    """A signal or a fusion tried to claim more than it observed."""


# How two signals stand to one another. UNKNOWN is a real answer and the
# default: two signals that assert nothing in common are not corroboration.
RELATIONS = ("SUPPORTING", "CONTRADICTORY", "DUPLICATE", "CORRELATED",
             "STALE", "UNKNOWN")

# Money states, deliberately mirroring `opportunity`'s reward discipline
# rather than inventing a second ladder. NOT_OBSERVED is not zero.
MONEY_STATES = ("NOT_OBSERVED", "ADVERTISED", "VERIFIED_CURRENT", "PAID")

# Value pressure: evidence that something exerts real external pull.
# NONE is the default and is not a deficiency -- most observations carry
# no pressure at all, and pretending otherwise is how a radar invents
# demand. Every non-NONE class must name the evidence that earned it.
PRESSURE_CLASSES = ("NONE", "EXPLICIT_DEMAND", "UNRESOLVED_PAIN",
                    "INCENTIVE", "URGENCY")

# How this signal's `target` came to be trusted. A demand issue names its
# own repository (SOURCE_NATIVE); a directed read is trusted only because
# a mapping was established (DECLARED_MATCH); anything else is a guess and
# is never allowed to create convergence mass, because convergence between
# two targets that merely share a string is the most expensive kind of
# false evidence this radar can produce.
TARGET_PROVENANCE = ("SOURCE_NATIVE", "DECLARED_MATCH", "ASSUMED")
TRUSTED_TARGET_PROVENANCE = ("SOURCE_NATIVE", "DECLARED_MATCH")

STALE_AFTER_DAYS = 21

_UNKNOWN_TIME = "UNKNOWN"


def _now(now: Optional[datetime] = None) -> datetime:
    return now or datetime.now(timezone.utc)


def _parse(stamp: str) -> Optional[datetime]:
    """Return None for anything unreadable. Unreadable means unknown, and
    unknown must never read as fresh."""
    if not stamp or stamp == _UNKNOWN_TIME:
        return None
    try:
        parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _fingerprint(text: str) -> str:
    """Collapse presentational differences so an echo is recognisable as
    an echo. Two feeds announcing one release word it differently."""
    flat = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    return hashlib.sha256(flat.encode()).hexdigest()[:16]


@dataclass(frozen=True)
class CanonicalSignal:
    """The smallest shape every tentacle can emit without pretending the
    tentacles are the same kind of instrument.

    `source_lineage` is the load-bearing field. It names the upstream
    thing this observation is DOWNSTREAM OF -- not the feed that carried
    it. Two feeds reporting one release share a lineage, and that is what
    stops them being counted as two independent facts.
    """

    signal_id: str
    source_id: str            # which tentacle observed it
    source_type: str          # from opportunity.SOURCE_TYPES
    source_ref: str           # where it can be re-read
    target: str               # what it points at
    kind: str                 # ACTIVITY / DEMAND / REWARD / RELEASE / ...
    claim: str                # human-readable, never parsed for meaning
    observed_at: str          # when the system saw it
    event_at: str = _UNKNOWN_TIME     # when the world event happened
    source_lineage: str = ""  # upstream event this derives from
    target_established_by: str = "SOURCE_NATIVE"
    facts: Mapping[str, str] = field(default_factory=dict)
    evidence: Mapping[str, Any] = field(default_factory=dict)
    pressure_class: str = "NONE"
    pressure_evidence: str = ""   # what was observed, not what it implies
    money_state: str = "NOT_OBSERVED"
    money_observed: str = ""  # verbatim, never parsed into a number
    unknowns: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.source_type not in SOURCE_TYPES:
            raise SignalIntegrityError(
                f"unknown source type {self.source_type!r}; a tentacle may "
                f"not invent its own authority")
        if not self.claim.strip():
            raise SignalIntegrityError("a signal must state what was seen")
        if not self.source_id.strip():
            raise SignalIntegrityError(
                "a signal must name the tentacle that observed it, or "
                "provenance is already lost at the first hop")
        if self.target_established_by not in TARGET_PROVENANCE:
            raise SignalIntegrityError(
                f"unknown target provenance {self.target_established_by!r}")
        if self.pressure_class not in PRESSURE_CLASSES:
            raise SignalIntegrityError(
                f"unknown pressure class {self.pressure_class!r}")
        if self.pressure_class != "NONE" and not self.pressure_evidence.strip():
            raise SignalIntegrityError(
                f"pressure class {self.pressure_class!r} claims external pull "
                f"but names no evidence for it")
        if self.money_state not in MONEY_STATES:
            raise SignalIntegrityError(
                f"unknown money state {self.money_state!r}")
        if self.money_state != "NOT_OBSERVED" and not self.money_observed.strip():
            raise SignalIntegrityError(
                f"money_state {self.money_state!r} claims money was seen but "
                f"records none")
        if self.money_observed.strip() and self.money_state == "NOT_OBSERVED":
            raise SignalIntegrityError(
                "money was recorded but the state says none was observed")
        # Freeze the mappings so a later caller cannot edit the evidence a
        # fusion decision was already made from.
        object.__setattr__(self, "facts", MappingProxyType(dict(self.facts)))
        object.__setattr__(self, "evidence",
                           MappingProxyType(dict(self.evidence)))

    def claim_fingerprint(self) -> str:
        return _fingerprint(self.claim)

    def is_authoritative(self) -> bool:
        return self.source_type in AUTHORITATIVE_SOURCES

    def target_is_established(self) -> bool:
        """Whether this signal earned the right to be about this target."""
        return self.target_established_by in TRUSTED_TARGET_PROVENANCE

    def is_stale(self, now: Optional[datetime] = None) -> bool:
        """Staleness is measured on the EVENT, not the observation.

        Reading a five-year-old page today does not make its contents
        current, and this is the exact way a radar lies to itself.
        """
        stamp = self.event_at if self.event_at != _UNKNOWN_TIME else self.observed_at
        seen = _parse(stamp)
        if seen is None:
            return True
        return _now(now) - seen > timedelta(days=STALE_AFTER_DAYS)

    def money_claim(self) -> str:
        """Only PAID money is money. Everything else is a figure on a page."""
        if self.money_state == "PAID":
            return self.money_observed
        return "NOT_MEASURED"


@dataclass(frozen=True)
class Relation:
    """How two signals stand, and why. The why is not decoration -- a
    fusion nobody can audit is a black box with a score on it."""

    kind: str
    reason: str
    shared_keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.kind not in RELATIONS:
            raise SignalIntegrityError(f"unknown relation {self.kind!r}")

    def counts_as_independent_support(self) -> bool:
        return self.kind == "SUPPORTING"


def relate(a: CanonicalSignal, b: CanonicalSignal,
           now: Optional[datetime] = None) -> Relation:
    """Compare two signals structurally. No language model, no guessing.

    The order of these checks is the whole design. Contradiction is
    reported before agreement, staleness before corroboration, and shared
    lineage before independence -- because every one of those is a way a
    naive fuser talks itself into confidence it has not earned.
    """
    if a.target != b.target:
        return Relation("UNKNOWN", "different targets; not comparable")

    shared = tuple(sorted(set(a.facts) & set(b.facts)))
    if not shared:
        return Relation(
            "UNKNOWN",
            "no overlapping asserted facts; two signals about different "
            "aspects of one target are not corroboration")

    disagreements = tuple(k for k in shared if a.facts[k] != b.facts[k])
    if disagreements:
        return Relation(
            "CONTRADICTORY",
            f"sources disagree on {', '.join(disagreements)}: "
            f"{a.source_id} says {a.facts[disagreements[0]]!r}, "
            f"{b.source_id} says {b.facts[disagreements[0]]!r}",
            shared)

    # They agree. The only question left is whether that means anything.
    if a.is_stale(now) or b.is_stale(now):
        return Relation(
            "STALE",
            "the signals agree, but at least one describes an event too old "
            "to stand as current evidence", shared)

    if a.source_lineage and a.source_lineage == b.source_lineage:
        return Relation(
            "DUPLICATE",
            f"both derive from the same upstream event "
            f"({a.source_lineage}); one fact observed twice is one fact",
            shared)

    if a.claim_fingerprint() == b.claim_fingerprint():
        return Relation(
            "DUPLICATE",
            "identical claim text; an echo, not a second observation",
            shared)

    if a.source_id == b.source_id:
        return Relation(
            "CORRELATED",
            f"both observed by {a.source_id}; one instrument agreeing with "
            f"itself is not two instruments", shared)

    return Relation(
        "SUPPORTING",
        f"independently observed by {a.source_id} and {b.source_id} from "
        f"distinct lineages, agreeing on {', '.join(shared)}", shared)


@dataclass(frozen=True)
class FusedTarget:
    """What a target looks like after the echoes are collapsed.

    `independent_facts` is deliberately not `len(signals)`. The gap
    between those two numbers is the entire value of this module.
    """

    target: str
    signals: tuple[CanonicalSignal, ...]
    relations: tuple[tuple[str, str, Relation], ...]
    independent_facts: int
    corroborations: int          # distinct sources agreeing on ONE fact
    convergences: int            # distinct DIMENSIONS pointing at one target
    echoes: int
    contradictions: tuple[Relation, ...]
    stale_signals: tuple[str, ...]
    unknown_pairs: int
    unknowns: tuple[str, ...]

    def has_contradiction(self) -> bool:
        return bool(self.contradictions)

    def show_the_math(self) -> str:
        lines = [f"TARGET {self.target}",
                 f"  signals observed        {len(self.signals)}",
                 f"  independent facts       {self.independent_facts}",
                 f"  corroborations          {self.corroborations}",
                 f"  convergent dimensions   {self.convergences}",
                 f"  echoes collapsed        {self.echoes}",
                 f"  contradictions          {len(self.contradictions)}",
                 f"  stale signals           {len(self.stale_signals)}"]
        for a_id, b_id, rel in self.relations:
            lines.append(f"  {a_id} <-> {b_id}: {rel.kind} -- {rel.reason}")
        return "\n".join(lines)


def fuse(signals: Iterable[CanonicalSignal],
         now: Optional[datetime] = None) -> FusedTarget:
    """Collapse a target's signals without collapsing their differences.

    Independence is computed by grouping: signals joined by any
    DUPLICATE/CORRELATED/STALE relation form one cluster, and a cluster
    contributes exactly one independent fact however many members it has.
    """
    sigs = tuple(signals)
    if not sigs:
        raise SignalIntegrityError("cannot fuse nothing")
    targets = {s.target for s in sigs}
    if len(targets) != 1:
        raise SignalIntegrityError(
            f"fuse() operates on one target; got {sorted(targets)}")

    relations: list[tuple[str, str, Relation]] = []
    contradictions: list[Relation] = []
    unknown_pairs = 0
    corroborations = 0
    # Distinct KIND-PAIRS, not qualifying signal pairs. Counting signal
    # pairs is quadratic in signal count: five demand issues plus one
    # activity signal plus one pressure signal produced ELEVEN
    # "convergent dimensions" on a live target when there were only
    # three dimensions present. That inflated gravity by 5,500 for
    # evidence that had not multiplied -- the echo failure in a new
    # shape. Found by running the full chain live, not by review.
    convergent_kinds: set = set()

    # Union-find over signal indices. Anything that is not genuinely
    # independent gets merged into one cluster.
    parent = list(range(len(sigs)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[max(ri, rj)] = min(ri, rj)

    for i in range(len(sigs)):
        for j in range(i + 1, len(sigs)):
            rel = relate(sigs[i], sigs[j], now)
            relations.append((sigs[i].signal_id, sigs[j].signal_id, rel))
            if rel.kind == "CONTRADICTORY":
                contradictions.append(rel)
            elif rel.kind == "SUPPORTING":
                corroborations += 1
            elif rel.kind == "UNKNOWN":
                unknown_pairs += 1
                # Different dimensions of ONE target, from distinct
                # lineages, is convergence -- real evidence, but NOT
                # agreement about anything. A release and a demand signal
                # never corroborate each other; they pull from different
                # directions on the same point. Two signals of the SAME
                # kind are two voices in one dimension, which is also real
                # and is deliberately not called convergence.
                if (sigs[i].target == sigs[j].target
                        and sigs[i].kind != sigs[j].kind
                        and sigs[i].source_lineage != sigs[j].source_lineage
                        and sigs[i].target_is_established()
                        and sigs[j].target_is_established()
                        and not sigs[i].is_stale(now)
                        and not sigs[j].is_stale(now)):
                    convergent_kinds.add(
                        tuple(sorted((sigs[i].kind, sigs[j].kind))))
            elif rel.kind in ("DUPLICATE", "CORRELATED", "STALE"):
                union(i, j)

    clusters = {find(i) for i in range(len(sigs))}
    independent = len(clusters)
    echoes = len(sigs) - independent

    stale = tuple(s.signal_id for s in sigs if s.is_stale(now))
    unknowns: tuple[str, ...] = tuple(dict.fromkeys(
        u for s in sigs for u in s.unknowns))

    return FusedTarget(
        target=sigs[0].target, signals=sigs, relations=tuple(relations),
        independent_facts=independent, corroborations=corroborations,
        convergences=len(convergent_kinds), echoes=echoes,
        contradictions=tuple(contradictions), stale_signals=stale,
        unknown_pairs=unknown_pairs, unknowns=unknowns)


@dataclass(frozen=True)
class GravityProfile:
    """Why the system is being pulled toward a target.

    Gravity is not power and not confidence. Power is how big the prize
    might be; confidence is how well established the evidence is; gravity
    is how many genuinely independent verified forces point at this one
    place. A single enormous unverified rumour has power and no gravity.
    """

    mass: int
    breakdown: tuple[tuple[str, int], ...]
    independent_facts: int
    corroborations: int
    convergences: int
    pressure_observed: tuple[str, ...]
    contradictions: int
    echoes_ignored: int
    money_observed: str
    money_unknown: bool

    def show_the_math(self) -> str:
        lines = [f"GRAVITY {self.mass}"]
        for label, value in self.breakdown:
            lines.append(f"  {'+' if value >= 0 else '-'} {label}="
                         f"{abs(value)}")
        lines.append(f"  independent facts   {self.independent_facts}")
        lines.append(f"  corroborations      {self.corroborations}")
        lines.append(f"  convergent dims     {self.convergences}")
        lines.append(f"  pressure observed   "
                     f"{', '.join(self.pressure_observed) or 'NONE'}")
        lines.append(f"  echoes ignored      {self.echoes_ignored}")
        lines.append(f"  contradictions      {self.contradictions}")
        lines.append(f"  money observed      "
                     f"{self.money_observed or 'NONE'}")
        if self.money_unknown:
            lines.append("  money unknown       yes (contributes nothing)")
        return "\n".join(lines)


def gravity(fused: FusedTarget, now: Optional[datetime] = None) -> GravityProfile:
    """Mass from independent evidence only. Echoes are counted and ignored.

    Money is reported alongside and never added, because a large advertised
    figure is not a force -- it is a claim on a web page.
    """
    parts: list[tuple[str, int]] = []

    # Corroboration and convergence are different evidence and are never
    # merged into one line. Two sources agreeing on one fact is not the
    # same as a release and a complaint pointing at one project, and a map
    # that calls both "corroboration" is lying about what it saw.
    if fused.corroborations:
        parts.append(("INDEPENDENT_CORROBORATION", 600 * fused.corroborations))
    if fused.convergences:
        parts.append(("MULTI_DIMENSIONAL_CONVERGENCE", 500 * fused.convergences))
    if any(s.is_authoritative() for s in fused.signals):
        parts.append(("AUTHORITATIVE_SOURCE_PRESENT", 800))
    fresh = [s for s in fused.signals if not s.is_stale(now)]
    if fresh:
        parts.append(("FRESH_EVIDENCE", 400))
    if fused.contradictions:
        parts.append(("UNRESOLVED_CONTRADICTION",
                      -500 * len(fused.contradictions)))
    if fused.stale_signals:
        parts.append(("STALE_EVIDENCE", -200 * len(fused.stale_signals)))
    if fused.independent_facts == 1 and fused.echoes:
        parts.append(("ECHO_ONLY_NO_CORROBORATION", -300))

    # Pressure creates mass only from signals that are both non-stale and
    # carry named evidence. An expired complaint is not current pull.
    pressure_weights = {"EXPLICIT_DEMAND": 700, "UNRESOLVED_PAIN": 600,
                        "URGENCY": 800, "INCENTIVE": 400}
    live_pressure = sorted({
        s.pressure_class for s in fused.signals
        if s.pressure_class != "NONE" and not s.is_stale(now)})
    for cls in live_pressure:
        parts.append((f"VALUE_PRESSURE_{cls}", pressure_weights[cls]))

    all_pressure = tuple(sorted({s.pressure_class for s in fused.signals
                                 if s.pressure_class != "NONE"}))

    money = [s for s in fused.signals if s.money_state != "NOT_OBSERVED"]
    observed = "; ".join(f"{s.money_observed} ({s.money_state})" for s in money)

    return GravityProfile(
        mass=sum(v for _, v in parts), breakdown=tuple(parts),
        independent_facts=fused.independent_facts,
        corroborations=fused.corroborations,
        convergences=fused.convergences,
        pressure_observed=all_pressure,
        contradictions=len(fused.contradictions),
        echoes_ignored=fused.echoes, money_observed=observed,
        money_unknown=not money)


@dataclass(frozen=True)
class RawValueMapEntry:
    """One place on the map, and every question it must be able to answer.

    It answers them by carrying the evidence, not by carrying a score.
    """

    target: str
    fused: FusedTarget
    gravity_profile: GravityProfile
    why_on_the_map: tuple[str, ...]
    disqualifiers: tuple[str, ...]
    what_would_kill_it: str
    next_cheapest_experiment: str

    def who_said_what_when(self) -> tuple[dict[str, str], ...]:
        return tuple({
            "source": s.source_id, "source_type": s.source_type,
            "said": s.claim, "observed_at": s.observed_at,
            "event_at": s.event_at, "ref": s.source_ref,
        } for s in self.fused.signals)

    def money_observed(self) -> str:
        return self.gravity_profile.money_observed or "NONE"

    def money_unknown(self) -> bool:
        return self.gravity_profile.money_unknown

    def value_signals_without_money(self) -> tuple[str, ...]:
        return tuple(s.claim for s in self.fused.signals
                     if s.money_state == "NOT_OBSERVED")

    def bug_claim(self) -> str:
        """A map entry is a place worth looking, never a defect."""
        return "NONE"

    def value_claim(self) -> str:
        return "NOT_MEASURED"

    def render(self) -> str:
        rows = [f"RAW VALUE MAP // {self.target}", "",
                self.fused.show_the_math(), "",
                self.gravity_profile.show_the_math(), "",
                "WHY ON THE MAP"]
        rows += [f"  - {r}" for r in self.why_on_the_map]
        rows.append("WHO SAID WHAT, WHEN")
        for row in self.who_said_what_when():
            # `said` is a signal's `claim`, which for a GitHub demand
            # signal contains an ISSUE TITLE -- text an attacker controls
            # completely by opening an issue on their own public repo.
            # This line is the operator-facing surface, and until
            # 2026-09-01 it interpolated that text raw: ANSI escapes
            # reached a terminal and embedded newlines forged extra lines
            # in the report. Found by an adversarial suite, which noted
            # correctly that `untrusted_text.neutralise()` already existed
            # and solved this -- nothing called it. Same unwired-defence
            # shape as the network gate that had no consumer.
            #
            # Neutralisation is for DISPLAY only. The verbatim claim is
            # untouched on the signal itself; evidence is never mutated.
            rows.append(f"  [{_neutralise(row['source_type'])}] "
                        f"{_neutralise(row['source'])}: "
                        f"{_neutralise(row['said'])}")
            rows.append(f"      event {row['event_at']} / observed "
                        f"{row['observed_at']} / {row['ref']}")
        rows.append(f"MONEY OBSERVED   {self.money_observed()}")
        rows.append(f"MONEY UNKNOWN    {self.money_unknown()}")
        rows.append("VALUE WITHOUT MONEY")
        rows += [f"  - {v}" for v in self.value_signals_without_money()]
        rows.append("UNKNOWNS")
        rows += [f"  - {u}" for u in self.fused.unknowns] or ["  - none recorded"]
        rows.append("DISQUALIFIERS")
        rows += [f"  - {d}" for d in self.disqualifiers] or ["  - none"]
        rows.append(f"WHAT WOULD KILL IT   {self.what_would_kill_it}")
        rows.append(f"NEXT CHEAPEST TEST   {self.next_cheapest_experiment}")
        rows.append(f"BUG CLAIM            {self.bug_claim()}")
        rows.append(f"VALUE CLAIM          {self.value_claim()}")
        return "\n".join(rows)


def raw_value_map_entry(fused: FusedTarget, why_on_the_map: Iterable[str],
                        what_would_kill_it: str,
                        next_cheapest_experiment: str,
                        disqualifiers: Iterable[str] = (),
                        now: Optional[datetime] = None) -> RawValueMapEntry:
    why = tuple(why_on_the_map)
    if not why:
        raise SignalIntegrityError(
            "an entry that cannot say why it is on the map is not "
            "intelligence, it is a bookmark")
    if not what_would_kill_it.strip():
        raise SignalIntegrityError(
            "an entry must name what would take it off the map")
    if not next_cheapest_experiment.strip():
        raise SignalIntegrityError(
            "an entry must name the cheapest experiment that could kill it")
    return RawValueMapEntry(
        target=fused.target, fused=fused,
        gravity_profile=gravity(fused, now), why_on_the_map=why,
        disqualifiers=tuple(disqualifiers),
        what_would_kill_it=what_would_kill_it,
        next_cheapest_experiment=next_cheapest_experiment)


TARGET_LOCK_STATES = ("LOCKED", "WATCH", "HUMAN_REVIEW_REQUIRED",
                      "RESOLVE_CONTRADICTION_FIRST", "IGNORE")

# Below this, the pull is not strong enough to spend a unit of work on.
LOCK_THRESHOLD = 1000


@dataclass(frozen=True)
class TargetLock:
    state: str
    reasons: tuple[str, ...]

    def authorises_investigation(self) -> bool:
        """A lock is a recommendation to look, never permission to act.

        The mission gate in `opportunity.handoff()` still runs, and still
        refuses independently.
        """
        return self.state == "LOCKED"


def target_lock(entry: RawValueMapEntry) -> TargetLock:
    """Decide whether the pull earned the next unit of work.

    A disqualifier outranks any mass, and an unresolved contradiction
    outranks a strong score -- believing two incompatible things harder
    is not intelligence.
    """
    reasons: list[str] = []
    if entry.disqualifiers:
        return TargetLock("HUMAN_REVIEW_REQUIRED", (
            f"disqualifiers present ({', '.join(entry.disqualifiers)}); "
            f"no gravity may outrank a disqualifier",))
    if entry.fused.has_contradiction():
        return TargetLock("RESOLVE_CONTRADICTION_FIRST", tuple(
            c.reason for c in entry.fused.contradictions))
    if entry.fused.independent_facts < 2:
        reasons.append(
            "only one independent fact; multiplicity of sources was not "
            "multiplicity of evidence")
        return TargetLock("WATCH", tuple(reasons))
    mass = entry.gravity_profile.mass
    if mass < LOCK_THRESHOLD:
        return TargetLock("WATCH", (
            f"gravity {mass} below lock threshold {LOCK_THRESHOLD}",))
    # Name WHICH kind of evidence carried the lock. Four people asking on
    # one project and two instruments observing different dimensions are
    # both "independent facts", and a lock that will not say which one it
    # stood on is a black box with a threshold in front of it.
    if entry.fused.convergences:
        basis = (f"{entry.fused.convergences} convergent dimension(s) "
                 f"across independent instruments")
    elif entry.fused.corroborations:
        basis = (f"{entry.fused.corroborations} independent source(s) "
                 f"agreeing on one fact")
    else:
        basis = (f"{entry.fused.independent_facts} independent fact(s) in a "
                 f"SINGLE dimension -- volume, not cross-dimensional support")
    reasons.append(f"gravity {mass} from {basis}")
    reasons.append("lock recommends investigation; it does not authorise it")
    return TargetLock("LOCKED", tuple(reasons))


class LockNotEarned(ValueError):
    """A map entry tried to become a hunt without earning the lock."""


def to_opportunity(entry: "RawValueMapEntry", lock: "TargetLock",
                   activity_class: str = "ACTIVE",
                   locally_reproducible: str = "UNKNOWN") -> OpportunityReceipt:
    """Hand a locked target to the EXISTING hunter.

    There is no mission_v2 and no second investigation type. This builds
    the `OpportunityReceipt` that `opportunity.rank()` and
    `opportunity.handoff()` already consume, so a fused target enters the
    same gates as any other lead and gets refused by the same rules.

    Only the independent signals cross over. Echoes are deliberately left
    behind: carrying five copies of one fact into the hunt would rebuild,
    one layer later, exactly the inflation this module exists to prevent.
    """
    if not lock.authorises_investigation():
        raise LockNotEarned(
            f"lock state is {lock.state}; the map does not authorise its own "
            f"hunt any more than the radar does")

    seen: set[str] = set()
    carried: list[SignalEvidence] = []
    for sig in entry.fused.signals:
        key = sig.source_lineage or sig.claim_fingerprint()
        if key in seen:
            continue
        seen.add(key)
        carried.append(SignalEvidence(
            kind=sig.kind, detail=sig.claim, source_type=sig.source_type,
            source_ref=sig.source_ref))

    return OpportunityReceipt(
        opportunity_id=opportunity_id_for(entry.target, "fused"),
        target=entry.target,
        discovered_at=min(s.observed_at for s in entry.fused.signals),
        signals=tuple(carried),
        activity_class=activity_class,
        locally_reproducible=locally_reproducible,
        disqualifiers=entry.disqualifiers,
        unknowns=entry.fused.unknowns)
