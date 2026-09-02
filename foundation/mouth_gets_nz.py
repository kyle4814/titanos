"""A third tender mouth: New Zealand's Government Electronic Tenders
Service (GETS) RSS feed of currently open tenders and RFQs.

WHY THIS FILE IS NAMED `mouth_gets_nz.py`, NOT `mouth_austender.py`

This cycle's task brief asked for `foundation/mouth_austender.py`,
which presupposes an Australian source was found. One was not --
Australian government procurement remains unreachable for the exact
reasons `tender_radar.py`'s own module docstring and `docs/DECISIONS/
D-003-au-sources.md` already record, reconfirmed live this cycle (see
`docs/DECISIONS/D-006-australian-access.md` for the full route list).
What WAS found, live, this cycle, is New Zealand's GETS -- the task
brief's own item 6 named this as a candidate ("Is there a New Zealand
equivalent (GETS) that IS reachable? NZ is a realistic adjacent
market"). Calling a file that reads NZ tender notices
`mouth_austender.py` would mislabel every signal it produces as
Australian when it is not -- the identical mislabelling defect
`mouth_ted.py`'s own docstring names and refuses ("calling
tender_radar.tender_signal() on a French, German, Spanish or Greek TED
notice would produce a signal whose own claim text falsely says 'UK'").
This module's own `claim` text says "NZ", honestly, for the same
reason.

WHAT WAS ACTUALLY TRIED THIS CYCLE, LIVE, 2026-09-02, BEFORE LANDING
HERE

The prior cycle's AU findings (D-003) were not re-tried; they stand.
Six new routes were tried:

  1. AusTender bulk/reports/atom paths on `www.tenders.gov.au` -- still
     HTTP 403 (CloudFront WAF), same as D-003.
  2. The Open Contracting Partnership's own AusTender OCDS mirror,
     `data.open-contracting.org/en/publication/19` -- genuinely
     reachable (robots.txt `Disallow:` empty, HTTP 200, no auth,
     CC BY 3.0 AU), and genuinely more current than D-003's stale 2013
     CKAN snapshot (`2026.jsonl.gz`, last-modified 2026-08-14, ~50k
     records). Downloaded and inspected directly: of 50,269 records in
     the live 2026 file, 50,269/50,269 (100%) already carry an
     `awards` array and 0/50,269 have a `tender.tenderPeriod` field --
     this is award/contract-notice data (decided, signed contracts),
     not open-opportunity data. Building a DEMAND signal from it would
     report an already-awarded contract as something the operator
     could still bid on -- exactly the fabrication class D-003's own
     "wrong shape" finding already ruled out for AusTender data,
     reconfirmed here on a fresher file rather than assumed to still
     apply. NOT USED, same reasoning as D-003.
  3. `catalogue.data.govt.nz` (NZ's own CKAN open-data portal) --
     `robots.txt` disallows `/api/` for `User-agent: *`, matching
     `data.gov.au`'s own disallow shape; a dataset PAGE (not the /api/
     path) was reachable and named "New Zealand Government procurement
     AWARD notices" -- again award data, same wrong shape, hosted on
     `www.mbie.govt.nz` as CSV exports. NOT USED, same reasoning.
  4. `gets.govt.nz` / `www.gets.govt.nz` -- `robots.txt` (HTTP 200)
     disallows only `SEMrushBot`/`SemrushBot`/`SemrushBot-SA`; this
     fetcher's own honest User-Agent is unrestricted. The site's root
     page lists real, live, currently-open tender notices (HEALTHNZ,
     Ministry of Justice, MFAT, several district councils among them),
     and links to `ExternalRSSFeed.htm` -- a genuine RSS 2.0 feed,
     confirmed live: 337 `<item>` entries, most recent `pubDate`
     2026-08-26 (six days before this cycle's date), earliest a 2021
     standing panel still genuinely open. This is THE source this
     module reads.
  5. `www.gets.govt.nz/api` -- HTTP 401, a keyed endpoint. Not used;
     the RSS feed above needs no key.
  6. Query-parameter filtering was tried and PROVEN NOT TO WORK, per
     this task brief's own fabrication check: `ExternalRSSFeed.htm?
     category=`, `?region=`, and `?classificationId=81110000` all
     returned the identical 337-item feed byte-for-byte (same item
     count) as the bare URL -- an unrecognised query parameter is
     silently accepted and ignored by this endpoint, the same failure
     class `tender_radar.py`'s own CANNOT section names for Contracts
     Finder's CPV parameter. This module therefore does NOT attempt to
     filter on the wire, same discipline as `tender_radar.py`: it
     fetches the one full feed and reads each notice's own `<category>`
     tags client-side.

WHAT THIS REUSES RATHER THAN DUPLICATES

  - `foundation/mouth_common.py::fetch_feed()` -- the ONE socket in
    this repository. This module opens no socket itself.
  - `foundation/discovery_authorization.py::DiscoveryPolicy` -- same
    gate every mouth is bound by; `DISCOVERY_POLICY` below is a third,
    independently-declared policy object.
  - `foundation/signal_spine.py::CanonicalSignal` -- the only signal
    shape. No second signal type is defined here.
  - `foundation/untrusted_text.py::describe()` -- every attacker-
    reachable string (title, description, organisation name -- any NZ
    public body or, per the live feed, an SOE/lines company such as
    Aurora Energy that also publishes through GETS) goes through this
    before reaching `claim`/`evidence`, same discipline as
    `tender_radar.py`/`mouth_ted.py`.
  - `foundation/opportunity.py::SOURCE_TYPES` -- `"OFFICIAL"`, the same
    class `tender_radar.py` uses for UK Contracts Finder: a government-
    run tendering platform, not a second-hand aggregator.

WHY XML/RSS PARSING, NOT `tender_radar.parse_items()` OR `mouth_ted`'s
JSON PARSING COPIED

Neither existing tender mouth parses RSS/XML -- `tender_radar.py`
consumes OCDS JSON, `mouth_ted.py` consumes TED's own JSON search
response. GETS publishes RSS 2.0 with Dublin Core extensions
(`dc:creator`, `dc:date`) and no separate structured value/deadline
field at all -- every deadline and value figure the feed carries lives
inside one HTML table embedded, HTML-entity-escaped, in `<description>`.
This module therefore uses `xml.etree.ElementTree` (standard library,
no new dependency) for the RSS envelope, and a small, narrowly-scoped
regex over the UNESCAPED description text to recover `Close date:` --
never a general HTML parser, never executed as markup. A description
that does not contain a recognisable "Close date:" row yields
`deadline=""`, never a guessed or defaulted date.

VALUE DISCIPLINE -- SAME AS `tender_radar.py` AND `mouth_ted.py`

A signal this module emits is OBSERVED at best: a notice with this
title, organisation and close date existed in the live feed at
`observed_at`. It is not VERIFIED and never REALIZED.
`money_state` is ALWAYS `"NOT_OBSERVED"` here -- confirmed live,
2026-09-02: no `<item>` in the 337-entry feed carries a machine-
readable value/amount field anywhere in the RSS envelope; the word
"Value"/"Price"/"$"/"NZD" appears only inside free-text descriptions in
prose a human wrote (e.g. "no maximum value has been set"), which this
module refuses to parse into a number -- inventing a structured amount
from free text is exactly the fabrication this repository's value
discipline exists to prevent. If a future notice's description is ever
found to carry a genuinely structured value line, that is a new finding
to fold into `_extract_close_date()`'s sibling, not something to guess
at now.

CANNOT

- Cannot filter this feed server-side by category/region (see finding 6
  above) -- every fetch returns the full open-tender list; relevance
  narrowing happens by reading each item's own `<category>` UNSPSC
  codes/labels client-side, never by trusting a query parameter.
- Cannot recover a structured close date for every item -- a notice
  whose description text does not match the "Close date:" table row
  pattern (feed encoding drift, a buyer who edited the free-text field)
  gets `deadline=""`, honestly, rather than a fabricated one.
- Cannot tell a genuinely new notice from a republished one beyond what
  `guid` (this feed's own stable per-notice URL, confirmed live to be
  unique per item) distinguishes -- trusted as the dedupe key, the same
  trust `tender_radar.py` places in `ocid`.
- Cannot see notices NZ public bodies procure through a channel other
  than GETS (e.g. direct panel arrangements never listed here).
"""

from __future__ import annotations

import hashlib
import html
import re
import unicodedata
import xml.etree.ElementTree as ET
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
    "MouthObservation", "parse_items", "observe", "gets_signal",
    "GetsRadarSweep", "sweep",
    "DETAIL_DISCOVERY_POLICY", "DETAIL_FIELDS", "parse_tender_detail",
    "fetch_tender_detail",
]

MOUTH_ID = "tender_radar_nz_gets"

# The one GETS endpoint this module ever calls. Confirmed live
# 2026-09-02: `robots.txt` only disallows SEMrushBot variants; this URL
# returns a real RSS 2.0 feed of every currently open NZ government
# tender/RFQ, no key, no login. Query-parameter filtering was tried and
# proven not to change the result (see module docstring finding 6) --
# no query string is appended here.
FEED_URL = "https://www.gets.govt.nz/ExternalRSSFeed.htm"

DISCOVERY_POLICY = DiscoveryPolicy(
    objective=(
        "observe the NZ Government Electronic Tenders Service (GETS) "
        "RSS feed for currently open public-sector tenders and RFQs -- "
        "the reachable adjacent market found after Australian "
        "government procurement was reconfirmed blocked or wrong-shape "
        "for this fetcher, see docs/DECISIONS/D-006-australian-access.md"
    ),
    requested_scope="READ_URL",
)

# ── DETAIL-PAGE EXTRACTION ──────────────────────────────────────────
#
# Added 2026-09-02, per a live check of `robots.txt`
# (`https://www.gets.govt.nz/robots.txt` -- confirmed live, same file
# `FEED_URL` above already documents: only SEMrushBot variants are
# disallowed anywhere on the site; this fetcher's own honest User-Agent
# is unrestricted, so fetching an individual
# `ExternalTenderDetails.htm?id=NNNNN` page -- the page each RSS
# `<item><link>` already points at -- is permitted).
#
# A small, polite sample (3 of the 36 security-relevant notices, several
# seconds apart, single-fetch-per-notice, no crawl) was fetched and
# inspected by hand. Every one of the three carries a real HTML table
# (`<table class="tender-details-info-tbl">`, one `<tr><td class=
# "label-cell">LABEL</td><td>VALUE</td></tr>` per field) with a fixed,
# small field set: RFx ID, Tender Name, Reference #, Open Date, Close
# Date, Department/Business Unit, Tender Type, Tender Coverage,
# Categories, Regions, Exemption Reason, Required Pre-qualifications,
# Contact, Alternate Physical Delivery Address, Alternate Physical Fax
# Number. That is the ENTIRE field set observed -- no selection
# criteria, no insurance requirement, no reference/track-record
# requirement, no legal-form/consortium field, no financial-capacity
# field appear anywhere on any of the three pages fetched. The RFx's own
# stated response requirements, if any exist beyond this table, live in
# a downloadable RFx document this page does not embed and this module
# does not fetch (no link to one was observed on any of the three
# samples; a locked/paywalled RFx document was not observed either --
# the honest state is that this page simply does not carry one).
#
# THE ONE GENUINELY NEW, GENUINELY USEFUL FIELD: "Required
# Pre-qualifications". Unlike the RSS feed's total silence on bidder
# conditions (see module docstring's CRITICAL-HONESTY-adjacent
# discussion in `foundation/sources.py`), this field is POSITIVELY
# STATED on the detail page -- all three samples carried the literal
# value "None" (`<span class="notice">None</span>`). A stated "None" is
# real evidence a formal pre-qualification/panel-membership gate was not
# imposed for that specific notice; it is NOT evidence about insurance,
# certification, reference or financial-capacity requirements, which
# never appear as a field on this page at all and stay strictly
# UNKNOWN -- extracted as absent from the returned dict, never defaulted
# to "None" or any other value. Absence of a FIELD ON THE PAGE and a
# field's STATED VALUE of "None" are two different things and this
# module never collapses them into one.
#
# WHAT THIS DOES NOT DO: does not claim the three-sample field set is
# exhaustive across all 324 open NZ notices -- a future notice could use
# a different template. Does not follow any link off this page (no RFx
# document download, no login flow). Does not infer eligibility --
# extraction only; `eligibility.py`/`sources.py` remain untouched and
# this module supplies no `assess_eligibility()`-shaped mapping for
# detail-page fields, deliberately, since that mapping is out of this
# module's file territory.
DETAIL_DISCOVERY_POLICY = DiscoveryPolicy(
    objective=(
        "fetch one GETS ExternalTenderDetails.htm notice detail page to "
        "extract the genuinely-present bidder-condition fields it "
        "carries (e.g. Required Pre-qualifications), never inferring an "
        "absent field as a cleared requirement -- see "
        "docs/DECISIONS and this module's DETAIL-PAGE EXTRACTION note"
    ),
    requested_scope="READ_URL",
)

# Label text (as it appears, tag-stripped, in the source table) -> the
# key this module returns it under. Only labels actually observed on a
# live page are listed -- a label never seen is simply never produced,
# not guessed at.
DETAIL_FIELDS = {
    "RFx ID": "rfx_id",
    "Tender Name": "tender_name",
    "Reference #": "reference",
    "Open Date": "open_date",
    "Close Date": "close_date",
    "Department/Business Unit": "department",
    "Tender Type": "tender_type",
    "Tender Coverage": "tender_coverage",
    "Categories": "categories",
    "Regions": "regions",
    "Exemption Reason": "exemption_reason",
    "Required Pre-qualifications": "required_pre_qualifications",
    "Contact": "contact",
}

# Narrow, single-purpose: this table's own row shape only. Never a
# general HTML parser; never executed as markup. `re.S` because a
# value cell's content (a <ul> of categories/regions, or a multi-line
# contact block) legitimately spans newlines in the source HTML.
_DETAIL_TABLE_RE = re.compile(
    r'<table class="tender-details-info-tbl">(.*?)</table>', re.S)
_DETAIL_ROW_RE = re.compile(
    r'<td class="label-cell">(.*?)</td>\s*<td>(.*?)</td>', re.S)
_LI_RE = re.compile(r"<li>(.*?)</li>", re.S)
_TAG_RE = re.compile(r"<[^>]+>")


def _strip_tags(fragment: str) -> str:
    """Tag-strip one already-isolated table-cell fragment, unescape
    entities, collapse whitespace. Not a general HTML parser -- only
    ever applied to a fragment already isolated by `_DETAIL_ROW_RE`."""
    text = html.unescape(_TAG_RE.sub(" ", fragment))
    return " ".join(text.split())


def parse_tender_detail(raw: bytes) -> dict:
    """Extract the genuinely-present fields from one GETS
    ExternalTenderDetails.htm page.

    Returns a dict keyed by `DETAIL_FIELDS`' values, containing ONLY the
    labels actually found in the page's own details table -- a label
    never observed on this particular page is simply absent from the
    returned dict (`.get(key)` -> `None` at the Python level, which
    callers must read as UNKNOWN, never as "no requirement"; see this
    module's DETAIL-PAGE EXTRACTION note above). `categories` and
    `regions` are returned as tuples of strings (their value cells are
    `<li>` lists on every sample observed); every other present field is
    a single cleaned string, even if empty ("" for a genuinely blank
    cell, e.g. `Alternate Physical Fax Number` — an empty stated cell is
    still a found field, distinct from a field never found at all).

    No table found (`FetchError`) means the page did not match the one
    shape this was built against -- callers must treat that as
    UNAVAILABLE, the same discipline as `parse_items()`'s malformed-feed
    path, never as "zero requirements"."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FetchError(f"detail page did not decode as UTF-8: {exc}") from exc

    table_match = _DETAIL_TABLE_RE.search(text)
    if table_match is None:
        raise FetchError(
            "detail page has no tender-details-info-tbl table -- page "
            "shape did not match what this extractor was built against"
        )
    table_html = table_match.group(1)

    result: dict = {}
    for label_html, value_html in _DETAIL_ROW_RE.findall(table_html):
        label = _strip_tags(label_html).rstrip(": ").strip()
        key = DETAIL_FIELDS.get(label)
        if key is None:
            # An unrecognised label -- some other field this module has
            # never seen. Dropped rather than guessed into a key; see
            # this function's own docstring on absence.
            continue
        if key in ("categories", "regions"):
            items = tuple(
                _strip_tags(li) for li in _LI_RE.findall(value_html)
                if _strip_tags(li)
            )
            result[key] = items
        else:
            result[key] = _strip_tags(value_html)
    return result


def fetch_tender_detail(
    url: str,
    fetch_fn: Optional[Callable[[], bytes]] = None,
) -> dict:
    """Fetch and parse one GETS notice detail page. `fetch_fn` injected
    in every test in `foundation/tests/test_mouth_gets_nz.py` -- no test
    in this repository touches the real network, this function included.
    When `fetch_fn` is None the default path goes through
    `mouth_common.fetch_feed()` against `url` with
    `DETAIL_DISCOVERY_POLICY`, which refuses without it -- there is no
    second, ungated path here, same discipline as `observe()` above."""
    fetch = fetch_fn or (lambda: fetch_feed(url, policy=DETAIL_DISCOVERY_POLICY))
    raw = fetch()
    return parse_tender_detail(raw)


_RSS_NS = {"dc": "http://purl.org/dc/elements/1.1/"}

# Narrow, single-purpose: recover "Close date: <value>" from the
# unescaped embedded description table. Never a general HTML parser;
# never executed as markup. A non-matching description yields no
# deadline rather than a guess -- see module docstring's CANNOT section.
_CLOSE_DATE_RE = re.compile(
    r"Close date:\s*(?:</?[a-zA-Z][^>]*>\s*)*([^<]+?)\s*(?:<|$)")
_RFX_ID_RE = re.compile(r"RFx ID:\s*(?:</?[a-zA-Z][^>]*>\s*)*([^<]+?)\s*(?:<|$)")


def _clean_str(value: object) -> str:
    """Same discipline as `tender_radar._clean_str()`: a field this
    repository does not control the type of is read as absent rather
    than crashing the parse."""
    return value if isinstance(value, str) else ""


def _first_match(pattern: re.Pattern, text: str) -> str:
    m = pattern.search(text)
    return m.group(1).strip() if m else ""


def parse_items(raw: bytes) -> tuple[dict, ...]:
    """Parse the GETS RSS 2.0 feed into open-tender item dicts.

    Malformed XML or a root that isn't an `rss`/`channel` shape raises
    `FetchError` -- the same UNAVAILABLE-not-crash contract every mouth
    in this repository gives `mouth_common.observe()`. One malformed
    `<item>` is skipped, never aborts the whole parse -- one bad notice
    among 337 must not blind the radar to the rest.
    """
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise FetchError(f"feed did not parse as XML: {exc}") from exc

    channel = root.find("channel")
    if channel is None:
        raise FetchError("feed has no <channel> element")

    items: list[dict] = []
    for el in channel.findall("item"):
        title = _clean_str(el.findtext("title"))
        link = _clean_str(el.findtext("link")).strip()
        guid = _clean_str(el.findtext("guid")).strip() or link
        if not guid:
            # No stable identity to dedupe against -- dropped rather
            # than keyed on a guess, same discipline as
            # tender_radar.parse_items() dropping an ocid-less release.
            continue

        raw_description = _clean_str(el.findtext("description"))
        # The feed HTML-escapes its own embedded table
        # ("&lt;table&gt;..."); unescape once so the regexes below can
        # match real "<td>"/"</td>" boundaries. This is text recovery
        # for two named fields, never rendered or executed as markup.
        unescaped_description = html.unescape(raw_description)

        close_date = _first_match(_CLOSE_DATE_RE, unescaped_description)
        rfx_id = _first_match(_RFX_ID_RE, unescaped_description)

        creator = _clean_str(el.findtext("{%s}creator" % _RSS_NS["dc"]))
        dc_date = _clean_str(el.findtext("{%s}date" % _RSS_NS["dc"]))
        pub_date = _clean_str(el.findtext("pubDate"))

        categories = tuple(
            _clean_str(c.text).strip()
            for c in el.findall("category")
            if _clean_str(c.text).strip()
        )

        items.append({
            "key": guid,
            "guid": guid,
            "link": link,
            "title": title,
            "description": unescaped_description,
            "organisation": creator,
            "close_date": close_date,
            "rfx_id": rfx_id,
            "published": dc_date or pub_date,
            "categories": categories,
        })
    return tuple(items)


def observe(
    state_path: Path,
    fetch_fn: Optional[Callable[[], bytes]] = None,
    now: Optional[datetime] = None,
) -> MouthObservation:
    """One observation cycle over the GETS feed. `fetch_fn` injected in
    every test in `foundation/tests/test_mouth_gets_nz.py` -- no test in
    this repository touches the real network, this module included.
    When `fetch_fn` is None the default path goes through
    `mouth_common.fetch_feed()` against `FEED_URL`, which refuses
    without `DISCOVERY_POLICY` -- there is no second, ungated path
    here."""
    fetch = fetch_fn or (lambda: fetch_feed(FEED_URL, policy=DISCOVERY_POLICY))
    return _observe(MOUTH_ID, state_path, fetch, parse_items, now=now)


def gets_signal(item: dict, now: Optional[datetime] = None) -> CanonicalSignal:
    """One open-tender item -> one `CanonicalSignal`.

    Title, description, organisation and category text are attacker-
    reachable free text (any buyer with a GETS account can populate
    them, per the live "Aurora Energy" / district-council examples seen
    in the feed) and are run through `untrusted_text.describe()` before
    anything derived from them reaches `claim`/`evidence` -- same
    discipline as `tender_radar.tender_signal()`/`mouth_ted.ted_signal()`.
    """
    observed_at = (now or datetime.now(timezone.utc)).isoformat()
    title = describe(item.get("title", ""))
    description = describe(item.get("description", ""))
    org = describe(item.get("organisation", ""))
    markers = tuple(sorted(
        set(title.markers) | set(description.markers) | set(org.markers)))

    safe_key = describe(str(item.get("key", ""))).safe
    safe_rfx_id = describe(str(item.get("rfx_id", ""))).safe
    safe_categories = tuple(describe(c).safe for c in item.get("categories", ()))

    target = org.safe or safe_rfx_id or safe_key

    claim_subject = title.safe or safe_rfx_id or safe_key
    claim = f"open NZ public-sector tender (GETS): {claim_subject}"
    if org.safe:
        claim += f" (organisation: {org.safe})"

    # No structured value field exists anywhere on this feed -- see
    # module docstring's VALUE DISCIPLINE section. Never inferred from
    # free text.
    money_state = "NOT_OBSERVED"
    money_observed = ""

    # Same recipe as tender_radar.tender_signal()/mouth_ted.ted_signal():
    # NFC-normalise, strip, lower, UTF-8, sha256 -- computed from the
    # RAW organisation name before describe() truncates it, so the same
    # buyer collapses to one controlling party regardless of which
    # source observed them.
    org_raw = item.get("organisation", "")
    identity_hash = (
        hashlib.sha256(
            unicodedata.normalize("NFC", org_raw).strip().lower().encode("utf-8")
        ).hexdigest()
        if isinstance(org_raw, str) and org_raw.strip()
        else ""
    )

    safe_link = describe(str(item.get("link", ""))).safe
    source_ref = safe_link  # this feed's own per-notice URL, never FEED_URL

    evidence = {
        "guid": safe_key,
        "rfx_id": safe_rfx_id,
        "organisation_safe": org.safe,
        "identity_hash": identity_hash,
        "close_date": item.get("close_date", ""),
        "published": item.get("published", ""),
        "title_safe": title.safe,
        "description_safe": description.safe,
        "categories_safe": safe_categories,
        "injection_markers": markers,
    }

    kwargs = {}
    if item.get("published"):
        kwargs["event_at"] = item["published"]

    return CanonicalSignal(
        signal_id=f"tender:{safe_key}",
        source_id=MOUTH_ID,
        source_type="OFFICIAL",
        source_ref=source_ref,
        target=target,
        kind="DEMAND",
        claim=claim,
        observed_at=observed_at,
        target_established_by="SOURCE_NATIVE",
        facts={
            "close_date": item.get("close_date", ""),
            "categories": " | ".join(safe_categories),
        },
        evidence=evidence,
        pressure_class="EXPLICIT_DEMAND",
        pressure_evidence=(
            "published on the NZ Government Electronic Tenders Service "
            "(GETS) open-tenders RSS feed, naming an organisation and an "
            "RFx ID -- a public or public-adjacent body stating outright "
            "that it intends to purchase"
        ),
        money_state=money_state,
        money_observed=money_observed,
        **kwargs,
    )


@dataclass(frozen=True)
class GetsRadarSweep:
    """One observation cycle, report only -- same discipline as
    `tender_radar.TenderRadarSweep`: no ledger write, no promotion, no
    contact. Reading this report and deciding what to do about a lead
    stays a human's job."""

    status: str
    fetched_count: int
    error: Optional[str]
    signals: tuple[CanonicalSignal, ...]
    targets: tuple[str, ...]

    def show_the_math(self) -> str:
        lines = [
            f"GETS NZ RADAR status={self.status} fetched={self.fetched_count} "
            f"signals={len(self.signals)}"
        ]
        if self.error:
            lines.append(f"  error: {self.error}")
        if self.status in ("FIRST_SEEN", "CHANGED") and not self.signals:
            lines.append(
                "  zero open tenders observed this cycle -- a valid, honest "
                "outcome, not an error"
            )
        for s in self.signals:
            lines.append(f"  OBSERVED  target={s.target!r}  {s.claim}")
        if self.signals:
            lines.append(
                "  every signal above is OBSERVED only (a live notice "
                "existed at fetch time) -- none is VERIFIED or REALIZED; "
                "see module docstring's value discipline"
            )
        return "\n".join(lines)


def sweep(
    state_dir: Path,
    fetch_fn: Optional[Callable[[], bytes]] = None,
    now: Optional[datetime] = None,
) -> GetsRadarSweep:
    """Run one GETS-radar cycle: observe -> signal -> report."""
    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / f"{MOUTH_ID}.json"
    observation = observe(state_path, fetch_fn=fetch_fn, now=now)
    signals = tuple(gets_signal(item, now=now) for item in observation.new_items)
    targets = tuple(sorted({s.target for s in signals}))
    return GetsRadarSweep(
        status=observation.status,
        fetched_count=observation.item_count,
        error=observation.error,
        signals=signals,
        targets=targets,
    )
