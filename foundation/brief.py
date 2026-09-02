"""The output layer -- what an operator actually reads each morning.

WHY THIS EXISTS
----------------
`hunt.py` produces a `HuntReport`: every notice, banded, in a fixed
order, nothing collapsed into a score. That is the right shape for a
machine or a careful reader working top to bottom. It is the wrong shape
for someone with two minutes before their first meeting -- they need to
be told, in order: what closes soon enough to matter today, what showed
up since they last looked, what is stuck and needs one click to unstick,
and what to stop thinking about entirely.

`build_brief()` reshapes one `HuntReport` into that four-section
`Brief`; `render_brief()` renders it as plain text. Neither function
scores, re-bands, or re-orders a notice's own verdict -- every fact in a
`Brief` traces back to a field `hunt.py`, `qualification.py`, or
`eligibility.py` already computed. This module adds exactly one new
kind of judgment: "does this deserve the operator's attention today,
and in what order."

WHAT THIS IS NOT, RESTATED FROM `shortlist.py` BECAUSE IT MATTERS MOST
HERE
------------------------------------------------------------------------
`shortlist.py`'s digest header says its list is not a lead, not an
assessed opportunity, not revenue, and states it every render, not as a
footnote. A morning brief is the single most tempting place in this
whole repository to soften that -- a short, ranked, "here's what needs
you today" list reads exactly like a queue of leads even when every
individual fact in it is honest. It is not one. A `QUALIFIED` band is
still only a statement that no PUBLISHED criterion blocks this operator;
it is not a bid recommendation and it is not revenue. `render_brief()`
carries the same discipline forward, unconditionally, every render.

The words "lead", "opportunity", and "prospect" never appear anywhere
this module renders for an unassessed notice -- enforced by
`foundation/tests/test_brief.py::TestVocabularyDiscipline`, not merely
asserted here. A public notice is a public notice.

HONESTY RULES THIS MODULE ENFORCES
------------------------------------
- Never invents a deadline, a value, or a count. A deadline this module
  cannot read from the underlying signal is `UNKNOWN`, rendered as the
  literal string `UNKNOWN`, never a blank and never a fabricated date.
- An `UNKNOWN` deadline is treated as URGENT, never as safe -- it sorts
  into ACTION REQUIRED unconditionally, ahead of every entry with a real
  number, because "we don't know when this closes" is a worse position
  to be in than "this closes in 3 days", not a better one.
- An empty section says so in one plain sentence. It is never padded
  with an invented entry, and a fully empty brief ("nothing closing,
  nothing new, nothing unresolved, nothing blocked") is treated as a
  valid, useful result, not something to apologise for.

WHERE A DEADLINE ACTUALLY COMES FROM
---------------------------------------
`HuntEntry` carries no deadline field of its own -- `qualification.py`
and `eligibility.py` deliberately do not read TED's `deadline-receipt-
request` field (see `eligibility.py`'s own scope). The one place a
deadline reaches a `HuntEntry` is `entry.signal.facts["deadline"]`, and
`entry.signal` is only populated when `hunt()` was called with a
`capability` profile (see `hunt.py`'s docstring on `relevance`/`signal`
being additive, optional colour). Calling `build_brief()` on a report
built WITHOUT a capability profile is not an error -- every entry then
has an `UNKNOWN` deadline, which per the rule above means every non-
blocked entry surfaces in ACTION REQUIRED. That is the honest behaviour
for "we genuinely don't know when any of these close," not a defect in
this module.

FILE TERRITORY
---------------
This module owns exactly `foundation/brief.py` and
`foundation/tests/test_brief.py`. It imports `HuntReport`/`HuntEntry`
from `hunt.py` and reads `EligibilityAssessment`/`QualificationResult`
fields those already computed -- it does not edit `hunt.py`,
`shortlist.py`, `qualification.py`, or `eligibility.py`, and it performs
no network I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Optional, Sequence, Tuple

from foundation.hunt import HuntEntry, HuntReport
from foundation.notice_class import classify_notice

__all__ = [
    "BriefIntegrityError",
    "DeadlineEntry",
    "NewEntry",
    "UnresolvedEntry",
    "BlockedEntry",
    "Brief",
    "build_brief",
    "render_brief",
]


class BriefIntegrityError(ValueError):
    """Raised when a caller asks this module to build or render a brief
    it cannot honestly support -- a non-`HuntReport` input, a negative
    window, or an internal entry whose own fields contradict each
    other (e.g. a BLOCKED entry with no quoted clause)."""


# Never used to describe an unassessed public notice anywhere this
# module renders text. See module docstring and
# `test_brief.py::TestVocabularyDiscipline`, which greps for these.
_FORBIDDEN_WORDS = ("lead", "opportunity", "prospect")

UNKNOWN = "UNKNOWN"


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


# Fact keys that carry a closing date, in priority order.
#
# WHY MORE THAN ONE -- measured live 2026-09-02. A multi-source brief
# across TED + NZ GETS + UK Contracts Finder put all 30 NZ notices into
# ACTION REQUIRED with "closes in: UNKNOWN -- treat as urgent". That
# looked like the honest-unknown rule working. It was a mapping bug:
# GETS publishes a real closing date on every notice and
# `mouth_gets_nz.gets_signal()` carries it as `close_date`, while
# `mouth_ted.ted_signal()` uses `deadline`. This module read only
# `deadline`, so a source with perfectly good dates read as a source
# with none.
#
# The failure direction was safe -- unknown urgency sorts as urgent --
# which is exactly why it was invisible until a live run: nothing threw,
# nothing looked wrong, and the brief just quietly filled its most
# important section with noise. A rule that is safe when it fires is
# still a defect when it fires for the wrong reason.
_DEADLINE_FACT_KEYS = ("deadline", "close_date")

# Non-ISO closing-date formats a real source actually emits.
_NON_ISO_DEADLINE_FORMATS = (
    "%A, %d %B %Y %I:%M %p %z",   # NZ GETS
)


def _notice_class_of(entry) -> str:
    """The entry's notice class, or "" when the source said nothing.

    WHY THE BRIEF NEEDS THIS: five Irish tenders closed at EUR400,000 to
    EUR2,600,000 turnover and three notices with NO qualification
    barrier all scored INSUFFICIENT_DATA identically, because none
    published structured criteria. Ranking them together told the
    operator to spend equal attention on a door and a wall.

    A MARKET_ENGAGEMENT notice is answerable by anyone; a COMPETITIVE
    one may not be. That distinction belongs in front of the operator,
    not in a module nothing calls -- this repository already documents
    what happens to capabilities with no production caller.
    """
    elig = entry.eligibility
    title = ""
    tm = getattr(elig, "notice_title", None)
    if isinstance(tm, dict):
        for texts in tm.values():
            if texts:
                title = str(texts[0])
                break
    procedure = getattr(elig, "procedure_type_label", None) or \
        getattr(elig, "procedure_type_code", None) or ""
    c = classify_notice(title=title, procedure=str(procedure))
    return "" if c.notice_class == "UNKNOWN" else c.notice_class


def _title_of(entry) -> str:
    """A human-readable name for a notice, or "" if the source gave none.

    WHY THIS EXISTS: a live multi-source brief rendered every NZ entry as
    a bare `https://www.gets.govt.nz//DC/ExternalTenderDetails.htm?id=...`
    with no title. An operator cannot act on that -- they cannot even
    tell whether it is worth clicking. The titles were present all along;
    `eligibility._text_map()` silently dropped tuple-shaped values, so
    every non-TED source arrived with `notice_title=None`.

    That is fixed at the source. This renders what now survives, and
    returns "" rather than a placeholder when a notice genuinely has no
    title -- a fabricated name would be worse than an honest URL.
    """
    title_map = getattr(entry.eligibility, "notice_title", None)
    if not isinstance(title_map, dict):
        return ""
    for lang in ("eng", "ENG", "en"):
        texts = title_map.get(lang)
        if texts:
            return str(texts[0])
    for texts in title_map.values():
        if texts:
            return str(texts[0])
    return ""


def _raw_deadline(entry) -> str:
    """The closing date a `HuntEntry`'s signal carries, whichever key
    its source uses. Returns "" when the signal genuinely has none --
    which then means UNKNOWN, and UNKNOWN still means urgent."""
    if entry.signal is None:
        return ""
    facts = entry.signal.facts
    for key in _DEADLINE_FACT_KEYS:
        value = str(facts.get(key) or "").strip()
        if value:
            return value
    return ""


def _parse_deadline(raw: str) -> Optional[datetime]:
    """Parse a TED-shaped ISO-8601 deadline string. Returns `None` for
    anything empty, malformed, or otherwise unparseable -- NEVER raises,
    because an unparseable deadline is a real, expected, honest UNKNOWN
    state for this module, not a programming error.

    TED emits both trailing-`Z` ("2026-10-01T00:00:00Z") and explicit-
    offset ("2026-09-09T12:00:00+03:00") forms -- see
    `foundation/tests/test_mouth_ted.py`. `datetime.fromisoformat`
    does not accept a trailing `Z` on the Python versions this
    repository targets, so it is normalised to `+00:00` first.
    """
    text = (raw or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return _as_utc(datetime.fromisoformat(text))
    except ValueError:
        pass
    # NZ GETS publishes a human-readable date, not ISO-8601 --
    # "Monday, 31 December 2029 5:00 PM +13:00", confirmed live
    # 2026-09-02. Parsed explicitly rather than by loosening the ISO
    # path, so a genuinely malformed date still returns None instead of
    # being coerced into a plausible-looking wrong one.
    for fmt in _NON_ISO_DEADLINE_FORMATS:
        try:
            return _as_utc(datetime.strptime(text, fmt))
        except ValueError:
            continue
    return None


def _days_remaining(deadline: datetime, now: datetime) -> int:
    """Whole calendar days between `now` and `deadline`, both already
    normalised to UTC. Deliberately date-based, not second-based -- a
    deadline later today should not sort as "0.3 days", it should read
    as "0 days" (today)."""
    return (deadline.date() - now.date()).days


@dataclass(frozen=True)
class DeadlineEntry:
    """One notice in ACTION REQUIRED. `days_remaining` is `None` exactly
    when `deadline_display` is `UNKNOWN` -- never a fabricated number
    standing in for an unparseable or absent date."""

    publication_number: str
    band: str
    days_remaining: Optional[int]
    deadline_display: str
    notice_url: str

    # Human-readable name, or "" when the source published none.
    # Defaulted and last so every existing positional construction
    # keeps working -- see _title_of() for why this field exists.
    title: str = ""

    # Notice class from `notice_class.py`, "" when the source said
    # nothing. Defaulted and last so existing constructions still work.
    notice_class: str = ""

    def __post_init__(self) -> None:
        if not self.publication_number.strip():
            raise BriefIntegrityError(
                "a deadline entry must name the notice it is about")
        if self.band not in ("QUALIFIED", "INSUFFICIENT_DATA"):
            raise BriefIntegrityError(
                f"ACTION REQUIRED never carries a DISQUALIFIED entry -- "
                f"a blocked notice needs no action, got band {self.band!r}")
        if (self.days_remaining is None) != (self.deadline_display == UNKNOWN):
            raise BriefIntegrityError(
                "days_remaining must be None exactly when deadline_display "
                "is UNKNOWN -- a numeric urgency without an UNKNOWN label, "
                "or vice versa, is a contradiction between this entry's own "
                "fields")
        if self.days_remaining is not None and self.days_remaining < 0:
            raise BriefIntegrityError(
                "a deadline already in the past is not an action-required "
                "entry -- it should have been excluded, not carried through "
                "with a negative count")


@dataclass(frozen=True)
class NewEntry:
    """One notice appearing in this brief that was not in the caller-
    supplied prior state. Carries only identity fields -- an operator
    who wants full detail follows `notice_url`."""

    publication_number: str
    band: str
    notice_url: str

    # Human-readable name, or "" when the source published none.
    # Defaulted and last so every existing positional construction
    # keeps working -- see _title_of() for why this field exists.
    title: str = ""

    # Notice class from `notice_class.py`, "" when the source said
    # nothing. Defaulted and last so existing constructions still work.
    notice_class: str = ""

    def __post_init__(self) -> None:
        if not self.publication_number.strip():
            raise BriefIntegrityError(
                "a new entry must name the notice it is about")


@dataclass(frozen=True)
class UnresolvedEntry:
    """One INSUFFICIENT_DATA notice. `document_url` is the highest-value
    field on this whole module: the exact link a human opens to turn
    'we don't know' into an answer. Never fabricated -- `UNKNOWN` when
    this notice genuinely carries no document or notice URL at all."""

    publication_number: str
    document_url: str
    unresolved_dimensions: Tuple[str, ...]

    # Human-readable name, or "" when the source published none.
    # Defaulted and last so every existing positional construction
    # keeps working -- see _title_of() for why this field exists.
    title: str = ""

    # Notice class from `notice_class.py`, "" when the source said
    # nothing. Defaulted and last so existing constructions still work.
    notice_class: str = ""

    def __post_init__(self) -> None:
        if not self.publication_number.strip():
            raise BriefIntegrityError(
                "an unresolved entry must name the notice it is about")
        if not self.document_url.strip():
            raise BriefIntegrityError(
                "document_url must be a real URL or the literal 'UNKNOWN' "
                "string -- never blank, which a skimming reader could "
                "mistake for 'nothing to check'")
        if not self.unresolved_dimensions:
            raise BriefIntegrityError(
                "an UNRESOLVED entry must name at least one dimension that "
                "is actually unresolved -- an INSUFFICIENT_DATA band with "
                "no UNKNOWN/INFO factor behind it would be a fabricated "
                "verdict, and QualificationResult itself already refuses "
                "to construct one")


@dataclass(frozen=True)
class BlockedEntry:
    """One DISQUALIFIED notice, collapsed to the minimum a reader needs:
    which notice, and the exact clause that blocked it. Never a second
    guess at the verdict -- `qualification.py` already produced it."""

    publication_number: str
    blocking_clause: str

    # Human-readable name, or "" when the source published none.
    # Defaulted and last so every existing positional construction
    # keeps working -- see _title_of() for why this field exists.
    title: str = ""

    # Notice class from `notice_class.py`, "" when the source said
    # nothing. Defaulted and last so existing constructions still work.
    notice_class: str = ""

    def __post_init__(self) -> None:
        if not self.publication_number.strip():
            raise BriefIntegrityError(
                "a blocked entry must name the notice it is about")
        if not self.blocking_clause.strip():
            raise BriefIntegrityError(
                "BLOCKED requires a quoted blocking clause -- a verdict "
                "a human cannot check is the exact failure this "
                "repository's own qualification.py docstring names")


@dataclass(frozen=True)
class Brief:
    """The whole morning brief. Every field is already ordered the way
    it should render -- `render_brief()` performs no further sorting."""

    generated_at: datetime
    objective: str
    closing_within_days: int
    action_required: Tuple[DeadlineEntry, ...]
    has_previous_state: bool
    new_since_last: Tuple[NewEntry, ...]
    unresolved: Tuple[UnresolvedEntry, ...]
    blocked: Tuple[BlockedEntry, ...]

    def __post_init__(self) -> None:
        if self.closing_within_days < 0:
            raise BriefIntegrityError("closing_within_days cannot be negative")
        if not self.has_previous_state and self.new_since_last:
            raise BriefIntegrityError(
                "new_since_last must be empty when no prior state was "
                "supplied -- an empty list here means 'not computed', "
                "never 'nothing new', and this dataclass cannot hold both "
                "meanings at once")


def _dimensions_needing_resolution(qualification) -> Tuple[str, ...]:
    return tuple(
        f.dimension for f in qualification.factors
        if f.status == "UNKNOWN" or f.verdict == "INFO"
    )


def _first_document_url(entry: HuntEntry) -> str:
    docs = entry.eligibility.procurement_documents_urls or ()
    if docs:
        return docs[0]
    return entry.eligibility.notice_url or ""


def build_brief(
    report: HuntReport,
    *,
    now: datetime,
    closing_within_days: int = 14,
    previous_publication_numbers: Optional[Iterable[str]] = None,
) -> Brief:
    """Build a `Brief` from one `HuntReport`.

    `now` is required, never defaulted to the real clock -- a brief
    built for a test or a re-run must be reproducible from its inputs
    alone, same discipline `winnability.assess()` and `hunt()`'s own
    `now` parameter already use elsewhere in this repository.

    `previous_publication_numbers`: the publication numbers present in
    the LAST brief shown to the operator, if any. `None` (the default)
    means "no prior state available" -- section 2 then says so plainly
    rather than rendering an empty list, because those are different
    facts (`not computed` vs `computed, found nothing new`).

    DISQUALIFIED entries never appear in ACTION REQUIRED or NEW SINCE
    LAST BRIEF -- a blocked notice needs no action and is not news worth
    a second look; it appears exactly once, in BLOCKED.
    """
    if not isinstance(report, HuntReport):
        raise BriefIntegrityError(
            f"report must be a HuntReport, got {type(report).__name__}")
    if not isinstance(now, datetime):
        raise BriefIntegrityError(
            f"now must be a datetime, got {type(now).__name__}")
    if closing_within_days < 0:
        raise BriefIntegrityError(
            f"closing_within_days cannot be negative, got {closing_within_days}")

    now_utc = _as_utc(now)

    action_required = []
    for entry in report.entries:
        if entry.band == "DISQUALIFIED":
            continue
        raw_deadline = _raw_deadline(entry)
        parsed = _parse_deadline(raw_deadline)

        if parsed is None:
            # UNKNOWN urgency is urgent, never safe -- always included.
            days: Optional[int] = None
            display = UNKNOWN
        else:
            days = _days_remaining(parsed, now_utc)
            display = raw_deadline.strip()
            if days < 0 or days > closing_within_days:
                continue

        action_required.append(DeadlineEntry(
            publication_number=entry.publication_number,
        title=_title_of(entry),
        notice_class=_notice_class_of(entry),
            band=entry.band,
            days_remaining=days,
            deadline_display=display,
            notice_url=entry.eligibility.notice_url or "",
        ))

    action_required.sort(key=lambda e: (
        0 if e.days_remaining is None else 1,
        e.days_remaining if e.days_remaining is not None else 0,
        e.publication_number,
    ))

    has_previous_state = previous_publication_numbers is not None
    new_since_last: Tuple[NewEntry, ...] = ()
    if has_previous_state:
        seen = {p for p in previous_publication_numbers}
        new_since_last = tuple(
            NewEntry(
                publication_number=entry.publication_number,
        title=_title_of(entry),
        notice_class=_notice_class_of(entry),
                band=entry.band,
                notice_url=entry.eligibility.notice_url or "",
            )
            for entry in report.entries
            if entry.band != "DISQUALIFIED"
            and entry.publication_number not in seen
        )

    unresolved = tuple(
        UnresolvedEntry(
            publication_number=entry.publication_number,
        title=_title_of(entry),
        notice_class=_notice_class_of(entry),
            document_url=_first_document_url(entry) or UNKNOWN,
            unresolved_dimensions=_dimensions_needing_resolution(entry.qualification),
        )
        for entry in report.by_band("INSUFFICIENT_DATA")
    )

    blocked = tuple(
        BlockedEntry(
            publication_number=entry.publication_number,
        title=_title_of(entry),
        notice_class=_notice_class_of(entry),
            blocking_clause=" | ".join(entry.blocking_clauses) or UNKNOWN,
        )
        for entry in report.by_band("DISQUALIFIED")
    )

    return Brief(
        generated_at=now,
        objective=report.objective,
        closing_within_days=closing_within_days,
        action_required=tuple(action_required),
        has_previous_state=has_previous_state,
        new_since_last=new_since_last,
        unresolved=unresolved,
        blocked=blocked,
    )


_HEADER = (
    "=" * 72,
    "MORNING BRIEF -- PUBLIC PROCUREMENT NOTICES",
    "=" * 72,
    "Every entry below is a public notice a buyer published, carried",
    "through the same qualification pass as this repository's hunt.py.",
    "A band is a statement about PUBLISHED criteria only -- it is not a",
    "bid recommendation, not a statement this operator can win, and not",
    "revenue. Nothing here has been reviewed by a human.",
    "=" * 72,
)


def render_brief(brief: Brief) -> str:
    """Render a `Brief` as plain text a human reads in under a minute.

    Section order is fixed: ACTION REQUIRED, NEW SINCE LAST BRIEF,
    UNRESOLVED, BLOCKED. Every section renders even when empty, with an
    explicit one-line statement of emptiness -- never a silently
    vanished section, never a fabricated entry to avoid looking empty.
    """
    if not isinstance(brief, Brief):
        raise BriefIntegrityError(
            f"expected a Brief, got {type(brief).__name__}")

    lines = list(_HEADER)
    lines.append(f"generated : {brief.generated_at.isoformat()}")
    lines.append(f"objective : {brief.objective}")
    lines.append(f"window    : closing within {brief.closing_within_days} day(s)")
    lines.append("")

    lines.append("-" * 72)
    lines.append(f"1. ACTION REQUIRED ({len(brief.action_required)})")
    lines.append("-" * 72)
    if not brief.action_required:
        lines.append(
            "Nothing closing inside the window. Nothing to act on today.")
    else:
        for e in brief.action_required:
            urgency = (
                "UNKNOWN -- treat as urgent" if e.days_remaining is None
                else f"{e.days_remaining} day(s)"
            )
            lines.append(
                f"  [{e.band}] {e.title or e.publication_number}"
                f"  closes in: {urgency}"
                f"  (deadline: {e.deadline_display})")
            if e.notice_class:
                lines.append(f"      class: {e.notice_class}")
            if e.title:
                lines.append(f"      ref: {e.publication_number}")
            if e.notice_url:
                lines.append(f"      notice: {e.notice_url}")
    lines.append("")

    lines.append("-" * 72)
    lines.append("2. NEW SINCE LAST BRIEF")
    lines.append("-" * 72)
    if not brief.has_previous_state:
        lines.append(
            "No prior state was supplied to this run -- this section "
            "cannot be computed, and is not the same as 'nothing new'.")
    elif not brief.new_since_last:
        lines.append("Nothing new since the last brief.")
    else:
        for e in brief.new_since_last:
            lines.append(f"  [{e.band}] {e.title or e.publication_number}")
            if e.title:
                lines.append(f"      ref: {e.publication_number}")
            if e.notice_url:
                lines.append(f"      notice: {e.notice_url}")
    lines.append("")

    lines.append("-" * 72)
    lines.append(f"3. UNRESOLVED -- open the document to resolve ({len(brief.unresolved)})")
    lines.append("-" * 72)
    if not brief.unresolved:
        lines.append("Nothing unresolved.")
    else:
        for e in brief.unresolved:
            lines.append(f"  {e.title or e.publication_number}")
            if e.notice_class:
                lines.append(f"      class: {e.notice_class}")
            if e.title:
                lines.append(f"      ref: {e.publication_number}")
            lines.append(f"      open this document: {e.document_url}")
            lines.append(
                f"      unresolved: {', '.join(e.unresolved_dimensions)}")
    lines.append("")

    lines.append("-" * 72)
    lines.append(f"4. BLOCKED ({len(brief.blocked)})")
    lines.append("-" * 72)
    if not brief.blocked:
        lines.append("Nothing blocked.")
    else:
        for e in brief.blocked:
            lines.append(
                f"  {e.title or e.publication_number}: {e.blocking_clause}")

    nothing_to_show = (
        not brief.action_required
        and not brief.unresolved
        and not brief.blocked
        and (not brief.has_previous_state or not brief.new_since_last)
    )
    if nothing_to_show:
        lines.append("")
        lines.append(
            "Nothing closing, nothing new, nothing unresolved, nothing "
            "blocked. A quiet morning is a real and useful result.")

    return "\n".join(lines) + "\n"
