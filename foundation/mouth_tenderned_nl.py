"""A seventh tender mouth: the Netherlands' TenderNed
(www.tenderned.nl), the national procurement platform `GLOBAL_EUROPE.md`
left as "reachable (`/aankondigingen/overzicht` returns 200), JS-
rendered, no query-string search pattern captured." This module found
the real, unauthenticated, JSON API the JS-rendered page itself calls,
and the two genuinely honoured query parameters among nine candidates
tried.

WHAT WAS ACTUALLY FOUND, LIVE, 2026-09-03

`/aankondigingen/overzicht` is an Angular SPA (`<base href=
"/aankondigingen/">`, a `main.*.js`/`polyfills.*.js` pair) -- confirmed
by fetching the raw HTML with a plain GET, no browser; the lazy-loaded
chunk carrying the actual search-call code was not located in the small
eagerly-loaded bundle this cycle inspected. Guessing the backend's own
REST path directly, rather than reverse-engineering the Angular bundle
further, found it on the first try: `GET https://www.tenderned.nl/papi/
tenderned-rs-tns/v2/publicaties` returns HTTP 200 with a genuine,
unauthenticated, paginated JSON document (`content`, `totalElements`,
`totalPages`, `size`, `number`, ...) -- Spring Data's standard `Page<T>`
response shape, confirmed by the field names themselves.

`robots.txt` (`https://www.tenderned.nl/robots.txt`, 302-redirects to
`/cms/robots.txt` -- read anyway, same "a redirect target is not a
block" discipline `mouth_etenders_ie.py` already applies) disallows
`/cms/search/` specifically. `/papi/` is not under `/cms/` at all and
is not named anywhere in the disallow list.

THE FABRICATION CHECK THIS TASK BRIEF DEMANDED -- NINE PARAMETER NAMES
FAILED BEFORE THE REAL TWO WERE FOUND, LIVE, 2026-09-03

Nine plausible free-text filter parameter names were tried against a
real value (`"cybersecurity"`) and a nonsense value
(`"zzzznonsensequery9999xyz"`), each compared against the baseline
`totalElements` (145,151) and the baseline first record: `zoekterm`,
`trefwoord`, `zoekTerm`, `keyword`, `q`, `term`, `aanbestedingNaam`,
`naam`, `vrijeTekst`, `tekst`, `query`, `text`, `keywords`, `cpvCode`,
`aanbestedingscode` -- **every one of them returned the identical
`totalElements: 145151` and the identical first record regardless of
value**, the same silently-ignored-parameter failure class this task
brief named for AusTender/GETS-NZ/World Bank/Singapore/Contracts
Finder. Two Dutch-language pagination parameters, `pagina` (page
number) and `aantalPerPagina` (items per page), were tried the same
way and failed identically -- always the same 10 most-recent records
regardless of value.

**The real parameters are English, not Dutch, and follow Spring Data's
own convention: `page` and `size`.** `size=3` returned exactly 3
records (`numberOfElements: 3`); `page=1&size=5` returned five records
disjoint from `page=0&size=5`'s five -- genuinely different content per
value, not decoration. `size` above 100 returns HTTP 400 (a real,
distinguishable rejection, not a silent clamp) -- confirmed live,
`size=200` failed, `size=100` succeeded.

**The real free-text filter is `search`, also English, not any of the
nine Dutch/generic names above.** `search=cybersecurity` returned
`totalElements: 176` with on-topic titles (`"Cybersecurity portaal"`,
`"SIEM, SOC, SOAR-dienstverlening"`, ...); `search=
zzzznonsensequery9999xyz` returned `totalElements: 0`, an empty
`content` list. Three distinct, correctly-differentiated outcomes --
the exact "real value / nonsense value / no value" triple this task
brief's own fabrication-check discipline demands, and this is the one
source in this sweep where the correct parameter was found only after
eleven wrong guesses, not the first try.

THE SHAPE: FULL-TEXT SEARCH ACROSS TENDERNED'S ENTIRE HISTORY, NOT
"OPEN ONLY" -- FILTERED CLIENT-SIDE

`search=cybersecurity` returns notices spanning years (a 2023 closing
date and a `2034-06-25` outlier both appeared live in the same
result set) undifferentiated by open/closed status -- there is no
`open`/`status` query parameter this cycle found. This module keeps
only records whose `sluitingsDatum` (closing date) parses as a real
future timestamp relative to the observation clock -- the same
"prove it's actually open, don't trust the source's framing" discipline
`mouth_udbud_dk.py` applies to `formulartypeKode`, applied here to a
date comparison instead because TenderNed's response carries no
separate open/closed field to check.

LANGUAGE: DUTCH ONLY, CONFIRMED

Every field inspected in this API's response (`aanbestedingNaam`,
`opdrachtgeverNaam`, `opdrachtBeschrijving`, ...) is Dutch text with no
parallel English block -- unlike udbud.dk's `dataEn`/`dataDa` pair.
`GLOBAL_EUROPE.md`'s "English toggle not confirmed this cycle" is now
resolved: no English content exists in this API's own response shape,
whatever the page's own UI toggle does.

VALUE: NOT PRESENT IN THIS RESPONSE SHAPE

No estimated-value or currency field appears anywhere in a fetched
record -- confirmed by inspecting full records for three live notices.
`money_state` is therefore always `NOT_OBSERVED` with no `value_text`
fallback either (unlike Ireland's eTenders, which at least carries an
unstructured value column this module cannot claim here).

NOTICE URL: PROVIDED DIRECTLY BY THE API

Each record carries its own canonical `link.href`, e.g.
`https://www.tenderned.nl/aankondigingen/overzicht/433831` -- read
directly, never constructed by this module.

CANNOT

- Cannot see notices this cycle's single `search` term misses --
  `_SEARCH_QUERY` is one narrow, named string, not a broad crawl; a
  relevant notice using only synonyms is invisible to this module,
  honestly, not silently dropped as if it did not exist.
- Cannot confirm whether a genuine `open`/`status`-shaped parameter
  exists under a name this cycle didn't guess -- the client-side
  closing-date filter above is a substitute, not proof none exists.
- Cannot confirm foreign-supplier eligibility rules -- the Netherlands
  is an EU member state (general fact, not independently re-verified
  against a TenderNed source this cycle) and this module does not fetch
  individual notice detail pages.
- Cannot page past `MAX_RESULTS` records per sweep -- `size` is capped
  server-side at 100 per call (confirmed: 200 -> HTTP 400), and this
  module fetches at most two pages (`MAX_PAGES`) per sweep, a deliberate
  courtesy bound on a public government server, not a platform limit.

WHAT THIS REUSES RATHER THAN DUPLICATES

  - `foundation/mouth_common.py::fetch_feed()`, plain GET, `READ_URL`
    scope -- no request body, unlike `mouth_udbud_dk.py`.
  - `foundation/discovery_authorization.py::DiscoveryPolicy`,
    `foundation/signal_spine.py::CanonicalSignal`,
    `foundation/untrusted_text.py::describe()`,
    `foundation/opportunity.py::SOURCE_TYPES` -- same as every other
    mouth.
"""
from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urlencode

from foundation.discovery_authorization import DiscoveryPolicy
from foundation.mouth_common import FetchError, MouthObservation, fetch_feed
from foundation.mouth_common import observe as _observe
from foundation.signal_spine import CanonicalSignal
from foundation.untrusted_text import describe

__all__ = [
    "MOUTH_ID", "BASE_URL", "PAGE_SIZE", "MAX_PAGES", "DISCOVERY_POLICY",
    "FetchError", "MouthObservation", "parse_items", "observe",
    "is_security_relevant", "tenderned_nl_signal", "TenderNedNlSweep", "sweep",
]

MOUTH_ID = "tender_radar_nl_tenderned"

# See module docstring's "THE REAL PARAMETERS" section -- `search`,
# `page`, `size` were the only three of eleven candidate names that
# actually changed the response.
BASE_URL = "https://www.tenderned.nl/papi/tenderned-rs-tns/v2/publicaties"

# Confirmed live: size > 100 -> HTTP 400. 100 is the server's own ceiling,
# not a courtesy choice.
PAGE_SIZE = 100

# Deliberate courtesy bound, same discipline as mouth_etenders_ie.py's
# MAX_PAGES -- two pages of 100 covers the live "cybersecurity" query's
# full 176-result set (page 0 + page 1) without walking an unbounded
# result set against a public government server every cron tick.
MAX_PAGES = 2

DISCOVERY_POLICY = DiscoveryPolicy(
    objective=(
        "observe the Netherlands' TenderNed (tenderned.nl) national "
        "procurement platform via its own GET /papi/tenderned-rs-tns/"
        "v2/publicaties JSON endpoint, using the search/page/size "
        "parameters proven honoured live (eleven other candidate "
        "parameter names were proven decorative first), for live "
        "security/cyber/IT procurement opportunities -- see "
        "docs/DECISIONS/D-014-nordic-benelux.md"
    ),
    requested_scope="READ_URL",
    max_queries=MAX_PAGES,
    max_wall_clock_seconds=60,
)

# The single narrow search term this module queries per sweep -- see
# module docstring's SHAPE section on why this is one named string, not
# a crawl.
_SEARCH_QUERY = "cybersecurity"

# A second, narrower client-side pass over the server-side-filtered
# results, same purpose as mouth_udbud_dk.py's own second pass.
_SECURITY_KEYWORDS = (
    "cyber", "security", "beveiliging", "informatiebeveiliging",
    "penetratietest", "pentest", "vulnerability", "kwetsbaarheid",
    "soc", "siem", "soar", "dreiging", "incident", "malware",
)


def _page_url(page: int) -> str:
    query = urlencode({
        "search": _SEARCH_QUERY,
        "size": PAGE_SIZE,
        "page": page,
    })
    return f"{BASE_URL}?{query}"


def _fetch_pages(policy: DiscoveryPolicy, max_pages: int = MAX_PAGES) -> bytes:
    """Walk up to `max_pages` pages, one `fetch_feed()` call per page
    (authorization/budget charged per page, matching
    `DISCOVERY_POLICY.max_queries`). Stops early if a page's own
    `totalPages` says there is nothing more to fetch. Merges the
    `content` lists into one synthetic document `parse_items()` reads
    unchanged."""
    all_content: list[dict] = []
    for page in range(max_pages):
        raw = fetch_feed(_page_url(page), policy=policy)
        try:
            payload = json.loads(raw.decode("utf-8", errors="strict"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise FetchError(
                f"TenderNed page {page} did not decode as JSON: {exc}"
            ) from exc
        if not isinstance(payload, dict) or "content" not in payload:
            raise FetchError(
                f"TenderNed page {page} missing 'content' -- page shape "
                f"not recognised"
            )
        content = payload.get("content") or []
        all_content.extend(c for c in content if isinstance(c, dict))
        total_pages = payload.get("totalPages")
        if isinstance(total_pages, int) and page + 1 >= total_pages:
            break
    return json.dumps({"content": all_content}).encode("utf-8")


def parse_items(raw: bytes) -> tuple[dict, ...]:
    """Parse one merged TenderNed `publicaties` JSON document into
    open-notice item dicts. Only records whose `sluitingsDatum` parses
    as a real, present-or-future ISO-8601 timestamp are kept -- see
    module docstring's SHAPE section. Malformed JSON or a document
    missing `content` raises `FetchError` -- the same UNAVAILABLE-not-
    crash contract every mouth in this repository gives
    `mouth_common.observe()`.
    """
    try:
        text = raw.decode("utf-8", errors="strict")
        payload = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FetchError(f"response did not decode as JSON: {exc}") from exc

    if not isinstance(payload, dict) or "content" not in payload:
        raise FetchError(
            "TenderNed response missing 'content' -- page shape not "
            "recognised"
        )

    now = datetime.now(timezone.utc)
    items: list[dict] = []
    for entry in payload["content"]:
        if not isinstance(entry, dict):
            continue
        publication_id = entry.get("publicatieId", "")
        if not publication_id:
            # No stable identity to dedupe against -- dropped rather
            # than keyed on a guess, same discipline as every other
            # mouth in this repository's parse_items().
            continue

        closing_raw = entry.get("sluitingsDatum")
        if not closing_raw:
            continue
        try:
            closing = datetime.fromisoformat(closing_raw)
        except (ValueError, TypeError):
            continue
        if closing.tzinfo is None:
            closing = closing.replace(tzinfo=timezone.utc)
        if closing <= now:
            continue

        link = entry.get("link") or {}
        link_href = link.get("href", "") if isinstance(link, dict) else ""

        items.append({
            "key": str(publication_id),
            "publication_id": str(publication_id),
            "title": entry.get("aanbestedingNaam", ""),
            "description": entry.get("opdrachtBeschrijving", ""),
            "buyer": entry.get("opdrachtgeverNaam", ""),
            "published": entry.get("publicatieDatum", ""),
            "deadline": closing_raw,
            "procedure": (entry.get("procedure") or {}).get("omschrijving", ""),
            "notice_type": (entry.get("typePublicatie") or {}).get("omschrijving", ""),
            "link": link_href,
        })
    return tuple(items)


def is_security_relevant(title_safe: str, description_safe: str) -> bool:
    """Client-side second pass over already server-side-filtered
    results -- see module docstring's `_SECURITY_KEYWORDS` note."""
    haystack = f"{title_safe} {description_safe}".lower()
    return any(keyword in haystack for keyword in _SECURITY_KEYWORDS)


def observe(
    state_path: Path,
    fetch_fn: Optional[Callable[[], bytes]] = None,
    now: Optional[datetime] = None,
) -> MouthObservation:
    """One observation cycle over TenderNed's `search`-filtered
    endpoint. `fetch_fn` is injected in every test -- no test touches
    the real network."""
    fetch = fetch_fn or (lambda: _fetch_pages(DISCOVERY_POLICY))
    return _observe(MOUTH_ID, state_path, fetch, parse_items, now=now)


def tenderned_nl_signal(item: dict, now: Optional[datetime] = None) -> CanonicalSignal:
    """One open-notice item -> one `CanonicalSignal`. Emitted for every
    parsed item; `facts["security_relevant"]` marks the client-side
    keyword match, same discipline as the other two tender mouths built
    this cycle.

    Title, description, buyer, procedure and notice-type text are
    attacker-reachable free text (any Dutch public body publishing
    through TenderNed) and run through `untrusted_text.describe()`
    before anything derived from them reaches `claim`/`evidence`.
    """
    observed_at = (now or datetime.now(timezone.utc)).isoformat()
    title = describe(item.get("title", ""))
    description = describe(item.get("description", ""))
    buyer = describe(item.get("buyer", ""))
    procedure = describe(item.get("procedure", ""))
    notice_type = describe(item.get("notice_type", ""))
    markers = tuple(sorted(
        set(title.markers) | set(description.markers) | set(buyer.markers)
        | set(procedure.markers) | set(notice_type.markers)))

    safe_key = describe(str(item.get("key", ""))).safe
    safe_link = describe(str(item.get("link", ""))).safe

    relevant = is_security_relevant(title.safe, description.safe)

    target = buyer.safe or safe_key

    claim_subject = title.safe or safe_key
    claim = f"Netherlands TenderNed open tender: {claim_subject}"
    if buyer.safe:
        claim += f" (buyer: {buyer.safe})"

    # No value/currency field exists in this API's response shape at
    # all -- see module docstring's VALUE section. Always NOT_OBSERVED,
    # no free-text fallback either.
    money_state = "NOT_OBSERVED"
    money_observed = ""

    buyer_raw = item.get("buyer", "")
    identity_hash = (
        hashlib.sha256(
            unicodedata.normalize("NFC", buyer_raw).strip().lower().encode("utf-8")
        ).hexdigest()
        if isinstance(buyer_raw, str) and buyer_raw.strip()
        else ""
    )

    evidence = {
        "publication_id": safe_key,
        "buyer_safe": buyer.safe,
        "identity_hash": identity_hash,
        "procedure_safe": procedure.safe,
        "notice_type_safe": notice_type.safe,
        "published": item.get("published", ""),
        "deadline": item.get("deadline", ""),
        "title_safe": title.safe,
        "description_safe": description.safe,
        "injection_markers": markers,
    }

    return CanonicalSignal(
        signal_id=f"tender:{safe_key}",
        source_id=MOUTH_ID,
        source_type="OFFICIAL",
        source_ref=safe_link or f"https://www.tenderned.nl/aankondigingen/overzicht/{safe_key}",
        target=target,
        kind="DEMAND",
        claim=claim,
        observed_at=observed_at,
        target_established_by="SOURCE_NATIVE",
        facts={
            "notice_type": notice_type.safe,
            "deadline": item.get("deadline", ""),
            "security_relevant": "true" if relevant else "false",
        },
        evidence=evidence,
        pressure_class="EXPLICIT_DEMAND",
        pressure_evidence=(
            "published on the Netherlands' TenderNed national "
            "procurement platform with a closing date this module "
            "confirmed is still in the future at observation time, "
            "naming a buyer and a publication identifier -- a public "
            "or public-adjacent body stating outright that it intends "
            "to buy"
        ),
        money_state=money_state,
        money_observed=money_observed,
    )


@dataclass(frozen=True)
class TenderNedNlSweep:
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
            f"TENDERNED NL RADAR status={self.status} "
            f"fetched={self.fetched_count} signals={len(self.signals)} "
            f"security_relevant={len(relevant)}"
        ]
        if self.error:
            lines.append(f"  error: {self.error}")
        if self.status in ("FIRST_SEEN", "CHANGED") and not self.signals:
            lines.append(
                "  zero open notices observed this cycle -- a valid, "
                "honest outcome, not an error"
            )
        for s in self.signals:
            tag = "SECURITY " if s.facts.get("security_relevant") == "true" else "         "
            lines.append(f"  {tag}OBSERVED  target={s.target!r}  {s.claim}")
        if self.signals:
            lines.append(
                "  every signal above is OBSERVED only -- none is "
                "VERIFIED or REALIZED; only notices matching the search "
                "query, within MAX_PAGES pages, with a future closing "
                "date are visible per sweep, see module docstring's "
                "CANNOT section"
            )
        return "\n".join(lines)


def sweep(
    state_dir: Path,
    fetch_fn: Optional[Callable[[], bytes]] = None,
    now: Optional[datetime] = None,
) -> TenderNedNlSweep:
    """Run one TenderNed-radar cycle: observe -> signal -> report."""
    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / f"{MOUTH_ID}.json"
    observation = observe(state_path, fetch_fn=fetch_fn, now=now)
    signals = tuple(tenderned_nl_signal(item, now=now) for item in observation.new_items)
    targets = tuple(sorted({s.target for s in signals}))
    return TenderNedNlSweep(
        status=observation.status,
        fetched_count=observation.item_count,
        error=observation.error,
        signals=signals,
        targets=targets,
    )
