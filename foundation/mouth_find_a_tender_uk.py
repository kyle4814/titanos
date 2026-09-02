"""A fourth tender mouth: UK Find a Tender Service (FTS) -- the
post-Brexit replacement for TED publication of above-threshold UK
public-sector notices, scoped to security/investigation-services work.

WHY THIS FILE EXISTS, LIVE, 2026-09-02

Task brief asked for English-language procurement sources beyond the
three already swept (TED, UK Contracts Finder, NZ GETS) plus four
already-rejected/blocked (AusTender, CanadaBuys, Singapore/World
Bank/SAM.gov/UNGM/NATO, Public Contracts Scotland). Eight candidates were
tried live this cycle; see `docs/DECISIONS/D-010-english-markets.md` for
the full route table. This module is the one candidate that passed every
check: reachable without spoofing, genuinely open-opportunity shape (not
award-only), a query parameter that demonstrably filters (not silently
ignored), and live security/cyber notices found by name.

WHAT WAS ACTUALLY FOUND, LIVE, BEFORE LANDING HERE

`www.find-tender.service.gov.uk/robots.txt` returns HTTP 404 with the
site's own "Page not found" page (not a blocking rule -- no robots.txt
is published at all, so nothing here is disallowed). The site's REST API
(`/api/latest/notice/submission/*`) is for buyers submitting notices and
requires a CDP-Api-Key -- not used, not needed. What IS reachable, no
key, plain GET: `/search/opportunities`, a server-rendered HTML search
page with real GET query parameters (`keyword`, `filters.cpv-codes`,
`filters.status`, `page`, ...). Confirmed live:

  - Baseline (no filter): "We've found 15,087 result(s)".
  - `filters.cpv-codes=79700000` (Investigation and security services):
    "We've found 200 result(s)".
  - `filters.cpv-codes=99999999-ZZZZ-NONSENSE` (this task brief's own
    fabrication check): "We've found 0 result(s)" -- a genuinely
    unrecognised value returns zero matches, not the unfiltered 15,087.
    This is the first source in this repository's tender-mouth sweep
    whose query parameter demonstrably changes behaviour rather than
    being silently accepted and ignored (AusTender's OCDS mirror, World
    Bank, and Singapore all failed exactly this check).
  - `keyword=penetration+testing` (unscoped): "We've found 206
    result(s)" across 11 pages, including real, live, named notices with
    real closing dates -- see LIVE SECURITY WORK below.
  - Every OCDS release/record package
    (`/api/1.0/ocdsReleasePackages/{ocid}`,
    `/api/1.0/ocdsRecordPackages/{ocid}`) is ALSO public and keyless:
    a bogus ocid returns HTTP 404 `{"exception": "'identifier' is not
    found"}` with no auth challenge, and a real ocid
    (`ocds-h6vhtk-06e59c`, drawn from the search results below) returns
    a full OCDS 1.1 JSON release package under the EU OCDS profile. This
    module does not call that endpoint -- see CANNOT below -- but its
    keyless reachability is recorded here because it is the authoritative
    structured-data path a future module extending this one should use
    for value, not free-text HTML.

LIVE SECURITY WORK FOUND THIS CYCLE (2026-09-02, `keyword=penetration
testing`, unfiltered by CPV so this list is broader than what
`FEED_URL` itself fetches):

  - "Ad-Hoc Application Penetration Testing and IT Health Checks (PSN)
    and Other Security Services" -- City of Bradford Metropolitan
    District Council, ACTIVE TENDER, submission deadline 14 September
    2026, value GBP 300,327.00,
    ocds-h6vhtk-06e59c,
    https://www.find-tender.service.gov.uk/procurement/ocds-h6vhtk-06e59c
  - "Penetration Testing Services 2026-2030" -- NHS England, PIPELINE,
    contract start date (estimated) 28 October 2026, value
    GBP 7,200,000.00, ocds-h6vhtk-067639.
  - "Threat Led Penetration Testing - Black Team" -- UK Space Agency,
    PLANNED PROCUREMENT, tender publication date (estimated) 8 October
    2025, value GBP 240,000.00, ocds-h6vhtk-05a180.
  - "BLC0201 Cyber Security Penetration Testing Framework" -- Bluelight
    Commercial Limited, PIPELINE, value GBP 4,000,000.00,
    ocds-h6vhtk-054520.

These four are real, named, dated, valued -- read directly off the live
search response, not fabricated. Only the ACTIVE TENDER (Bradford) has a
genuine submission deadline still open for a bid; the others are earlier
lifecycle stages (Pipeline/Planned/PME), which this repository's own
value discipline (see money_state below) already refuses to conflate
with a live open competition.

FILTER USED BY THIS MODULE'S OWN `FEED_URL`

CPV 79700000 (Investigation and security services) rather than a free
keyword: a CPV code is the buyer's own structured classification, not a
guess this module makes about which words a title contains --
`tender_radar.py`'s own CPV-based value discipline, applied here to the
one field this source lets a caller filter on server-side that isn't
free text. 200 live results at time of writing (page 1 of 10, this
module fetches page 1 only -- see CANNOT).

ELIGIBILITY

`https://www.find-tender.service.gov.uk/Home/TermsAndConditions`, read
directly: no nationality/residency restriction anywhere in the page.
"You can use Find a Tender as a supplier to search for contract
opportunities..." with no geographic qualifier. Individual notices may
still carry their own eligibility conditions (a buyer-set restriction
inside a specific notice's own text) -- this module does not read notice
detail pages, so it cannot confirm or rule out a per-notice restriction;
recorded as a genuine unknown, not asserted either way.

WHAT THIS REUSES RATHER THAN DUPLICATES

  - `foundation/mouth_common.py::fetch_feed()` -- the one socket in this
    repository.
  - `foundation/discovery_authorization.py::DiscoveryPolicy` -- a fourth,
    independently-declared policy object.
  - `foundation/signal_spine.py::CanonicalSignal` -- the only signal
    shape.
  - `foundation/untrusted_text.py::describe()` -- every attacker-
    reachable string (title, authority name, delivery location -- any
    UK public body or private utility that publishes through FTS) goes
    through this before reaching `claim`/`evidence`.
  - `foundation/opportunity.py::SOURCE_TYPES` -- `"OFFICIAL"`, same
    class every other government tendering-platform mouth uses.

WHY A NARROW REGEX OVER THE HTML CARD MARKUP, NOT A GENERAL HTML PARSER

This source has no RSS/XML/JSON feed for the search results themselves
(only individual OCDS packages are JSON, keyed by an ocid this module
does not yet have -- see CANNOT). The search page IS the feed. Each
result renders as a fixed, repeated markup shape:
`<div class="app-search__item ...">` wrapping one
`<h2 class="govuk-heading-m app-search__title..."><a href="...">Title</a>
</h2>`, one status `<span class="govuk-tag app-search__tag...">Status
</span>`, and a fixed `<dt>Label:</dt><dd>Value</dd>` sequence -- the
same "narrow, single-purpose regex over a known, live-confirmed markup
shape, never a general HTML parser, never executed as markup" discipline
`mouth_gets_nz.py`'s module docstring already established for that
source's embedded HTML table. Confirmed live against a real fetched page
(200 CPV-79700000 results, 20 items on page 1) before being written here.

VALUE DISCIPLINE -- SAME AS `mouth_gets_nz.py`

`money_state` is ALWAYS `"NOT_OBSERVED"` here. A "Total value including
VAT" figure DOES appear on many cards (e.g. "£2,400,000.00"), but it is
free text inside an HTML `<dd>`, not a structured OCDS `tender.value`
field -- the structured version exists, but only behind the separate
OCDS package endpoint this module does not call (see CANNOT). Parsing a
currency-formatted string into a number here would be exactly the
fabrication `mouth_gets_nz.py`'s own module docstring already refuses;
the raw text is preserved verbatim (through `describe()`) in
`evidence["value_text_safe"]` instead, inspectable but never promoted to
a money figure this module did not itself verify structurally.

CANNOT

- Cannot fetch the authoritative structured value, buyer identifier, or
  full notice text -- that lives behind
  `/api/1.0/ocdsReleasePackages/{ocid}`, a second fetch per notice this
  module does not make. Extending this module (or building a sibling) to
  chase that endpoint is a real future increment, not done this cycle:
  it would turn one bounded fetch into up to 20 (one per item on a
  page), which is a materially different budget/shape than every other
  mouth in this repository and deserves its own DiscoveryPolicy
  accounting, not a silent addition here.
- Cannot see beyond page 1 (20 items) of the CPV-79700000 filter -- 200
  results exist across 10 pages; page 2+ URLs carry a `search-flow-id`
  this module has not verified is stable across requests without a
  session, so only the page-1 URL (verified stateless: works with no
  cookie) is fetched.
- Cannot confirm per-notice eligibility restrictions -- see ELIGIBILITY
  above.
- Cannot tell a genuinely new notice from a re-ordered one beyond what
  the `ocds-h6vhtk-XXXXXX` procurement identifier in each card's own
  `<dd>` distinguishes -- trusted as the dedupe key, same trust
  `tender_radar.py` places in `ocid` and `mouth_gets_nz.py` places in
  `guid`.
- Cannot filter out lifecycle stage from the fetch itself --
  `filters.status` was not combined with `filters.cpv-codes` in the
  live-verified `FEED_URL` below (verifying two combined parameters was
  out of this cycle's scope); this module's own `find_a_tender_signal()`
  therefore emits a signal for every stage (Pipeline through Active
  tender) and callers distinguish stage via `facts["status"]`, never by
  this module silently dropping the earlier stages.
"""
from __future__ import annotations

import hashlib
import html
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from foundation.discovery_authorization import DiscoveryPolicy
from foundation.mouth_common import FetchError, MouthObservation, fetch_feed
from foundation.mouth_common import observe as _observe
from foundation.signal_spine import CanonicalSignal
from foundation.untrusted_text import describe

__all__ = [
    "MOUTH_ID", "FEED_URL", "DISCOVERY_POLICY", "FetchError",
    "MouthObservation", "parse_items", "observe",
    "find_a_tender_signal", "FindATenderSweep", "sweep",
]

MOUTH_ID = "tender_radar_uk_find_a_tender"

# CPV 79700000 = "Investigation and security services". Page 1 only
# (20 items) -- confirmed live 2026-09-02 to need no cookie/session:
# a bare GET with no prior request returns the identical result set a
# session-established request does. `language=en_GB` pinned explicitly
# so this module never silently reads the Welsh-language rendering.
FEED_URL = (
    "https://www.find-tender.service.gov.uk/search/opportunities"
    "?language=en_GB&filters.cpv-codes=79700000"
)

DISCOVERY_POLICY = DiscoveryPolicy(
    objective=(
        "observe the UK Find a Tender Service (FTS) search-results page "
        "for currently listed security/investigation-services "
        "procurement opportunities (CPV 79700000) -- the post-Brexit "
        "TED-replacement source found reachable after Public Contracts "
        "Scotland was reconfirmed robots-blocked, see "
        "docs/DECISIONS/D-010-english-markets.md"
    ),
    requested_scope="READ_URL",
)

_ITEM_START_RE = re.compile(r'<div class="app-search__item[^"]*">')
_TITLE_RE = re.compile(
    r'<h2 class="govuk-heading-m app-search__title[^"]*">\s*'
    r'<a href="([^"]+)"[^>]*>([^<]+)</a>'
)
_STATUS_RE = re.compile(r'<span class="govuk-tag app-search__tag[^"]*">\s*([^<]+?)\s*</span>')
_DTDD_RE = re.compile(r'<dt[^>]*>([^<]+):</dt>\s*<dd[^>]*>([^<]*)</dd>')
_OCID_RE = re.compile(r'\b(ocds-[a-z0-9]{6}-[a-zA-Z0-9]+)\b')

# Preference order for which dt/dd label becomes `close_date` -- the
# label that means "you must act by this date to still take part",
# checked in this order because a card only ever carries the one label
# matching its own lifecycle stage. No fallback to a guessed date; a
# card matching none of these yields close_date="".
_DEADLINE_LABELS = (
    "Submission deadline date",
    "Engagement deadline date",
    "Tender or transparency notice publication date (estimated)",
    "Tender publication date (estimated)",
    "Contract start date (estimated)",
)


def _clean_str(value: object) -> str:
    return value if isinstance(value, str) else ""


def _split_items(raw_text: str) -> list[str]:
    """Split the search-results page into per-notice HTML chunks at each
    `app-search__item` card boundary. A page with zero matches (a real,
    honest outcome -- confirmed live for a nonsense CPV filter) yields an
    empty list, never an error."""
    starts = [m.start() for m in _ITEM_START_RE.finditer(raw_text)]
    if not starts:
        return []
    starts.append(len(raw_text))
    return [raw_text[starts[i]:starts[i + 1]] for i in range(len(starts) - 1)]


def parse_items(raw: bytes) -> tuple[dict, ...]:
    """Parse the FTS `/search/opportunities` HTML results page into
    open-opportunity item dicts.

    Decoding failure or a page carrying zero recognisable item cards AND
    no "0 result(s)" honest-empty marker raises `FetchError` -- the same
    UNAVAILABLE-not-crash contract every mouth in this repository gives
    `mouth_common.observe()`. A genuinely empty result set (the
    nonsense-filter case) is NOT an error and parses to an empty tuple.
    """
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise FetchError(f"response did not decode as UTF-8: {exc}") from exc

    chunks = _split_items(text)
    if not chunks and "result(s)" not in text:
        # Neither a parseable card nor the page's own "N result(s)"
        # marker -- this is not a shape this module recognises (a
        # redesigned page, an error page, a maintenance banner), so it
        # is UNAVAILABLE rather than a silent zero.
        raise FetchError(
            "search-results page carried no recognisable item card and "
            "no 'result(s)' marker -- page shape not recognised"
        )

    items: list[dict] = []
    for chunk in chunks:
        title_match = _TITLE_RE.search(chunk)
        if not title_match:
            continue
        link = html.unescape(title_match.group(1)).strip()
        title = html.unescape(title_match.group(2)).strip()

        ocid_match = _OCID_RE.search(link)
        ocid = ocid_match.group(1) if ocid_match else ""

        status_match = _STATUS_RE.search(chunk)
        status = html.unescape(status_match.group(1)).strip() if status_match else ""

        fields: dict[str, str] = {}
        for label, value in _DTDD_RE.findall(chunk):
            fields[html.unescape(label).strip()] = html.unescape(value).strip()

        procurement_id = fields.get("Procurement identifier", "") or ocid
        key = procurement_id or link
        if not key:
            # No stable identity to dedupe against -- dropped rather
            # than keyed on a guess, same discipline as
            # mouth_gets_nz.parse_items() dropping a guid-less entry.
            continue

        close_date = ""
        for label in _DEADLINE_LABELS:
            if fields.get(label):
                close_date = fields[label]
                break

        items.append({
            "key": key,
            "ocid": procurement_id,
            "link": link,
            "title": title,
            "status": status,
            "organisation": fields.get("Contracting authority name", ""),
            "organisation_type": fields.get("Contracting authority type", ""),
            "close_date": close_date,
            "value_text": fields.get("Total value including VAT", ""),
            "delivery_location": fields.get("Delivery location", ""),
        })
    return tuple(items)


def observe(
    state_path: Path,
    fetch_fn: Optional[Callable[[], bytes]] = None,
    now: Optional[datetime] = None,
) -> MouthObservation:
    """One observation cycle over the FTS CPV-79700000 search page.
    `fetch_fn` is injected in every test in
    `foundation/tests/test_mouth_find_a_tender_uk.py` -- no test touches
    the real network. Default path goes through
    `mouth_common.fetch_feed()` against `FEED_URL`, gated by
    `DISCOVERY_POLICY`."""
    fetch = fetch_fn or (lambda: fetch_feed(FEED_URL, policy=DISCOVERY_POLICY))
    return _observe(MOUTH_ID, state_path, fetch, parse_items, now=now)


def find_a_tender_signal(item: dict, now: Optional[datetime] = None) -> CanonicalSignal:
    """One open-opportunity item -> one `CanonicalSignal`.

    Title, organisation, status and delivery-location text are attacker-
    reachable free text (any buyer publishing through FTS, including a
    private utility per the live "Codi Group Ltd" example seen in the
    feed) and run through `untrusted_text.describe()` before anything
    derived from them reaches `claim`/`evidence` -- same discipline as
    every other mouth in this repository.
    """
    observed_at = (now or datetime.now(timezone.utc)).isoformat()
    title = describe(item.get("title", ""))
    org = describe(item.get("organisation", ""))
    status = describe(item.get("status", ""))
    location = describe(item.get("delivery_location", ""))
    value_text = describe(item.get("value_text", ""))
    markers = tuple(sorted(
        set(title.markers) | set(org.markers) | set(status.markers)
        | set(location.markers) | set(value_text.markers)))

    safe_key = describe(str(item.get("key", ""))).safe
    safe_ocid = describe(str(item.get("ocid", ""))).safe
    safe_link = describe(str(item.get("link", ""))).safe

    target = org.safe or safe_ocid or safe_key

    claim_subject = title.safe or safe_ocid or safe_key
    claim = f"UK Find a Tender opportunity ({status.safe or 'status unknown'}): {claim_subject}"
    if org.safe:
        claim += f" (contracting authority: {org.safe})"

    # No structured OCDS value field is read by this module -- see
    # module docstring's VALUE DISCIPLINE section. The free-text figure
    # is preserved in evidence, never parsed into a number.
    money_state = "NOT_OBSERVED"
    money_observed = ""

    org_raw = item.get("organisation", "")
    identity_hash = (
        hashlib.sha256(
            unicodedata.normalize("NFC", org_raw).strip().lower().encode("utf-8")
        ).hexdigest()
        if isinstance(org_raw, str) and org_raw.strip()
        else ""
    )

    evidence = {
        "ocid": safe_ocid,
        "procurement_identifier": safe_key,
        "organisation_safe": org.safe,
        "organisation_type_safe": describe(item.get("organisation_type", "")).safe,
        "identity_hash": identity_hash,
        "status_safe": status.safe,
        "close_date": item.get("close_date", ""),
        "value_text_safe": value_text.safe,
        "delivery_location_safe": location.safe,
        "title_safe": title.safe,
        "injection_markers": markers,
    }

    return CanonicalSignal(
        signal_id=f"tender:{safe_key}",
        source_id=MOUTH_ID,
        source_type="OFFICIAL",
        source_ref=safe_link,
        target=target,
        kind="DEMAND",
        claim=claim,
        observed_at=observed_at,
        target_established_by="SOURCE_NATIVE",
        facts={
            "status": status.safe,
            "close_date": item.get("close_date", ""),
        },
        evidence=evidence,
        pressure_class="EXPLICIT_DEMAND",
        pressure_evidence=(
            "published on the UK Find a Tender Service (FTS) search "
            "index under CPV 79700000 (investigation and security "
            "services), naming a contracting authority and a "
            "procurement identifier -- a public or public-adjacent body "
            "stating outright that it intends to buy security-related "
            "work"
        ),
        money_state=money_state,
        money_observed=money_observed,
    )


@dataclass(frozen=True)
class FindATenderSweep:
    """One observation cycle, report only -- same discipline as
    `tender_radar.TenderRadarSweep` / `GetsRadarSweep`: no ledger write,
    no promotion, no contact."""

    status: str
    fetched_count: int
    error: Optional[str]
    signals: tuple[CanonicalSignal, ...]
    targets: tuple[str, ...]

    def show_the_math(self) -> str:
        lines = [
            f"FIND-A-TENDER UK RADAR status={self.status} "
            f"fetched={self.fetched_count} signals={len(self.signals)}"
        ]
        if self.error:
            lines.append(f"  error: {self.error}")
        if self.status in ("FIRST_SEEN", "CHANGED") and not self.signals:
            lines.append(
                "  zero matching opportunities observed this cycle -- a "
                "valid, honest outcome, not an error"
            )
        for s in self.signals:
            lines.append(f"  OBSERVED  target={s.target!r}  {s.claim}")
        if self.signals:
            lines.append(
                "  every signal above is OBSERVED only -- none is "
                "VERIFIED or REALIZED; see module docstring's value "
                "discipline"
            )
        return "\n".join(lines)


def sweep(
    state_dir: Path,
    fetch_fn: Optional[Callable[[], bytes]] = None,
    now: Optional[datetime] = None,
) -> FindATenderSweep:
    """Run one FTS-radar cycle: observe -> signal -> report."""
    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / f"{MOUTH_ID}.json"
    observation = observe(state_path, fetch_fn=fetch_fn, now=now)
    signals = tuple(find_a_tender_signal(item, now=now) for item in observation.new_items)
    targets = tuple(sorted({s.target for s in signals}))
    return FindATenderSweep(
        status=observation.status,
        fetched_count=observation.item_count,
        error=observation.error,
        signals=signals,
        targets=targets,
    )
