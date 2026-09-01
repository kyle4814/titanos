"""A tender mouth: reads genuinely open, currently-live public-sector
procurement notices and turns them into canonical signals.

WHY THIS EXISTS

Every mouth in this repository so far watches software (releases,
issues, commits). None of them can ever find a customer -- a GitHub
release is not a buyer. This repository has never had an external
ping: no customer, no revenue, no tender response. This module is the
instrument aimed at that gap: it reads a source where someone with
money has publicly stated they want to buy something.

WHAT WAS ACTUALLY TRIED, AND WHAT WAS FOUND (2026-09-01)

The obvious first target was Australian government procurement, since
the operator is Australian. It does not work, for a reason worth
recording precisely rather than papering over:

  - www.tenders.gov.au (AusTender) and www.grants.gov.au: `robots.txt`
    itself disallows `/Search/*` and `/Reports/*` -- exactly the paths
    that carry the Atom search-result feed. Separately, and more
    fundamentally, EVERY path on both hosts -- including the homepage
    and robots.txt -- returns HTTP 403 from a CloudFront WAF to any
    request that does not carry a full desktop-browser User-Agent
    string. This repository's one fetcher (`mouth_common.fetch_feed`)
    identifies itself honestly as
    `titanos-cosmic-library-mouth/1 (+https://github.com/kyle4814/titanos)`,
    and a bare `curl/8.x` or `Mozilla/5.0` (no version tail) is blocked
    identically -- confirmed live, 2026-09-01. Getting through requires
    presenting a fabricated full Chrome UA string, which is evading an
    access control the site operator put there on purpose. This
    repository's fetch discipline is to identify itself truthfully;
    spoofing a browser to defeat a WAF is not "lawfully accessible
    without authentication", it is exactly the case the task brief
    named as a finding to record and move past, not defeat.
  - data.gov.au: `robots.txt` is `User-agent: * / Disallow: /` -- a
    blanket disallow of the entire site, API paths included. Honoured
    as written; nothing on this host is fetched here.
  - api.tenders.gov.au: returns API-Gateway `MISSING_AUTHENTICATION_TOKEN`
    on every path tried -- this is a keyed API, not an open one.
  - State portals tried next (tenders.nsw.gov.au, tenders.vic.gov.au,
    tenders.qld.gov.au, tenders.wa.gov.au, tenders.sa.gov.au): every
    one of them sits behind Cloudflare or an Azure Application Gateway
    WAF that 403s this fetcher's honest User-Agent the same way
    AusTender does (or times out outright, tenders.qld.gov.au). None
    publish a documented no-auth machine-readable feed this fetcher
    could reach without the same UA-spoofing problem.

  FINDING: no Australian government procurement source is reachable by
  a fetcher that identifies itself honestly and respects robots.txt.
  That is a real, load-bearing finding about the state of Australian
  open-data infrastructure, not a bug in this module.

  IMPLICATION: broaden the search rather than fabricate Australian
  data. Several countries publish procurement notices under the Open
  Contracting Data Standard (OCDS) with no authentication at all.

  DECISION: use the UK Government's Contracts Finder OCDS Search API
  -- verified live, 2026-09-01:
    - `https://www.contractsfinder.service.gov.uk/robots.txt` returns
      HTTP 404 (no robots.txt exists on this host at all -- read as no
      crawl restriction is asserted, the standard interpretation of an
      absent robots.txt).
    - The API endpoint itself answers this fetcher's own honest
      User-Agent with HTTP 200 and real, current JSON -- no browser
      spoofing required, no API key, no login.
    - Content is published under the Open Government Licence v3.0
      (stated in every response's `license` field).
    - A live pull on 2026-09-01 returned real open notices, e.g.
      "RA360100 - PHW WINTER GRITTING" (NHS Wales, status=active,
      tenderPeriod closing), "Contract for the Provision of Floral
      Arrangements" (Neston Town Council, closing 30 Sept 2026),
      "Replacement Bio-Mass Boiler & Associated Works" (National Coal
      Mining Museum, closing 9 Sept 2026) -- genuine, dated, addressed
      opportunities with real contact emails, not fixtures.

  This is a UK source, not an Australian one. That is reported
  honestly rather than dressed up: the operator is Australian, the one
  source that actually works without spoofing or a key is British.
  Reusing this shape for AusTender-or-equivalent later is one line
  (a new `FEED_URL` + `parse_items`) IF a lawfully reachable AU feed is
  ever found -- see the findings above for what that would require.

WHAT THIS REUSES RATHER THAN DUPLICATES

  - `foundation/mouth_common.py::fetch_feed()` / `observe()` -- the
    ONE socket in this repository, and the fetch->parse->hash->dedupe
    shape every other mouth uses. This module opens no socket itself.
  - `foundation/discovery_authorization.py::DiscoveryPolicy` -- the
    same gate every other mouth is bound by. `DISCOVERY_POLICY` below
    is checked live against `authorize_discovery()` by this module's
    own tests and would be checked by
    `test_network_control_plane.py::TestEveryFetcherDeclaresAnObjective`
    if this module's name were added to that file's `MOUTHS` tuple --
    left to the file's own owner rather than edited here.
  - `foundation/signal_spine.py::CanonicalSignal` -- the only signal
    shape. No second signal type is defined here.
  - `foundation/untrusted_text.py::describe()` -- every attacker-
    reachable string (title, description, buyer name: any public body
    or, per the live sample above, apparently anyone submitting a
    notice through a buyer's account can populate these) is rendered
    through this before it goes anywhere near `evidence` for display,
    and `looks_like_injection()` markers are recorded as evidence, on
    the same "report, never self-certify" discipline as
    `demand_direction.py`.
  - `foundation/opportunity.py::SOURCE_TYPES` -- signals are typed
    `"OFFICIAL"` (a UK government service publishing under OGL v3.0),
    not a new source class.

WHY `demand_direction.py` IS NOT USED HERE, NAMED RATHER THAN SILENTLY
SKIPPED

`demand_direction.classify_direction()` exists to separate a GitHub
issue that is a genuine ask for help from one that is a maintainer
manufacturing beginner tasks (`WORK_OFFERED` vs `NEED_NOT_EXCLUDED`),
read off a vocabulary of contributor-onboarding labels
(`good first issue`, `difficulty:`, `cohort:`, ...). An OCDS tender
notice carries no such labels, and the ambiguity the module was built
to resolve does not exist in this domain: a public body publishing a
tender notice with a closing date and a buyer identity IS the demand
-- there is no "offering work to attract a contributor" reading of a
government procurement notice. Calling `classify_direction(labels=())`
would return `UNKNOWN` for every single item (no labels to read) and
would silently discard every real signal this module finds. That
would be misapplying an instrument built for a different domain to
manufacture a false negative, which is worse than not calling it and
saying so. Recorded here on the same discipline
`demand_direction.py`'s own docstring uses for its rejected fork:star
discriminator: a considered, measured "does not transfer", not an
oversight.

VALUE DISCIPLINE -- READ THIS BEFORE TRUSTING A NUMBER FROM THIS MODULE

A signal this module emits is OBSERVED at best: a notice with these
exact contents existed in the feed at `observed_at`. It is not
MODELLED (a projection), not VERIFIED (nobody here confirmed the
notice is still open, unretracted, or genuine beyond what the feed
states), and absolutely not REALIZED (a bid was never submitted here,
let alone a contract won). `money_state="ADVERTISED"` on a signal means
exactly that a figure was published, in the OCDS `tender.value` field
-- never that it was paid, or ever will be. See `signal_spine.py`'s own
money-state discipline, which this module inherits rather than
reinvents.

CANNOT

- Cannot tell a genuinely new opportunity from a re-published one:
  `ocid` is the OCDS-assigned identity and is trusted as the dedupe
  key, but a buyer could in principle recycle text across notices.
- Cannot verify a stable, fetchable per-notice URL. The Contracts
  Finder *website* (as opposed to the API) 403s this fetcher's honest
  User-Agent exactly like AusTender does, so `Notice/<id>`-shaped URLs
  were tried and could not be verified live; none is fabricated here.
  `source_ref` instead names the feed this signal was read from, and
  `evidence["ocid"]` is the key to re-find the same notice in a fresh
  pull -- honest about the limitation rather than guessing a link.
- Cannot see notices published by a body using a different Contracts
  Finder-shaped platform (MultiQuote, in-house portals) that this feed
  only references by name in free text -- several live notices above
  say "to access this competition, log in to https://suppliers.multiquote.com"; this module reports
  the notice's existence and terms as published here, not what sits
  behind that second login.
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
    "MOUTH_ID", "FEED_URL", "DISCOVERY_POLICY", "OPEN_TENDER_STATUSES",
    "FetchError", "MouthObservation", "parse_items", "observe",
    "tender_signal", "TenderRadarSweep", "sweep",
]

MOUTH_ID = "tender_radar_uk_contracts_finder"

# UK Government Contracts Finder OCDS Search API. See module docstring
# for what was tried and rejected before landing here. `size=100` is
# the feed's own page-size parameter, not a second pagination layer --
# one request, same "bounded by construction" discipline as every
# other mouth in this repository.
FEED_URL = (
    "https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/"
    "Search?order_by=publishedDate&order_direction=desc&size=100"
)

DISCOVERY_POLICY = DiscoveryPolicy(
    objective=(
        "observe the UK Contracts Finder OCDS search feed for currently "
        "open public-sector tender notices"
    ),
    requested_scope="READ_API",
)

# OCDS release tags: 'tender' (a notice is open for bids), 'award' /
# 'awardUpdate' (the contract has already been decided -- not an open
# opportunity, and reporting it as one would be a fabrication). Only
# 'tender'-tagged releases are ever candidates here.
_OPEN_TAG = "tender"

# tender.status values that mean "you can still respond": 'active' is
# a live competition; 'planning' is a request-for-information / market-
# engagement notice, genuinely pre-competitive but still a real signal
# that a buyer is about to spend money. 'complete', 'cancelled',
# 'unsuccessful', 'withdrawn' are deliberately excluded.
OPEN_TENDER_STATUSES = ("active", "planning")


def _clean_str(value: object) -> str:
    """A JSON field this repository does not control the type of. GitHub
    and PyPI feeds are trusted to be well-typed by the mouths that came
    before this one; a public-sector notice API filled in by hundreds of
    different buyer organisations is not given that benefit -- a field
    that should be a string but arrives as a number, null, or list is
    read as absent rather than crashing the parse."""
    return value if isinstance(value, str) else ""


def parse_items(raw: bytes) -> tuple[dict, ...]:
    """Parse an OCDS release package into open-tender item dicts.

    Malformed JSON, a non-object root, or a missing/mistyped `releases`
    array all raise `FetchError` -- the same UNAVAILABLE-not-crash
    contract every mouth in this repository gives `mouth_common.observe()`.
    A release that is present but individually malformed (not a dict,
    missing `tender`, wrong-typed sub-fields) is skipped rather than
    aborting the whole parse -- one bad notice among a hundred must not
    blind the radar to the other ninety-nine.
    """
    try:
        payload = json.loads(raw)
    # RecursionError is in this tuple deliberately. `json.loads` recurses
    # per nesting level, so a feed answering with 60,000 opening brackets
    # blows the interpreter stack -- and RecursionError inherits from
    # RuntimeError, not from any of the three exceptions above, so it
    # escaped as an unhandled crash. Confirmed by execution during
    # blue-team pass 004, not reasoned about: the sweep died instead of
    # reporting UNAVAILABLE.
    #
    # This module's whole contract is that a malformed feed produces a
    # structured refusal rather than a crash. A remote server choosing
    # its own response body must never be able to take the process down.
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError,
            RecursionError) as exc:
        raise FetchError(f"feed did not parse as JSON: {type(exc).__name__}") from exc
    if not isinstance(payload, dict):
        raise FetchError("feed root is not a JSON object")
    releases = payload.get("releases")
    if not isinstance(releases, list):
        raise FetchError("feed has no 'releases' array")

    items: list[dict] = []
    for rel in releases:
        if not isinstance(rel, dict):
            continue
        tags = rel.get("tag")
        if not isinstance(tags, list) or _OPEN_TAG not in tags:
            continue  # award / awardUpdate: already decided, not an opportunity
        tender = rel.get("tender")
        if not isinstance(tender, dict):
            continue
        status = tender.get("status")
        if status not in OPEN_TENDER_STATUSES:
            continue
        ocid = rel.get("ocid")
        if not isinstance(ocid, str) or not ocid.strip():
            # No stable OCDS identity -- cannot dedupe this safely against
            # prior state, so it is dropped rather than keyed on a guess.
            continue

        value = tender.get("value")
        value = value if isinstance(value, dict) else {}
        amount = value.get("amount")
        amount = amount if isinstance(amount, (int, float)) and not isinstance(amount, bool) else None
        currency = _clean_str(value.get("currency"))

        tender_period = tender.get("tenderPeriod")
        tender_period = tender_period if isinstance(tender_period, dict) else {}
        deadline = _clean_str(tender_period.get("endDate"))

        buyer = rel.get("buyer")
        buyer = buyer if isinstance(buyer, dict) else {}
        buyer_name = _clean_str(buyer.get("name"))

        items.append({
            "key": ocid,
            "ocid": ocid,
            "tender_id": _clean_str(tender.get("id")),
            "title": _clean_str(tender.get("title")),
            "description": _clean_str(tender.get("description")),
            "status": status if isinstance(status, str) else "",
            "amount": amount,
            "currency": currency,
            "deadline": deadline,
            "buyer_name": buyer_name,
            "published": _clean_str(rel.get("date")),
        })
    return tuple(items)


def observe(
    state_path: Path,
    fetch_fn: Optional[Callable[[], bytes]] = None,
    now: Optional[datetime] = None,
) -> MouthObservation:
    """One observation cycle over the tender feed. `fetch_fn` injected in
    every test in `foundation/tests/test_tender_radar.py` -- no test in
    this repository touches the real network, this module included.
    When `fetch_fn` is None the default path goes through
    `mouth_common.fetch_feed()`, which refuses without `DISCOVERY_POLICY`
    -- there is no second, ungated path here."""
    fetch = fetch_fn or (lambda: fetch_feed(FEED_URL, policy=DISCOVERY_POLICY))
    return _observe(MOUTH_ID, state_path, fetch, parse_items, now=now)


def tender_signal(item: dict, now: Optional[datetime] = None) -> CanonicalSignal:
    """One open-tender item -> one `CanonicalSignal`.

    Title, description and buyer name are attacker-reachable free text
    (anyone with access to a buyer's Contracts Finder account can write
    them) and are run through `untrusted_text.describe()` before
    anything derived from them is placed in `claim` or `evidence` --
    the render-safe form is used for display, the verbatim original is
    never discarded (see that module's own docstring for why), and any
    `looks_like_injection()` marker is recorded as evidence for a human
    or caller to weigh, never acted on.
    """
    observed_at = (now or datetime.now(timezone.utc)).isoformat()
    title = describe(item.get("title", ""))
    description = describe(item.get("description", ""))
    buyer = describe(item.get("buyer_name", ""))
    markers = tuple(sorted(set(title.markers) | set(description.markers) | set(buyer.markers)))

    # TRUNCATED, and deliberately not the raw field. `buyer.safe` is the
    # describe()d value; `item["buyer_name"]` is whatever the feed sent.
    # Blue-team pass 004 finding 8a: this line used the raw value, so a
    # 2MB buyer name produced a 4MB write into the durable outcome
    # ledger -- the display fields were bounded and the one field that
    # reaches persistent storage was not. An attacker-controlled field
    # that is bounded on screen and unbounded on disk is the wrong way
    # round.
    target = (buyer.safe or describe(item.get("tender_id", "")).safe
              or describe(str(item.get("key", ""))).safe)

    claim_subject = title.safe or item.get("tender_id") or item["key"]
    claim = f"open UK public-sector tender: {claim_subject}"
    if buyer.safe:
        claim += f" (buyer: {buyer.safe})"

    amount = item.get("amount")
    currency = item.get("currency", "")
    money_state = "NOT_OBSERVED"
    money_observed = ""
    if amount is not None and currency:
        money_state = "ADVERTISED"
        money_observed = f"{amount} {currency}"

    evidence = {
        "ocid": item["key"],
        "tender_id": item.get("tender_id", ""),
        "status": item.get("status", ""),
        "buyer_name_safe": buyer.safe,
        "deadline": item.get("deadline", ""),
        "published": item.get("published", ""),
        "title_safe": title.safe,
        "description_safe": description.safe,
        "injection_markers": markers,
    }

    kwargs = {}
    if item.get("published"):
        kwargs["event_at"] = item["published"]

    return CanonicalSignal(
        signal_id=f"tender:{item['key']}",
        source_id=MOUTH_ID,
        source_type="OFFICIAL",
        # Website Notice/<id> pages could not be verified reachable by
        # this fetcher's honest User-Agent (see module docstring) -- the
        # feed itself, re-fetchable and matched by evidence["ocid"], is
        # the honest source_ref rather than a guessed link.
        source_ref=FEED_URL,
        target=target,
        kind="DEMAND",
        claim=claim,
        observed_at=observed_at,
        target_established_by="SOURCE_NATIVE",
        facts={
            "tender_status": item.get("status", ""),
            "deadline": item.get("deadline", ""),
        },
        evidence=evidence,
        pressure_class="EXPLICIT_DEMAND",
        pressure_evidence=(
            f"published OCDS tender notice, status={item.get('status')!r}, "
            f"naming a buyer and a tenderPeriod -- a public body stating "
            f"outright that it intends to purchase"
        ),
        money_state=money_state,
        money_observed=money_observed,
        **kwargs,
    )


@dataclass(frozen=True)
class TenderRadarSweep:
    """One observation cycle, report only -- see `radar_rail.RadarSweep`
    for the identical discipline this mirrors: no ledger write, no
    promotion, no contact. Reading this report and deciding what to do
    about a lead stays a human's job."""

    status: str
    fetched_count: int
    error: Optional[str]
    signals: tuple[CanonicalSignal, ...]
    targets: tuple[str, ...]

    def show_the_math(self) -> str:
        lines = [
            f"TENDER RADAR status={self.status} fetched={self.fetched_count} "
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
                "  every signal above is OBSERVED only (a live notice existed "
                "at fetch time) -- none is VERIFIED or REALIZED; see module "
                "docstring's value discipline"
            )
        return "\n".join(lines)


def sweep(
    state_dir: Path,
    fetch_fn: Optional[Callable[[], bytes]] = None,
    now: Optional[datetime] = None,
) -> TenderRadarSweep:
    """Run one tender-radar cycle: observe -> signal -> report."""
    state_dir = Path(state_dir)
    # A first run has no state directory. Found on the very first live
    # sweep, which raised FileNotFoundError before a single byte was
    # fetched -- the identical cold-start defect `autonomous_window.py`
    # already carries a comment about. A mouth that cannot run on a
    # machine that has never run it is not a mouth.
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / f"{MOUTH_ID}.json"
    observation = observe(state_path, fetch_fn=fetch_fn, now=now)
    signals = tuple(tender_signal(item, now=now) for item in observation.new_items)
    targets = tuple(sorted({s.target for s in signals}))
    return TenderRadarSweep(
        status=observation.status,
        fetched_count=observation.item_count,
        error=observation.error,
        signals=signals,
        targets=targets,
    )
