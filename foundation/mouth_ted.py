"""A second tender mouth: EU TED (Tenders Electronic Daily), reachable
only because `mouth_common.fetch_feed()` learned to POST on 2026-09-01.

WHY THIS EXISTS, AND WHY IT WASN'T POSSIBLE BEFORE TODAY

`tender_sources.py`'s own docstring records TED as a verified-live,
verified-lawful, verified-licensed source that was NOT REGISTERED for
one disqualifying reason: `api.ted.europa.eu/v3/notices/search` answers
only `POST` (`GET` returns HTTP 405), and `fetch_feed()` used to issue
an unconditional GET with no request body. That is fixed —
`fetch_feed()` now accepts a `json_body` mapping, serialises it, charges
the same `DiscoveryPolicy` budget before the socket opens, and is capped
by `MAX_REQUEST_BYTES` the same way `MAX_FEED_BYTES` already capped the
response (see that function's own docstring). TED is the reason that
capability was added. This module is the first, and so far only,
consumer of it.

WHAT WAS ACTUALLY VERIFIED LIVE (2026-09-01), NOT ASSUMED

  - `https://api.ted.europa.eu/robots.txt` -> HTTP 404 (no restriction
    asserted, same reading `tender_radar.py` already gives
    contractsfinder's absent robots.txt).
  - `GET https://api.ted.europa.eu/v3/notices/search` -> HTTP 405
    `{"message":"Request method 'GET' is not supported"}`, confirmed
    live, matching `tender_sources.py`'s prior finding exactly.
  - `POST` with a JSON body and this repository's own honest
    User-Agent -> HTTP 200, real current data, no key, no login.
  - Licence: CC BY 4.0, per `ted.europa.eu/en/legal-notice` -- "the
    procurement notices published in the Supplement to the Official
    Journal of the European Union can be freely reused, for commercial
    or non-commercial purposes."

THE QUERY, AND HOW THE CPV FILTER WAS PROVEN TO ACTUALLY FILTER

`EXPERT_QUERY` is:

    deadline-receipt-request >= today() AND
    classification-cpv IN (72000000, 79000000, 48000000)

`deadline-receipt-request` is TED's own field for "when does this
notice stop accepting submissions" -- `>= today()` is what separates a
genuinely open notice from TED's much larger historical archive.
`classification-cpv` is the notice's CPV code(s); `IN (72000000, ...)`
was verified to match the whole CPV *family*, not just an exact code,
by fetching `classification-cpv` back in the response and observing
child codes (e.g. `72253000`, `72254000` under the `72000000` "IT
services" branch) present in matched notices -- not assumed from field
naming.

The filter was proven to actually filter, not silently pass everything
through, by comparing live `totalNoticeCount` across three real queries
run back to back on 2026-09-01:

    deadline-receipt-request >= today()                          -> 49,002
    ... AND classification-cpv IN (72000000)                     ->  2,930
    ... AND classification-cpv IN (72000000, 79000000, 48000000) ->  7,140

Three different numbers from three different queries is the evidence
the CPV clause changes what is returned, rather than a defect where an
unrecognised field is accepted syntactically but ignored -- the exact
failure class this module's task brief named as a thing to check for,
not assume.

FIELDS -- WHY THIS IS NOT `tender_radar.parse_items` COPY-PASTED

TED's expert-search API has hundreds of field names (`notice-title`,
`description-proc`, `description-lot`, `buyer-name`,
`deadline-receipt-request`, `publication-number`, `classification-cpv`,
...) and none of them look like OCDS. `notice-title` and `buyer-name`
came back as `{lang_code: value, ...}` maps across ~25 EU languages, not
a single string -- confirmed live, not assumed from documentation.
`description-proc` is `{lang: str}`; `description-lot` is
`{lang: [str, ...]}` -- two different shapes for "the description",
and a real, live 2026-08 notice (publication-number 533561-2026, a
Greek DAPEEP server tender) had `description-proc` populated but no
`description-lot`, while another (533775-2026) had `description-lot`
with two lot-level strings and a `description-proc` too -- confirmed
by inspecting real API output, not guessed. `_first_text()` below
prefers `eng` when present and otherwise takes the first available
language deterministically (sorted by key) rather than an arbitrary
dict-iteration order, so the same input always normalises the same way.

WHY `tender_radar.tender_signal()` IS IMPORTED FOR SHAPE BUT NOT CALLED
DIRECTLY ON TED ITEMS -- NAMED, NOT SILENTLY DUPLICATED

The task brief for this module says: do not duplicate tender_radar's
signal construction, import it if it's needed. It is needed as a
*template* -- the describe()/markers/target/money_state/pressure_class
shape below is deliberately the same shape `tender_radar.tender_signal()`
already uses -- but it cannot be called verbatim on a TED item, because
`tender_radar.tender_signal()` hardcodes the literal string "open UK
public-sector tender" into every `claim` it builds. Calling it on a
French, German, Spanish or Greek TED notice would produce a signal
whose own claim text falsely says "UK" -- a factual inaccuracy this
repository's own value discipline (`tender_radar.py`'s "VALUE
DISCIPLINE" section, `signal_spine.py`'s echo-collapse discipline) would
never accept if a human wrote it by hand. `ted_signal()` below is
therefore a second, EU-labelled construction function with the same
disciplines applied (describe() before anything untrusted reaches
`claim`/`evidence`, ADVERTISED money only when both amount and currency
are present, EXPLICIT_DEMAND pressure class with real pressure_evidence,
never PAID/REALIZED) -- not a rewrite of what tender_radar does, a
correction of the one field that cannot be reused unmodified.

WHAT THIS REUSES RATHER THAN DUPLICATES

  - `foundation/mouth_common.py::fetch_feed()` / `observe()` -- the ONE
    socket in this repository. This module opens no socket itself and
    performs no POST outside `fetch_feed(..., json_body=...)`.
  - `foundation/discovery_authorization.py::DiscoveryPolicy` -- same
    gate every mouth is bound by; `DISCOVERY_POLICY` below is a second,
    independently-declared policy object (own objective, own budget),
    not the UK module's policy reused for a different source.
  - `foundation/signal_spine.py::CanonicalSignal` -- the only signal
    shape. No second signal type is defined here.
  - `foundation/untrusted_text.py::describe()` -- every attacker-
    reachable string (title, description, buyer name -- any of ~250,000
    EU contracting authorities can populate these) goes through this
    before reaching `claim`/`evidence`, same discipline as
    `tender_radar.py`.
  - `foundation/opportunity.py::SOURCE_TYPES` -- `"OFFICIAL"`, an EU
    institution publishing under CC BY 4.0. Not a new source class.

VALUE DISCIPLINE -- SAME AS `tender_radar.py`, RESTATED FOR THIS SOURCE

A signal this module emits is OBSERVED at best: a notice with these
exact contents existed in the feed at `observed_at`, with a
deadline-receipt-request in the future at query time. It is not
VERIFIED (nobody here confirmed the notice is still open, unwithdrawn,
or genuine beyond what TED's own API states) and never REALIZED (no bid
was submitted here). `money_state="ADVERTISED"` means a figure was
published in TED's own value field -- never that it was paid or ever
will be. TED does not surface an amount field through the query shape
this module uses (see CANNOT below); every signal this module has
actually emitted carries `money_state="NOT_OBSERVED"` as a result, and
that is reported honestly rather than papered over with a fabricated
figure.

CANNOT

- Cannot report a monetary amount from the fields this module reads.
  TED's contract-value fields live under lot-level BT codes this
  module's query does not request (adding them was not necessary to
  prove the source works, and guessing a value field name and being
  wrong would be worse than reporting NOT_OBSERVED honestly). `amount`
  and `currency` are therefore always empty/None in every item this
  parser produces -- not a bug, a documented scope boundary.
- Cannot tell a genuinely new notice from a republished one beyond what
  `publication-number` distinguishes -- trusted as the dedupe key
  because TED assigns it per publication, the same trust
  `tender_radar.py` places in OCDS `ocid`.
- Cannot verify a per-notice URL is fetchable by this fetcher's honest
  User-Agent (the `links.html.ENG` URL TED returns points at
  `ted.europa.eu`, a different host to the API, and was not separately
  probed this cycle) -- `source_ref` names the API query itself rather
  than a guessed working link.
- Cannot see the notice text itself, only the title/description fields
  TED's own API chose to populate for that specific record -- several
  real notices had `description-lot` but no `description-proc` or vice
  versa, and older archived-but-still-open notices (framework
  agreements with a multi-year `deadline-receipt-request`) sometimes had
  neither populated at all -- items without either become
  `description=""`, not a fabricated summary.
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
    "MOUTH_ID", "FEED_URL", "EXPERT_QUERY", "REQUEST_FIELDS",
    "DISCOVERY_POLICY", "FetchError", "MouthObservation",
    "parse_items", "observe", "ted_signal", "TedRadarSweep", "sweep",
]

MOUTH_ID = "tender_radar_eu_ted"

# The one TED endpoint this module ever calls. POST-only -- see module
# docstring for the confirmed GET->405 finding this depends on.
FEED_URL = "https://api.ted.europa.eu/v3/notices/search"

# `>= today()` is TED's own live-filter syntax for "the submission
# deadline has not yet passed" -- proven to change totalNoticeCount
# (see module docstring). `classification-cpv IN (...)` is proven, by
# the same method, to match the CPV code and its family:
#   72000000 -- IT services: consulting, software development, Internet
#               and support
#   79000000 -- business services: law, marketing, consulting,
#               recruitment, printing and security
#   48000000 -- software package and information systems
EXPERT_QUERY = (
    "deadline-receipt-request >= today() AND "
    "classification-cpv IN (72000000, 79000000, 48000000)"
)

# Every field this module's parser actually reads. Confirmed live
# (2026-09-01) to be accepted by the API and to return real values for
# at least some current notices -- see module docstring for the exact
# shapes observed. Requesting a field this API doesn't recognise fails
# the whole call with QUERY_UNKNOWN_FIELD/"unsupported value", so this
# list is deliberately the minimum this parser needs, not a wishlist.
REQUEST_FIELDS = (
    "publication-number",
    "notice-title",
    "description-proc",
    "description-lot",
    "buyer-name",
    "deadline-receipt-request",
)

# `limit=250` matches the live-verified page size (a real call with
# limit=250 returned exactly 250 notices out of totalNoticeCount=7140,
# confirmed 2026-09-01) -- one request, same "bounded by construction,
# no second pagination layer" discipline as `tender_radar.FEED_URL`'s
# own `size=100`.
_REQUEST_LIMIT = 250

DISCOVERY_POLICY = DiscoveryPolicy(
    objective=(
        "observe the EU TED notices/search API for currently open "
        "public-sector tender notices in IT, software and business "
        "consulting CPV categories"
    ),
    requested_scope="READ_API",
)


def _clean_str(value: object) -> str:
    """Same discipline as `tender_radar._clean_str()`: a field this
    repository does not control the type of, filled in by any of TED's
    ~250,000 contracting authorities, is read as absent rather than
    crashing the parse on an unexpected type."""
    return value if isinstance(value, str) else ""


def _first_text(value: object) -> str:
    """Normalise one of TED's `{lang_code: str}` / `{lang_code: [str,
    ...]}` multilingual maps into a single display string.

    Prefers `eng` when present -- most notices carry at least a
    machine-translated English title even when the buyer's own
    submission was in another language, confirmed live across the
    samples in the module docstring. Otherwise picks the
    lexicographically first language key present, so the same input
    dict always normalises to the same output string regardless of
    Python's dict-ordering behaviour -- deterministic, not "whichever
    key iteration happened to return first".

    A missing map, a non-dict value, or a dict with no string-bearing
    entries all return "" -- never a guessed value. `TypeError`/
    `AttributeError` from an unexpected inner shape (e.g. a list of
    dicts instead of a list of strings) are caught here rather than
    escaping the parse, per this module's "one malformed record must
    not blind the parse to the rest" contract.
    """
    if not isinstance(value, dict) or not value:
        return ""
    try:
        keys = sorted(k for k in value if isinstance(k, str))
        ordered = (["eng"] if "eng" in value else []) + [k for k in keys if k != "eng"]
        for lang in ordered:
            entry = value.get(lang)
            if isinstance(entry, str) and entry.strip():
                return entry
            if isinstance(entry, list):
                for item in entry:
                    if isinstance(item, str) and item.strip():
                        return item
    except (TypeError, AttributeError):
        return ""
    return ""


def parse_items(raw: bytes) -> tuple[dict, ...]:
    """Parse a TED `/v3/notices/search` JSON response into the same
    item-dict shape `tender_radar.parse_items()` produces: `key`,
    `buyer_name`, `title`, `description`, `tender_id`, `status`,
    `deadline`, plus `amount`/`currency`/`published` for field-shape
    parity even though TED (via the fields this module requests) never
    populates the first two -- see module docstring's CANNOT section.

    Malformed JSON, a non-object root, or a missing/mistyped `notices`
    array all raise `FetchError` -- same UNAVAILABLE-not-crash contract
    every mouth in this repository gives `mouth_common.observe()`. TED
    itself reports certain caller errors (bad query syntax, unknown
    field) as HTTP 200 with a JSON body carrying `message`/`error`
    instead of an HTTP error code or a `notices` array -- confirmed
    live, 2026-09-01 -- so a well-formed-JSON response with no
    `notices` key is a parse failure here too, not zero results; an
    honestly empty result set is `{"notices": [], ...}` and is handled
    below as zero items, not as a refusal.
    """
    try:
        payload = json.loads(raw)
    # RecursionError included deliberately -- same reasoning as
    # tender_radar.parse_items(): json.loads recurses per nesting
    # level, and RecursionError inherits RuntimeError, not any of the
    # three below, so it would otherwise escape as an unhandled crash.
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError,
            RecursionError) as exc:
        raise FetchError(f"feed did not parse as JSON: {type(exc).__name__}") from exc
    if not isinstance(payload, dict):
        raise FetchError("feed root is not a JSON object")
    if "notices" not in payload:
        # TED's own error responses (bad query, unknown field, syntax
        # error) are well-formed JSON objects with a "message"/"error"
        # key and no "notices" key at all -- treated as UNAVAILABLE,
        # never as "zero notices found".
        message = payload.get("message")
        detail = f": {message}" if isinstance(message, str) and message else ""
        raise FetchError(f"feed has no 'notices' array{detail}")
    notices = payload.get("notices")
    if not isinstance(notices, list):
        raise FetchError("feed 'notices' field is not a list")

    items: list[dict] = []
    for notice in notices:
        if not isinstance(notice, dict):
            continue
        pub_number = notice.get("publication-number")
        if not isinstance(pub_number, str) or not pub_number.strip():
            # No stable identity to dedupe on -- dropped rather than
            # keyed on a guess, same discipline as tender_radar's
            # missing-ocid handling.
            continue

        title = _first_text(notice.get("notice-title"))
        description = _first_text(notice.get("description-proc"))
        if not description:
            description = _first_text(notice.get("description-lot"))

        buyer_name = _first_text(notice.get("buyer-name"))

        deadlines = notice.get("deadline-receipt-request")
        deadline = ""
        if isinstance(deadlines, list):
            for candidate in deadlines:
                if isinstance(candidate, str) and candidate.strip():
                    deadline = candidate
                    break
        elif isinstance(deadlines, str):
            deadline = deadlines

        items.append({
            "key": pub_number,
            "ocid": "",
            "tender_id": pub_number,
            "title": title,
            "description": description,
            # TED's own status vocabulary is not requested by this
            # module's field list -- every item here matched the
            # EXPERT_QUERY's own deadline-in-the-future filter, which is
            # the honest basis for calling it open; a separate
            # buyer-declared "status" string is not fabricated to fill
            # this field.
            "status": "",
            "amount": None,
            "currency": "",
            "deadline": deadline,
            "buyer_name": buyer_name,
            "published": "",
        })
    return tuple(items)


def observe(
    state_path: Path,
    fetch_fn: Optional[Callable[[], bytes]] = None,
    now: Optional[datetime] = None,
) -> MouthObservation:
    """One observation cycle over the TED feed. `fetch_fn` is injected in
    every test in `foundation/tests/test_mouth_ted.py` -- no test in this
    repository touches the real network, this module included. When
    `fetch_fn` is None the default path goes through
    `mouth_common.fetch_feed()` with `json_body=` set, which refuses
    without `DISCOVERY_POLICY` -- there is no second, ungated path here.
    """
    fetch = fetch_fn or (lambda: fetch_feed(
        FEED_URL,
        policy=DISCOVERY_POLICY,
        json_body={
            "query": EXPERT_QUERY,
            "fields": list(REQUEST_FIELDS),
            "limit": _REQUEST_LIMIT,
        },
    ))
    return _observe(MOUTH_ID, state_path, fetch, parse_items, now=now)


def ted_signal(item: dict, now: Optional[datetime] = None) -> CanonicalSignal:
    """One open-EU-tender item -> one `CanonicalSignal`.

    Same disciplines as `tender_radar.tender_signal()` -- describe()
    every attacker-reachable string before it reaches `claim`/
    `evidence`, EXPLICIT_DEMAND pressure class with real evidence, only
    ADVERTISED money when both amount and currency are actually
    present (never here -- see module docstring's CANNOT section) --
    but with EU-correct claim text. See module docstring for why this
    is not a call into `tender_radar.tender_signal()`: that function
    hardcodes "open UK public-sector tender" into its claim, which
    would misdescribe a Greek, French, German or Spanish TED notice.
    """
    observed_at = (now or datetime.now(timezone.utc)).isoformat()
    title = describe(item.get("title", ""))
    description = describe(item.get("description", ""))
    buyer = describe(item.get("buyer_name", ""))
    markers = tuple(sorted(set(title.markers) | set(description.markers) | set(buyer.markers)))

    # Bounded, display-safe value reaches the durable evidence field --
    # same fix tender_radar.py's own docstring documents finding and
    # applying (blue-team pass 004, finding 8a): the raw field is never
    # the one written to persistent storage.
    target = (buyer.safe or describe(item.get("tender_id", "")).safe
              or describe(str(item.get("key", ""))).safe)

    claim_subject = title.safe or item.get("tender_id") or item["key"]
    claim = f"open EU TED public-sector tender: {claim_subject}"
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
        "publication_number": item["key"],
        "tender_id": item.get("tender_id", ""),
        "buyer_name_safe": buyer.safe,
        "deadline": item.get("deadline", ""),
        "title_safe": title.safe,
        "description_safe": description.safe,
        "injection_markers": markers,
    }

    return CanonicalSignal(
        signal_id=f"tender:{MOUTH_ID}:{item['key']}",
        source_id=MOUTH_ID,
        source_type="OFFICIAL",
        source_ref=f"{FEED_URL} query={EXPERT_QUERY!r}",
        target=target,
        kind="DEMAND",
        claim=claim,
        observed_at=observed_at,
        target_established_by="SOURCE_NATIVE",
        facts={
            "deadline": item.get("deadline", ""),
        },
        evidence=evidence,
        pressure_class="EXPLICIT_DEMAND",
        pressure_evidence=(
            f"TED notice with publication-number {item['key']!r} and a "
            f"deadline-receipt-request in the future at query time, "
            f"matching CPV family 72000000/79000000/48000000 -- an EU "
            f"contracting authority stating outright that it intends to "
            f"purchase IT/software/business-consulting services"
        ),
        money_state=money_state,
        money_observed=money_observed,
    )


@dataclass(frozen=True)
class TedRadarSweep:
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
            f"TED RADAR status={self.status} fetched={self.fetched_count} "
            f"signals={len(self.signals)}"
        ]
        if self.error:
            lines.append(f"  error: {self.error}")
        if self.status in ("FIRST_SEEN", "CHANGED") and not self.signals:
            lines.append(
                "  zero open, matching TED notices observed this cycle -- "
                "a valid, honest outcome, not an error"
            )
        for s in self.signals:
            lines.append(f"  OBSERVED  target={s.target!r}  {s.claim}")
        if self.signals:
            lines.append(
                "  every signal above is OBSERVED only (a live notice "
                "existed at fetch time, with a future deadline) -- none "
                "is VERIFIED or REALIZED; see module docstring's value "
                "discipline"
            )
        return "\n".join(lines)


def sweep(
    state_dir: Path,
    fetch_fn: Optional[Callable[[], bytes]] = None,
    now: Optional[datetime] = None,
) -> TedRadarSweep:
    """Run one TED-radar cycle: observe -> signal -> report."""
    state_dir = Path(state_dir)
    # Same cold-start fix tender_radar.sweep()'s own docstring documents
    # -- a first run has no state directory yet.
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / f"{MOUTH_ID}.json"
    observation = observe(state_path, fetch_fn=fetch_fn, now=now)
    signals = tuple(ted_signal(item, now=now) for item in observation.new_items)
    targets = tuple(sorted({s.target for s in signals}))
    return TedRadarSweep(
        status=observation.status,
        fetched_count=observation.item_count,
        error=observation.error,
        signals=signals,
        targets=targets,
    )
