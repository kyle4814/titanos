"""One entrypoint for the whole procurement chain.

WHY THIS EXISTS
---------------
Every piece of this pipeline already worked, and none of them were
connected. Fetching notices lived in `mouth_ted.py`; reading a notice's
bidder conditions lived in `eligibility.py`; scoring those conditions
against a real operator lived in `qualification.py`; surface-text
relevance lived in `relevance.py`. Running them end to end meant hand-
writing a throwaway script every time, and a chain that only exists in a
throwaway script is a chain that gets a step wrong under pressure --
which is exactly how this repository once reported a confident verdict
("this operator probably cannot bid") that turned out to be false.

`hunt()` is that chain as one callable, so the sequence is fixed in code
rather than in whoever is typing.

WHAT IT REFUSES TO DO
---------------------
The output is NOT a lead list. `shortlist.py`'s digest header already
says this at length and it is not softened here: a notice is a public
document a buyer published, nothing more. This module adds exactly one
thing on top of that -- a qualification band -- and that band is a
statement about *published criteria*, never about whether the operator
will win.

Three properties are load-bearing:

1. `INSUFFICIENT_DATA` outranks `DISQUALIFIED` in the ordering, and
   `QUALIFIED` outranks both. An operator reading top-down must never
   see a proven-blocked notice above an unresolved one. Ranking is the
   whole point of a hunt: putting the wrong thing first wastes the
   scarcest resource in this project, which is the operator's attention.

2. A notice whose criteria TED does not publish comes back
   `INSUFFICIENT_DATA` and is presented as *unresolved*, never as
   promising. `qualification.py` enforces that absence cannot produce
   `QUALIFIED`; this module must not undo it by rendering unresolved
   entries as if they were opportunities.

3. Every `DISQUALIFIED` verdict carries its quoted blocking clause
   through to the rendered output. A verdict a human cannot check is a
   verdict this repository has already been burned by.

NETWORK
-------
`hunt()` fetches through `mouth_common.fetch_feed()` like every other
network path here, which means it needs a real `DiscoveryPolicy` naming
a concrete objective and budget. `fetch_notices_fn` is injectable so
every test in `foundation/tests/test_hunt.py` runs offline -- no test in
this repository opens a socket, this module included.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional, Sequence, Tuple

from foundation.discovery_authorization import DiscoveryPolicy
from foundation.eligibility import (
    FIELDS as ELIGIBILITY_FIELDS,
    EligibilityAssessment,
    assess_eligibility,
)
from foundation.mouth_common import fetch_feed
from foundation.mouth_ted import FEED_URL, REQUEST_FIELDS, ted_signal
from foundation.mouth_ted import parse_items as parse_ted_items
from foundation.qualification import (
    OperatorProfile,
    QualificationResult,
    assess,
)
from foundation.relevance import CapabilityProfile, RelevanceAssessment, score
from foundation.signal_spine import CanonicalSignal

__all__ = [
    "HuntIntegrityError",
    "BAND_ORDER",
    "HuntEntry",
    "HuntReport",
    "hunt",
    "hunt_multi",
    "render_hunt",
    "with_recency",
    "with_open_deadline",
    "REQUEST_FIELDS_UNION",
]


class HuntIntegrityError(ValueError):
    """Raised when a caller asks this module to present a result it
    cannot honestly support -- an entry whose rendered band disagrees
    with its own `QualificationResult`, or a report claiming more
    entries than it holds."""


# Presentation order. NOT severity, NOT confidence -- this is "what
# deserves the operator's attention first". INSUFFICIENT_DATA sits above
# DISQUALIFIED deliberately: an unresolved notice can still turn into
# work once someone opens the procurement documents, whereas a
# disqualified one is closed on published evidence.
BAND_ORDER = ("QUALIFIED", "INSUFFICIENT_DATA", "DISQUALIFIED")

# One request carrying both modules' field needs. Neither list is
# edited: a field either module stops reading should be removed there,
# not silently dropped here.
REQUEST_FIELDS_UNION = tuple(sorted(set(REQUEST_FIELDS) | set(ELIGIBILITY_FIELDS)))

_MAX_NOTICES_HARD_CAP = 250


# RECENCY -- measured against the live API on 2026-09-02, not assumed.
# CORRECTED same day: an earlier version of this comment claimed
# `deadline-receipt-request` never filters. That was a wrong-grammar
# artefact (`today(0)` is not a form the API accepts as meaning "today"
# -- it silently matches nothing rather than erroring, same silent-drop
# class as UK Contracts Finder's ignored `keyword`), not a property of
# the field. Retested with the correct bare-`today()` grammar, same
# session:
#
#   FT ~ ("penetration testing" OR "cyber security")                 -> 54
#   ... AND deadline-receipt-request >= today()                      ->  0
#   ... AND deadline-receipt-request >  today()                      ->  0
#   ... AND deadline-receipt-request >= today(0)                     ->  0
#   deadline-receipt-request >= today() AND classification-cpv IN
#     (72000000, 79000000, 48000000, 72212730, 48730000, 72810000)   -> 7142
#
# Two separate findings, not one:
#
#   1. `today(0)` is simply wrong grammar -- always returns 0, with or
#      without FT. `mouth_ted.py`'s own EXPERT_QUERY has used bare
#      `today()` all along; this module must never emit `today(0)`.
#   2. `deadline-receipt-request >= today()` genuinely works (7,142
#      live matches) when combined with `classification-cpv`, but
#      returns 0 when combined with the `FT ~ (...)` full-text
#      operator specifically -- FT and the deadline filter are mutually
#      exclusive on this API. A query combining them looks like a
#      normal query and silently matches nothing, which is the actual
#      silent-drop finding worth keeping.
#
# `publication-date` filters correctly with FT, which is why
# `with_recency()` (FT-oriented) still uses it. `with_open_deadline()`
# below is for CPV-shaped queries, where the real "still open" filter
# does work -- it must never be appended to an FT query.
_RECENCY_FIELD = "publication-date"
_DEADLINE_FIELD = "deadline-receipt-request"
_MAX_RECENCY_DAYS = 3650


def with_recency(query: str, days: int) -> str:
    """Append a publication-date bound to a TED expert query.

    This narrows to notices PUBLISHED in the last `days`. It does not
    narrow to notices still accepting tenders -- for that, on a
    non-FT (e.g. CPV-based) query, see `with_open_deadline()` instead;
    combining the two on an FT query silently returns nothing (see the
    measurement above).
    """
    if not query.strip():
        raise HuntIntegrityError("cannot add recency to an empty query")
    if days < 1 or days > _MAX_RECENCY_DAYS:
        raise HuntIntegrityError(
            f"days must be between 1 and {_MAX_RECENCY_DAYS}, got {days}")
    return f"{query} AND {_RECENCY_FIELD} >= today(-{days})"


def with_open_deadline(query: str) -> str:
    """Append a genuinely-working `deadline-receipt-request >= today()`
    bound to a TED expert query -- narrows to notices still accepting
    tenders, confirmed live (7,142 matches combined with
    `classification-cpv`, see the measurement above).

    CPV-compatible, FT-INCOMPATIBLE: combining this with an `FT ~ (...)`
    full-text clause measured 0 results live, silently, even though
    each half matches plenty alone. Do not call this on a query that
    contains an `FT ~` clause -- raises `HuntIntegrityError` if it
    detects one, rather than building a query proven to return nothing.

    Always emits bare `today()`, never `today(0)` -- `today(0)` is
    wrong grammar that silently matches nothing regardless of what it
    is combined with (see the measurement above); this function must
    never regress to emitting it.
    """
    if not query.strip():
        raise HuntIntegrityError("cannot add a deadline bound to an empty query")
    if "FT ~" in query or "FT~" in query:
        raise HuntIntegrityError(
            "with_open_deadline() cannot be combined with an FT ~ (...) "
            "full-text clause -- measured live to silently return zero "
            "results even though each half matches plenty alone; use "
            "with_recency() for an FT query instead")
    return f"{query} AND {_DEADLINE_FIELD} >= today()"


@dataclass(frozen=True)
class HuntEntry:
    """One notice, carried through every stage of the chain with each
    stage's own verdict kept separate and inspectable. Nothing here is
    a composite score -- there is deliberately no single number, because
    a single number is what lets a reader stop checking."""

    publication_number: str
    band: str
    eligibility: EligibilityAssessment
    qualification: QualificationResult
    relevance: Optional[RelevanceAssessment]
    signal: Optional[CanonicalSignal]
    # Which source this notice came from ("TED" for the single-source
    # `hunt()` path -- kept as a real value, never "" for that path, so
    # a merged report from `hunt_multi()` can always tell TED entries
    # apart from every other source without a special case). Defaulted
    # so every pre-existing direct `HuntEntry(...)` construction (this
    # module's own tests included) keeps working unchanged.
    source: str = "TED"

    def __post_init__(self) -> None:
        if self.band not in BAND_ORDER:
            raise HuntIntegrityError(
                f"band must be one of {BAND_ORDER}, got {self.band!r}")
        if self.band != self.qualification.band:
            raise HuntIntegrityError(
                "a hunt entry's band must be the band its own "
                f"QualificationResult produced ({self.qualification.band!r}), "
                f"never a separately-supplied {self.band!r} -- a presentation "
                "layer that can restate a verdict is a presentation layer "
                "that can launder one")
        if not self.publication_number.strip():
            raise HuntIntegrityError(
                "a hunt entry must name the notice it is about")

    @property
    def blocking_clauses(self) -> Tuple[str, ...]:
        """The quoted clauses that produced a DISQUALIFIED band. Empty
        for every other band -- a non-blocking entry has no blockers,
        and inventing one would be fabrication."""
        return tuple(self.qualification.blocking_clauses)


@dataclass(frozen=True)
class HuntReport:
    """The outcome of one hunt. `fetched` and `assessed` are kept apart
    because they differ whenever a notice arrives without a usable
    publication number, and a report that quietly conflated them would
    hide exactly that."""

    entries: Tuple[HuntEntry, ...]
    fetched: int
    assessed: int
    skipped: Tuple[str, ...]
    objective: str

    def __post_init__(self) -> None:
        if self.assessed != len(self.entries):
            raise HuntIntegrityError(
                f"report claims {self.assessed} assessed notices but holds "
                f"{len(self.entries)} entries")
        if self.fetched < self.assessed:
            raise HuntIntegrityError(
                f"cannot assess {self.assessed} notices from {self.fetched} "
                "fetched -- an assessment with no notice behind it is "
                "fabricated by definition")

    def by_band(self, band: str) -> Tuple[HuntEntry, ...]:
        if band not in BAND_ORDER:
            raise HuntIntegrityError(
                f"band must be one of {BAND_ORDER}, got {band!r}")
        return tuple(e for e in self.entries if e.band == band)


def _sort_key(entry: HuntEntry) -> Tuple[int, str, str]:
    """Band first, then publication number, then source, for
    determinism. No value ordering inside a band: `shortlist.py` owns
    money ranking and duplicating that logic here would give this
    repository two answers to one question -- the defect its own
    doctrine names most often. The `source` tiebreaker only ever
    matters for `hunt_multi()`'s merged report, where two different
    sources could coincidentally mint the same publication number --
    for the single-source `hunt()` path every entry's source is the
    same constant and this changes nothing."""
    return (BAND_ORDER.index(entry.band), entry.publication_number, entry.source)


def _default_fetch(
    policy: DiscoveryPolicy,
    query: str,
    limit: int,
) -> Tuple[dict, ...]:
    """The one network path. Goes through the same gated `fetch_feed()`
    every other mouth uses -- there is no second, ungated route here."""
    raw = fetch_feed(
        FEED_URL,
        policy=policy,
        json_body={
            "query": query,
            "limit": limit,
            "fields": list(REQUEST_FIELDS_UNION),
        },
    )
    payload = json.loads(raw)
    notices = payload.get("notices")
    if not isinstance(notices, list):
        return ()
    return tuple(n for n in notices if isinstance(n, dict))


def _parsed_ted_items_by_key(notices: Sequence[dict]) -> dict:
    """Re-shape the same raw TED notices already fetched into
    `mouth_ted.parse_items()`'s flat, non-hyphenated item shape
    (`deadline`, `title`, `key`, `amount`, ...), keyed by each item's
    own `key` (== the raw notice's `publication-number`). No second
    fetch: `parse_items()` only accepts its one documented input shape
    (the `{"notices": [...]}` envelope `/v3/notices/search` itself
    returns), so the already-fetched notices are re-wrapped into that
    shape locally, in memory, and parsed once.

    Never raises: a notice `parse_items()` itself would drop (no usable
    `publication-number`) is simply absent from the returned mapping --
    `ted_signal()`'s caller falls back to the raw notice for that one
    case (see `hunt()`), which is a strictly safer degrade than a crash
    mid-hunt over a single malformed notice.
    """
    try:
        raw_bytes = json.dumps({"notices": list(notices)}).encode("utf-8")
        parsed = parse_ted_items(raw_bytes)
    except (TypeError, ValueError):
        # A notice containing something json.dumps cannot serialise
        # (should not happen for a dict already round-tripped through
        # json.loads, but never assumed) -- degrade to "no parsed
        # counterpart for anything", not a crash.
        return {}
    return {item.get("key"): item for item in parsed if item.get("key")}


def _assess_notice(
    notice: dict,
    operator: OperatorProfile,
    *,
    capability: Optional[CapabilityProfile] = None,
    now: Optional[datetime] = None,
    signal_fn: Optional[Callable[[dict, Optional[datetime]], CanonicalSignal]] = None,
    source: str = "TED",
) -> Tuple[Optional[HuntEntry], Optional[str]]:
    """The one per-notice chain -- eligibility -> qualification (and
    relevance, when both `capability` and `signal_fn` are supplied) --
    shared by `hunt()` and `hunt_multi()` so there is exactly one place
    this sequence is written, not two copies that can drift apart.

    Returns `(entry, note)`. `entry` is `None` only when the notice
    could not be assessed at all (no stable identity) -- `note` then
    names why and the caller must not add anything to its report.
    `entry` non-`None` with a non-`None` `note` means the notice WAS
    assessed but relevance additionally could not be computed --
    relevance is additive colour, not the verdict, so a signal this
    function cannot build must not discard a qualification verdict it
    already computed correctly (see `hunt()`'s original docstring
    reasoning, preserved here rather than restated).
    """
    try:
        eligibility = assess_eligibility(notice)
    except ValueError as exc:
        return None, f"unassessable notice: {exc}"
    qualification = assess(eligibility, operator)
    relevance = None
    signal = None
    note = None
    if capability is not None and signal_fn is not None:
        try:
            signal = signal_fn(notice, now)
            relevance = score(signal, capability)
        except Exception as exc:  # noqa: BLE001 - see below
            note = (
                f"{eligibility.publication_number}: relevance unavailable "
                f"({type(exc).__name__})")
    entry = HuntEntry(
        publication_number=eligibility.publication_number,
        band=qualification.band,
        eligibility=eligibility,
        qualification=qualification,
        relevance=relevance,
        signal=signal,
        source=source,
    )
    return entry, note


def hunt(
    query: str,
    operator: OperatorProfile,
    *,
    policy: Optional[DiscoveryPolicy] = None,
    capability: Optional[CapabilityProfile] = None,
    limit: int = 50,
    fetch_notices_fn: Optional[Callable[[], Sequence[dict]]] = None,
    now: Optional[datetime] = None,
) -> HuntReport:
    """Fetch notices for `query`, then run every one through
    eligibility -> qualification (and relevance, when a `capability`
    profile is supplied), and return them ranked by `BAND_ORDER`.

    `fetch_notices_fn` bypasses the network entirely and is how every
    test here runs offline. When it is None a real `policy` is required
    -- this module will not silently construct its own authorization,
    because a caller that did not think about objective and budget has
    not earned a socket.
    """
    if not isinstance(operator, OperatorProfile):
        raise HuntIntegrityError(
            f"operator must be an OperatorProfile, got {type(operator).__name__}")
    if not query.strip():
        raise HuntIntegrityError(
            "a hunt must name what it is looking for -- an empty query "
            "would fetch whatever the source felt like returning")
    if limit < 1 or limit > _MAX_NOTICES_HARD_CAP:
        raise HuntIntegrityError(
            f"limit must be between 1 and {_MAX_NOTICES_HARD_CAP}, got {limit}")

    if fetch_notices_fn is not None:
        notices = tuple(n for n in fetch_notices_fn() if isinstance(n, dict))
        objective = "injected fetch (no network)"
    else:
        if policy is None:
            raise HuntIntegrityError(
                "hunt() needs either a DiscoveryPolicy or an injected "
                "fetch_notices_fn -- it will not open a socket without an "
                "authorization naming a concrete objective and budget")
        notices = _default_fetch(policy, query, limit)
        objective = policy.objective

    # `ted_signal()` reads FLAT, non-hyphenated keys (`deadline`,
    # `title`, `key`, `amount`, ...) -- `mouth_ted.parse_items()`'s own
    # output shape. `notices` here are the RAW search-API dicts
    # `assess_eligibility()` needs (hyphenated: `deadline-receipt-
    # request`, `notice-title`, `publication-number`). Passing a raw
    # notice straight to `ted_signal()` silently produces a signal with
    # an empty deadline and no title -- caught 2026-09-02: it fails in
    # the safe direction (UNKNOWN, not a wrong date) which is exactly
    # why it went unnoticed by any test asserting only "a signal
    # exists". `parse_ted_items()` is re-run here, on the SAME notices
    # already fetched (re-wrapped into the one JSON shape it accepts,
    # never a second network call), to get the correctly-shaped
    # counterpart for each notice, matched by its own publication
    # number -- both shapes come from one fetch.
    parsed_by_key = _parsed_ted_items_by_key(notices) if capability is not None else {}

    entries = []
    skipped = []
    for notice in notices:
        # A notice with no stable identity cannot be keyed, tracked or
        # re-checked -- `_assess_notice` returns `entry=None` for that
        # case and it is recorded by reason, never dropped silently.
        entry, note = _assess_notice(
            notice, operator,
            capability=capability, now=now,
            signal_fn=(
                lambda n, t: ted_signal(
                    parsed_by_key.get(n.get("publication-number"), n), now=t)
            ) if capability is not None else None,
            source="TED",
        )
        if entry is None:
            skipped.append(note)
            continue
        if note is not None:
            skipped.append(note)
        entries.append(entry)

    ordered = tuple(sorted(entries, key=_sort_key))
    return HuntReport(
        entries=ordered,
        fetched=len(notices),
        assessed=len(ordered),
        skipped=tuple(skipped),
        objective=objective,
    )


def hunt_multi(
    query: str,
    operator: OperatorProfile,
    sources: Sequence["Source"],
    *,
    capability: Optional[CapabilityProfile] = None,
    now: Optional[datetime] = None,
) -> HuntReport:
    """Run the same eligibility -> qualification (and relevance) chain
    `hunt()` runs, across every `Source` in `sources`, and return ONE
    merged, ranked `HuntReport` -- every `HuntReport`/`HuntEntry`
    invariant from the single-source path applies unchanged: band
    ordering, `INSUFFICIENT_DATA` outranking `DISQUALIFIED`, an entry
    that cannot restate its own band.

    `sources` are `foundation.sources.Source` instances (imported
    lazily below, not at module load time, so `hunt.py` gains no new
    hard dependency on `sources.py` for callers who only ever use the
    single-source `hunt()`). Each source's own `fetch_items` is the
    offline-injection point -- exactly like `hunt()`'s
    `fetch_notices_fn`, no test anywhere in this repository opens a
    socket.

    For a source that is not server-side query-filterable (see
    `Source.server_side_filterable`), `query` is applied client-side as
    a case-insensitive substring match over that source's own declared
    `keyword_fields`, BEFORE normalisation -- never trusted to a query
    parameter a source is known to silently ignore.
    """
    if not isinstance(operator, OperatorProfile):
        raise HuntIntegrityError(
            f"operator must be an OperatorProfile, got {type(operator).__name__}")
    if not query.strip():
        raise HuntIntegrityError(
            "a hunt must name what it is looking for -- an empty query "
            "would fetch whatever the source felt like returning")
    if not sources:
        raise HuntIntegrityError(
            "hunt_multi() needs at least one Source -- an empty source "
            "list would silently report zero notices from every source "
            "at once, indistinguishable from every source genuinely "
            "having nothing")

    entries = []
    skipped = []
    fetched_total = 0
    needle = query.strip().lower()

    for src in sources:
        try:
            raw_items = tuple(i for i in src.fetch_items() if isinstance(i, dict))
        except Exception as exc:  # noqa: BLE001 - one bad source must not blind the rest
            # A WHOLE SOURCE FAILING IS NOT THE SAME AS ONE NOTICE BEING
            # SKIPPED, and burying both in one list hides the worse of
            # the two. On 2026-09-03 a nightly sweep reported "fetched
            # 360, assessed 50, skipped 1" while TED -- the largest
            # source -- had returned HTTP 400 and contributed nothing.
            # Nothing lied: the failure was in `skipped`. It was just
            # one line among per-notice noise, under a total that looked
            # entirely plausible.
            #
            # The prefix makes it greppable and `render_hunt` now calls
            # it out separately, because an operator who thinks they
            # swept five sources and actually swept four has a false
            # picture of the market, not a smaller one.
            skipped.append(
                f"SOURCE FAILED -- {src.source_id}: fetch failed "
                f"({type(exc).__name__}: {exc})")
            continue
        fetched_total += len(raw_items)

        if not src.server_side_filterable:
            def _matches(item: dict) -> bool:
                for field in src.keyword_fields:
                    value = item.get(field)
                    if isinstance(value, str) and needle in value.lower():
                        return True
                return False
            raw_items = tuple(i for i in raw_items if _matches(i))

        signal_fn = None
        if capability is not None and src.signal_fn is not None:
            signal_fn = src.signal_fn

        for raw in raw_items:
            try:
                notice = src.normalise(raw)
            except Exception as exc:  # noqa: BLE001
                skipped.append(
                    f"{src.source_id}: normalise failed "
                    f"({type(exc).__name__}: {exc})")
                continue
            if notice is None:
                # The source's own normaliser declined this item --
                # most commonly no stable identity to key on. Recorded,
                # never silently dropped.
                skipped.append(
                    f"{src.source_id}: item skipped by normaliser "
                    "(no stable identity)")
                continue
            # `signal_fn` (a source's own `ted_signal`/`gets_signal`/
            # `tender_signal`) reads that source's RAW item shape, never
            # the TED-shaped adapter dict `src.normalise()` just built
            # for `assess_eligibility()` -- passing the normalised
            # `notice` here would be the exact "wrong input shape,
            # fails quietly in the safe direction" bug found and fixed
            # in `hunt()`'s own TED path (see `_parsed_ted_items_by_key()`),
            # reproduced source-by-source if `raw` were not captured by
            # closure instead of relying on `_assess_notice`'s own
            # `notice` argument.
            entry, note = _assess_notice(
                notice, operator,
                capability=capability, now=now,
                signal_fn=(lambda n, t, fn=signal_fn, r=raw: fn(r, t)) if signal_fn else None,
                source=src.source_id,
            )
            if entry is None:
                skipped.append(f"{src.source_id}: {note}")
                continue
            if note is not None:
                skipped.append(f"{src.source_id}: {note}")
            entries.append(entry)

    ordered = tuple(sorted(entries, key=_sort_key))
    return HuntReport(
        entries=ordered,
        fetched=fetched_total,
        assessed=len(ordered),
        skipped=tuple(skipped),
        objective=(
            f"multi-source hunt for {query!r} across "
            f"{len(sources)} source(s): "
            + ", ".join(s.source_id for s in sources)
        ),
    )


_HEADER = (
    "=" * 72,
    "QUALIFICATION PASS OVER PUBLIC PROCUREMENT NOTICES",
    "=" * 72,
    "Every entry is a public notice a buyer published. A band below is a",
    "statement about the criteria that notice PUBLISHED, and about nothing",
    "else. It is not a bid recommendation, not a statement that this",
    "operator can win, and not revenue.",
    "",
    "QUALIFIED         no published criterion blocks this operator. Criteria",
    "                  held back in the procurement documents may still.",
    "INSUFFICIENT_DATA the notice does not publish enough to decide. This is",
    "                  UNRESOLVED, not promising -- someone must open the",
    "                  procurement documents.",
    "DISQUALIFIED      a published clause blocks this operator. The clause",
    "                  is quoted so it can be checked and disputed.",
    "",
)


def render_hunt(report: HuntReport, limit: Optional[int] = None) -> str:
    """Render a report as inspectable text. Order is `BAND_ORDER`;
    every DISQUALIFIED entry prints its quoted blocking clause, because
    a verdict without its evidence is the thing this module exists to
    stop producing."""
    if not isinstance(report, HuntReport):
        raise HuntIntegrityError(
            f"expected a HuntReport, got {type(report).__name__}")
    lines = list(_HEADER)
    lines.append(f"objective : {report.objective}")
    lines.append(
        f"fetched   : {report.fetched}   assessed: {report.assessed}   "
        f"skipped: {len(report.skipped)}")
    counts = {b: len(report.by_band(b)) for b in BAND_ORDER}
    lines.append("bands     : " + "  ".join(f"{b}={counts[b]}" for b in BAND_ORDER))
    lines.append("")

    shown = report.entries if limit is None else report.entries[:limit]
    if not shown:
        lines.append("No notice was assessed. That is a real result, not an error.")
    for entry in shown:
        lines.append("-" * 72)
        lines.append(f"{entry.publication_number}   {entry.band}")
        url = entry.eligibility.notice_url
        if url:
            lines.append(f"  notice   : {url}")
        for doc in (entry.eligibility.procurement_documents_urls or ())[:2]:
            lines.append(f"  documents: {doc}")
        if entry.relevance is not None:
            lines.append(f"  relevance: {entry.relevance.band}")
        for factor in entry.qualification.factors:
            lines.append(
                f"    {factor.dimension:24s} {factor.status:12s} {factor.verdict}")
        for clause in entry.blocking_clauses:
            lines.append(f"    BLOCKED BY: {clause}")
    # A failed SOURCE is surfaced above the per-notice skips and never
    # mixed in with them -- see the SOURCE FAILED comment in
    # `hunt_multi()` for the sweep this distinction was added after.
    source_failures = [r for r in report.skipped if r.startswith("SOURCE FAILED")]
    other_skips = [r for r in report.skipped if not r.startswith("SOURCE FAILED")]
    if source_failures:
        lines.append("=" * 72)
        lines.append(
            f"WARNING: {len(source_failures)} SOURCE(S) RETURNED NOTHING. "
            "This report covers less than it appears to.")
        for reason in source_failures:
            lines.append(f"  {reason}")
        lines.append("=" * 72)
    if other_skips:
        lines.append("-" * 72)
        lines.append("skipped:")
        for reason in other_skips:
            lines.append(f"  {reason}")
    return "\n".join(lines)
