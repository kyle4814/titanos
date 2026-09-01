"""A registry of genuinely-reachable public procurement sources, for
`tender_radar.py`-shaped mouths to draw on. Built to answer one question
honestly: is `tender_radar.py`'s UK Contracts Finder source the only
lawfully reachable public-sector tender feed, or are there others?

WHAT THIS IS NOT

Not a second mouth, not a second signal type, not a modification of
`tender_radar.py` — that module remains the one that fetches, sweeps,
and emits `CanonicalSignal`s. This module is a REGISTRY: for each source
verified live this cycle, it names the source's identity, licence,
payload shape, and a parser that normalises that payload into the exact
same item-dict shape `tender_radar.parse_items()` already produces
(`key`, `ocid`, `tender_id`, `title`, `description`, `status`, `amount`,
`currency`, `deadline`, `buyer_name`, `published`) — so any future caller
that wants to sweep an additional source can do so without inventing a
second shape. `foundation/mouth_common.py::fetch_feed()` remains the
only socket this repository opens; nothing here performs network I/O
independently, and nothing here defines a second signal type.

THE HONEST RESULT OF THIS CYCLE'S SEARCH (2026-09-01)

`tender_radar.py`'s UK Contracts Finder OCDS API turns out to be the
only source found that is simultaneously: (a) live and returning real,
current data, (b) `robots.txt`-permitted for this repository's honest
User-Agent, (c) reachable with no key/login, (d) licensed for this use,
AND (e) fetchable through `mouth_common.fetch_feed()` as it actually
exists — one GET request, returning the complete item payload in a
single response. Two other candidates were verified LIVE and REAL but
are structurally incompatible with (e), which is a genuine, load-bearing
finding, not a shortfall in effort:

  - EU TED (Tenders Electronic Daily), `api.ted.europa.eu/v3/notices/
    search` — verified live 2026-09-01. `robots.txt` on the API host
    returns HTTP 404 (no restriction asserted, same reading
    `tender_radar.py` already gives contractsfinder's absent
    `robots.txt`). Content is licensed CC BY 4.0 (`ted.europa.eu/en/
    legal-notice`, fetched and read live: "the procurement notices
    published in the Supplement to the Official Journal of the European
    Union can be freely reused, for commercial or non-commercial
    purposes"). A live query
    (`{"query":"deadline-receipt-request>=today()","fields":[...],
    "limit":100}`) returned real, current, open notices — 49,002 total
    matching the live count field at query time, e.g. a Swedish
    HLR/AED-equipment tender (buyer: Räddningstjänstförbundet
    Storgöteborg, deadline 2026-09-26, value 5,000,000 SEK) and a
    Croatian tyre-supply tender (value 746.42, currency not resolved in
    that specific record). THE DISQUALIFYING FACT: this endpoint answers
    only `POST` — `GET https://api.ted.europa.eu/v3/notices/search` with
    the exact same query as URL parameters returns HTTP 405
    `{"message":"Request method 'GET' is not supported"}`, confirmed
    live. `mouth_common.fetch_feed()` issues
    `urllib.request.Request(url, headers=...)` with no request body —
    an unconditional GET, by design, and this module does not own that
    file and was explicitly told not to modify it. A real, live, lawful,
    licensed source that this repository's one socket genuinely cannot
    reach is a finding about the socket's shape, not a reason to build a
    second one — doing that would violate the "one socket" discipline
    `mouth_common.py`'s own docstring and `TITANOS_COMMUNICATION_SWITCH_
    001.md` both hold to. NOT REGISTERED.

  - Ukraine Prozorro, `public.api.openprocurement.org/api/2.5/tenders`
    — verified live 2026-09-01. `robots.txt` returns HTTP 404 (no
    restriction). A single GET with no key or login returns real,
    current tender records (confirmed against a live record:
    status=`active.qualification`, a genuine buyer name, a genuine
    UAH amount, a real `tenderPeriod`). THE DISQUALIFYING FACT: the
    list/changefeed endpoint this module would have to poll for new
    items — the one shape that fits `mouth_common.observe()`'s
    single-fetch contract — does NOT return `title` or `value` no
    matter what `opt_fields` is requested (confirmed live: three
    consecutive real records all returned `"title": null, "value":
    null` from the list endpoint while the exact same tenders' full
    detail, fetched individually by ID, DOES carry both). Getting a
    real title and amount requires a second, per-tender GET — an N+1
    fan-out this module's single `fetch_fn() -> bytes` shape cannot
    express without either a second socket call per item (not what
    `fetch_feed()` is) or emitting signals with no title and no amount,
    which is exactly the "right domain, wrong shape" fabrication risk
    `docs/DECISIONS/D-003-au-sources.md` already refused for
    `data.sa.gov.au`'s CKAN catalogue. NOT REGISTERED, for the same
    value-discipline reason, not a reachability reason.

FINDINGS RECORDED BUT NOT REGISTERED, FOR OTHER REASONS

  - Public Contracts Scotland (`www.publiccontractsscotland.gov.uk`):
    `robots.txt` disallows `/` for `User-agent: *`, permitting only
    Googlebot/Yahoo-slurp/bingbot/Msnbot by name — this fetcher is none
    of those. Four plausible OCDS/search endpoint paths were tried
    (`/api/search_ocds`, `/OCDS`, `/publish/opensearch.aspx`,
    `/search/search_ocds.aspx`) and none resolved to a working feed
    even before the robots question, so this is belt-and-braces: BOTH
    disallowed and no confirmed feed. DISALLOWED.
  - French BOAMP via `data.economie.gouv.fr` (OpenDataSoft): `robots.txt`
    disallows `/api/` for `User-agent: *`, Googlebot-only allowed — the
    identical pattern `docs/DECISIONS/D-003-au-sources.md` already found
    at `data.brisbane.qld.gov.au` and `data.melbourne.vic.gov.au`.
    DISALLOWED, not tried further.
  - CanadaBuys (`canadabuys.canada.ca`): both `robots.txt` and the site
    root return HTTP 403 to this fetcher's honest User-Agent — the same
    WAF-class block `tender_radar.py`'s own docstring documents for
    AusTender. BLOCKED.
  - World Bank Documents & Reports API (`search.worldbank.org/api/v3/
    wds`): live, no auth, `robots.txt` permits it — but it returns
    project documents and reports (e.g. "Environmental and Social Review
    Summary — Rwanda"), not procurement notices with a buyer and a
    deadline. WRONG SHAPE, same class of finding as the AU CKAN
    catalogue in D-003.
  - UN Global Marketplace (`www.ungm.org/Public/Notice`): live, `robots.
    txt` permits it, but the page is an HTML single-page application
    (Angular), not a documented machine-readable feed. Reverse-
    engineering whatever internal API its JavaScript calls was
    considered and rejected on the same discipline D-003 already
    applied to `business.gov.au`: this repository calls documented,
    intended-for-machine-consumption endpoints, not a page's private
    client-side calls. NO DOCUMENTED FEED FOUND.
  - New Zealand GETS (`www.gets.govt.nz`): `robots.txt` only disallows
    SemrushBot — genuinely open to this fetcher — but no documented
    OCDS/search API endpoint was found; two guessed paths
    (`/ext/tenders.OCDS`, `/GETSOCDS/Search`) both 404'd. Guessing
    further undocumented paths was not pursued, per the same "call
    documented endpoints, don't guess" discipline. NO DOCUMENTED FEED
    FOUND (not disallowed — a genuine open question a future cycle with
    GETS's actual API docs in hand could resolve).
  - Ireland eTenders (`www.etenders.gov.ie`) and Sell2Wales (`www.
    sell2wales.gov.wales`): both return a `robots.txt` with no
    disallow rules for this fetcher, but neither has a documented public
    search API found within this cycle's time-box. NO DOCUMENTED FEED
    FOUND.
  - SAM.gov (`sam.gov`) / `api.sam.gov`: `api.sam.gov` returns HTTP 404
    on every path tried with no key; SAM.gov's documented Get
    Opportunities API is a keyed API (`api_key` required) per its own
    published documentation — not pursued further, matching this
    module's "keyed API, not open" refusal class.

THE RESULT

One source registered: `tender_radar_uk_contracts_finder`, wrapping
`tender_radar.py`'s own already-verified `FEED_URL`, `DISCOVERY_POLICY`,
and `parse_items` rather than re-declaring them — the exact "reuse, do
not duplicate" discipline this repository's doctrine files require. This
is a registry of one honest, already-proven source, not a registry
padded with aspirational entries that were live but unreachable through
this repository's actual fetch contract. A future source becomes
registrable the moment a candidate satisfies all five conditions above,
same shape as this one entry.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from foundation.discovery_authorization import DiscoveryPolicy
from foundation.mouth_common import FetchError
from foundation.tender_radar import (
    DISCOVERY_POLICY as _UK_DISCOVERY_POLICY,
    FEED_URL as _UK_FEED_URL,
    MOUTH_ID as _UK_MOUTH_ID,
    parse_items as _uk_parse_items,
)

__all__ = [
    "FetchError",
    "TenderSource",
    "UnknownSourceError",
    "SOURCES",
    "UNREGISTERED_CANDIDATES",
    "get_source",
    "list_sources",
    "parse_source",
]


class UnknownSourceError(KeyError):
    """Raised by `get_source()`/`parse_source()` for any source id not
    present in `SOURCES` — including a candidate this module's own
    docstring names and verified live but declined to register. A
    caller cannot get a working parser for a source by guessing its id;
    only genuinely registered sources are reachable this way."""


@dataclass(frozen=True)
class TenderSource:
    """One registry entry. `parser` normalises fetched bytes into the
    same item-dict shape `tender_radar.parse_items()` produces — see
    that function's own docstring for the field contract every parser
    here must honour (malformed input raises `FetchError`, never
    crashes; an individually malformed record is skipped, not fatal to
    the whole parse)."""

    source_id: str
    name: str
    base_url: str
    feed_url: str
    licence: str
    licence_note: str
    payload_shape: str
    discovery_policy: DiscoveryPolicy
    parser: Callable[[bytes], "tuple[dict, ...]"]
    verified_at: str
    verified_note: str


SOURCES: dict[str, TenderSource] = {
    _UK_MOUTH_ID: TenderSource(
        source_id=_UK_MOUTH_ID,
        name="UK Government Contracts Finder",
        base_url="https://www.contractsfinder.service.gov.uk",
        feed_url=_UK_FEED_URL,
        licence="Open Government Licence v3.0",
        licence_note=(
            "stated in every response's own 'license' field, per "
            "tender_radar.py's module docstring"
        ),
        payload_shape=(
            "OCDS release package: {'releases': [{'tag': [...], 'ocid': "
            "str, 'tender': {'status', 'title', 'description', "
            "'tenderPeriod': {'endDate'}, 'value': {'amount', "
            "'currency'}}, 'buyer': {'name'}, 'date': str}, ...]}"
        ),
        discovery_policy=_UK_DISCOVERY_POLICY,
        parser=_uk_parse_items,
        verified_at="2026-09-01",
        verified_note=(
            "verified live by the prior cycle that built tender_radar.py "
            "— 6 real open notices observed; re-verified as reachable "
            "and unchanged this cycle by inspection of that module's own "
            "docstring and tests, not re-fetched independently since "
            "this module owns no new network call to it"
        ),
    ),
}


# Candidates verified LIVE this cycle (real current data, no fabrication)
# but not registered, keyed by id -> one-line reason. See this module's
# docstring for the full evidence behind each entry. A caller must not
# be able to reach a working parser for any of these via get_source() /
# parse_source() — see TestUnverifiedCandidatesAreNeverRegistered.
UNREGISTERED_CANDIDATES: dict[str, str] = {
    "ted_eu": (
        "live, lawful, CC BY 4.0, but api.ted.europa.eu/v3/notices/search "
        "answers only POST (confirmed HTTP 405 on GET) — incompatible "
        "with mouth_common.fetch_feed()'s GET-only single socket"
    ),
    "prozorro_ua": (
        "live, lawful, no-auth, but the single-fetch changefeed endpoint "
        "returns null title/value for every record regardless of "
        "opt_fields — a real item requires a second per-tender GET, an "
        "N+1 shape this module's single fetch_fn() cannot express "
        "without fabricating title/amount from the wrong-shape response"
    ),
    "public_contracts_scotland": (
        "robots.txt disallows / for this fetcher's User-Agent (only "
        "named search-engine bots permitted); no confirmed feed anyway"
    ),
    "boamp_fr": (
        "robots.txt disallows /api/ for this fetcher's User-Agent "
        "(Googlebot-only allowed) — same pattern as D-003's AU CKAN/"
        "OpenDataSoft findings"
    ),
    "canadabuys_ca": (
        "robots.txt and site root both return HTTP 403 to this "
        "fetcher's honest User-Agent — WAF block, same class as AusTender"
    ),
    "world_bank_documents": (
        "live, no-auth, robots-permitted, but returns project documents "
        "and reports, not procurement notices with a buyer and deadline "
        "— wrong shape"
    ),
    "ungm": (
        "robots-permitted, but the public notice page is an HTML "
        "single-page application with no documented machine-readable "
        "feed found"
    ),
    "gets_nz": (
        "robots.txt permits this fetcher, but no documented OCDS/search "
        "API endpoint was found within this cycle's time-box"
    ),
    "etenders_ie": (
        "robots.txt has no disallow rules for this fetcher, but no "
        "documented public search API was found"
    ),
    "sell2wales": (
        "robots.txt has no disallow rules for this fetcher, but no "
        "documented public search API was found"
    ),
    "sam_gov": (
        "api.sam.gov returns HTTP 404 with no key; SAM.gov's documented "
        "Get Opportunities API requires an api_key — keyed, not open"
    ),
}


def list_sources() -> tuple[str, ...]:
    """Registered source ids, sorted — never includes an
    `UNREGISTERED_CANDIDATES` key."""
    return tuple(sorted(SOURCES))


def get_source(source_id: str) -> TenderSource:
    """Look up one registered source. Raises `UnknownSourceError` — never
    `KeyError` bare, never `None` — for anything not in `SOURCES`,
    including every id listed in `UNREGISTERED_CANDIDATES`: a source
    verified live but declined for a stated reason must be exactly as
    unreachable through this function as a source never investigated at
    all."""
    try:
        return SOURCES[source_id]
    except KeyError:
        reason = UNREGISTERED_CANDIDATES.get(source_id)
        detail = f" ({reason})" if reason else ""
        raise UnknownSourceError(
            f"{source_id!r} is not a registered tender source{detail}. "
            f"Registered sources: {list_sources()!r}"
        ) from None


def parse_source(source_id: str, raw: bytes) -> "tuple[dict, ...]":
    """Parse `raw` bytes fetched from `source_id`'s feed using that
    source's own registered parser. Raises `UnknownSourceError` for an
    unregistered id (checked before any parsing is attempted) and lets
    `FetchError` propagate unchanged for a malformed payload — the same
    structured-refusal-not-crash contract every parser in this registry
    is required to honour, never caught and swallowed here."""
    source = get_source(source_id)
    return source.parser(raw)
