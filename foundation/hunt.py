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
    "render_hunt",
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


def _sort_key(entry: HuntEntry) -> Tuple[int, str]:
    """Band first, then publication number for determinism. No value
    ordering inside a band: `shortlist.py` owns money ranking and
    duplicating that logic here would give this repository two answers
    to one question -- the defect its own doctrine names most often."""
    return (BAND_ORDER.index(entry.band), entry.publication_number)


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

    entries = []
    skipped = []
    for notice in notices:
        try:
            eligibility = assess_eligibility(notice)
        except ValueError as exc:
            # A notice with no stable identity cannot be keyed, tracked
            # or re-checked. Recorded by reason, never dropped silently.
            skipped.append(f"unassessable notice: {exc}")
            continue
        qualification = assess(eligibility, operator)
        relevance = None
        signal = None
        if capability is not None:
            try:
                signal = ted_signal(notice, now=now)
                relevance = score(signal, capability)
            except Exception as exc:  # noqa: BLE001 - see below
                # Relevance is additive colour, not the verdict. A
                # signal this module cannot build must not discard a
                # qualification verdict it already computed correctly.
                skipped.append(
                    f"{eligibility.publication_number}: relevance unavailable "
                    f"({type(exc).__name__})")
        entries.append(
            HuntEntry(
                publication_number=eligibility.publication_number,
                band=qualification.band,
                eligibility=eligibility,
                qualification=qualification,
                relevance=relevance,
                signal=signal,
            )
        )

    ordered = tuple(sorted(entries, key=_sort_key))
    return HuntReport(
        entries=ordered,
        fetched=len(notices),
        assessed=len(ordered),
        skipped=tuple(skipped),
        objective=objective,
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
    if report.skipped:
        lines.append("-" * 72)
        lines.append("skipped:")
        for reason in report.skipped:
            lines.append(f"  {reason}")
    return "\n".join(lines)
