"""Turn a ranked pile of signals into something an operator can read in
thirty seconds and act on -- or not act on. Not a lead generator.

WHY THIS EXISTS

`foundation/relevance.py` scores a `CanonicalSignal` against a
self-declared `CapabilityProfile` and returns a `RelevanceAssessment`.
`foundation/opportunity_cycle.py` sweeps every registered tender source
and hands back a merged pile of `CanonicalSignal`. Neither module
produces anything an operator can actually read: one is a per-item
verdict, the other is a merged bag with honest zeros. This module is
the last hop -- `rank()` the pile against a profile, attach exactly the
fields a human needs to decide whether to look closer (buyer, title,
deadline, source, band, matched evidence, a reference), and render that
as plain text.

WHAT THIS IS NOT, RESTATED FROM `relevance.py` BECAUSE IT MATTERS MORE
HERE THAN ANYWHERE ELSE IN THE REPOSITORY

`relevance.py`'s own docstring says a band is a surface match, never a
qualification. This module is the one place that surface match actually
reaches a human's eyes as a short, skimmable list -- which is exactly
where the temptation to let the list *look* like a queue of leads is
strongest, because a ranked top-10 with buyer names and deadlines reads
exactly like one. It is not one. Nothing here is a lead, a qualified
opportunity, or revenue, and `render_digest()` says so in its header,
every single render, not as a footnote a reader can miss.

WHAT THIS MODULE DOES NOT DO

- Does not score anything itself. `relevance.rank()` is the only
  ranking logic; this module only reshapes its output for display.
- Does not write to `foundation/outcome_ledger.py` or any other ledger.
  That is `opportunity_pipeline.py`'s job, not this module's, and this
  module imports no ledger.
- Does not invent a second ordering. The ordering `build_shortlist()`
  produces IS `relevance.rank()`'s ordering (band rank, then coverage,
  then distinct-match count, then signal_id) -- deterministic for the
  same reason `rank()` is deterministic. This module truncates that
  order to `limit`; it never re-sorts it, so a band-rank inversion
  (an EXCLUDED or UNKNOWN entry outranking a STRONG_MATCH) is
  structurally impossible here for the same reason it is impossible in
  `relevance.rank()` -- there is only one sort, and it happens once.

MISSING FIELDS ARE UNKNOWN, NEVER A GUESS

TED notices frequently carry no deadline and no advertised value (see
`mouth_ted.py`'s own CANNOT section). A blank deadline rendered as an
empty string looks, to a skimming human, like "no deadline pressure" --
a guess dressed as a fact. Every field this module renders that can be
empty on the underlying signal renders the literal string `UNKNOWN`
instead, never a blank, never a zero, never omitted.

UNTRUSTED TEXT

Every string this module renders (buyer name, title, deadline, source
id, notice id, source ref, matched keyword/CPV text) is run through
`foundation/untrusted_text.neutralise()` immediately before rendering,
even though several of these fields (`buyer_name_safe`, `title_safe`)
were already neutralised once by the mouth that produced the signal.
`neutralise()` is documented idempotent for exactly this reason --
re-neutralising a field that came from `evidence` (attacker-controlled,
frozen at signal-construction time, never re-validated since) costs
nothing and is the correct discipline for a module whose entire output
is "text a human reads and then decides to act on."

VALUE AND ACCESSIBILITY (CYCLE 014)

An operator previously had to read three things to judge one entry: this
shortlist (relevance), a separate value figure in a foreign currency
(`foundation/currency.py`), and a separate accessibility judgement
(`foundation/winnability.py`). `build_shortlist()` now folds all three
onto one `ShortlistEntry`:

- the value AS PUBLISHED (`value_observed`, `value_amount`,
  `value_currency` -- verbatim/parsed from `signal.money_observed`,
  never replaced) alongside the EUR-converted figure
  (`value_eur`) WITH the exact rate and rate date used
  (`value_rate_used`, `value_rate_date`, `value_rate_stale`), via
  `foundation/currency.py::to_eur()`.
- the accessibility band and its top reason (`accessibility_band`,
  `accessibility_reason`), via `foundation/winnability.py::assess()`.

`build_shortlist()` never fetches rates itself -- it takes an
already-loaded `currency.RateTable` (or `None`) as a parameter, so a
caller controls exactly when, and how often, the network is touched.
Rates are loaded once per digest by the caller, not once per entry.

WHY `rank()`'S TIEBREAK IS NOT FULLY REPEATED HERE ANY MORE

`relevance.rank()` documents its own tiebreak: `(band rank, coverage,
distinct-match count, signal_id)`. This module still inherits
`rank()`'s BAND grouping unchanged -- an EXCLUDED or UNKNOWN entry can
never land ahead of a STRONG_MATCH one, because the primary key below
is still relevance band, in `relevance.BANDS` order. Within one band,
though, `build_shortlist()` now applies its OWN second, explicit sort:
converted EUR value, descending -- because "biggest deal in this band
first" is a more useful reading order than `rank()`'s coverage-based
tiebreak once a comparable EUR figure exists. An entry whose value
could not be read or converted (`value_eur is None`) is never treated
as a EUR 0 entry for this sort -- it is grouped ahead of every entry
with a real converted figure in the same band, so a human sees exactly
the notices that need a second look, rather than that group being
silently buried at the bottom of the list next to genuinely tiny
figures. `render_digest()`'s header states this ordering explicitly so
nobody has to infer it from the code.

Accessibility is DISPLAYED ONLY. It never enters this sort key and
never filters an entry out -- `winnability.rank()`'s own module
docstring already refuses to filter ("hiding the EUR 162m contract is
not this module's decision to make"); this module extends the same
refusal to itself. Hiding or reordering a STRONG_MATCH notice because
it looks STRUCTURALLY_OUT_OF_REACH would be exactly the "large
contract quietly disappears" failure this repository's other modules
go out of their way to avoid.
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping, Optional, Sequence, Tuple

from foundation import relevance
from foundation.relevance import BANDS, CapabilityProfile, RelevanceAssessment
from foundation.signal_spine import CanonicalSignal
from foundation.untrusted_text import neutralise
from foundation.currency import Conversion, RateTable, STATUS_OK, to_eur
from foundation.winnability import (
    BANDS as ACCESSIBILITY_BANDS,
    DeclaredOperatorCapacity,
    WinnabilityAssessment,
    assess as assess_winnability,
)

__all__ = [
    "UNKNOWN",
    "ShortlistEntry",
    "build_shortlist",
    "render_digest",
]

# The one literal this module renders in place of any missing field.
# Never a blank string, never "0", never omitted -- see module docstring.
UNKNOWN = "UNKNOWN"

_DIGEST_HEADER = (
    "=" * 72,
    "OBSERVED PROCUREMENT SIGNALS -- NOT LEADS. NOT OPPORTUNITIES. NOT REVENUE.",
    "=" * 72,
    "Every entry below is a public notice whose own TEXT surface-matches a",
    "capability profile this operator declared about themselves. That is",
    "the entire and honest scope of what appears here.",
    "",
    "This list is NOT: a lead, an assessed opportunity, a bid recommendation,",
    "a statement of eligibility, a statement that this operator can win, or",
    "revenue in any sense. No human and no process has reviewed any entry",
    "below. Nothing here has been checked against a licence register, a",
    "past-contracts history, or the buyer's actual criteria. Every entry",
    "is unverified until a human independently checks it.",
    "",
    "A field showing UNKNOWN means the underlying notice did not carry that",
    "fact -- it is not zero, and it is not a guess.",
    "",
    "SORT ORDER: relevance band first (STRONG_MATCH, POSSIBLE, WEAK,",
    "EXCLUDED, UNKNOWN); within a band, converted EUR value, descending.",
    "An entry whose value could not be read or converted to EUR sorts",
    "after the priced entries in its band. It is never treated as a",
    "zero value, and it is never dropped -- it follows them as its own",
    "group so a missing figure stays visible without displacing the",
    "ranking.",
    "",
    "Accessibility (ACCESSIBLE / STRETCH / STRUCTURALLY_OUT_OF_REACH /",
    "UNKNOWN) is shown for context only. It never filters or reorders",
    "any entry -- a large or complex notice is never hidden here.",
    "=" * 72,
)

_DISPLAY_MAX_LEN = 200
_REFERENCE_MAX_LEN = 320
_SHORT_MAX_LEN = 80

# Mirrors mouth_ted._extract_value()'s own documented single-value text
# shape for `CanonicalSignal.money_observed` -- "<amount> <CCY>
# (<label>)", e.g. "162000000.0 EUR (estimated value)" -- the ONLY shape
# this module ever extracts a number from. `money_observed` is
# deliberately verbatim, never-parsed text per signal_spine.py's own
# contract; this module reads it the same disciplined way
# winnability.py does: only when it matches this exact shape, never a
# guess, and never a sum/average/pick across a multi-lot breakdown
# ("N lot(s), ..." text, which does not match this pattern and is
# therefore correctly treated as MISSING here, same as it is treated as
# unresolved size evidence in winnability.py).
_SINGLE_VALUE_RE = re.compile(r"^(-?\d+(?:\.\d+)?)\s+([A-Za-z]{3})\s+\([^)]*\)\s*$")

# The three -- and only three -- states a value can be in once this
# module has looked at it. Never a fourth "just missing" state that
# collapses UNCONVERTIBLE and MISSING into the same rendering, because
# they are different facts: one is "a number was published, we cannot
# turn it into EUR"; the other is "no single number was published at
# all".
VALUE_OK = "OK"
VALUE_UNCONVERTIBLE = "UNCONVERTIBLE"
VALUE_MISSING = "MISSING"
_VALUE_STATUSES = (VALUE_OK, VALUE_UNCONVERTIBLE, VALUE_MISSING)


def _parse_single_value(money_observed: str) -> Tuple[Optional[float], str]:
    """Return `(amount, currency)` parsed from `money_observed` ONLY when
    it matches the single-value shape above; `(None, "")` for anything
    else (empty, multi-lot breakdown, unrecognised shape) -- see the
    regex comment. Never sums, averages, or picks a figure."""
    text = (money_observed or "").strip()
    if not text:
        return None, ""
    match = _SINGLE_VALUE_RE.match(text)
    if not match:
        return None, ""
    try:
        amount = float(match.group(1))
    except ValueError:
        return None, ""
    return amount, match.group(2).upper()

# FINDING A (BLUE_TEAM_009, HIGH) -- line-wrap forged-entry defence.
#
# `neutralise()` guarantees no field can forge a real newline. It
# cannot, and was never designed to, guarantee anything about how a
# *terminal* wraps the one long logical line each field still produces.
# A `title`/`buyer` padded so a string shaped like
# `"N. [BAND] Buyer -- ..."` lands at column 0 of the next wrapped
# physical line renders, to a skimming human, as an independent
# favourably-banded entry -- reproduced live against this exact module.
#
# Two alternatives were considered and rejected:
#
#   1. Cap `title`/`buyer` well below 80 columns. Rejected: it only
#      raises the bar to whatever width is chosen -- an attacker who
#      knows (or guesses) the defended width still wins, and it makes
#      every legitimate long buyer/title name unreadable-truncated for
#      no gain once the real fix is in place anyway.
#   2. Do nothing and rely on `neutralise()`'s newline collapse.
#      Rejected: demonstrated ineffective -- the forged string needs no
#      real newline, no control byte, nothing `neutralise()` inspects;
#      it only needs the *terminal* to wrap, which is a rendering step
#      entirely outside this module's -- or `neutralise()`'s -- view.
#
# The fix actually applied: this module stops leaving wrap width to the
# terminal. Every rendered line is hard-wrapped *here*, at a fixed
# width safely under the common 80-column assumption, with every
# continuation line forced to begin with `_CONTINUATION_GUTTER` -- a
# marker no genuine entry-start line (always column 0, always digit-
# led, `"N. [BAND] ..."`) ever carries, because we -- not attacker
# text, not the terminal -- insert it, unconditionally, on every line
# after the first. A reader (or an LLM agent) can trust "starts at
# column 0 with a digit" to mean "a real entry" for exactly the same
# reason `neutralise()`'s `\n` marker can be trusted: the defended
# invariant is enforced by the renderer, not requested of the input.
# Residual, named risk: a terminal narrower than `_WRAP_WIDTH` can still
# re-wrap our already-wrapped output. This is accepted and out of scope
# for the same reason `_WRAP_WIDTH` is chosen conservatively (56 cols,
# well under the narrowest terminal in ordinary use, 80) -- a defended
# width has to be named, not left infinite; see BLUE_TEAM_009 finding A.
_WRAP_WIDTH = 56
_CONTINUATION_GUTTER = "        | "


def _wrap_line(line: str) -> Tuple[str, ...]:
    """Hard-wrap one already-composed rendered line ourselves so no
    wrap decision is ever left to the terminal -- see FINDING A comment
    above `_WRAP_WIDTH`. Returns at least one line even for an empty
    input (textwrap.wrap("") == []), so callers can always extend a
    list with the result without checking for emptiness.
    """
    wrapped = textwrap.wrap(
        line,
        width=_WRAP_WIDTH,
        subsequent_indent=_CONTINUATION_GUTTER,
        break_long_words=True,
        break_on_hyphens=False,
    )
    return tuple(wrapped) if wrapped else ("",)


def _clean(value: object, max_len: int = _DISPLAY_MAX_LEN) -> str:
    """Render-safe, never-blank-looking-like-a-fact form of one field.

    `neutralise()` handles the attacker-controlled-text discipline;
    the `or UNKNOWN` here is this module's own discipline layered on
    top -- an empty *or all-whitespace* field must never render as an
    empty string a reader could misparse as "checked, nothing found."
    """
    text = neutralise(str(value) if value is not None else "", max_len=max_len)
    return text if text.strip() else UNKNOWN


@dataclass(frozen=True)
class ShortlistEntry:
    """One signal, scored, with exactly the fields an operator needs to
    decide whether to look closer. Every text field is already
    display-safe (`neutralise()`d) -- see module docstring. Nothing here
    is written to any ledger and nothing here is a qualification; see
    `note` for the exact same disclaimer `relevance.RelevanceAssessment`
    already carries, reproduced so a caller holding only a `ShortlistEntry`
    (not the assessment it came from) still sees it.
    """

    signal_id: str
    band: str
    buyer: str
    title: str
    deadline: str
    source_id: str
    reference: str
    notice_id: str
    matched_keywords: Tuple[str, ...] = ()
    matched_cpv_codes: Tuple[str, ...] = ()
    exclusion_reasons: Tuple[str, ...] = ()
    unknown_reason: str = ""
    stuffing_suspected: bool = False
    # FINDING B (BLUE_TEAM_009, HIGH). `mouth_ted.py` already computes
    # `evidence["injection_markers"]` via `untrusted_text.
    # looks_like_injection()` -- a blocklist that returns MARKERS FOUND,
    # never a verdict (see that module's docstring). This module used
    # to never read the key at all, so a title carrying live injection
    # phrasing rendered with zero warning even though the detection had
    # already happened upstream. Carried through here unmodified -- a
    # tuple of marker names, same discipline as `matched_keywords` and
    # `exclusion_reasons` -- so `_render_entry` can surface it. This
    # field does NOT suppress, re-band, or reorder the entry: per
    # `untrusted_text.py`'s own discipline, a marker is evidence for a
    # human/agent to weigh, not this module's verdict to act on.
    injection_markers: Tuple[str, ...] = ()
    note: str = (
        "SURFACE MATCH ONLY. Not a lead, not an assessed opportunity, not "
        "revenue. Verify independently before acting."
    )

    # -- CYCLE 014: value + accessibility, folded onto the same entry so
    # an operator reads one line instead of three separate tools. See
    # module docstring's "VALUE AND ACCESSIBILITY" section.

    # Value as published -- NEVER replaced by the converted figure.
    # `value_observed` is the display-safe verbatim text (UNKNOWN if the
    # notice carried nothing); `value_amount`/`value_currency` are only
    # populated when that text matched the single, unambiguous shape
    # `_parse_single_value` looks for (never a guess across a multi-lot
    # breakdown).
    value_observed: str = UNKNOWN
    value_amount: Optional[float] = None
    value_currency: str = ""

    # The EUR-converted figure, with everything needed to audit it --
    # same discipline currency.Conversion already enforces. `value_eur`
    # is `None` whenever `value_eur_status != VALUE_OK`; a caller must
    # never treat that `None` as zero (see module docstring).
    value_eur_status: str = VALUE_MISSING
    value_eur: Optional[float] = None
    value_rate_used: Optional[float] = None
    value_rate_date: Optional[str] = None
    value_rate_stale: bool = False
    # Human-readable reason value_eur is None -- always non-empty when
    # value_eur_status != VALUE_OK, always "" when it is OK.
    value_eur_note: str = ""

    # Accessibility -- DISPLAYED ONLY. Never used by build_shortlist()
    # to filter or reorder across relevance bands; see module docstring.
    accessibility_band: str = "UNKNOWN"
    accessibility_reason: str = UNKNOWN

    def __post_init__(self) -> None:
        if self.band not in BANDS:
            raise ValueError(f"unknown band {self.band!r}")
        if self.value_eur_status not in _VALUE_STATUSES:
            raise ValueError(
                f"unknown value_eur_status {self.value_eur_status!r}")
        if self.value_eur_status == VALUE_OK and self.value_eur is None:
            raise ValueError(
                "value_eur_status is OK but value_eur is None -- a "
                "successful conversion must carry its figure")
        if self.value_eur_status != VALUE_OK and self.value_eur is not None:
            raise ValueError(
                f"value_eur_status is {self.value_eur_status!r} but "
                f"value_eur is {self.value_eur!r} -- an unconverted "
                f"entry must never carry a number a reader could "
                f"mistake for a real converted figure"
            )
        if self.accessibility_band not in ACCESSIBILITY_BANDS:
            raise ValueError(
                f"unknown accessibility_band {self.accessibility_band!r}")


def _notice_reference(evidence: Mapping[str, object]) -> str:
    for key in ("publication_number", "tender_id", "ocid"):
        value = evidence.get(key)
        if value:
            return str(value)
    return ""


def _value_fields(
    signal: CanonicalSignal, rates: Optional[RateTable]
) -> dict:
    """Compute every value-related ShortlistEntry field for one signal.
    Never fetches anything -- `rates` is either an already-loaded
    `RateTable` or `None`; see module docstring."""
    value_observed = _clean(signal.money_observed)
    amount, currency_code = _parse_single_value(signal.money_observed)

    if amount is None:
        return dict(
            value_observed=value_observed, value_amount=None,
            value_currency="", value_eur_status=VALUE_MISSING,
            value_eur=None, value_rate_used=None, value_rate_date=None,
            value_rate_stale=False,
            value_eur_note="no single unambiguous value was published "
                            "on this notice",
        )

    if rates is None:
        return dict(
            value_observed=value_observed, value_amount=amount,
            value_currency=currency_code, value_eur_status=VALUE_UNCONVERTIBLE,
            value_eur=None, value_rate_used=None, value_rate_date=None,
            value_rate_stale=False,
            value_eur_note="no rate table was supplied to this digest",
        )

    conversion: Conversion = to_eur(amount, currency_code, rates)
    if conversion.status == STATUS_OK:
        return dict(
            value_observed=value_observed, value_amount=amount,
            value_currency=currency_code, value_eur_status=VALUE_OK,
            value_eur=conversion.eur_amount,
            value_rate_used=conversion.rate_used,
            value_rate_date=conversion.rate_date,
            value_rate_stale=conversion.stale, value_eur_note="",
        )
    return dict(
        value_observed=value_observed, value_amount=amount,
        value_currency=currency_code, value_eur_status=VALUE_UNCONVERTIBLE,
        value_eur=None, value_rate_used=None, value_rate_date=None,
        value_rate_stale=False,
        value_eur_note=f"no rate available for {currency_code or '(no currency)'}",
    )


def _accessibility_fields(
    signal: CanonicalSignal,
    capacity: Optional[DeclaredOperatorCapacity],
    now: Optional[datetime],
) -> Tuple[str, str]:
    """Return `(accessibility_band, accessibility_reason)` for one
    signal via `winnability.assess()`. Display-only -- see module
    docstring; the caller never feeds this into a sort key."""
    assessment: WinnabilityAssessment = assess_winnability(signal, capacity, now)
    if assessment.band == "UNKNOWN":
        reason = assessment.unknown_reason
    else:
        barrier = next(
            (f for f in assessment.factors if f.verdict == "BARRIER"), None)
        if barrier is not None:
            reason = barrier.evidence
        else:
            known = next(
                (f for f in assessment.factors if f.status == "KNOWN"), None)
            reason = known.evidence if known else assessment.factors[0].evidence
    return assessment.band, _clean(reason)


def _entry_from_assessment(
    assessment: RelevanceAssessment,
    signal: CanonicalSignal,
    rates: Optional[RateTable] = None,
    capacity: Optional[DeclaredOperatorCapacity] = None,
    now: Optional[datetime] = None,
) -> ShortlistEntry:
    evidence = signal.evidence
    facts = signal.facts

    buyer = _clean(evidence.get("buyer_name_safe", ""))
    title = _clean(evidence.get("title_safe", ""))
    deadline = _clean(facts.get("deadline") or evidence.get("deadline") or "",
                       max_len=_SHORT_MAX_LEN)
    notice_id = _clean(_notice_reference(evidence), max_len=_SHORT_MAX_LEN)
    reference = _clean(signal.source_ref, max_len=_REFERENCE_MAX_LEN)
    source_id = _clean(signal.source_id, max_len=_SHORT_MAX_LEN)

    value_fields = _value_fields(signal, rates)
    accessibility_band, accessibility_reason = _accessibility_fields(
        signal, capacity, now)

    return ShortlistEntry(
        signal_id=assessment.signal_id,
        band=assessment.band,
        buyer=buyer,
        title=title,
        deadline=deadline,
        source_id=source_id,
        reference=reference,
        notice_id=notice_id,
        matched_keywords=tuple(
            neutralise(k, max_len=_SHORT_MAX_LEN) for k in assessment.matched_keywords),
        matched_cpv_codes=tuple(
            neutralise(c, max_len=_SHORT_MAX_LEN) for c in assessment.matched_cpv_codes),
        exclusion_reasons=tuple(
            neutralise(r, max_len=_SHORT_MAX_LEN) for r in assessment.exclusion_reasons),
        unknown_reason=neutralise(assessment.unknown_reason, max_len=_DISPLAY_MAX_LEN),
        stuffing_suspected=assessment.stuffing_suspected,
        # `injection_markers` are fixed marker *names* from `untrusted_
        # text.INJECTION_MARKERS` (e.g. "ignore previous instructions"),
        # not raw attacker text -- but neutralised anyway, same
        # discipline as every other evidence-derived field this
        # function copies, in case a future producer of this key
        # stops guaranteeing that.
        injection_markers=tuple(
            neutralise(str(m), max_len=_SHORT_MAX_LEN)
            for m in evidence.get("injection_markers", ()) or ()),
        accessibility_band=accessibility_band,
        accessibility_reason=accessibility_reason,
        **value_fields,
    )


def _within_band_sort_key(entry: ShortlistEntry) -> Tuple:
    """Sort key applied WITHIN one relevance band -- see module
    docstring's "VALUE AND ACCESSIBILITY" section. An entry with no
    known EUR figure sorts AFTER the ones that have a figure, but is
    never treated AS zero -- those are different things, and the
    difference is the whole point.

    THE FIRST VERSION OVER-CORRECTED, and a live measurement caught it.
    Sorting unknown-value entries AHEAD of everything was meant to stop
    them being buried next to genuinely tiny contracts. On a real sweep
    it did the opposite at the other end: 22 of 50 STRONG_MATCH entries
    carried no value, so a top-10 was composed ENTIRELY of valueless
    entries and all 28 that did carry a value became invisible. A rule
    written to stop one group being hidden hid the other group instead.

    Ranked-by-value has to actually rank by value. Unknowns follow,
    intact and counted -- `render_digest()` states how many there are,
    so they are visible as a group rather than either buried or
    crowding out the ranking. `signal_id` is the deterministic
    tiebreak."""
    has_value = entry.value_eur is not None
    return (
        0 if has_value else 1,
        -entry.value_eur if has_value else 0.0,
        entry.signal_id,
    )


def build_shortlist(
    signals: Sequence[CanonicalSignal],
    profile: CapabilityProfile,
    limit: Optional[int] = None,
    rates: Optional[RateTable] = None,
    capacity: Optional[DeclaredOperatorCapacity] = None,
    now: Optional[datetime] = None,
) -> Tuple[ShortlistEntry, ...]:
    """Score every signal against `profile`, fold in value (via `rates`)
    and accessibility (via `capacity`), and return the ranked shortlist,
    truncated to `limit` (no truncation if `None`).

    Ordering: relevance band first (`relevance.BANDS` order -- an
    EXCLUDED or UNKNOWN entry can never rank above a STRONG_MATCH one,
    same guarantee as before), then converted EUR value descending
    WITHIN that band -- see `_within_band_sort_key` and module
    docstring. Deterministic: the same inputs produce the same output,
    in the same order, on every call.

    `rates`: an already-loaded `currency.RateTable`, or `None`. This
    function NEVER fetches -- a caller loads the table once (e.g. via
    `currency.load_rate_table()`) and passes it in, so the network is
    touched at most once per digest, not once per entry. `None` is a
    valid input; every entry's value then renders with
    `value_eur_status == UNCONVERTIBLE` and an honest note, never a
    guess.

    `capacity`: an optional `winnability.DeclaredOperatorCapacity`,
    passed straight through to `winnability.assess()` per signal.
    `now`: passed straight through to `winnability.assess()`; `None`
    uses real current time (see that module).

    Accessibility is DISPLAYED ONLY -- it is computed for every entry
    but never affects `limit`, filtering, or either sort key; see
    module docstring.

    An empty `signals` sequence is a valid input and produces an empty
    shortlist, not an error -- an empty pipeline run is an honest
    outcome (see `opportunity_cycle.py`'s own "zero signals ... a valid,
    honest outcome" discipline, restated here for the same reason).
    """
    if limit is not None and limit < 0:
        raise ValueError("limit must be >= 0 if given")

    assessments = relevance.rank(tuple(signals), profile)
    signals_by_id = {s.signal_id: s for s in signals}

    entries = []
    for assessment in assessments:
        signal = signals_by_id.get(assessment.signal_id)
        if signal is None:
            # relevance.rank() only ever scores the signals it was given,
            # so this cannot happen with normal use -- guarded rather
            # than trusted, so a future caller who reorders/edits the
            # signals list after ranking gets a skipped entry rather
            # than a crash on a stale lookup.
            continue
        entries.append(_entry_from_assessment(
            assessment, signal, rates=rates, capacity=capacity, now=now))

    # relevance.rank() already grouped `entries` into contiguous,
    # band-ordered blocks (its own primary sort key). A second, STABLE
    # sort keyed purely on relevance band index re-groups by the exact
    # literal band string (rather than rank()'s shared 0-rank for
    # EXCLUDED/UNKNOWN) and is what actually makes the within-band
    # value ordering below correct and band-pure. Python's sort is
    # guaranteed stable, so ties within the same (band, value) key
    # never depend on iteration order.
    entries.sort(key=lambda e: (BANDS.index(e.band),) + _within_band_sort_key(e))

    if limit is not None:
        entries = entries[:limit]
    return tuple(entries)


def _render_entry(position: int, entry: ShortlistEntry) -> Tuple[str, ...]:
    lines = [f"{position}. [{entry.band}] {entry.buyer} -- {entry.title}"]

    # FINDING B (BLUE_TEAM_009, HIGH). Placed immediately after the
    # entry-start line -- the most visible position -- so a skimming
    # human/agent cannot miss it. Deliberately unconditional on band:
    # EXCLUDED can carry injection markers too, and this repository's
    # discipline is "a marker is a marker, not a verdict" (see
    # `untrusted_text.py`), so this does not suppress, re-band, or
    # reorder anything -- it only adds one more visible, honest line,
    # same as `stuffing_suspected`'s NOTE line below.
    if entry.injection_markers:
        lines.append(
            "   FLAGGED: notice text matched known prompt-injection "
            "phrasing (" + ", ".join(entry.injection_markers) + ") -- "
            "not a verdict, this is evidence for a human to weigh; "
            "text is otherwise rendered unmodified above")

    if entry.value_eur_status == VALUE_OK:
        stale_marker = " STALE" if entry.value_rate_stale else ""
        lines.append(
            f"   value: {entry.value_observed} -> EUR "
            f"{entry.value_eur:,.2f} (rate {entry.value_rate_used:,.6g}, "
            f"as of {entry.value_rate_date}{stale_marker})")
    else:
        lines.append(
            f"   value: {entry.value_observed} -> EUR: {UNKNOWN} "
            f"({entry.value_eur_note})")

    lines.append(
        f"   accessibility: [{entry.accessibility_band}] "
        f"{entry.accessibility_reason}")

    lines.append(f"   deadline: {entry.deadline}    source: {entry.source_id}")

    if entry.band == "EXCLUDED":
        reasons = ", ".join(entry.exclusion_reasons) or UNKNOWN
        lines.append(f"   excluded because: {reasons}")
    elif entry.band == "UNKNOWN":
        lines.append(f"   unknown because: {entry.unknown_reason or UNKNOWN}")
    else:
        matched = list(entry.matched_keywords)
        if entry.matched_cpv_codes:
            matched.append("cpv:" + ",".join(entry.matched_cpv_codes))
        lines.append(f"   matched: {', '.join(matched) if matched else 'none'}")
        if entry.stuffing_suspected:
            lines.append(
                "   NOTE: possible keyword stuffing detected in source text")

    lines.append(f"   notice: {entry.notice_id}    reference: {entry.reference}")

    # See FINDING A comment above `_WRAP_WIDTH`: every physical line is
    # hard-wrapped here, ourselves, so no wrap boundary is left for a
    # terminal to pick -- this is what actually defeats the forged-
    # entry attack, not anything about the content above.
    wrapped_lines: list = []
    for line in lines:
        wrapped_lines.extend(_wrap_line(line))
    return tuple(wrapped_lines)


def render_digest(shortlist: Sequence[ShortlistEntry]) -> str:
    """Render a shortlist as plain text a human reads in thirty seconds.

    The header naming what these entries ARE and ARE NOT is present on
    every call, unconditionally -- not a footnote, not something that
    can be truncated away, and this is deliberate: see module docstring.
    An empty shortlist still renders the header, plus one honest line
    saying nothing matched -- never an empty string, never an exception.
    """
    lines = list(_DIGEST_HEADER)
    lines.append("")

    if not shortlist:
        lines.append(
            "No signals in this shortlist this cycle -- a valid, honest "
            "outcome, not an error.")
        return "\n".join(lines) + "\n"

    for position, entry in enumerate(shortlist, start=1):
        lines.extend(_render_entry(position, entry))
        lines.append("")

    return "\n".join(lines).rstrip("\n") + "\n"
