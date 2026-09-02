"""A fifth tender mouth: Ireland's eTenders (etenders.gov.ie), the
national above/below-threshold public procurement platform, scoped to
security/cyber/penetration-testing work found by client-side keyword
matching over live, currently-open Call for Tenders (CFT) notices.

WHY THIS FILE EXISTS, LIVE, 2026-09-02

`docs/DECISIONS/D-010-english-markets.md` left four European-Dynamics
e-PPS platform sites (Sell2Wales, eSourcing NI, Ireland eTenders, Malta
eTenders) as "reachable, recon incomplete" -- the shared open question
was "what does the actual results-listing POST/GET look like." This
cycle traced it, for Ireland specifically. NI and Malta run a visibly
different landing shape on the identically-named endpoint (see CANNOT
below) and were NOT independently cracked this cycle -- this module
makes no claim about them.

WHAT WAS ACTUALLY FOUND, LIVE, BEFORE LANDING HERE

`www.etenders.gov.ie/robots.txt` returns HTTP 302 (redirects to the
homepage rather than serving a text file) -- read the same way
`docs/DECISIONS/D-010-english-markets.md` already reads NI/Malta's
identical redirect: "no robots.txt is published," not a block.

The task brief's own hypothesis was a session-bound POST behind
`prepareCurrentOpportunities.do?currentType=cft`. That page IS
session-bound for search/sort/paginate -- but it is NOT merely a
"search-form-preparation page" as D-010 recorded it. Confirmed live,
2026-09-02, with a completely fresh `curl` process carrying no cookie
jar at all: a bare, stateless GET to
`https://www.etenders.gov.ie/epps/prepareCurrentOpportunities.do?currentType=cft`
returns HTTP 200 with the first page of the live "currently open CFT"
results table ALREADY EMBEDDED in the HTML -- real titles, contracting
authorities, publication dates, submission deadlines, procedure,
status, and estimated value, for whatever is open right now (2,916
total open CFTs at time of writing). Two independent fresh fetches
(no cookies, then again with a cookie jar) returned byte-identical
`resourceId` sets for the same 10 rows -- this is genuinely stateless,
not an artifact of session reuse.

WHAT DOES NOT WORK -- TESTED AND PROVEN, NOT ASSUMED (this task
brief's own fabrication-check discipline, the same one that already
caught GETS NZ's, AusTender's, World Bank's, Singapore's and Contracts
Finder's silently-ignored parameters)

  - `freeText=<keyword>` on the stateless GET: identical "2,916 results
    in total" and identical row set with `freeText=security` and with
    `freeText=zzzznonsensequery9999` as with no `freeText` at all --
    silently ignored, same failure class as every other source's
    ignored filter parameter in this repository's sweep.
  - Pagination (`d-3680175-p=2&searchType=cftFTS&latest=true`, copied
    verbatim from the page's own "Next" link): identical 10
    `resourceId`s as page 1 when appended to
    `prepareCurrentOpportunities.do`. **This conclusion was wrong --
    see the module docstring's CORRECTION section below, added later
    the same day.** The parameter was appended to a page that always
    redirects to page 1 regardless of query string; appended to the
    page it actually redirects TO
    (`quickSearchAction.do?searchType=cftFTS&latest=true`), it is
    genuinely honoured. Left here, uncorrected in place, rather than
    edited away, because the mistake and the fix are both real
    provenance.
  - Sorting (`d-3680175-s=title.keyword&d-3680175-o=2`, copied verbatim
    from the page's own column-sort link): identical row order as the
    default fetch -- same cause as pagination.
  - Page-size guesses (`d-3680175-c=100`, `pageSize=100`,
    `rowsPerPage=100`): all silently ignored, still exactly 10 rows.
  - The form's own POST target (`/epps/viewCFTSAction.do`,
    `isExport=true`) DOES exist and, reached with a real two-step
    session (GET the search page for a session cookie, then POST the
    same field set as an ordinary HTML form -- normal client behaviour,
    not a bypass) returns a genuine live CSV-shaped export of the CFT
    dataset. This module does NOT use it and does not treat it as
    reachable by this repository's own rules: `foundation/
    mouth_common.py::fetch_feed()`'s `json_body` parameter serialises a
    caller's mapping as a JSON request body with `Content-Type:
    application/json` -- confirmed live that this Java/Struts-era form
    handler does not read a JSON body as form parameters at all; POSTing
    it returns the plain search page, not the export, exactly as if no
    body had been sent. Making this endpoint reachable would require
    `mouth_common.py` to gain a form-urlencoded POST mode, which is
    explicitly out of this module's file territory this cycle -- a real,
    named future increment, not silently worked around by, e.g., hand-
    rolling a second socket in this file (this repository has exactly
    one; see `CLAUDE.md`'s "value radar" section).
  - No RSS/Atom feed, OCDS endpoint, or documented public API was found
    anywhere in the homepage or search-page HTML (checked by grepping
    for `rss`/`atom`/`.xml`/`api/`/`ocds`/`feed` case-insensitively;
    the only match anywhere was the plain word "Export" as a UI label,
    not a link).

CONSEQUENCE FOR THIS MODULE'S SHAPE (see CORRECTION below for the
2026-09-02 update to this section)

The only genuinely reachable, stateless, keyless, no-forged-identity
GET is the unfiltered results endpoint, in whatever default order the
server returns them (consistently the same order across independent
fetches -- appears to be most-recently-published-first, not verified
as a documented contract), walked across `MAX_PAGES` pages of 10 rows
each (see CORRECTION). Relevance is still judged entirely client-side,
by reading each item's OWN title/description text, never by trusting a
server-side filter parameter this cycle proved does nothing (`freeText`
remains confirmed ignored -- only pagination's earlier "ignored"
finding was wrong, see below). Coverage is real but bounded -- up to
`MAX_PAGES` * 10 of however many CFTs are open at fetch time, not all
of them; see CANNOT.

WHAT THIS REUSES RATHER THAN DUPLICATES

  - `foundation/mouth_common.py::fetch_feed()` -- the one socket in this
    repository. No second POST/session mechanism is built here.
  - `foundation/discovery_authorization.py::DiscoveryPolicy` -- a fifth,
    independently-declared policy object, `requested_scope="READ_URL"`
    (this module never sends a request body).
  - `foundation/signal_spine.py::CanonicalSignal` -- the only signal
    shape.
  - `foundation/untrusted_text.py::describe()` -- every attacker-
    reachable string (title, description, contracting authority name --
    any Irish public body or private utility publishing through
    eTenders) goes through this before reaching `claim`/`evidence`.
  - `foundation/opportunity.py::SOURCE_TYPES` -- `"OFFICIAL"`, same
    class every other government tendering-platform mouth in this
    repository uses.

WHY A NARROW REGEX OVER THE HTML TABLE, NOT A GENERAL HTML PARSER

Same discipline as `mouth_find_a_tender_uk.py` and `mouth_gets_nz.py`:
this source has no structured feed for the results themselves, only a
fixed, repeated `<table id="T01">` markup shape with one `<tr>` per
notice and thirteen `<td>` columns in a fixed order (confirmed live
against the real page's own `<thead>` labels: #, Title, Resource ID,
CA, Info, Date published, Tenders Submission Deadline, Procedure,
Status, Notice PDF, Award date, Estimated value, Cycle). Parsed by
splitting on `<tr>...</tr>` boundaries and then on `<td...>...</td>`
boundaries within each row, stripping inner markup from each cell's
text -- never a general HTML parser, never executed as markup. A page
with zero rows (a real, honest outcome if the platform is ever between
open notices) yields an empty tuple, never an error.

CLIENT-SIDE SECURITY/CYBER RELEVANCE FILTER

Because the server ignores every filter parameter this cycle tried,
relevance is judged the only place left to judge it honestly: this
module's own `is_security_relevant()` checks the notice's own title and
description text (post-`describe()`, i.e. the same untrusted-text-safe
string that reaches `claim`/`evidence`) against a small, explicit
keyword list (security, cyber, penetration test, pen test, IT health
check, vulnerability, SOC, threat, incident response, ISO 27001). This
is the same class of client-side text match `mouth_gets_nz.py` already
uses to read `<category>` tags it cannot filter server-side -- applied
here to free text because this source, unlike GETS, has no structured
category field on this page at all. A false negative (a relevant notice
using different wording) is possible and expected; a false positive is
possible too -- this is a narrowing heuristic over an already-real,
already-live 10-item window, not a claim of completeness.

VALUE DISCIPLINE -- SAME AS EVERY OTHER MOUTH IN THIS REPOSITORY

`money_state` is ALWAYS `"NOT_OBSERVED"`. The "Estimated value" column
does carry a raw number on many rows (e.g. `836000.0`), but it is free
text inside an HTML `<td>`, not independently verified as a currency-
denominated structured field (no currency symbol or code appears next
to it on this page; the CSV export's own header literally reads
`ESTIMATED_VALUE` with no currency column either). Preserved verbatim,
through `describe()`, in `evidence["value_text_safe"]`, never promoted
to a money figure this module did not itself verify structurally.

CORRECTION -- 2026-09-02, LATER THE SAME DAY: PAGINATION DOES WORK

The finding directly above ("pagination silently ignored") was tested
against the wrong URL and the conclusion was wrong. `d-3680175-p=2` was
appended to `prepareCurrentOpportunities.do` -- a page whose only real
job is a 302 redirect to `quickSearchAction.do?searchType=cftFTS&
latest=true` (confirmed live: `curl -sv` on the prepare URL returns
`HTTP/1.1 302` with `Location: .../quickSearchAction.do?searchType=
cftFTS&latest=true`, no query string carried through). The prepare
endpoint ignores every parameter appended to it because it isn't the
results endpoint at all -- it always redirects to page 1 of the real
one. Re-run against `quickSearchAction.do` directly, `d-3680175-p=N`
IS honoured, statelessly, with no cookie of any kind:

  - `d-3680175-p=1` and `d-3680175-p=2` return disjoint `resourceId`
    sets (confirmed live, zero overlap across two independent fetches).
  - `d-3680175-p=3` returns a third disjoint set.
  - A nonsense out-of-range value (`d-3680175-p=99999`, and the
    genuinely-past-the-end `d-3680175-p=293` when the live total was
    2,916 CFTs / 10 per page = 292 pages) returns an honest, distinct,
    in-band "no more results" shape: no `<table id="T01">`, no
    "results in total" marker, page text containing "No results" --
    not a repeat of page 1, not an error. This is exactly the
    fabrication-check this task brief demanded: a parameter that is
    truly ignored returns IDENTICAL content regardless of value; this
    one returns DIFFERENT, deterministic, disjoint content per value,
    and a well-formed, distinguishable end-of-data signal past the
    last real page.
  - Fetched twice in a row with no cookies at all: byte-identical
    `resourceId` sets per page -- confirmed still stateless, exactly
    as page 1 always was.
  - `d-3680175-c=100` (page-size) remains silently ignored on this
    endpoint too -- confirmed unchanged, still exactly 10 rows
    regardless of the value supplied. Only pagination was mis-tested
    before; page-size genuinely is not honoured.

This module now fetches multiple pages of `quickSearchAction.do` per
sweep (bounded by `MAX_PAGES`, see below) rather than one fixed page of
`prepareCurrentOpportunities.do`. The earlier "silently ignored"
paragraph is left in place above, struck through in spirit rather than
deleted, because this is exactly the kind of self-correction
`docs/DECISIONS/D-013-etenders-depth.md` records in full -- a doctrine
file that quietly edited away its own prior wrong conclusion would be
worse than one that shows the mistake and the fix.

CANNOT

- Cannot see all 2,916 open CFTs in one sweep -- `MAX_PAGES` (currently
  20, 200 potential open CFTs, wired into `DISCOVERY_POLICY.max_queries`
  so the budget matches exactly what one full sweep can spend) bounds
  how many pages one sweep fetches, a deliberate courtesy limit, not a
  platform restriction -- the platform itself was proven above to honour
  every page up to the real end of data. Raising `MAX_PAGES` costs
  nothing structurally; it was kept modest so one cron tick does not
  issue ~292 sequential requests against a public government server
  every run. A relevant notice past page `MAX_PAGES` is invisible to a
  given sweep, honestly, not silently dropped as if it did not exist.
- Cannot pick a larger page size -- `d-3680175-c` is confirmed silently
  ignored (see CORRECTION above); the only way to see more than 10 rows
  in one request is to change `d-3680175-p`, which this module now does.
- Cannot reach the full CSV-shaped export behind `viewCFTSAction.do` --
  see WHAT DOES NOT WORK above; blocked on `mouth_common.py` needing a
  form-urlencoded POST mode this module's file territory does not
  include building.
- Cannot confirm eSourcing NI (etendersni.gov.uk) or Malta eTenders
  (etenders.gov.mt) share this exact shape -- checked live, briefly,
  this cycle: both return a visibly different "Simple search" landing
  page on the identically-named
  `prepareCurrentOpportunities.do?currentType=cft` endpoint (zero
  `resourceId` matches, no "results in total" marker, `<title>European
  Dynamics - Simple search</title>` / `<title>Electronic Tendering -
  Simple search</title>`), not the embedded-results shape Ireland
  returns. The four sites are the same platform *family*, confirmed
  from `<title>`/branding text, but not proven to expose the same
  results shape -- D-010's "crack one, likely crack all four" hypothesis
  is NOT confirmed by this cycle's work and this module makes no claim
  about NI, Malta, or Sell2Wales.
- Cannot confirm a structured currency/value field -- see VALUE
  DISCIPLINE above.
- Cannot tell a genuinely new notice from a re-ordered one beyond what
  the `resourceId` in each row's own link distinguishes -- trusted as
  the dedupe key, same trust every other mouth in this repository
  places in its own source-native identifier.
- Cannot confirm per-notice eligibility restrictions for non-Irish
  suppliers -- this module does not read notice detail pages.
"""
from __future__ import annotations

import hashlib
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
    "MOUTH_ID", "FEED_URL", "RESULTS_URL", "MAX_PAGES", "DISCOVERY_POLICY",
    "FetchError", "MouthObservation", "parse_items", "observe",
    "is_security_relevant", "etenders_ie_signal", "EtendersIeSweep", "sweep",
]

MOUTH_ID = "tender_radar_ie_etenders"

# The results endpoint -- see module docstring's CORRECTION section
# (2026-09-02). `prepareCurrentOpportunities.do?currentType=cft` is NOT
# the results page; it is a 302 redirect to this URL, always landing on
# page 1. Fetching this URL directly, with an explicit `d-3680175-p=N`,
# is what actually walks pages -- confirmed live, disjoint resourceId
# sets per page, honest end-of-data signal past the real last page.
RESULTS_URL = (
    "https://www.etenders.gov.ie/epps/quickSearchAction.do"
    "?searchType=cftFTS&latest=true"
)

# FEED_URL retained as the page-1 URL: the module's "primary" URL for
# gate/policy tests that only need a single valid destination, and the
# first page any sweep fetches.
FEED_URL = f"{RESULTS_URL}&d-3680175-p=1"

# Deliberate courtesy bound, not a platform limit (see CORRECTION /
# CANNOT in the module docstring) -- one sweep fetches at most this many
# pages (10 rows each) of a public government server rather than
# walking the full ~292-page result set every cron tick.
# `DISCOVERY_POLICY.max_queries` below is set to match exactly, so one
# full sweep is the unit the budget bounds, not an arbitrary number.
MAX_PAGES = 20

# `d-3680175-p=N` is honoured; `d-3680175-c` (page size) is not (see
# CORRECTION) -- so the only lever this module has to see more than 10
# rows per request is walking `p`, which costs one HTTP request per
# page. MAX_PAGES pages, each a distinct fetch_feed() call, is why the
# budget below is MAX_PAGES rather than the single-digit default every
# other one-page-per-sweep mouth in this repository uses.
DISCOVERY_POLICY = DiscoveryPolicy(
    objective=(
        "observe Ireland's eTenders (etenders.gov.ie) currently-open "
        "Call for Tenders listing, walked across up to MAX_PAGES pages "
        "of the real results endpoint, for live security/cyber/"
        "penetration-testing procurement opportunities -- one of four "
        "European Dynamics e-PPS platform sites left as 'reachable, "
        "recon incomplete' by docs/DECISIONS/D-010-english-markets.md, "
        "traced through this cycle for Ireland specifically, see "
        "docs/DECISIONS/D-012-epps-platform.md and "
        "docs/DECISIONS/D-013-etenders-depth.md"
    ),
    requested_scope="READ_URL",
    max_queries=MAX_PAGES,
    max_wall_clock_seconds=180,
)

# Column order confirmed live against the real page's own <thead>: #,
# Title, Resource ID, CA, Info, Date published, Tenders Submission
# Deadline, Procedure, Status, Notice PDF, Award date, Estimated value,
# Cycle. Thirteen columns, zero-indexed 0-12 below.
_ROW_RE = re.compile(r'<tr>(.*?)</tr>', re.DOTALL)
_TD_RE = re.compile(r'<td[^>]*>(.*?)</td>', re.DOTALL)
_TAG_RE = re.compile(r'<[^>]+>')
_WS_RE = re.compile(r'\s+')
_TITLE_LINK_RE = re.compile(r'<a href="([^"]+)"[^>]*>([^<]*)</a>')
_RESOURCE_ID_RE = re.compile(r'resourceId=(\d+)')
# The description lives as a single-quoted HTML attribute on an <img>,
# not as element text -- the only field on this page that needs its own
# targeted pattern rather than plain tag-stripping.
_DESC_RE = re.compile(r"<img[^>]*title='([^']*)'")

_COL_TITLE = 1
_COL_ORG = 3
_COL_INFO = 4
_COL_PUBLISHED = 5
_COL_DEADLINE = 6
_COL_PROCEDURE = 7
_COL_STATUS = 8
_COL_AWARD_DATE = 10
_COL_VALUE = 11
_EXPECTED_COLUMNS = 13

# Explicit, narrow, client-side relevance keywords -- see module
# docstring's CLIENT-SIDE SECURITY/CYBER RELEVANCE FILTER section. Kept
# lowercase; matching is done against a lowercased haystack.
_SECURITY_KEYWORDS = (
    "security", "cyber", "penetration test", "pen test", "pentest",
    "it health check", "vulnerability", "soc ", "threat", "incident response",
    "iso 27001", "infosec", "malware", "firewall", "encryption",
)


def _clean_text(cell_html: str) -> str:
    """Strip inner markup from one <td> cell and collapse whitespace --
    never a general HTML parser, never executed as markup."""
    return _WS_RE.sub(' ', _TAG_RE.sub('', cell_html)).strip()


_MARKER_RE = re.compile(r'[\d,]+\s+results in total\.?', re.IGNORECASE)


def _page_url(page: int) -> str:
    """Build the URL for one results page. `page` is 1-indexed, matching
    the site's own "Page" control (confirmed live)."""
    return f"{RESULTS_URL}&d-3680175-p={page}"


def _merge_pages_html(pages_raw: list[bytes]) -> bytes:
    """Concatenate the `<tbody>` row content of each already-fetched page
    into one synthetic document `parse_items()` can read unchanged --
    keeps the parser single-page-shaped while the fetch side walks many
    pages. Never fabricates a "results in total" marker: if none of the
    fetched pages carried a recognisable marker, none is emitted here
    either, so `parse_items()`'s own "no rows AND no marker -> FetchError"
    rule still fires on a genuinely unrecognised page shape (a WAF
    challenge, a redesign) rather than being silently swallowed as an
    honest empty result.
    """
    rows_html: list[str] = []
    marker = ""
    for raw in pages_raw:
        text = raw.decode("utf-8", errors="replace")
        tbody_start = text.find("<tbody>")
        tbody_end = text.find("</tbody>")
        if tbody_start != -1 and tbody_end != -1:
            rows_html.append(text[tbody_start + len("<tbody>"):tbody_end])
        if not marker:
            match = _MARKER_RE.search(text)
            if match:
                marker = match.group(0)
    marker_html = f"<div>{marker}</div>" if marker else ""
    body = "\n".join(rows_html)
    return (
        f"<html><body>{marker_html}"
        f'<table id="T01"><thead></thead><tbody>{body}</tbody></table>'
        "</body></html>"
    ).encode("utf-8")


def _fetch_pages(policy: DiscoveryPolicy, max_pages: int = MAX_PAGES) -> bytes:
    """Walk up to `max_pages` pages of `RESULTS_URL`, one `fetch_feed()`
    call per page (so authorization and budget are charged per page, not
    once for the whole walk -- see `DISCOVERY_POLICY.max_queries`).
    Stops early, honestly, the moment a fetched page carries no
    `<tbody>` at all -- confirmed live (module docstring's CORRECTION
    section) that a page past the real last page returns a distinct
    "No results" shape with no results table, not a repeat of an
    earlier page and not an error. Returns the merged synthetic
    document; `parse_items()` does the real parsing, unchanged.
    """
    pages_raw: list[bytes] = []
    for page in range(1, max_pages + 1):
        raw = fetch_feed(_page_url(page), policy=policy)
        pages_raw.append(raw)
        if b"<tbody>" not in raw:
            break
    return _merge_pages_html(pages_raw)


def parse_items(raw: bytes) -> tuple[dict, ...]:
    """Parse the eTenders IE `prepareCurrentOpportunities.do?
    currentType=cft` HTML page into open-CFT item dicts.

    Decoding failure, or a page carrying no recognisable `<table
    id="T01">` row AND no "results in total" honest-empty marker, raises
    `FetchError` -- the same UNAVAILABLE-not-crash contract every mouth
    in this repository gives `mouth_common.observe()`. A row that does
    not have exactly the expected 13 columns is skipped rather than
    guessed at -- a redesigned page should surface as fewer parsed items,
    not corrupted ones.
    """
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise FetchError(f"response did not decode as UTF-8: {exc}") from exc

    tbody_start = text.find("<tbody>")
    tbody_end = text.find("</tbody>")
    has_tbody = tbody_start != -1 and tbody_end != -1 and tbody_end > tbody_start
    rows = _ROW_RE.findall(text[tbody_start:tbody_end]) if has_tbody else []

    if not rows and "results in total" not in text:
        # Neither a parseable row nor the page's own "N results in
        # total" marker -- not a shape this module recognises (a
        # redesigned page, an error page, a WAF challenge page), so it
        # is UNAVAILABLE rather than a silent zero.
        raise FetchError(
            "eTenders IE page carried no recognisable results row and "
            "no 'results in total' marker -- page shape not recognised"
        )

    items: list[dict] = []
    for row in rows:
        cells = _TD_RE.findall(row)
        if len(cells) != _EXPECTED_COLUMNS:
            # Not the shape this module was built against -- dropped,
            # never guessed at. Real future increment if this ever
            # fires on a live fetch: re-verify the column order rather
            # than silently reindexing.
            continue

        title_match = _TITLE_LINK_RE.search(cells[_COL_TITLE])
        if not title_match:
            continue
        link_path = title_match.group(1).strip()
        title = _clean_text(title_match.group(2))

        rid_match = _RESOURCE_ID_RE.search(link_path)
        resource_id = rid_match.group(1) if rid_match else ""
        if not resource_id:
            # No stable identity to dedupe against -- dropped rather
            # than keyed on a guess, same discipline as every other
            # mouth in this repository's parse_items().
            continue

        link = (
            link_path if link_path.startswith("http")
            else f"https://www.etenders.gov.ie{link_path}"
        )

        desc_match = _DESC_RE.search(cells[_COL_INFO])
        description = _clean_text(desc_match.group(1)) if desc_match else ""

        items.append({
            "key": resource_id,
            "resource_id": resource_id,
            "link": link,
            "title": title,
            "description": description,
            "organisation": _clean_text(cells[_COL_ORG]),
            "published": _clean_text(cells[_COL_PUBLISHED]),
            "deadline": _clean_text(cells[_COL_DEADLINE]),
            "procedure": _clean_text(cells[_COL_PROCEDURE]),
            "status": _clean_text(cells[_COL_STATUS]),
            "award_date": _clean_text(cells[_COL_AWARD_DATE]),
            "value_text": _clean_text(cells[_COL_VALUE]),
        })
    return tuple(items)


def is_security_relevant(title_safe: str, description_safe: str) -> bool:
    """Client-side relevance judgment -- see module docstring's CLIENT-
    SIDE SECURITY/CYBER RELEVANCE FILTER section. Operates on the
    already-`describe()`-safe text, the same string that reaches
    `claim`/`evidence`, so this check and what a caller can inspect
    never disagree about what was matched."""
    haystack = f"{title_safe} {description_safe}".lower()
    return any(keyword in haystack for keyword in _SECURITY_KEYWORDS)


def observe(
    state_path: Path,
    fetch_fn: Optional[Callable[[], bytes]] = None,
    now: Optional[datetime] = None,
) -> MouthObservation:
    """One observation cycle over the eTenders IE open-CFT page.
    `fetch_fn` is injected in every test in
    `foundation/tests/test_mouth_etenders_ie.py` -- no test touches the
    real network. Default path walks up to `MAX_PAGES` pages of
    `RESULTS_URL` via `_fetch_pages()`, each page its own
    `mouth_common.fetch_feed()` call gated by `DISCOVERY_POLICY` (see
    module docstring's CORRECTION section for why this is now
    multi-page rather than the single fixed page this module used to
    fetch)."""
    fetch = fetch_fn or (lambda: _fetch_pages(DISCOVERY_POLICY))
    return _observe(MOUTH_ID, state_path, fetch, parse_items, now=now)


def etenders_ie_signal(item: dict, now: Optional[datetime] = None) -> CanonicalSignal:
    """One open-CFT item -> one `CanonicalSignal`. Emitted for EVERY
    parsed item regardless of `is_security_relevant()` -- the same
    discipline `mouth_find_a_tender_uk.py` uses for lifecycle stage:
    this module does not silently drop items a caller might judge
    differently. `EtendersIeSweep.show_the_math()` marks which signals
    matched the security/cyber keyword filter; callers that only want
    those can read `facts["security_relevant"]`.

    Title, description and organisation text are attacker-reachable
    free text (any Irish public body or private utility publishing
    through eTenders) and run through `untrusted_text.describe()`
    before anything derived from them reaches `claim`/`evidence` --
    same discipline as every other mouth in this repository.
    """
    observed_at = (now or datetime.now(timezone.utc)).isoformat()
    title = describe(item.get("title", ""))
    description = describe(item.get("description", ""))
    org = describe(item.get("organisation", ""))
    procedure = describe(item.get("procedure", ""))
    status = describe(item.get("status", ""))
    value_text = describe(item.get("value_text", ""))
    markers = tuple(sorted(
        set(title.markers) | set(description.markers) | set(org.markers)
        | set(procedure.markers) | set(status.markers) | set(value_text.markers)))

    safe_key = describe(str(item.get("key", ""))).safe
    safe_link = describe(str(item.get("link", ""))).safe

    relevant = is_security_relevant(title.safe, description.safe)

    target = org.safe or safe_key

    claim_subject = title.safe or safe_key
    claim = f"Ireland eTenders open CFT ({status.safe or 'status unknown'}): {claim_subject}"
    if org.safe:
        claim += f" (contracting authority: {org.safe})"

    # No structured currency field is read by this module -- see module
    # docstring's VALUE DISCIPLINE section.
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
        "resource_id": safe_key,
        "organisation_safe": org.safe,
        "identity_hash": identity_hash,
        "procedure_safe": procedure.safe,
        "status_safe": status.safe,
        "published": item.get("published", ""),
        "deadline": item.get("deadline", ""),
        "award_date": item.get("award_date", ""),
        "value_text_safe": value_text.safe,
        "title_safe": title.safe,
        "description_safe": description.safe,
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
            "procedure": procedure.safe,
            "deadline": item.get("deadline", ""),
            "security_relevant": "true" if relevant else "false",
        },
        evidence=evidence,
        pressure_class="EXPLICIT_DEMAND",
        pressure_evidence=(
            "published on Ireland's eTenders (etenders.gov.ie) as a "
            "currently open Call for Tenders, naming a contracting "
            "authority and a resource identifier -- a public or public-"
            "adjacent body stating outright that it intends to buy"
        ),
        money_state=money_state,
        money_observed=money_observed,
    )


@dataclass(frozen=True)
class EtendersIeSweep:
    """One observation cycle, report only -- same discipline as every
    other `*Sweep` in this repository: no ledger write, no promotion,
    no contact."""

    status: str
    fetched_count: int
    error: Optional[str]
    signals: tuple[CanonicalSignal, ...]
    targets: tuple[str, ...]

    def security_relevant_signals(self) -> tuple[CanonicalSignal, ...]:
        return tuple(
            s for s in self.signals if s.facts.get("security_relevant") == "true"
        )

    def show_the_math(self) -> str:
        relevant = self.security_relevant_signals()
        lines = [
            f"ETENDERS IE RADAR status={self.status} "
            f"fetched={self.fetched_count} signals={len(self.signals)} "
            f"security_relevant={len(relevant)}"
        ]
        if self.error:
            lines.append(f"  error: {self.error}")
        if self.status in ("FIRST_SEEN", "CHANGED") and not self.signals:
            lines.append(
                "  zero open CFT notices observed this cycle -- a valid, "
                "honest outcome, not an error"
            )
        for s in self.signals:
            tag = "SECURITY " if s.facts.get("security_relevant") == "true" else "         "
            lines.append(f"  {tag}OBSERVED  target={s.target!r}  {s.claim}")
        if self.signals:
            lines.append(
                "  every signal above is OBSERVED only -- none is "
                "VERIFIED or REALIZED; only up to MAX_PAGES pages of "
                "open CFTs are visible per sweep, see module "
                "docstring's CANNOT section"
            )
        return "\n".join(lines)


def sweep(
    state_dir: Path,
    fetch_fn: Optional[Callable[[], bytes]] = None,
    now: Optional[datetime] = None,
) -> EtendersIeSweep:
    """Run one eTenders-IE-radar cycle: observe -> signal -> report."""
    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / f"{MOUTH_ID}.json"
    observation = observe(state_path, fetch_fn=fetch_fn, now=now)
    signals = tuple(etenders_ie_signal(item, now=now) for item in observation.new_items)
    targets = tuple(sorted({s.target for s in signals}))
    return EtendersIeSweep(
        status=observation.status,
        fetched_count=observation.item_count,
        error=observation.error,
        signals=signals,
        targets=targets,
    )
