"""Structural accessibility of a procurement notice to a small operator.
Not a probability. Not a qualification.

WHY THIS EXISTS

`foundation/relevance.py` answers "does this notice's text surface-match
what the operator says they do?" A notice can pass that check and still
be a EUR 162,000,000 nine-figure national framework that a two-person
firm has no realistic path to win outright -- and a value-ranked list
puts exactly that notice above a EUR 30,000 municipal penetration test
that the same firm could actually deliver. Ranking by size alone is not
neutral; it actively misleads, because it treats "large" as "good"
without ever asking whether the operator can reach it.

This module answers a narrower, structural question: given what the
notice itself says (and what the operator has DECLARED about their own
capacity), is there a legible, arithmetic-level or evidence-level reason
this notice is or is not within realistic reach? It is not a forecast.

THE TRAP THIS MODULE REFUSES TO WALK INTO

This module NEVER emits a probability, a score out of ten, or the phrase
"likely to win" (or any paraphrase of it). It cannot know whether the
operator will win a given notice -- nobody can, before a bid exists, a
buyer evaluates it, and a decision is made. A module that implied
otherwise would be exactly the false certainty this repository exists to
refuse (see `foundation/relevance.py`'s own module docstring, and
`foundation/value_model.py`'s "a figure may only be as strong as its
weakest input"). What CAN be said honestly is structural: arithmetic
comparisons of declared numbers, and dates that have already been
published. "A EUR 162,000,000 framework is out of reach for a firm that
declares a EUR 2,000,000 capacity ceiling" is arithmetic, not prediction.
"A complex notice closing in three days cannot realistically receive a
newcomer's bid" is a fact about elapsed time, not a forecast about
evaluation outcomes.

WHAT `DeclaredOperatorCapacity` ACTUALLY IS

Exactly what `CapabilityProfile` is in `relevance.py`: a caller-supplied
self-report, unverified by this module. Nothing here checks it against
a bank statement, a past-contracts register, or any external authority.
An operator who overstates their own capacity ceiling will get an
optimistic assessment back -- that is a property of self-reported data,
not a defect unique to this module, and it is why `DeclaredOperatorCapacity`
is optional: an assessment with none supplied still runs, just with the
size-vs-capacity dimension honestly UNKNOWN rather than silently assuming
either extreme.

WHICH CANDIDATE SIGNALS ARE ACTUALLY AVAILABLE ON A `CanonicalSignal`

Verified against `foundation/mouth_ted.py` (the only mouth that currently
emits procurement `CanonicalSignal`s) and `foundation/signal_spine.py`
before writing a single line of assessment logic:

  AVAILABLE, used directly:
    - `facts["deadline"]` / `evidence["deadline"]` -- an ISO-8601
      timestamp string, TED's own `deadline-receipt-request`. Used for
      deadline-proximity.
    - `signal.money_state` / `signal.money_observed` -- `money_observed`
      is DELIBERATELY verbatim text, never a parsed number
      (`signal_spine.py`'s own contract: "verbatim, never parsed into a
      number"). This module parses it ONLY when the text matches one of
      `mouth_ted._extract_value()`'s own two unambiguous formats (a
      single "`<amount> <CCY> (<label>)`" string, or its "`<label>`"
      naming "framework maximum value" specifically for a framework/DPS
      ceiling field) -- and falls back to UNKNOWN rather than guessing
      whenever the text does not match one of those exact shapes (e.g.
      the honest multi-lot breakdown text, which is read for its LOT
      COUNT but never summed, averaged, or picked-from into one figure --
      the same refusal `_extract_value()` itself already makes).

  AVAILABLE, but NOT what the task brief assumed:
    - "contract size relative to a declared operator capacity" IS
      arithmetic, but only when TED gave a single unambiguous value.
      Roughly a third of live TED notices carry a genuine multi-lot
      breakdown with no aggregate (see `mouth_ted.py`'s own docstring);
      for those, size-vs-capacity is honestly UNKNOWN, not guessed from
      a sum of lot figures.
    - "whether it is a framework agreement / DPS" is NOT a field TED
      exposes as a boolean anywhere this repository requests. The one
      real, structural (not keyword-guessed) proxy available is whether
      `_extract_value()` had to fall back to the `framework-maximum-value-*`
      field (eForms BT-271) to find a number at all -- that field only
      exists on framework/DPS-shaped notices. Its PRESENCE is real
      evidence; its ABSENCE is not evidence of a discrete contract (the
      notice may be a framework that happened to report a `total-value`
      instead), so this module marks the absence UNKNOWN, never
      "discrete contract confirmed".
    - "lot count" has no dedicated field either. TED's per-lot value
      breakdown (`estimated-value-lot`) is the only place a lot count is
      derivable, and only when the notice actually falls into the
      multi-lot text branch of `value_detail`.

  NOT AVAILABLE AT ALL, structurally UNKNOWN on every notice today:
    - Contract DURATION. TED's own duration fields (eForms BT-36/BT-537)
      are not in `mouth_ted.REQUEST_FIELDS`, are not read by
      `parse_items()`, and appear nowhere on `CanonicalSignal`. This
      dimension is reported as UNKNOWN on every single assessment this
      module produces, by construction -- not a per-notice gap, a
      whole-source gap. Fixing it requires `mouth_ted.py` (owned
      elsewhere this cycle) to request and expose the field first.

NO CURRENCY CONVERSION

`amount`/`capacity.ceiling_amount` are compared only when their currency
codes match, case-insensitively, as literal strings. There is no FX-rate
source anywhere in this offline repository (per this repo's own Obelisk
Zero-Dependency audit), so a EUR contract is never compared against a
declared SEK ceiling -- that comparison is UNKNOWN, not converted at a
guessed rate.

THE "LARGE/COMPLEX" HEURISTIC IS A POLICY CONSTANT, NOT A FACT

`LARGE_VALUE_THRESHOLD` gates how many days this module treats as the
honest minimum bid-preparation window. It is applied to the raw
advertised figure regardless of currency (no FX conversion, as above),
so a large-denomination currency (SEK, HUF, ...) is systematically more
likely to cross it than its EUR-equivalent scale alone would justify.
Documented, not corrected -- correcting it needs real exchange rates,
which this module does not have.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Tuple

from foundation.signal_spine import CanonicalSignal

__all__ = [
    "BANDS",
    "DIMENSIONS",
    "LARGE_VALUE_THRESHOLD",
    "SMALL_CONTRACT_MIN_DAYS",
    "LARGE_CONTRACT_MIN_DAYS",
    "CAPACITY_RATIO_BARRIER",
    "LARGE_LOT_COUNT",
    "WinnabilityIntegrityError",
    "DeclaredOperatorCapacity",
    "WinnabilityFactor",
    "WinnabilityAssessment",
    "assess",
    "rank",
]


class WinnabilityIntegrityError(ValueError):
    """A caller tried to make this module claim more than structural fact."""


# Deliberately small, deliberately not `relevance.py`'s vocabulary and not
# the outcome ledger's vocabulary -- this is a different question again
# ("can a small firm structurally reach this?" vs. "does the text match?"
# vs. "did an outcome happen?").
#
#   ACCESSIBLE                  no structural barrier found in what is
#                                known; genuinely reduced confidence when
#                                large parts of the picture are UNKNOWN
#                                (see STRETCH below).
#   STRETCH                     either a genuine barrier was found but a
#                                real mitigating structural fact (a
#                                framework/DPS a firm could join later)
#                                tempers it, OR too much of the picture
#                                is UNKNOWN to call it clean ACCESSIBLE.
#   STRUCTURALLY_OUT_OF_REACH   a hard structural barrier was found and
#                                nothing in the notice's own facts
#                                tempers it.
#   UNKNOWN                     none of the accessibility-relevant facts
#                                (size vs. capacity, deadline, lot
#                                division) could be read from this
#                                notice at all. Never conflated with
#                                STRUCTURALLY_OUT_OF_REACH -- that band
#                                means "we looked and found a barrier",
#                                this one means "there was nothing to
#                                look at".
BANDS = ("ACCESSIBLE", "STRETCH", "STRUCTURALLY_OUT_OF_REACH", "UNKNOWN")

# The four dimensions this module ever assesses. `contract_duration` is
# always UNKNOWN today -- see module docstring's "NOT AVAILABLE AT ALL"
# section. Listed explicitly so a reader (and a test) can enumerate every
# dimension a `WinnabilityAssessment` is required to carry.
DIMENSIONS = (
    "contract_size_vs_declared_capacity",
    "deadline_proximity",
    "procurement_vehicle",
    "lot_division",
    "contract_duration",
)

_FACTOR_STATUSES = ("KNOWN", "UNKNOWN")
_FACTOR_VERDICTS = ("BARRIER", "NOT_BARRIER", "INFO")

# ---------------------------------------------------------------------
# Policy constants. Every one of these is a judgment call this module
# makes explicit and documents, never a fact discovered in a notice.
# ---------------------------------------------------------------------

# Advertised value at/above this (raw figure, no currency conversion --
# see module docstring) is treated as "large/complex" for the purpose of
# picking the deadline-proximity minimum window below.
LARGE_VALUE_THRESHOLD = 5_000_000.0

# Minimum days-to-deadline this module treats as a workable preparation
# window for a small, simple, single-lot notice.
SMALL_CONTRACT_MIN_DAYS = 10

# Minimum days-to-deadline for a notice this module has classified as
# large/complex (by value, by framework/DPS marker, or by a large lot
# count).
LARGE_CONTRACT_MIN_DAYS = 28

# Advertised value more than this multiple of the operator's declared
# capacity ceiling is treated as a structural barrier. Arbitrary but
# documented: ten times a declared ceiling is far beyond "stretch
# assignment" territory for any self-reported capacity figure.
CAPACITY_RATIO_BARRIER = 10.0

# A multi-lot notice with at least this many lots is treated as
# "large/complex" for deadline-proximity purposes even when no single
# aggregate value could be read (a real aggregate procurement, not
# guessed from summing the lots).
LARGE_LOT_COUNT = 5

_MULTI_LOT_RE = re.compile(r"^(\d+)\s+lot\(s\),")
# THE LABEL IS OPTIONAL, BECAUSE ONE SOURCE DOES NOT WRITE ONE.
#
# This required a parenthesised label, which is mouth_ted's shape:
#     "50000000 EUR (total value)"
# tender_radar (UK Contracts Finder) emits no label:
#     "50000000 GBP"
# so EVERY UK signal silently lost its amount on ordinary real data, with
# no attacker involved.
#
# Blue-team pass 014 reproduced the consequence end to end: an identical
# 50,000,000 contract, 25x over a declared 2,000,000 ceiling and closing in
# 15 days, came back STRUCTURALLY_OUT_OF_REACH through TED and STRETCH
# through the UK mouth -- and STRETCH outranks STRUCTURALLY_OUT_OF_REACH,
# so the SAME deal was placed higher in the operator's list purely because
# of which feed carried it.
#
# A parser that knows one producer's format and silently degrades on
# another's is a cross-source consistency bug wearing a formatting bug's
# clothes.
_SINGLE_VALUE_RE = re.compile(
    r"^(-?\d+(?:\.\d+)?)\s+([A-Za-z]{3})(?:\s+\(([^)]*)\))?\s*$")


@dataclass(frozen=True)
class DeclaredOperatorCapacity:
    """A caller-supplied CLAIM about what this operator can realistically
    deliver. Not a verified fact -- exactly the same status as
    `relevance.CapabilityProfile`. See that module's docstring for the
    full reasoning; it applies here unchanged.

    `ceiling_amount`/`ceiling_currency` describe the largest single
    contract value the operator believes they could realistically
    deliver alone -- not their total annual revenue, not their total
    pipeline capacity across many simultaneous contracts. That framing
    is the caller's responsibility; this module only does arithmetic on
    whatever number it is given.
    """

    name: str
    declared_by: str
    ceiling_amount: float
    ceiling_currency: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise WinnabilityIntegrityError(
                "a declared operator capacity must be named")
        if not self.declared_by.strip():
            raise WinnabilityIntegrityError(
                "a declared operator capacity must record who declared it "
                "-- an unattributed self-report cannot be weighed by a reader")
        if not self.ceiling_currency.strip():
            raise WinnabilityIntegrityError(
                "a declared capacity ceiling must name its currency; a "
                "bare number cannot be compared to anything")
        if self.ceiling_amount <= 0:
            raise WinnabilityIntegrityError(
                "a declared capacity ceiling must be a positive amount")
        object.__setattr__(self, "ceiling_currency",
                            self.ceiling_currency.strip().upper())


@dataclass(frozen=True)
class WinnabilityFactor:
    """One dimension's verdict, with the evidence a reader can inspect
    and disagree with. There is no hidden score anywhere in this module
    -- every band traces back to a tuple of these.
    """

    dimension: str
    status: str            # KNOWN / UNKNOWN
    verdict: str            # BARRIER / NOT_BARRIER / INFO
    evidence: str

    def __post_init__(self) -> None:
        if self.dimension not in DIMENSIONS:
            raise WinnabilityIntegrityError(
                f"unknown dimension {self.dimension!r}")
        if self.status not in _FACTOR_STATUSES:
            raise WinnabilityIntegrityError(
                f"unknown factor status {self.status!r}")
        if self.verdict not in _FACTOR_VERDICTS:
            raise WinnabilityIntegrityError(
                f"unknown factor verdict {self.verdict!r}")
        if not self.evidence.strip():
            raise WinnabilityIntegrityError(
                f"factor {self.dimension!r} carries no evidence -- a "
                f"verdict with nothing a reader can check is not a "
                f"verdict, it is an assertion")
        if self.status == "UNKNOWN" and self.verdict != "INFO":
            raise WinnabilityIntegrityError(
                f"factor {self.dimension!r} is UNKNOWN but claims verdict "
                f"{self.verdict!r} -- an unresolved dimension cannot also "
                f"be a BARRIER or NOT_BARRIER")


_DISCLAIMER = (
    "STRUCTURAL ACCESSIBILITY ONLY. This band reflects arithmetic and "
    "dated facts already present in the notice (and, if supplied, in the "
    "operator's own declared capacity) -- it is not a prediction of the "
    "outcome of any bid, and no code in this module estimates one. "
    "Missing facts reduce confidence (toward STRETCH or UNKNOWN); they "
    "are never treated as evidence of accessibility either way. Verify "
    "independently before acting."
)


@dataclass(frozen=True)
class WinnabilityAssessment:
    """A structural-accessibility verdict for one signal.

    Every dimension in `DIMENSIONS` is represented exactly once in
    `factors`, in that fixed order, whether or not it could be resolved
    -- so a reader can always see what was checked, not just what
    happened to produce a positive result.
    """

    signal_id: str
    operator_name: str
    band: str
    factors: Tuple[WinnabilityFactor, ...] = ()
    unknown_reason: str = ""
    note: str = _DISCLAIMER

    def __post_init__(self) -> None:
        if self.band not in BANDS:
            raise WinnabilityIntegrityError(f"unknown band {self.band!r}")
        present = tuple(f.dimension for f in self.factors)
        if present != DIMENSIONS:
            raise WinnabilityIntegrityError(
                f"an assessment must carry exactly one factor per "
                f"dimension, in DIMENSIONS order; got {present!r}")
        if self.band == "UNKNOWN" and not self.unknown_reason.strip():
            raise WinnabilityIntegrityError(
                "an UNKNOWN assessment must name why nothing was "
                "resolvable -- UNKNOWN is not allowed to be a silent zero")
        lowered = " ".join(
            [self.note] + [f.evidence for f in self.factors]
        ).lower()
        for banned in ("probability", "likely to win", "% chance",
                       "chance of winning", "odds of winning",
                       "score out of 10", "win rate"):
            if banned in lowered:
                raise WinnabilityIntegrityError(
                    f"assessment text contains {banned!r} -- this module "
                    f"may never imply a probability of winning")

    def factor(self, dimension: str) -> WinnabilityFactor:
        for f in self.factors:
            if f.dimension == dimension:
                return f
        raise KeyError(dimension)  # pragma: no cover -- unreachable given __post_init__


def _parse_deadline(raw: str) -> Optional[datetime]:
    if not raw or not raw.strip():
        return None
    try:
        dt = datetime.fromisoformat(raw.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _parse_money(money_observed: str) -> Tuple[Optional[float], str,
                                                 Optional[int], bool]:
    """Return `(amount, currency, lot_count, framework_marker)`.

    `amount`/`currency` are populated ONLY when `money_observed` matches
    `mouth_ted._extract_value()`'s exact single-value text shape
    (`"<amount> <CCY> (<label>)"`). `lot_count` is populated ONLY when it
    matches the exact multi-lot shape (`"<N> lot(s), ..."`) -- the total
    is never summed, averaged, or picked from in that case, matching
    `_extract_value()`'s own refusal. `framework_marker` is True when the
    label naming the value explicitly says "framework maximum value"
    (TED's own BT-271 field name, read by `_extract_value()` only when no
    other value field was present) -- real structural evidence of a
    framework/DPS-shaped notice, not a keyword guess against free text.
    """
    text = (money_observed or "").strip()
    if not text:
        return None, "", None, False

    multi = _MULTI_LOT_RE.match(text)
    if multi:
        lot_count = int(multi.group(1))
        framework = "framework maximum value" in text.lower()
        return None, "", lot_count, framework

    single = _SINGLE_VALUE_RE.match(text)
    if single:
        try:
            amount = float(single.group(1))
        except ValueError:
            amount = None
        # A NEGATIVE CONTRACT VALUE IS NOT A SMALL CONTRACT.
        #
        # Only `== 0` was rejected upstream, so a negative amount reached
        # the size assessment and produced NOT_BARRIER -- "within reach on
        # arithmetic alone" -- off a nonsensical negative ratio against the
        # declared ceiling. Any negative is below any positive capacity, so
        # the arithmetic is technically correct and completely wrong.
        #
        # A negative value means the feed is malformed or hostile. That is
        # an information gap, so it becomes UNKNOWN and lands in STRETCH,
        # where a human looks -- not ACCESSIBLE, where they do not.
        if amount is not None and amount < 0:
            amount = None
        currency = single.group(2).upper()
        # The label is optional; the UK mouth emits none.
        label = (single.group(3) or "").lower()
        framework = "framework maximum value" in label
        return amount, currency, None, framework

    return None, "", None, False


def _looks_complex(amount: Optional[float], currency: str,
                    lot_count: Optional[int], framework_marker: bool) -> bool:
    if framework_marker:
        return True
    if lot_count is not None and lot_count >= LARGE_LOT_COUNT:
        return True
    if amount is not None and amount >= LARGE_VALUE_THRESHOLD:
        return True
    return False


def _assess_size(signal: CanonicalSignal,
                  capacity: Optional[DeclaredOperatorCapacity],
                  amount: Optional[float], currency: str) -> WinnabilityFactor:
    dim = "contract_size_vs_declared_capacity"
    if capacity is None:
        return WinnabilityFactor(
            dimension=dim, status="UNKNOWN", verdict="INFO",
            evidence="no operator capacity was declared for this "
                     "assessment -- size cannot be weighed against "
                     "nothing")
    if amount is None:
        return WinnabilityFactor(
            dimension=dim, status="UNKNOWN", verdict="INFO",
            evidence=(
                f"no single unambiguous contract value could be read from "
                f"this notice (money_state={signal.money_state!r}, "
                f"money_observed={signal.money_observed or '(not observed)'!r})"
            ))
    if currency.upper() != capacity.ceiling_currency:
        return WinnabilityFactor(
            dimension=dim, status="UNKNOWN", verdict="INFO",
            evidence=(
                f"advertised currency ({currency}) does not match the "
                f"declared capacity currency ({capacity.ceiling_currency}); "
                f"no exchange-rate conversion is performed by this module"
            ))
    ratio = amount / capacity.ceiling_amount
    if ratio >= CAPACITY_RATIO_BARRIER:
        return WinnabilityFactor(
            dimension=dim, status="KNOWN", verdict="BARRIER",
            evidence=(
                f"advertised value {amount:,g} {currency} is {ratio:.1f}x "
                f"{capacity.declared_by}'s declared capacity ceiling of "
                f"{capacity.ceiling_amount:,g} {capacity.ceiling_currency} "
                f"-- structurally out of reach on arithmetic alone"
            ))
    return WinnabilityFactor(
        dimension=dim, status="KNOWN", verdict="NOT_BARRIER",
        evidence=(
            f"advertised value {amount:,g} {currency} is {ratio:.1f}x "
            f"{capacity.declared_by}'s declared capacity ceiling of "
            f"{capacity.ceiling_amount:,g} {capacity.ceiling_currency} "
            f"-- within reach on arithmetic alone"
        ))


def _assess_deadline(signal: CanonicalSignal, now: datetime,
                      complex_notice: bool) -> WinnabilityFactor:
    dim = "deadline_proximity"
    raw = signal.facts.get("deadline", "") or ""
    deadline = _parse_deadline(raw)
    if deadline is None:
        return WinnabilityFactor(
            dimension=dim, status="UNKNOWN", verdict="INFO",
            evidence=(
                "no parseable deadline-receipt-request was present on "
                f"this notice (raw value: {raw or '(empty)'!r})"))
    days_remaining = (deadline - now).total_seconds() / 86400.0
    min_days = LARGE_CONTRACT_MIN_DAYS if complex_notice else SMALL_CONTRACT_MIN_DAYS
    scale = "scale/complexity" if complex_notice else "size"
    if days_remaining < 0:
        return WinnabilityFactor(
            dimension=dim, status="KNOWN", verdict="BARRIER",
            evidence=(
                f"deadline {raw} has already passed relative to this "
                f"assessment's reference time -- no bid window remains"))
    if days_remaining < min_days:
        return WinnabilityFactor(
            dimension=dim, status="KNOWN", verdict="BARRIER",
            evidence=(
                f"closes in {days_remaining:.0f} day(s) ({raw}); this "
                f"repository treats {min_days} days as the honest minimum "
                f"preparation window for a notice of this {scale}"))
    return WinnabilityFactor(
        dimension=dim, status="KNOWN", verdict="NOT_BARRIER",
        evidence=(
            f"closes in {days_remaining:.0f} day(s) ({raw}); at or above "
            f"the {min_days}-day minimum this repository treats as "
            f"workable preparation time for a notice of this {scale}"))


def _assess_vehicle(framework_marker: bool, money_observed: str) -> WinnabilityFactor:
    dim = "procurement_vehicle"
    if framework_marker:
        return WinnabilityFactor(
            dimension=dim, status="KNOWN", verdict="INFO",
            evidence=(
                "this notice's own advertised value came from TED's "
                "framework-maximum-value field (eForms BT-271) -- a "
                "framework agreement or DPS with a stated ceiling, not a "
                "single discrete award; a firm may be able to join it "
                "later even though the ceiling figure alone is out of "
                "reach for one bid"))
    return WinnabilityFactor(
        dimension=dim, status="UNKNOWN", verdict="INFO",
        evidence=(
            "no framework/DPS-specific value field (BT-271) was the "
            "source of this notice's advertised value; this does NOT "
            "confirm the notice is a single discrete contract -- TED "
            "exposes no dedicated framework/DPS flag this repository "
            "requests, so absence of the marker is unresolved, not "
            "evidence of a discrete contract"))


def _assess_lots(amount: Optional[float], lot_count: Optional[int],
                  money_observed: str) -> WinnabilityFactor:
    dim = "lot_division"
    if lot_count is not None:
        return WinnabilityFactor(
            dimension=dim, status="KNOWN", verdict="NOT_BARRIER",
            evidence=(
                f"TED's own value breakdown shows {lot_count} separate "
                f"lots on this notice ({money_observed}) -- lot division "
                f"is the standard mechanism by which a large procurement "
                f"becomes accessible to a smaller firm bidding one lot "
                f"rather than the whole notice"))
    if amount is not None:
        return WinnabilityFactor(
            dimension=dim, status="KNOWN", verdict="INFO",
            evidence=(
                "a single total value was advertised with no per-lot "
                "breakdown; this notice does not show as divided into "
                "lots from the fields available"))
    return WinnabilityFactor(
        dimension=dim, status="UNKNOWN", verdict="INFO",
        evidence=(
            "no TED value field was populated for this notice, so lot "
            "division cannot be read either"))


_DURATION_FACTOR = WinnabilityFactor(
    dimension="contract_duration", status="UNKNOWN", verdict="INFO",
    evidence=(
        "contract duration is not among the fields foundation/mouth_ted.py "
        "requests or exposes on a CanonicalSignal (TED's own BT-36/BT-537 "
        "duration fields are not fetched) -- this dimension is UNKNOWN on "
        "every assessment this module can currently produce, not a "
        "per-notice gap"))


def assess(signal: CanonicalSignal,
           capacity: Optional[DeclaredOperatorCapacity] = None,
           now: Optional[datetime] = None) -> WinnabilityAssessment:
    """Assess one signal's structural accessibility. Never mutates
    `signal` or `capacity`. Never writes anywhere -- no side effects
    beyond returning a value, same discipline as `relevance.score()`.
    """
    ref_now = now or datetime.now(timezone.utc)
    if ref_now.tzinfo is None:
        ref_now = ref_now.replace(tzinfo=timezone.utc)

    amount, currency, lot_count, framework_marker = _parse_money(
        signal.money_observed)
    complex_notice = _looks_complex(amount, currency, lot_count, framework_marker)

    size_factor = _assess_size(signal, capacity, amount, currency)
    deadline_factor = _assess_deadline(signal, ref_now, complex_notice)
    vehicle_factor = _assess_vehicle(framework_marker, signal.money_observed)
    lot_factor = _assess_lots(amount, lot_count, signal.money_observed)

    factors = (size_factor, deadline_factor, vehicle_factor, lot_factor,
               _DURATION_FACTOR)

    scoring = (size_factor, deadline_factor, lot_factor)
    known = tuple(f for f in scoring if f.status == "KNOWN")
    barriers = tuple(f for f in known if f.verdict == "BARRIER")

    if not known:
        band = "UNKNOWN"
        unknown_reason = (
            "none of contract size vs. declared capacity, deadline "
            "proximity, or lot division could be read from this notice")
    elif barriers:
        non_size_barriers = tuple(
            b for b in barriers
            if b.dimension != "contract_size_vs_declared_capacity")
        if non_size_barriers:
            band = "STRUCTURALLY_OUT_OF_REACH"
        elif vehicle_factor.status == "KNOWN":
            # Only a size barrier fired, and the notice is a confirmed
            # framework/DPS -- joinable later, so tempered to STRETCH
            # rather than called fully out of reach.
            band = "STRETCH"
        else:
            band = "STRUCTURALLY_OUT_OF_REACH"
        unknown_reason = ""
    elif len(known) < len(scoring):
        band = "STRETCH"
        unknown_reason = ""
    else:
        band = "ACCESSIBLE"
        unknown_reason = ""

    return WinnabilityAssessment(
        signal_id=signal.signal_id,
        operator_name=capacity.name if capacity else "",
        band=band,
        factors=factors,
        unknown_reason=unknown_reason,
    )


_BAND_RANK = {"ACCESSIBLE": 3, "STRETCH": 2, "UNKNOWN": 1,
              "STRUCTURALLY_OUT_OF_REACH": 0}


def rank(signals, capacity: Optional[DeclaredOperatorCapacity] = None,
          now: Optional[datetime] = None) -> Tuple[WinnabilityAssessment, ...]:
    """Assess every signal and return assessments ordered most- to
    least-accessible. This orders; it does not filter -- every signal
    handed in comes back out exactly once, including
    STRUCTURALLY_OUT_OF_REACH ones. Hiding the EUR 162m contract is not
    this module's decision to make.
    """
    assessments = [assess(s, capacity, now) for s in signals]
    return tuple(sorted(
        assessments,
        key=lambda a: (-_BAND_RANK[a.band], a.signal_id),
    ))
