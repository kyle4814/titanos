"""A bug-bounty-program mouth: watches YesWeHack's public program directory
for newly-added public programs.

WHY THIS TASK ASKED FOR A MONITOR, NOT A ONE-OFF REPORT

`BUG_BOUNTY_PLAN.md` and `SOLO_REVENUE_ROUTES.md` already established the
value of this lane by hand: Adobe's 1 September 2026 migration to Intigriti
reset its whole duplicate landscape, and that kind of event is exactly what
a static, once-read document cannot see happen. A NEW public program is the
single highest-value signal in this lane for a newcomer with no reputation
-- it is the only moment the duplicate landscape is briefly reset for
everyone at once. This module exists to notice that moment, not to
re-derive the researched conclusions those two files already contain.

WHAT WAS ACTUALLY CHECKED THIS CYCLE, LIVE, 2026-09-02, BEFORE LANDING HERE

Three candidate platforms named in the task brief:

  1. Intigriti (`www.intigriti.com/programs`) -- `robots.txt` (HTTP 200)
     is fully permissive (`User-agent: * / Allow: /`). The programs page
     itself is real, live data: a `window[Symbol.for(
     "InstantSearchInitialResults")] = {...}` blob embedded in the SSR
     HTML, containing genuine Algolia hits with `programId`, `handle`,
     `name`, `minBounty`/`maxBounty`, confirmed live (Adobe Public:
     minBounty $75, maxBounty $15,000 -- matches `SOLO_REVENUE_ROUTES.md`
     exactly). But this blob carries only page 1 of 8 (24 of 181 total
     programs, `hitsPerPage=24`), and query-string pagination
     (`?page=2`, `?hitsPerPage=200`) was tried and PROVEN NOT TO CHANGE
     the SSR result -- the page's client-side JS re-paginates via a
     browser XHR this fetcher cannot drive, not via the URL. It is also
     an UNDOCUMENTED internal Algolia SSR hydration payload, not a
     published API contract -- Intigriti could rename or restructure it
     with no notice and no deprecation window. NOT USED as the primary
     source: real and reachable, but structurally can only ever see
     ~13% of the population in one fetch, and that slice's membership
     rule (Algolia's own relevance ranking) is undocumented, not "the 24
     newest". Recorded here as a genuine finding, not silently dropped.
  2. HackerOne (`hackerone.com/directory/programs`) -- `robots.txt` (HTTP
     200) is the single line `Sitemap: https://hackerone.com/sitemap.xml`
     with zero `User-agent`/`Disallow` directives at all: nothing is
     restricted for any crawler. But the directory page itself is a bare
     client-rendered shell (1,941 bytes, no embedded data, confirmed by
     direct fetch) -- everything is drawn in by JavaScript this fetcher
     does not execute. `hackerone.com/programs.json` (a historically
     known unauthenticated endpoint) now 404s. NOT USED: permitted, but
     genuinely nothing machine-readable is reachable without executing
     the page's JS.
  3. YesWeHack (`yeswehack.com`) -- main site `robots.txt` disallows only
     `/vulnerability-center/`, `/dashboard-manager/`, `/business-units/`,
     `/reports/`, `/user/`, `/attack-surface/`; none of that applies
     here. The site's own frontend calls `api.yeswehack.com`, a separate
     host, confirmed live to carry NO `robots.txt` at all
     (`https://api.yeswehack.com/robots.txt` -> HTTP 404, confirmed with
     this module's own honest, non-spoofed User-Agent, not a browser
     impersonation). Per this repository's own established convention
     (`mouth_gets_nz.py`'s `gets.govt.nz` finding, and the general
     web convention that an absent robots.txt states no restriction),
     absence of the file is read as "nothing declared, nothing
     forbidden" -- the same reading already applied elsewhere in this
     codebase. `https://api.yeswehack.com/programs?page=1` returns a
     genuine, complete, documented-shape JSON payload: 61 total results
     across exactly 2 pages of up to 42 each, with a stable per-program
     `slug`, structured `bounty_reward_min`/`bounty_reward_max` integers,
     a `public` boolean, a `vdp` boolean, and a `business_unit.currency`
     field -- fetched and inspected directly with this module's own
     honest User-Agent, confirmed reachable with zero spoofing. USED.

WHY YESWEHACK OVER INTIGRITI DESPITE INTIGRITI HAVING THE MORE FAMOUS
CURRENT STORY (ADOBE)

`BUG_BOUNTY_PLAN.md`/`SOLO_REVENUE_ROUTES.md` already cover Intigriti's
Adobe migration by hand; this module's job is to find the NEXT one, on
whichever platform it happens on. Black Ice: prefer the simpler, complete,
genuinely public API contract over scraping an undocumented, 13%-visible,
JS-paginated internal payload from a competitor platform, when the
complete source exists and is reachable. If Intigriti later exposes an
actual public API or RSS feed, revisit -- this module's docstring records
exactly what was tried so nobody re-derives the same dead end.

WHAT THIS REUSES RATHER THAN DUPLICATES

  - `foundation/mouth_common.py::fetch_feed()` -- the one socket. No
    second one opened here.
  - `foundation/discovery_authorization.py::DiscoveryPolicy` -- a fourth,
    independently-declared policy object (after tender_radar's UK
    Contracts Finder policy, `mouth_ted`'s TED policy, and
    `mouth_gets_nz`'s GETS policy).
  - `foundation/signal_spine.py::CanonicalSignal` -- the only signal
    shape.
  - `foundation/untrusted_text.py::describe()` -- every attacker-reachable
    string (program name, company name, description) goes through this
    before reaching `claim`/`evidence`, same discipline as every other
    mouth in this repository.
  - `foundation/opportunity.py::SOURCE_TYPES` -- `"PLATFORM"`: YesWeHack
    is not the paying company itself (that would be `PRIMARY`/`OFFICIAL`)
    -- it is the crowd-testing platform relaying company-declared terms,
    the same relationship a marketplace has to its listed sellers.

VALUE DISCIPLINE

`bounty_reward_min`/`bounty_reward_max` are genuinely structured integer
fields on this API -- unlike `mouth_gets_nz.py`'s GETS feed, this source
earns `money_state="ADVERTISED"` for a program that pays
(`item["bounty"] is True` and `bounty_reward_max > 0`), because the number
is a real field the platform itself declares, never inferred from free
text. A VDP-only program (`item["vdp"] is True`, no bounty) gets
`money_state="NOT_OBSERVED"` honestly -- it is real demand for security
work, but it does not pay, and collapsing that distinction would be
exactly the fabrication `SOLO_REVENUE_ROUTES.md`'s own "do not let a long
program list read as a long list of paying programs" finding warns
against.

CANNOT

- Cannot see Intigriti's or HackerOne's new-program events (see above) --
  this module watches YesWeHack only. A second, source-specific module
  is the correct way to add either platform later if a real feed is ever
  found for them; bending this module's YesWeHack-shaped parser to a
  different platform's JSON would duplicate `mouth_ted.py`'s own
  "different shape -> copy and adapt, don't bend" precedent in reverse.
- Cannot detect a program that changes its bounty range without changing
  its item set membership as this module observes it -- `compute_state_hash`
  keys on `slug` only (see `mouth_common.compute_state_hash`), matching
  every other mouth in this repository; a reward-range change alone is
  invisible to CHANGED detection here, same limitation `mouth_gets_nz.py`
  and `mouth_ted.py` both carry for their own non-identity fields.
- Cannot fetch more than `MAX_PAGES` pages in one cycle -- bounded
  deliberately (see `_default_fetch`'s docstring) so a platform that grew
  its program count sharply cannot turn one cron tick into an unbounded
  fetch loop.
- Cannot tell whether a "new" slug this cycle is a genuinely brand-new
  program or one that re-entered the public list after being temporarily
  private/paused -- the API exposes no history, only current state.
"""

from __future__ import annotations

import json
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
    "MOUTH_ID", "API_BASE", "MAX_PAGES", "DISCOVERY_POLICY", "FetchError",
    "MouthObservation", "parse_items", "observe", "bounty_signal",
    "BountyRadarSweep", "sweep",
]

MOUTH_ID = "mouth_bounty_yeswehack"

# The one YesWeHack endpoint this module ever calls. Confirmed live
# 2026-09-02: `api.yeswehack.com` carries no robots.txt at all (HTTP 404),
# and this exact URL returns real, complete, unauthenticated JSON with
# this module's own honest User-Agent -- see module docstring finding 3.
API_BASE = "https://api.yeswehack.com/programs"

# Confirmed live 2026-09-02: 61 total results, 2 pages at the API's own
# default page size. Capped higher than the observed page count so
# modest real growth is still covered without a code change, but bounded
# so a runaway program count cannot turn one observation cycle into an
# unbounded fetch loop -- same bounded-work discipline as every other
# mouth's own fixed-shape fetch.
MAX_PAGES = 5

DISCOVERY_POLICY = DiscoveryPolicy(
    objective=(
        "observe YesWeHack's public bug bounty program directory "
        "(api.yeswehack.com/programs) for newly-added public programs -- "
        "a new program is the highest-value signal in this lane because "
        "it briefly resets the duplicate/reputation landscape for every "
        "researcher at once, see docs/DECISIONS/D-011-income-monitors.md"
    ),
    requested_scope="READ_URL",
    # One query to learn nb_pages, plus up to MAX_PAGES-1 more to fetch
    # the rest -- matches `mouth_ted.py`'s own precedent of setting
    # max_queries to exactly the real page ceiling this module needs,
    # rather than leaving the default and having a later page silently
    # refuse mid-cycle.
    max_queries=MAX_PAGES,
)


def _clean_str(value: object) -> str:
    """Same discipline as every other mouth's `_clean_str`: a field this
    repository does not control the type of is read as absent, never
    crashes the parse."""
    return value if isinstance(value, str) else ""


def parse_items(raw: bytes) -> tuple[dict, ...]:
    """Parse one or more merged YesWeHack `/programs` API pages into
    program item dicts.

    `raw` is a single JSON document of shape `{"items": [...]}` --
    `_default_fetch()` is the thing that merges multiple real page
    fetches into this one shape before `observe()` ever calls this
    function, so this parser itself stays a pure single-document parse,
    same as every other mouth in this repository.

    Only `public` programs are kept -- a private/invite-only program is
    not an opportunity this operator profile can act on, matching
    `LIVE_PAID_WORK.md`'s own operator-profile framing (solo, no prior
    reputation, no invitations). A disabled or archived program is
    dropped for the same reason: it is not currently a live opportunity,
    whatever it once was. One malformed item is skipped, never aborts
    the whole parse.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise FetchError(f"response did not parse as JSON: {exc}") from exc

    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise FetchError("response has no top-level 'items' list")

    items: list[dict] = []
    for entry in data["items"]:
        if not isinstance(entry, dict):
            continue
        slug = _clean_str(entry.get("slug")).strip()
        if not slug:
            # No stable identity to dedupe against -- dropped rather
            # than keyed on a guess, same discipline as every other
            # mouth's guid-less/ocid-less item handling.
            continue
        if entry.get("public") is not True:
            continue
        if entry.get("disabled") is True or entry.get("archived") is True:
            continue

        business_unit = entry.get("business_unit")
        business_unit = business_unit if isinstance(business_unit, dict) else {}
        company_name = _clean_str(business_unit.get("name"))
        currency = _clean_str(business_unit.get("currency"))

        reward_min = entry.get("bounty_reward_min")
        reward_max = entry.get("bounty_reward_max")
        reward_min = reward_min if isinstance(reward_min, (int, float)) else None
        reward_max = reward_max if isinstance(reward_max, (int, float)) else None

        items.append({
            "key": slug,
            "slug": slug,
            "title": _clean_str(entry.get("title")),
            "company_name": company_name,
            "country": _clean_str(entry.get("country")),
            "activity_area": _clean_str(entry.get("activity_area")),
            "program_type": _clean_str(entry.get("type")),
            "bounty": entry.get("bounty") is True,
            "vdp": entry.get("vdp") is True,
            "reports_count": entry.get("reports_count")
            if isinstance(entry.get("reports_count"), int) else 0,
            "bounty_reward_min": reward_min,
            "bounty_reward_max": reward_max,
            "currency": currency,
            "scopes_count": entry.get("scopes_count")
            if isinstance(entry.get("scopes_count"), int) else 0,
            "last_update_at": entry.get("last_update_at")
            if isinstance(entry.get("last_update_at"), (int, float)) else None,
        })
    return tuple(items)


def _default_fetch() -> bytes:
    """Fetch page 1, learn the real page count from the API's own
    pagination metadata, then fetch up to `MAX_PAGES` total and merge --
    the composition `mouth_common.observe()`'s single fetch_fn contract
    expects. Every real fetch goes through `mouth_common.fetch_feed()`;
    this function opens no socket itself."""
    raw_page1 = fetch_feed(f"{API_BASE}?page=1", policy=DISCOVERY_POLICY)
    try:
        page1 = json.loads(raw_page1)
    except json.JSONDecodeError as exc:
        raise FetchError(f"page 1 did not parse as JSON: {exc}") from exc
    if not isinstance(page1, dict) or not isinstance(page1.get("items"), list):
        raise FetchError("page 1 response has no top-level 'items' list")

    merged: list = list(page1["items"])
    pagination = page1.get("pagination")
    nb_pages = pagination.get("nb_pages") if isinstance(pagination, dict) else 1
    nb_pages = nb_pages if isinstance(nb_pages, int) and nb_pages > 0 else 1
    pages_to_fetch = min(nb_pages, MAX_PAGES)

    for page in range(2, pages_to_fetch + 1):
        raw_page = fetch_feed(f"{API_BASE}?page={page}", policy=DISCOVERY_POLICY)
        try:
            page_data = json.loads(raw_page)
        except json.JSONDecodeError as exc:
            raise FetchError(f"page {page} did not parse as JSON: {exc}") from exc
        if isinstance(page_data, dict) and isinstance(page_data.get("items"), list):
            merged.extend(page_data["items"])

    return json.dumps({"items": merged}).encode("utf-8")


def observe(
    state_path: Path,
    fetch_fn: Optional[Callable[[], bytes]] = None,
    now: Optional[datetime] = None,
) -> MouthObservation:
    """One observation cycle over the YesWeHack public program directory.
    `fetch_fn` injected in every test in
    `foundation/tests/test_mouth_bounty.py` -- no test in this repository
    touches the real network, this module included. When `fetch_fn` is
    None the default path goes through `_default_fetch()`, which refuses
    without `DISCOVERY_POLICY` -- there is no second, ungated path here."""
    fetch = fetch_fn or _default_fetch
    return _observe(MOUTH_ID, state_path, fetch, parse_items, now=now)


def bounty_signal(item: dict, now: Optional[datetime] = None) -> CanonicalSignal:
    """One public bug-bounty program item -> one `CanonicalSignal`.

    Title, company name, activity area are attacker-reachable free text
    (any company onboarded to YesWeHack can populate them) and are run
    through `untrusted_text.describe()` before anything derived from them
    reaches `claim`/`evidence` -- same discipline as every other mouth.
    """
    observed_at = (now or datetime.now(timezone.utc)).isoformat()
    title = describe(item.get("title", ""))
    company = describe(item.get("company_name", ""))
    activity = describe(item.get("activity_area", ""))
    markers = tuple(sorted(
        set(title.markers) | set(company.markers) | set(activity.markers)))

    safe_slug = describe(str(item.get("slug", ""))).safe
    target = company.safe or title.safe or safe_slug

    claim_subject = title.safe or safe_slug
    claim = f"public bug bounty program on YesWeHack: {claim_subject}"
    if company.safe:
        claim += f" (company: {company.safe})"

    is_paying = bool(item.get("bounty")) and isinstance(
        item.get("bounty_reward_max"), (int, float)) and item["bounty_reward_max"] > 0

    if is_paying:
        money_state = "ADVERTISED"
        currency = item.get("currency") or ""
        reward_min = item.get("bounty_reward_min")
        reward_max = item.get("bounty_reward_max")
        money_observed = f"{reward_min}-{reward_max} {currency}".strip()
        pressure_evidence = (
            "published as a public program on YesWeHack with a declared "
            "paying bounty range -- a company inviting security "
            "researchers to submit vulnerability reports for payment"
        )
    else:
        # VDP-only (or a malformed/zero range) -- real demand, no money.
        # Never inferred as paying from the mere presence of a program.
        money_state = "NOT_OBSERVED"
        money_observed = ""
        pressure_evidence = (
            "published as a public program on YesWeHack" +
            (" (VDP -- responsible disclosure, no bounty)"
             if item.get("vdp") else " (no declared paying bounty range)")
        )

    evidence = {
        "slug": safe_slug,
        "company_name_safe": company.safe,
        "activity_area_safe": activity.safe,
        "title_safe": title.safe,
        "program_type": item.get("program_type", ""),
        "vdp": item.get("vdp", False),
        "reports_count": item.get("reports_count", 0),
        "scopes_count": item.get("scopes_count", 0),
        "injection_markers": markers,
    }

    return CanonicalSignal(
        signal_id=f"bounty:yeswehack:{safe_slug}",
        source_id=MOUTH_ID,
        source_type="PLATFORM",
        source_ref=f"https://yeswehack.com/programs/{safe_slug}",
        target=target,
        kind="DEMAND",
        claim=claim,
        observed_at=observed_at,
        target_established_by="SOURCE_NATIVE",
        facts={
            "program_type": item.get("program_type", ""),
            "activity_area": activity.safe,
        },
        evidence=evidence,
        pressure_class="EXPLICIT_DEMAND",
        pressure_evidence=pressure_evidence,
        money_state=money_state,
        money_observed=money_observed,
    )


@dataclass(frozen=True)
class BountyRadarSweep:
    """One observation cycle, report only -- same discipline as
    `mouth_gets_nz.GetsRadarSweep`: no ledger write, no promotion, no
    contact, no application. Reading this report and deciding what to do
    about a lead stays a human's job."""

    status: str
    fetched_count: int
    error: Optional[str]
    signals: tuple[CanonicalSignal, ...]
    targets: tuple[str, ...]

    def show_the_math(self) -> str:
        lines = [
            f"YESWEHACK BOUNTY RADAR status={self.status} "
            f"fetched={self.fetched_count} signals={len(self.signals)}"
        ]
        if self.error:
            lines.append(f"  error: {self.error}")
        if self.status in ("FIRST_SEEN", "CHANGED") and not self.signals:
            lines.append(
                "  zero new public programs observed this cycle -- a "
                "valid, honest outcome, not an error"
            )
        for s in self.signals:
            paying = " PAYING" if s.money_state == "ADVERTISED" else " VDP/UNPAID"
            lines.append(f"  OBSERVED{paying}  target={s.target!r}  {s.claim}")
        if self.signals:
            lines.append(
                "  every signal above is OBSERVED only (a live public "
                "program existed at fetch time) -- none is VERIFIED or "
                "REALIZED; a listed bounty range is the platform's own "
                "declared terms, not a paid amount"
            )
        return "\n".join(lines)


def sweep(
    state_dir: Path,
    fetch_fn: Optional[Callable[[], bytes]] = None,
    now: Optional[datetime] = None,
) -> BountyRadarSweep:
    """Run one YesWeHack bounty-radar cycle: observe -> signal -> report."""
    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / f"{MOUTH_ID}.json"
    observation = observe(state_path, fetch_fn=fetch_fn, now=now)
    signals = tuple(bounty_signal(item, now=now) for item in observation.new_items)
    targets = tuple(sorted({s.target for s in signals}))
    return BountyRadarSweep(
        status=observation.status,
        fetched_count=observation.item_count,
        error=observation.error,
        signals=signals,
        targets=targets,
    )
