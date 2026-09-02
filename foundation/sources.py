"""Make `hunt()` reach every source, not just TED.

WHY THIS EXISTS
----------------
`hunt()` only ever understood one notice shape: TED's own, because
`eligibility.assess_eligibility()` reads TED field names
(`publication-number`, `selection-criterion-lot`, ...). NZ GETS
(`mouth_gets_nz.py`) and UK Contracts Finder (`tender_radar.py`) both
produce their own, different item shapes, and neither could flow
through the qualification pass at all -- every item from either source
would hit `assess_eligibility()`'s own "notice has no usable
publication-number" `ValueError` and be silently skipped, notice by
notice, forever.

This module is the adapter layer, not a rewrite of either mouth. It
does exactly one thing: turn each source's own raw item into the one
TED-shaped notice dict `eligibility.assess_eligibility()` already
knows how to read -- reusing that function's own, already-correct,
already-tested absence semantics rather than re-deriving them.

THE CRITICAL HONESTY RULE -- READ THIS BEFORE ADDING A SOURCE
---------------------------------------------------------------
NZ GETS's RSS feed carries a title, a description, an organisation
name and a close date. It carries NO selection criteria, NO exclusion
grounds, NO legal-form/consortium rule, NO subcontracting rule -- none
of that vocabulary exists anywhere in the feed. UK Contracts Finder's
OCDS releases, as this repository's own `tender_radar.parse_items()`
already extracts them, carry the same limited set: title, description,
buyer, value, deadline, CPV classification -- and nothing that maps to
a TED selection-criterion or exclusion-ground code either.

A source's SILENCE on a criterion is not evidence the criterion does
not exist. It is evidence the criterion was never asked about. The
normaliser for a criteria-less source must therefore never set ANY of
`eligibility.py`'s criteria-shaped fields on the TED-shaped dict it
builds (`selection-criterion-lot`, `selection-criterion-description-
lot`, `selection-criteria-source`, `exclusion-grounds`,
`exclusion-grounds-description`, `exclusion-grounds-source-proc`,
`tenderer-legal-form-lot`, `tenderer-legal-form-description-lot`,
`subcontracting-*`, `variant-allowed-lot`, `tender-variant`,
`submission-language`). `eligibility.assess_eligibility()` already
treats a field it never received as `None` (UNKNOWN) -- not as "no
requirement" -- for every one of those fields; this module's whole job
is to NOT interfere with that by fabricating a value, an empty tuple
standing in for "cleared", or any other shortcut.

The consequence is structural, not a policy this module has to
enforce by hand: `qualification.assess()` marks every dimension it
cannot resolve as `UNKNOWN`/`INFO`, and any unresolved dimension makes
`INSUFFICIENT_DATA` the band, unless a positively-identified barrier
exists (which cannot happen here, because nothing was ever set for it
to find) -- see `qualification.py`'s own `assess()`. A notice from a
criteria-less source can therefore only ever come out
`INSUFFICIENT_DATA`, never `QUALIFIED` and never `DISQUALIFIED`. Tested
explicitly in `foundation/tests/test_sources.py`
(`TestHonestyRule`), against BOTH non-TED sources, including a notice
that supplies every OTHER field this module knows how to read.

WHAT THIS REUSES RATHER THAN DUPLICATES
-----------------------------------------
  - `foundation.eligibility.assess_eligibility()` -- not re-implemented.
    Every normaliser here produces a dict shaped for that one function;
    the absence handling is entirely its, not this module's.
  - `foundation.qualification.assess()` -- not re-implemented, not
    touched.
  - `foundation.hunt._assess_notice()` / `hunt.hunt_multi()` -- the
    actual per-notice chain and the merge/rank logic live in
    `hunt.py`; this module supplies `Source` definitions, not a second
    pipeline.
  - Each mouth's own `parse_items()` (`mouth_ted.py`,
    `mouth_gets_nz.py`, `tender_radar.py`) is the fetch/parse boundary
    for its source; this module's normalisers consume that function's
    OWN OUTPUT SHAPE, never a re-parsed or re-fetched copy.

UK CONTRACTS FINDER -- TWO NAMED TRAPS, ENCODED HERE SO NO FUTURE
CALLER REDISCOVERS THEM THE HARD WAY
--------------------------------------------------------------------
`tender_radar.py`'s own module docstring already proved, live, that
this endpoint's `keyword`/`q`/`search`/... query parameters (eleven
names tried) and its CPV parameter are silently accepted and IGNORED --
a nonsense keyword returns the identical 100-release result set as no
keyword at all. Filtering by keyword therefore MUST happen client-side,
after fetching, against each item's own `title`/`description` text.
`UK_CONTRACTS_FINDER.server_side_filterable = False` and
`keyword_fields = ("title", "description")` encode exactly that, and
`hunt.hunt_multi()` reads those two fields to decide whether to filter
client-side before this module's normaliser ever runs -- a future
caller cannot "discover" that passing a keyword to Contracts Finder
works, because the flag already says it doesn't.

The same module also documents a hard rate limit: repeated unthrottled
requests against this endpoint return HTTP 429 after roughly two pages.
`UK_CONTRACTS_FINDER.throttle_seconds` names the minimum gap a future
paginating caller must hold between requests to this endpoint --
`sources.py` itself only ever issues the one bounded request
`tender_radar.FEED_URL` already represents (same "one request, bounded
by construction" discipline every mouth in this repository already
follows), so this field is not exercised by any code in this module
today. It exists so a future caller who adds pagination against this
source finds the number already recorded, instead of re-discovering
429 the hard way.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional, Sequence, Tuple
from urllib.parse import quote

from foundation import mouth_etenders_ie
from foundation import mouth_find_a_tender_uk
from foundation import mouth_gets_nz, mouth_ted, tender_radar
from foundation.discovery_authorization import DiscoveryPolicy
from foundation.mouth_common import fetch_feed
from foundation.signal_spine import CanonicalSignal

__all__ = [
    "Source",
    "normalise_ted",
    "normalise_gets_nz",
    "normalise_find_a_tender_uk",
    "normalise_etenders_ie",
    "UK_FIND_A_TENDER",
    "ETENDERS_IE",
    "normalise_uk_contracts_finder",
    "TED",
    "NZ_GETS",
    "UK_CONTRACTS_FINDER",
    "ALL_SOURCES",
]


@dataclass(frozen=True)
class Source:
    """One hunt-able source: how to fetch its raw items, and how to
    turn one raw item into the TED-shaped notice dict
    `eligibility.assess_eligibility()` reads.

    `fetch_items` is the offline-injection point -- exactly the same
    role `hunt()`'s own `fetch_notices_fn` plays. A test constructs a
    `Source` with a `lambda: [...]` here; no test in this repository
    opens a socket.

    `normalise` takes ONE raw item (as this source's own `parse_items`
    -- or, for TED, the raw search-API notice dict -- produces it) and
    returns either a TED-shaped notice dict (must carry a non-empty
    `publication-number`, may carry any of `eligibility.FIELDS`) or
    `None` if this particular item has no stable identity to key on.
    See the module docstring's CRITICAL HONESTY RULE before writing a
    new one: never set a criteria-shaped field this source did not
    itself carry.

    `server_side_filterable` is True only for a source whose own fetch
    already narrows by the hunt's query (TED's expert-query POST body).
    False means `hunt_multi()` must filter client-side over
    `keyword_fields` before normalising -- see the UK Contracts Finder
    section of the module docstring for why this is load-bearing, not
    optional polish.

    `signal_fn`, if given, builds this source's own `CanonicalSignal`
    from the RAW item (not the normalised notice) for relevance
    scoring -- `ted_signal`/`gets_signal`/`tender_signal` all take the
    source's own item shape, never the TED-shaped adapter output.
    """

    source_id: str
    fetch_items: Callable[[], Sequence[dict]]
    normalise: Callable[[dict], Optional[dict]]
    server_side_filterable: bool
    keyword_fields: Tuple[str, ...] = ()
    throttle_seconds: float = 0.0
    signal_fn: Optional[Callable[[dict, Optional[datetime]], CanonicalSignal]] = None
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("a Source must have a non-empty source_id")
        if not self.server_side_filterable and not self.keyword_fields:
            raise ValueError(
                f"{self.source_id!r} is not server-side filterable but "
                "declares no keyword_fields -- hunt_multi() would have "
                "nothing to client-side-filter against, silently "
                "returning every item regardless of query")
        if self.throttle_seconds < 0:
            raise ValueError("throttle_seconds cannot be negative")


# ── TED ──────────────────────────────────────────────────────────────
# TED notices already arrive in the exact shape
# `eligibility.assess_eligibility()` reads (they ARE that shape --
# `assess_eligibility()` was built directly against it). This
# normaliser is therefore a validating pass-through, not a
# transformation: it declines (`None`) an item with no usable
# publication-number rather than let `assess_eligibility()`'s
# `ValueError` propagate up through `hunt_multi()` uncaught for this
# one source only.
def normalise_ted(item: dict) -> Optional[dict]:
    pub = item.get("publication-number")
    if not isinstance(pub, str) or not pub.strip():
        return None
    return item


def _ted_signal_from_raw(notice: dict, now: Optional[datetime]) -> CanonicalSignal:
    """`hunt_multi()` calls a source's `signal_fn` with the RAW item
    (see `Source.signal_fn`'s own docstring) -- for TED that is the
    same hyphenated search-API shape `normalise_ted()` passes through
    unchanged (`deadline-receipt-request`, `notice-title`, ...).
    `mouth_ted.ted_signal()` itself reads a DIFFERENT, flat shape
    (`deadline`, `title`, `key`, ...) -- `mouth_ted.parse_items()`'s own
    output. Passing the raw notice straight to `ted_signal()` silently
    produces a signal with an empty deadline and no title (found
    2026-09-02 in `hunt()`'s own single-source path -- see
    `hunt._parsed_ted_items_by_key()` for the full story; this is the
    same bug, reproduced here for the multi-source path, fixed the same
    way: re-shape via the one JSON envelope `parse_items()` accepts,
    one notice at a time here since `hunt_multi()` processes item by
    item rather than in a batch."""
    try:
        raw_bytes = json.dumps({"notices": [notice]}).encode("utf-8")
        parsed = mouth_ted.parse_items(raw_bytes)
    except (TypeError, ValueError):
        parsed = ()
    item = parsed[0] if parsed else notice
    return mouth_ted.ted_signal(item, now=now)


# Largest `limit` TED accepts alongside the full eligibility+mouth field
# union. Measured, not guessed -- see _default_ted_fetch() below.
_TED_MAX_NOTICES_FOR_FIELD_COUNT = 100


def _default_ted_fetch(query: str, limit: int, policy: DiscoveryPolicy) -> Tuple[dict, ...]:
    """The real network path for TED, reusing `mouth_ted.FEED_URL` and
    `mouth_ted.REQUEST_FIELDS` (that module's own public field list --
    not edited, not re-derived) plus `eligibility.FIELDS` so a caller
    gets both modules' needs in one request, same union discipline
    `hunt.REQUEST_FIELDS_UNION` already establishes for the
    single-source path."""
    from foundation.eligibility import FIELDS as ELIGIBILITY_FIELDS

    fields = tuple(sorted(set(mouth_ted.REQUEST_FIELDS) | set(ELIGIBILITY_FIELDS)))

    # TED'S REAL CAP IS fields x limit, NOT limit ALONE. Measured live
    # 2026-09-03: with this 46-field union, limit=250 returns HTTP 400
    # and limit=100 succeeds -- while limit=250 with a ONE-field request
    # succeeds and returns 250 notices. The ceiling is on response size,
    # so a caller who only ever tuned `limit` would conclude 250 works,
    # which it does, right up until the field list grows.
    #
    # This was found because a nightly multi-source sweep reported
    # "fetched 360, assessed 50" while TED -- the largest source --
    # contributed nothing at all. The failure WAS recorded in
    # `HuntReport.skipped`, so nothing lied; it simply was not loud
    # enough to notice against a plausible-looking total.
    #
    # Clamped rather than left to fail: an operator asking for 250
    # notices should get the most this endpoint will actually return,
    # not an exception.
    safe_limit = min(limit, _TED_MAX_NOTICES_FOR_FIELD_COUNT)
    raw = fetch_feed(
        mouth_ted.FEED_URL,
        policy=policy,
        json_body={"query": query, "limit": safe_limit, "fields": list(fields)},
    )
    payload = json.loads(raw)
    notices = payload.get("notices")
    if not isinstance(notices, list):
        return ()
    return tuple(n for n in notices if isinstance(n, dict))


def _make_ted_source(query: str, limit: int = 50,
                      policy: Optional[DiscoveryPolicy] = None) -> Source:
    """Build a live-fetching TED `Source` for a given query. Not
    exported as a bare constant (unlike NZ_GETS/UK_CONTRACTS_FINDER)
    because TED's fetch needs a query and a limit that only the caller
    of `hunt_multi()` knows -- a parameterless TED constant would have
    to guess both."""
    pol = policy or mouth_ted.DISCOVERY_POLICY
    return Source(
        source_id="TED",
        fetch_items=lambda: _default_ted_fetch(query, limit, pol),
        normalise=normalise_ted,
        server_side_filterable=True,
        signal_fn=_ted_signal_from_raw,
        notes="EU TED expert-query search API; query filters server-side.",
    )


# A ready-to-use TED source, bound to a default query, for a caller
# that just wants a concrete example or the full static registry
# (`ALL_SOURCES` below). A caller who needs TED's server-side query to
# actually match `hunt_multi()`'s own `query` argument should build
# their own via `sources_for_query()` instead of using this constant
# directly -- see that function's docstring for why TED alone needs
# this (its fetch is server-side filtered; NZ_GETS and
# UK_CONTRACTS_FINDER are not, so they need no query at construction
# time).
TED = _make_ted_source(query='FT ~ ("cyber security")')


# ── NZ GETS ──────────────────────────────────────────────────────────
# See module docstring's CRITICAL HONESTY RULE. This feed carries
# title/description/organisation/close-date/RFx-id/categories and
# NOTHING that maps to any TED criteria field -- so none of those
# fields are ever set below, not even as an empty tuple.
def normalise_gets_nz(item: dict) -> Optional[dict]:
    key = item.get("guid") or item.get("key")
    if not isinstance(key, str) or not key.strip():
        return None
    notice: dict = {"publication-number": key.strip()}

    title = item.get("title")
    if isinstance(title, str) and title.strip():
        notice["notice-title"] = {"eng": (title,)}

    org = item.get("organisation")
    if isinstance(org, str) and org.strip():
        notice["buyer-name"] = {"eng": (org,)}

    link = item.get("link")
    if isinstance(link, str) and link.strip():
        notice["links"] = {"html": {"eng": link}}

    # Deliberately absent: procedure-type, submission-language, every
    # selection-criterion/exclusion-ground/legal-form/subcontracting/
    # variant field. GETS's RSS feed states none of these -- see the
    # module docstring. `assess_eligibility()` reads their absence as
    # UNKNOWN, never as "no requirement".
    return notice


def _default_gets_nz_fetch(policy: DiscoveryPolicy) -> Tuple[dict, ...]:
    raw = fetch_feed(mouth_gets_nz.FEED_URL, policy=policy)
    return mouth_gets_nz.parse_items(raw)


NZ_GETS = Source(
    source_id="NZ_GETS",
    fetch_items=lambda: _default_gets_nz_fetch(mouth_gets_nz.DISCOVERY_POLICY),
    normalise=normalise_gets_nz,
    # No keyword/category/region parameter narrows this feed server-
    # side -- proven live, see mouth_gets_nz.py's own module docstring
    # finding 6. Client-side filtering is mandatory, not optional.
    server_side_filterable=False,
    keyword_fields=("title", "description"),
    signal_fn=lambda item, now: mouth_gets_nz.gets_signal(item, now=now),
    notes=(
        "NZ GETS RSS feed: title/description/organisation/close-date "
        "only, NO bidder criteria of any kind. Every notice from this "
        "source is structurally incapable of being QUALIFIED or "
        "DISQUALIFIED -- see module docstring's CRITICAL HONESTY RULE."
    ),
)


# ── UK Contracts Finder ─────────────────────────────────────────────
# See module docstring's CRITICAL HONESTY RULE and its dedicated UK
# CONTRACTS FINDER section. `tender_radar.parse_items()`'s own output
# shape carries title/description/buyer/value/deadline/CPV and,
# likewise, nothing that maps to a TED criteria field.
def normalise_uk_contracts_finder(item: dict) -> Optional[dict]:
    key = item.get("release_id") or item.get("ocid") or item.get("key")
    if not isinstance(key, str) or not key.strip():
        return None
    notice: dict = {"publication-number": key.strip()}

    title = item.get("title")
    if isinstance(title, str) and title.strip():
        notice["notice-title"] = {"eng": (title,)}

    buyer = item.get("buyer_name")
    if isinstance(buyer, str) and buyer.strip():
        notice["buyer-name"] = {"eng": (buyer,)}

    release_id = item.get("release_id")
    if isinstance(release_id, str) and release_id.strip():
        url = tender_radar.NOTICE_URL_TEMPLATE.format(id=quote(release_id, safe=""))
        notice["links"] = {"html": {"eng": url}}

    # Deliberately absent: procedure-type, submission-language, every
    # selection-criterion/exclusion-ground/legal-form/subcontracting/
    # variant field. tender_radar.parse_items() carries none of these
    # -- see module docstring.
    return notice


def _default_uk_contracts_finder_fetch(policy: DiscoveryPolicy) -> Tuple[dict, ...]:
    raw = fetch_feed(tender_radar.FEED_URL, policy=policy)
    return tender_radar.parse_items(raw)


UK_CONTRACTS_FINDER = Source(
    source_id="UK_CONTRACTS_FINDER",
    fetch_items=lambda: _default_uk_contracts_finder_fetch(
        tender_radar.DISCOVERY_POLICY),
    normalise=normalise_uk_contracts_finder,
    # keyword/q/search/... AND the CPV parameter are both silently
    # accepted and ignored by this endpoint -- proven live, see
    # tender_radar.py's own module docstring CANNOT section. Client-
    # side filtering is mandatory, not optional.
    server_side_filterable=False,
    keyword_fields=("title", "description"),
    # Proven live in tender_radar.py's own recon: this endpoint 429s
    # after roughly two unthrottled pages. This module issues only the
    # one bounded FEED_URL request today (no pagination here), so this
    # number is not yet exercised by any code -- it exists so a future
    # caller who adds pagination finds it already recorded rather than
    # re-discovering 429 the hard way.
    throttle_seconds=2.0,
    signal_fn=lambda item, now: tender_radar.tender_signal(item, now=now),
    notes=(
        "UK Contracts Finder OCDS search feed: title/description/buyer/"
        "value/deadline/CPV only, NO bidder criteria of any kind. Every "
        "notice from this source is structurally incapable of being "
        "QUALIFIED or DISQUALIFIED -- see module docstring's CRITICAL "
        "HONESTY RULE. keyword/CPV filtering is silently ignored "
        "server-side (server_side_filterable=False); this endpoint "
        "rate-limits hard (throttle_seconds records the measured "
        "429 threshold for a future paginating caller)."
    ),
)


def sources_for_query(
    query: str,
    *,
    ted_limit: int = 50,
    ted_policy: Optional[DiscoveryPolicy] = None,
    include: Optional[Sequence[str]] = None,
) -> Tuple[Source, ...]:
    """Build the full source list for one `hunt_multi()` call
    -- a fresh TED `Source` bound to `query` (TED's fetch is server-
    side filtered, so it needs the query at construction time; NZ_GETS
    and UK_CONTRACTS_FINDER do not, and are filtered client-side by
    `hunt_multi()` itself using the same `query`), plus the two
    module-level constants. `include`, if given, names a subset of
    `ALL_SOURCES`'s ids to build -- default is
    every reachable source, which is the whole point of this module."""
    # MUST STAY IN STEP WITH `ALL_SOURCES`. On 2026-09-02 an end-to-end
    # verification run found UK_FIND_A_TENDER and ETENDERS_IE listed in
    # ALL_SOURCES, fully built, individually loadable -- and unreachable
    # from the operator CLI under any keyword, because this dict is what
    # the CLI actually calls and it named only three. Registering a
    # source in one list and not the other means it exists everywhere
    # except where someone would use it. `test_sources.py` now asserts
    # the two lists agree.
    all_by_id = {
        "TED": lambda: _make_ted_source(query, limit=ted_limit, policy=ted_policy),
        "NZ_GETS": lambda: NZ_GETS,
        "UK_CONTRACTS_FINDER": lambda: UK_CONTRACTS_FINDER,
        "UK_FIND_A_TENDER": lambda: UK_FIND_A_TENDER,
        "ETENDERS_IE": lambda: ETENDERS_IE,
    }
    ids = include if include is not None else tuple(all_by_id)
    unknown = [i for i in ids if i not in all_by_id]
    if unknown:
        raise ValueError(f"unknown source id(s): {unknown}")
    return tuple(all_by_id[i]() for i in ids)


def _normalise_criteria_less(item: dict, *, url_key: str = "link") -> Optional[dict]:
    """Shared normaliser for every source that publishes NO bidder
    criteria vocabulary at all.

    THE HONESTY RULE, restated because this is where it would be easiest
    to break: not one criteria-shaped field is ever set here. Not
    `selection-criterion-lot`, not `exclusion-grounds`, not
    `tenderer-legal-form-lot`. These feeds simply do not state bidder
    conditions, and `assess_eligibility()` already reads an absent field
    as UNKNOWN rather than as "no requirement", which
    `qualification.assess()` then refuses to turn into QUALIFIED.

    So a notice from any of these sources can only ever come back
    INSUFFICIENT_DATA. That is the correct answer -- the feed genuinely
    does not say -- and it falls out of existing, already-tested code
    rather than a second rule that could drift away from it.
    """
    key = item.get("key")
    if not isinstance(key, str) or not key.strip():
        return None
    notice: dict = {"publication-number": key.strip()}
    title = item.get("title")
    if isinstance(title, str) and title.strip():
        notice["notice-title"] = {"eng": (title,)}
    org = item.get("organisation")
    if isinstance(org, str) and org.strip():
        notice["buyer-name"] = {"eng": (org,)}
    link = item.get(url_key)
    if isinstance(link, str) and link.strip():
        notice["links"] = {"html": {"eng": link}}
    return notice


def normalise_find_a_tender_uk(item: dict) -> Optional[dict]:
    """UK Find a Tender Service. Publishes no criteria vocabulary."""
    return _normalise_criteria_less(item)


def normalise_etenders_ie(item: dict) -> Optional[dict]:
    """Ireland eTenders. Publishes no criteria vocabulary."""
    return _normalise_criteria_less(item)


def _default_find_a_tender_uk_fetch(policy: DiscoveryPolicy) -> Tuple[dict, ...]:
    raw = fetch_feed(mouth_find_a_tender_uk.FEED_URL, policy=policy)
    return mouth_find_a_tender_uk.parse_items(raw)


def _default_etenders_ie_fetch(policy: DiscoveryPolicy) -> Tuple[dict, ...]:
    raw = fetch_feed(mouth_etenders_ie.FEED_URL, policy=policy)
    return mouth_etenders_ie.parse_items(raw)


UK_FIND_A_TENDER = Source(
    source_id="UK_FIND_A_TENDER",
    fetch_items=lambda: _default_find_a_tender_uk_fetch(
        mouth_find_a_tender_uk.DISCOVERY_POLICY),
    normalise=normalise_find_a_tender_uk,
    # This source DOES filter server-side -- the only one in this
    # registry that provably does. Verified by comparing a real CPV
    # filter against a nonsense value against no filter at all
    # (200 / 0 / 15,087). Recorded because four other sources in this
    # project silently ignore their own documented parameters, so
    # "filters work" is a claim that has to be earned per source.
    server_side_filterable=True,
    keyword_fields=("title",),
    signal_fn=lambda item, now: mouth_find_a_tender_uk.find_a_tender_signal(
        item, now=now),
    notes=("UK post-Brexit above-threshold register. CPV filter verified "
           "to actually filter. Found the Bradford penetration-testing "
           "framework."),
)

ETENDERS_IE = Source(
    source_id="ETENDERS_IE",
    fetch_items=lambda: _default_etenders_ie_fetch(
        mouth_etenders_ie.DISCOVERY_POLICY),
    normalise=normalise_etenders_ie,
    # freeText, pagination and sorting are all silently ignored on the
    # stateless fetch -- proven live against nonsense values. Only the
    # first page of open CFTs is reachable without a session.
    server_side_filterable=False,
    keyword_fields=("title", "description"),
    signal_fn=lambda item, now: mouth_etenders_ie.etenders_ie_signal(
        item, now=now),
    notes=("Ireland eTenders. The only EU member state producing "
           "English-submission notices this project has found. Stateless "
           "fetch reaches page 1 only."),
)


# The full, static registry -- every source this module knows about,
# for a caller that just wants "everything reachable" without building
# a query-bound TED source (e.g. inspecting `notes`/`throttle_seconds`
# without fetching anything).
ALL_SOURCES = (TED, NZ_GETS, UK_CONTRACTS_FINDER,
               UK_FIND_A_TENDER, ETENDERS_IE)
