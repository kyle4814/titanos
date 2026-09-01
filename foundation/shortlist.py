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

WHY `rank()`'S TIEBREAK IS NOT REPEATED HERE

`relevance.rank()` already documents its own tiebreak explicitly:
`(band rank, coverage, distinct-match count, signal_id)`, all
descending except `signal_id` ascending. This module inherits that
tiebreak by construction (it never re-sorts `rank()`'s output) rather
than re-implementing or restating the ordering logic a second time --
one sort, one place it lives.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional, Sequence, Tuple

from foundation import relevance
from foundation.relevance import BANDS, CapabilityProfile, RelevanceAssessment
from foundation.signal_spine import CanonicalSignal
from foundation.untrusted_text import neutralise

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
    "=" * 72,
)

_DISPLAY_MAX_LEN = 200
_REFERENCE_MAX_LEN = 320
_SHORT_MAX_LEN = 80


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
    note: str = (
        "SURFACE MATCH ONLY. Not a lead, not an assessed opportunity, not "
        "revenue. Verify independently before acting."
    )

    def __post_init__(self) -> None:
        if self.band not in BANDS:
            raise ValueError(f"unknown band {self.band!r}")


def _notice_reference(evidence: Mapping[str, object]) -> str:
    for key in ("publication_number", "tender_id", "ocid"):
        value = evidence.get(key)
        if value:
            return str(value)
    return ""


def _entry_from_assessment(
    assessment: RelevanceAssessment, signal: CanonicalSignal
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
    )


def build_shortlist(
    signals: Sequence[CanonicalSignal],
    profile: CapabilityProfile,
    limit: Optional[int] = None,
) -> Tuple[ShortlistEntry, ...]:
    """Score every signal against `profile` and return the ranked,
    best-first shortlist, truncated to `limit` (no truncation if `None`).

    Ordering is exactly `relevance.rank()`'s ordering -- this function
    performs no second sort, so the guarantee `rank()` already proves
    (an EXCLUDED or UNKNOWN assessment can never rank above a
    STRONG_MATCH) carries over unchanged; see module docstring.
    Deterministic: the same `signals`/`profile` produce the same output,
    in the same order, on every call, because `rank()` itself is
    deterministic and this function does not reorder its result.

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
        entries.append(_entry_from_assessment(assessment, signal))

    if limit is not None:
        entries = entries[:limit]
    return tuple(entries)


def _render_entry(position: int, entry: ShortlistEntry) -> Tuple[str, ...]:
    lines = [f"{position}. [{entry.band}] {entry.buyer} -- {entry.title}"]
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
    return tuple(lines)


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
