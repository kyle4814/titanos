"""A sixth tender mouth: Denmark's udbud.dk, the national public
procurement board Kyle's own task brief named as the priority target
this cycle -- `GLOBAL_EUROPE.md` had confirmed a fully permissive
`robots.txt` but never fetched past it. This module fetches it.

WHAT WAS ACTUALLY FOUND, LIVE, 2026-09-03

`udbud.dk/` itself is a client-rendered SPA (`<div id="app"></div>`,
empty without JavaScript) -- confirmed by fetching the raw HTML with a
plain GET, no browser. Reading the app's own JS bundle
(`/assets/js/main-*.js`, ~2.9MB, fetched and grepped, not executed)
found the real backend the SPA itself calls: a component-scoped
`apiUrl` builder (`AuthService.getBaseUrl`) that resolves to
`https://udbud.dk` in production, plus a `SpaConfig.staticConfig.
baseUrl` map naming five component prefixes (`adfaerd`, `bruger`,
`konfiguration`, `soegning`, `udbud`). `soegning` (Danish: "search") is
the one this module uses.

THE REAL ENDPOINT: `POST https://udbud.dk/soegning/public/soegeresultat`

Found in the bundle as `getSoegeresultatController().hentSoegeresultater`,
calling `axios.post('/public/soegeresultat', soegningQueryDto, options)`
against the `soegning` base -- i.e. the full path above. Confirmed live
with a bare, unauthenticated, cookie-free `curl -X POST` carrying a
JSON body: HTTP 200, a genuine JSON response shaped
`{resultatElementDtoList, soegningQueryDto, totaltAntalResultater}`.
This is a POST-with-JSON-body endpoint, exactly the shape
`mouth_common.fetch_feed()`'s `json_body` parameter exists for --
no second socket, no session, no cookie jar.

THE REQUEST BODY, REVERSE-ENGINEERED FROM THE SAME BUNDLE (not guessed)

The frontend's Pinia store (`soegningValgStore`) shows the full DTO
shape: `fritekstQuery` (free-text query string), `pagineringDto`
(`aktuelSide` 1-indexed page, `maksElementer` page size, `sorteringFelt`,
`retning`), `udbudStatusFilter` (`AKTIV` | `ALLE` -- active/open vs.
all), `filterDto` (`publikationDatoFra/Til`, `tilbudsfristDatoFra/Til`
-- literally "bid deadline date from/to", `anslaaetVaerdiFra/Til/Valuta`
-- estimated value from/to/currency, `cpvKoder`, and more). This module
uses `fritekstQuery` + `udbudStatusFilter=AKTIV` only; the richer filter
fields are a named future increment, not built here.

THE FABRICATION CHECK THIS TASK BRIEF DEMANDED -- RUN AGAINST A REAL
VALUE, A NONSENSE VALUE, AND NO VALUE, LIVE, 2026-09-03

  - `fritekstQuery="cyber"` -> `totaltAntalResultater: 5`, five distinct,
    on-topic results (a live Danmarks Nationalbank cybersecurity
    tender among them).
  - `fritekstQuery="zzzznonsensequery9999xyz"` ->
    `resultatElementDtoList: []`, zero results.
  - No `fritekstQuery` at all, `udbudStatusFilter="AKTIV"` ->
    `totaltAntalResultater: 2424` (the live count of open notices at
    fetch time).

Three distinct outcomes for three distinct inputs -- this is a
genuinely honoured filter, not five other sources' silently-ignored
parameter. `udbudStatusFilter` was not independently isolated this
cycle (both `AKTIV` fetches above used it, no `ALLE` comparison was
run) -- a named, real gap, not concealed.

THE SHAPE: A MIX OF OPEN COMPETITIONS AND PAST AWARDS IN ONE STREAM,
DISTINGUISHED BY `formulartypeKode`

`udbudStatusFilter=AKTIV` does not mean "open opportunities only" --
live results for `fritekstQuery="sikkerhed"` (security) included
`formulartypeKode: "result"` (award notice, `tidsfrister: []`, no
deadline) alongside `formulartypeKode: "competition"` (open call,
non-empty `tidsfrister`) in the same response, undifferentiated by the
status filter. This module keeps only `formulartypeKode == "competition"`
items with a non-empty `tidsfrister` list as genuinely open -- the same
class of shape-check `tender_radar.py`'s own module docstring already
warns every mouth in this repository to run before trusting a source's
"currently open" framing.

LANGUAGE: GENUINELY BILINGUAL PER NOTICE

Every notice carries both `dataDa` (Danish) and `dataEn` (English)
blocks with parallel fields -- confirmed live: the Danmarks Nationalbank
notice's `dataEn.titel` reads "Tender for a framework agreement on the
delivery of Cybersecurity advisory and assessment services" alongside
`dataDa.titel`'s Danish original. This module reads `dataEn` only.

VALUE AND DEADLINE: STRUCTURED, NOT FREE TEXT

Unlike Ireland's eTenders (`mouth_etenders_ie.py`, whose "Estimated
value" column is unstructured free text), udbud.dk's `anslaaetVaerdi`
(estimated value) and `anslaaetVaerdiValuta` (currency, e.g. `"DKK"`,
`"EUR"`) are separate structured fields, and `tidsfrister` is a real
ISO-8601 timestamp list, not a free-text column. Preserved verbatim
through `describe()`, still never promoted past `NOT_OBSERVED` for
`money_state` -- this module has not independently verified udbud.dk's
own accounting of "estimated value" against the notice's underlying
legal documents, the same caution every other mouth in this repository
applies to a source-reported figure it has not itself audited.

NOTICE URL

`https://udbud.dk/bekendtgoerelse/{noticeId}` -- confirmed live to
return HTTP 200 (distinct from a guessed `/udbud/{noticeId}` path,
which returned HTTP 404, proving the SPA's router recognises this
specific path rather than blanket-200ing every URL). The page itself is
client-rendered and this module does not fetch it; the notice's own
data already comes from the search response.

ROBOTS.TXT

`https://udbud.dk/robots.txt`: `Allow: /` with a short, specific
disallow list (`/ordregiver/`, `/opretIndkoeb/`, `/agent/`, `/konfig/`,
`/indstillinger/`, `/demo/`, `/showMe/`, `/notfound/`, `/unauthorized/`)
-- all logged-in areas. `/soegning/` is not in that list.

CANNOT

- Cannot page past what `maksElementer` returns in one call this cycle
  chose (kept at 25, matching the richest live query run) -- pagination
  via `pagineringDto.aktuelSide` was found in the bundle but not
  exercised against a query with more than 25 results this cycle;
  walking multiple pages per sweep is a named future increment, not
  built here (see `mouth_etenders_ie.py`'s own multi-page walk for the
  pattern to copy if this becomes the next increment).
- Cannot confirm `udbudStatusFilter=AKTIV` vs `ALLE` differ in practice
  -- only `AKTIV` was queried live this cycle.
- Cannot confirm per-notice foreign-supplier eligibility rules --
  Denmark is an EU member state (general fact, not independently
  re-verified against a udbud.dk source this cycle) and this module
  does not fetch individual notice detail pages.
- Cannot confirm the richer `filterDto` fields (deadline range, value
  range, CPV code) are honoured the way `fritekstQuery` was proven to
  be -- not tested this cycle, not assumed.

WHAT THIS REUSES RATHER THAN DUPLICATES

  - `foundation/mouth_common.py::fetch_feed()`'s `json_body` parameter
    -- the exact POST-with-JSON-body shape this endpoint requires, no
    second socket.
  - `foundation/discovery_authorization.py::DiscoveryPolicy`, scope
    `READ_API` (this module sends a request body, unlike
    `mouth_etenders_ie.py`'s `READ_URL`).
  - `foundation/signal_spine.py::CanonicalSignal`,
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

from foundation.discovery_authorization import DiscoveryPolicy
from foundation.mouth_common import FetchError, MouthObservation, fetch_feed
from foundation.mouth_common import observe as _observe
from foundation.signal_spine import CanonicalSignal
from foundation.untrusted_text import describe

__all__ = [
    "MOUTH_ID", "SEARCH_URL", "MAX_ELEMENTS", "DISCOVERY_POLICY",
    "FetchError", "MouthObservation", "parse_items", "observe",
    "is_security_relevant", "udbud_dk_signal", "UdbudDkSweep", "sweep",
]

MOUTH_ID = "tender_radar_dk_udbud"

# See module docstring's "THE REAL ENDPOINT" section -- traced from the
# SPA's own JS bundle, confirmed live with a bare unauthenticated POST.
SEARCH_URL = "https://udbud.dk/soegning/public/soegeresultat"

# Kept modest -- the richest live query run this cycle ("sikkerhed")
# returned well under this many rows; raising it is a future increment
# once pagination is actually exercised (see module docstring's CANNOT).
MAX_ELEMENTS = 25

# READ_API, not READ_URL: this module sends a JSON request body (see
# mouth_common.fetch_feed()'s json_body parameter), unlike
# mouth_etenders_ie.py's plain GET.
DISCOVERY_POLICY = DiscoveryPolicy(
    objective=(
        "observe Denmark's udbud.dk national procurement board via its "
        "own POST /soegning/public/soegeresultat JSON search endpoint, "
        "traced from the site's own SPA bundle, for live security/"
        "cyber/IT procurement opportunities -- the below-threshold "
        "national board GLOBAL_EUROPE.md identified as the top "
        "priority lead and left unfetched past robots.txt, see "
        "docs/DECISIONS/D-014-nordic-benelux.md"
    ),
    requested_scope="READ_API",
    max_queries=4,
    max_wall_clock_seconds=60,
)

# The keyword this module searches with per sweep. A single, narrow,
# named query -- not a broad crawl -- same discipline as every other
# mouth's own client-side relevance filter, except here the filter is
# server-side and proven honoured (see module docstring's FABRICATION
# CHECK section), so it is applied at the query itself rather than
# post-hoc over an unfiltered page.
_SEARCH_QUERY = "cybersecurity"

# A second, narrower client-side pass over whatever the server-side
# query returns -- catches the case where "cybersecurity" as a single
# term misses an English notice using only one of its component words,
# without re-opening the broad-noise problem a bare "security" query
# proved to have live (insurance, physical fencing, prison security
# installations all matched "sikkerhed"/"security" upstream in this
# cycle's recon). Operates on the already-describe()-safe text.
_SECURITY_KEYWORDS = (
    "cyber", "security", "penetration test", "pen test", "pentest",
    "vulnerability", "soc ", "siem", "threat", "incident response",
    "iso 27001", "infosec", "malware", "encryption",
)


def _request_body(query: str) -> dict:
    return {
        "fritekstQuery": query,
        "pagineringDto": {
            "aktuelSide": 1,
            "maksElementer": MAX_ELEMENTS,
            "sorteringFelt": "PUBLIKATION_DATO",
            "retning": "Desc",
        },
        "udbudStatusFilter": "AKTIV",
        "filterDto": {},
    }


def _fetch(policy: DiscoveryPolicy, query: str = _SEARCH_QUERY) -> bytes:
    return fetch_feed(SEARCH_URL, policy=policy, json_body=_request_body(query))


def parse_items(raw: bytes) -> tuple[dict, ...]:
    """Parse one `soegeresultat` JSON response into open-notice item
    dicts. Only `formulartypeKode == "competition"` entries with a
    non-empty `tidsfrister` list are kept -- see module docstring's
    "THE SHAPE" section for why `udbudStatusFilter=AKTIV` alone is not
    sufficient to mean "open opportunity only". Malformed JSON or a
    response missing the expected top-level shape raises `FetchError`,
    the same UNAVAILABLE-not-crash contract every mouth in this
    repository gives `mouth_common.observe()`."""
    try:
        text = raw.decode("utf-8", errors="strict")
        payload = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FetchError(f"response did not decode as JSON: {exc}") from exc

    if not isinstance(payload, dict) or "resultatElementDtoList" not in payload:
        raise FetchError(
            "udbud.dk response missing 'resultatElementDtoList' -- page "
            "shape not recognised"
        )

    items: list[dict] = []
    for entry in payload["resultatElementDtoList"]:
        if not isinstance(entry, dict):
            continue
        notice_id = entry.get("noticeId", "")
        if not notice_id:
            # No stable identity to dedupe against -- dropped rather
            # than keyed on a guess, same discipline as every other
            # mouth in this repository's parse_items().
            continue
        data_en = entry.get("dataEn")
        if not isinstance(data_en, dict):
            continue
        if data_en.get("formulartypeKode") != "competition":
            continue
        deadlines = data_en.get("tidsfrister") or []
        if not deadlines:
            continue

        items.append({
            "key": notice_id,
            "notice_id": notice_id,
            "notice_publication_number": entry.get("noticePublicationNumber", ""),
            "title": data_en.get("titel", ""),
            "description": data_en.get("beskrivelse", ""),
            "buyer": data_en.get("ordregiver", ""),
            "cpv_title": data_en.get("cpvTitel", ""),
            "published": data_en.get("publiceringsdato", ""),
            "deadline": deadlines[0] if deadlines else "",
            "value": data_en.get("anslaaetVaerdi", ""),
            "value_currency": data_en.get("anslaaetVaerdiValuta", ""),
            "notice_type": data_en.get("bkSubType", ""),
        })
    return tuple(items)


def is_security_relevant(title_safe: str, description_safe: str) -> bool:
    """Client-side second pass over already server-side-filtered
    results -- see module docstring's `_SEARCH_KEYWORDS` note."""
    haystack = f"{title_safe} {description_safe}".lower()
    return any(keyword in haystack for keyword in _SECURITY_KEYWORDS)


def observe(
    state_path: Path,
    fetch_fn: Optional[Callable[[], bytes]] = None,
    now: Optional[datetime] = None,
) -> MouthObservation:
    """One observation cycle over udbud.dk's search endpoint, queried
    with `_SEARCH_QUERY`. `fetch_fn` is injected in every test -- no
    test touches the real network."""
    fetch = fetch_fn or (lambda: _fetch(DISCOVERY_POLICY))
    return _observe(MOUTH_ID, state_path, fetch, parse_items, now=now)


def udbud_dk_signal(item: dict, now: Optional[datetime] = None) -> CanonicalSignal:
    """One open-notice item -> one `CanonicalSignal`. Emitted for every
    parsed item; `facts["security_relevant"]` marks the client-side
    keyword match, same discipline as `mouth_etenders_ie.py`.

    Title, description, buyer and notice-type text are attacker-
    reachable free text (any Danish public body publishing through
    udbud.dk) and run through `untrusted_text.describe()` before
    anything derived from them reaches `claim`/`evidence`.
    """
    observed_at = (now or datetime.now(timezone.utc)).isoformat()
    title = describe(item.get("title", ""))
    description = describe(item.get("description", ""))
    buyer = describe(item.get("buyer", ""))
    cpv_title = describe(item.get("cpv_title", ""))
    notice_type = describe(item.get("notice_type", ""))
    markers = tuple(sorted(
        set(title.markers) | set(description.markers) | set(buyer.markers)
        | set(cpv_title.markers) | set(notice_type.markers)))

    safe_key = describe(str(item.get("key", ""))).safe

    relevant = is_security_relevant(title.safe, description.safe)

    target = buyer.safe or safe_key

    claim_subject = title.safe or safe_key
    claim = f"Denmark udbud.dk open tender: {claim_subject}"
    if buyer.safe:
        claim += f" (buyer: {buyer.safe})"

    # Structured fields exist (see module docstring's VALUE section)
    # but this module has not independently audited udbud.dk's own
    # "estimated value" figure against underlying tender documents --
    # same caution every other mouth applies to a source-reported
    # number it has not itself verified. Recorded as evidence, never
    # promoted past NOT_OBSERVED.
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

    value_safe = describe(str(item.get("value", ""))).safe
    currency_safe = describe(str(item.get("value_currency", ""))).safe

    evidence = {
        "notice_id": safe_key,
        "notice_publication_number": describe(
            str(item.get("notice_publication_number", ""))).safe,
        "buyer_safe": buyer.safe,
        "identity_hash": identity_hash,
        "cpv_title_safe": cpv_title.safe,
        "notice_type_safe": notice_type.safe,
        "published": item.get("published", ""),
        "deadline": item.get("deadline", ""),
        "estimated_value_safe": value_safe,
        "estimated_value_currency_safe": currency_safe,
        "title_safe": title.safe,
        "description_safe": description.safe,
        "injection_markers": markers,
    }

    return CanonicalSignal(
        signal_id=f"tender:{safe_key}",
        source_id=MOUTH_ID,
        source_type="OFFICIAL",
        source_ref=f"https://udbud.dk/bekendtgoerelse/{safe_key}",
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
            "published on Denmark's udbud.dk national procurement board "
            "as an open competition notice with a non-empty submission "
            "deadline, naming a buyer and a notice identifier -- a "
            "public or public-adjacent body stating outright that it "
            "intends to buy"
        ),
        money_state=money_state,
        money_observed=money_observed,
    )


@dataclass(frozen=True)
class UdbudDkSweep:
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
            f"UDBUD DK RADAR status={self.status} "
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
                "VERIFIED or REALIZED; only up to MAX_ELEMENTS notices "
                "matching the search query are visible per sweep, see "
                "module docstring's CANNOT section"
            )
        return "\n".join(lines)


def sweep(
    state_dir: Path,
    fetch_fn: Optional[Callable[[], bytes]] = None,
    now: Optional[datetime] = None,
) -> UdbudDkSweep:
    """Run one udbud.dk-radar cycle: observe -> signal -> report."""
    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / f"{MOUTH_ID}.json"
    observation = observe(state_path, fetch_fn=fetch_fn, now=now)
    signals = tuple(udbud_dk_signal(item, now=now) for item in observation.new_items)
    targets = tuple(sorted({s.target for s in signals}))
    return UdbudDkSweep(
        status=observation.status,
        fetched_count=observation.item_count,
        error=observation.error,
        signals=signals,
        targets=targets,
    )
