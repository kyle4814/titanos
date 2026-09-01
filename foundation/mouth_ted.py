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
- CORRECTED 2026-09-01: this bullet previously said this module could
  not verify a per-notice URL and used `source_ref = FEED_URL + query`
  instead -- identical on every signal, which is both misleading to a
  human and was the root cause of cycle 007's 96.4% false-positive
  relevance failure (a scorer reading source_ref matched the query's own
  CPV codes against themselves). `_notice_url()` now reads the real
  `links.html` map TED returns per notice and `ted_signal()` uses it as
  `source_ref`. It WAS separately probed this cycle: `curl -A
  <this fetcher's own User-Agent> https://ted.europa.eu/en/notice/-/
  detail/56666-2017` returned HTTP 202, not 404 -- reachable, though TED
  returns 202 rather than 200 for this specific host/path (not
  independently explained; recorded honestly rather than assumed to
  mean 200). `fetch_feed()` itself is never pointed at this URL --
  `_reject_unsafe_url()`'s https-only, public-host-only check would
  apply if it ever were, but no code path in this module does that.
- Cannot see the notice text itself, only the title/description fields
  TED's own API chose to populate for that specific record -- several
  real notices had `description-lot` but no `description-proc` or vice
  versa, and older archived-but-still-open notices (framework
  agreements with a multi-year `deadline-receipt-request`) sometimes had
  neither populated at all -- items without either become
  `description=""`, not a fabricated summary.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from foundation.communication_gate import CommunicationDenied
from foundation.discovery_authorization import DiscoveryPolicy
from foundation.mouth_common import (
    FetchError, MouthObservation, compute_state_hash, fetch_feed,
)
from foundation.mouth_common import observe as _observe
from foundation.signal_spine import CanonicalSignal
from foundation.untrusted_text import describe

__all__ = [
    "MOUTH_ID", "FEED_URL", "EXPERT_QUERY", "REQUEST_FIELDS",
    "DISCOVERY_POLICY", "FetchError", "MouthObservation",
    "parse_items", "observe", "ted_signal", "TedRadarSweep", "sweep",
    "MAX_PAGES_HARD_CAP", "TedPaginatedObservation", "observe_paginated",
    "sweep_paginated",
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
# `publication-date >= today(-90)` -- live-verified 2026-09-01, added
# alongside the pagination/source_ref work below because it fixes the
# same underlying problem the other two fixes do: the query previously
# had no recency constraint at all, so a notice PUBLISHED in 2017 with a
# multi-year framework-agreement deadline ranked identically to one
# published last week. `deadline-receipt-request >= today()` only
# guarantees the notice hasn't closed yet, not that it's recent.
#
# TED's expert-search grammar for this field is NOT free-form date
# arithmetic -- `today() - 90`, `now()-90` and `sysdate()-90` all fail
# with QUERY_SYNTAX_ERROR (confirmed live). The API's own error message
# for a malformed value states the real accepted pattern verbatim:
# `20[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])|today\([+-]?[0-9]*\)`
# -- i.e. either an unpunctuated `YYYYMMDD` literal, or `today(N)` with
# an optional signed integer day offset baked inside the parens (no
# space, no separate operator). `today(-90)` is the form used here.
#
# Proven to actually filter, not silently pass through, by three real
# totalNoticeCount comparisons run back to back on 2026-09-01, same
# method as the CPV proof above:
#
#   (no publication-date clause)                 -> 7,140
#   ... AND publication-date >= today(-365)      -> 6,040
#   ... AND publication-date >= today(-90)       -> 5,681
#   ... AND publication-date >= today(-30)       -> 4,064
#
# Monotonically decreasing as the window narrows -- the clause changes
# what's returned, not a defect where an unrecognised field is accepted
# syntactically but ignored. 90 days is chosen as "recently published"
# for this radar's purpose (a live procurement lead, not a historical
# archive entry); narrower or wider is a tuning choice, not a
# correctness one, and can change without re-verifying the syntax above.
EXPERT_QUERY = (
    "deadline-receipt-request >= today() AND "
    "classification-cpv IN (72000000, 79000000, 48000000) AND "
    "publication-date >= today(-90)"
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
    # The notice's OWN CPV classification. Absent until 2026-09-01, which
    # made the relevance scorer's CPV path unusable: with no real code on
    # the signal, the only CPV text anywhere was the fetch query stored in
    # source_ref, so a profile declaring those codes matched its own
    # filter on 100% of notices. Fetching the real code is what makes CPV
    # evidence about the notice rather than about the question.
    "classification-cpv",
    # This notice's own public TED page URL, as a {SCHEME: {LANG: url}}
    # map -- confirmed live 2026-09-01 to be returned unconditionally by
    # the API regardless of whether it's named here (same as
    # `publication-number`), but listed anyway per this module's own
    # "every field the parser actually reads" discipline: `_notice_url()`
    # below now reads it. Fixes a real defect: every signal this module
    # emitted before 2026-09-01 carried the search endpoint + query
    # string as source_ref, identical on every notice, because nothing
    # requested or read the per-notice link -- see `_notice_url()`.
    "links",
    # When TED published this notice -- NOT when it closes. Added
    # alongside the EXPERT_QUERY publication-date filter above: without
    # this, a 2017 framework-agreement notice with a 2031 deadline was
    # indistinguishable, on the data this module actually carried, from
    # one published last week.
    "publication-date",
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

# ── PAGINATION ──────────────────────────────────────────────────────
#
# THE GAP THIS CLOSES: with limit=250 and no pagination, one sweep saw
# 250 of totalNoticeCount=7140 open, CPV-relevant notices -- 3.5% of
# what this query can lawfully reach, one page out of ~29.
#
# HOW TED'S PAGINATION ACTUALLY WORKS -- VERIFIED LIVE 2026-09-01, NOT
# ASSUMED FROM THE FIELD NAME:
#
#   - The response always carries `iterationNextToken`. Across every
#     live call made investigating this (single-page and multi-page,
#     first page and deep pages), it was `null` every time. TED's own
#     v3 notices/search endpoint does NOT hand back a working
#     continuation token for this query shape -- whatever
#     `iterationNextToken` is for (a deeper scroll-cursor mode this
#     endpoint didn't engage for a query this size), it wasn't
#     observed working here.
#   - What DOES work, live-verified: an integer `page` field in the
#     POST body, 1-indexed. `page=1,limit=250` and `page=2,limit=250`
#     returned two disjoint 250-item sets with ZERO overlapping
#     publication-numbers (checked by set intersection, not assumed).
#     `page=29,limit=250` against a real totalNoticeCount of 7140
#     returned exactly 140 items -- (29-1)*250=7000, 7140-7000=140,
#     confirmed against the live count. `page=30` (past the end)
#     returned zero items, no error. `page=0` is REJECTED by the API
#     with a validation error ("must be greater than or equal to 1")
#     -- 1-indexed, not 0-indexed, confirmed by the error message
#     rather than assumed. `limit` above 250 is REJECTED
#     (SEARCH_EXCEEDS_MAX_LIMIT, maxLimits=250) -- 250 is a hard
#     server-side ceiling, not this module's own choice.
#
# So this module's pagination is offset/page-based against a real,
# live-verified `page` parameter -- NOT token-based, because the token
# this endpoint advertises was never observed to do anything. The
# non-advancing-TOKEN detection below is kept anyway, defensively: if
# TED's behaviour ever changes and `iterationNextToken` starts being
# populated, a repeating token still gets caught rather than trusted
# silently. The non-advancing-PAGE detection (a page repeating notices
# already seen) is the mechanism actually proven against this live API.
#
# THE HARD CEILING. `page` is caller-controlled and TED's own count
# controls how many pages exist -- a caller that just kept incrementing
# `page` while any items kept coming back would have no built-in stop
# against a server that, hypothetically, kept answering. 20 pages *
# 250 = 5,000 notices is generous headroom over the live 7,140-notice
# total while still being an explicit, finite number this process will
# never exceed regardless of what any DiscoveryPolicy authorizes or
# what the server claims is available.
MAX_PAGES_HARD_CAP = 20


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


def _notice_url(notice: dict) -> str:
    """Extract this notice's own public TED page URL from the API's
    `links` structure -- the fix for the defect found 2026-09-01: every
    signal this module emitted carried `source_ref = FEED_URL + query`,
    identical across every notice, because nothing read the per-notice
    link. A search endpoint is not a citation for one specific notice.

    Live-verified shape (2026-09-01): `links.html` is a
    `{LANG_CODE: url}` map (uppercase 3-letter codes, e.g. `"ENG"`),
    present on every sampled notice regardless of whether `links` was
    named in the request's `fields` list -- TED returns it
    unconditionally, the same way it always returns
    `publication-number`.

    Prefers `ENG` when present -- same discipline as `_first_text()` --
    otherwise the lexicographically first language key present, so the
    same input always normalises to the same output. Falls back to
    constructing the URL from `publication-number` using the exact
    pattern observed live (`https://ted.europa.eu/en/notice/-/detail/
    {publication-number}`, confirmed byte-for-byte identical to a real
    `links.html.ENG` value on multiple sampled notices) only when the
    API's own `links.html` map is absent or empty for this notice --
    never falls back to `FEED_URL`, which would misleadingly point a
    human at the search endpoint instead of the notice they're being
    shown. Returns `""` only if `publication-number` is itself absent,
    which cannot happen for an item that reaches this function (see
    `parse_items()` -- items without a publication-number are dropped
    before this is called).
    """
    links = notice.get("links")
    if isinstance(links, dict):
        html = links.get("html")
        if isinstance(html, dict) and html:
            keys = sorted(k for k in html if isinstance(k, str))
            ordered = (["ENG"] if "ENG" in html else []) + [k for k in keys if k != "ENG"]
            for lang in ordered:
                url = html.get(lang)
                if isinstance(url, str) and url.strip():
                    return url
    pub_number = notice.get("publication-number")
    if isinstance(pub_number, str) and pub_number.strip():
        return f"https://ted.europa.eu/en/notice/-/detail/{pub_number}"
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

        # The notice's own CPV code(s). TED returns these as a list, a
        # bare string, or a {lang: ...} mapping depending on the notice,
        # so every shape is coerced rather than assumed -- a wrong-typed
        # field must not crash a sweep.
        raw_cpv = notice.get("classification-cpv")
        if isinstance(raw_cpv, dict):
            raw_cpv = list(raw_cpv.values())
        if isinstance(raw_cpv, str):
            cpv_list = [raw_cpv]
        elif isinstance(raw_cpv, (list, tuple)):
            cpv_list = []
            for entry in raw_cpv:
                if isinstance(entry, (list, tuple)):
                    cpv_list.extend(str(x) for x in entry)
                elif entry is not None:
                    cpv_list.append(str(entry))
        else:
            cpv_list = []
        cpv = " ".join(_clean_str(c) for c in cpv_list if _clean_str(c))

        deadlines = notice.get("deadline-receipt-request")
        deadline = ""
        if isinstance(deadlines, list):
            for candidate in deadlines:
                if isinstance(candidate, str) and candidate.strip():
                    deadline = candidate
                    break
        elif isinstance(deadlines, str):
            deadline = deadlines

        pub_date = notice.get("publication-date")
        publication_date = pub_date if isinstance(pub_date, str) else ""

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
            "cpv": cpv,
            # Field-shape parity with tender_radar.parse_items() names
            # this "published" -- kept, but this module's own
            # `publication_date` (below) is the field actually populated
            # and actually read by ted_signal()/facts. "published" stays
            # "" for the same field-parity-not-fabrication reason the
            # module docstring already gives for amount/currency.
            "published": "",
            "publication_date": publication_date,
            # This notice's own public TED page -- see _notice_url()'s
            # own docstring for what this fixes.
            "url": _notice_url(notice),
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



# NFC, NOT NFKC -- identity normalisation, not search normalisation.
#
# This used NFKC, chosen to catch an organisation whose name arrives with
# compatibility-equivalent characters. Blue-team pass 011 showed the price:
# NFKC collapses characters that are genuinely DIFFERENT, and confirmed it
# live for Roman-numeral-I vs Latin-I, superscript-2 vs 2, the ff ligature
# vs ff, and fullwidth vs ASCII. Two unrelated buyers become one
# controlling party, using ordinary printable characters anyone can type --
# which defeats the exact self-dealing defence this function exists to
# provide, since collapsing two parties into one is how a single actor
# passes as corroborated.
#
# NFC applies canonical equivalence only. It still fixes the problem that
# motivated normalising at all -- the same accented name composed and
# decomposed, verified still collapsing correctly -- without merging
# distinct characters. A search index wants NFKC. An identity does not.

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

    # blue-team pass 008, finding 8: `item["key"]` (TED's own
    # publication-number) is never length-capped or type-checked by
    # `parse_items()`'s coercion -- unlike `target` above (already fixed
    # for this same reason), the raw value used to flow straight into
    # `signal_id`/`evidence` and from there into
    # `opportunity_pipeline`'s `facts["signal_ids"]`, which
    # `OutcomeLedger.record()` persists to the durable jsonl ledger with
    # no length cap anywhere in that path. A 2,000,000-character key
    # reproduced a >2MB single-record ledger write. `describe()` is the
    # existing, already-used bounding mechanism for exactly this class
    # of field (see `target` above); reusing it here rather than adding
    # a second length-capping mechanism. A real TED publication-number
    # is short (e.g. "533561-2026") -- anything this cap actually
    # truncates is by definition hostile or broken, never a legitimate
    # value lost.
    safe_key = describe(str(item.get("key", ""))).safe
    safe_tender_id = describe(str(item.get("tender_id", ""))).safe

    claim_subject = title.safe or safe_tender_id or safe_key
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

    # blue-team pass 008, findings 3 and 4: `controlling_party()`
    # (opportunity.py) used to derive identity straight from the
    # truncated `target`/buyer display string -- two different buyer
    # names sharing a ~290-char prefix and equal total length truncate
    # to the byte-identical `.safe` string and collapse into one
    # controlling party; separately, NFC vs. NFD encodings of the
    # identical name produced two different parties. Both are fixed at
    # `controlling_party()` itself, but that function needs a FULL-
    # length-derived, FIXED-SIZE input to do it -- `identity_hash` is
    # that input: a normalised sha256 digest (64 hex chars, bounded
    # regardless of input length) of the buyer name computed BEFORE
    # `describe()` truncates it, so a truncation collision downstream
    # never happens, and NFKC-normalised before hashing so NFC/NFD
    # variants of the same name hash identically. Never the raw name
    # itself -- only its digest reaches this field, so this does not
    # reopen finding 8's unbounded-write class.
    buyer_raw = item.get("buyer_name", "")
    identity_hash = (
        hashlib.sha256(
            unicodedata.normalize("NFC", buyer_raw).strip().lower().encode("utf-8")
        ).hexdigest()
        if isinstance(buyer_raw, str) and buyer_raw.strip()
        else ""
    )

    evidence = {
        "publication_number": safe_key,
        "tender_id": safe_tender_id,
        "buyer_name_safe": buyer.safe,
        "identity_hash": identity_hash,
        "deadline": item.get("deadline", ""),
        "title_safe": title.safe,
        "description_safe": description.safe,
        "injection_markers": markers,
    }

    return CanonicalSignal(
        signal_id=f"tender:{MOUTH_ID}:{safe_key}",
        source_id=MOUTH_ID,
        source_type="OFFICIAL",
        # THIS NOTICE's own public TED page -- not the search endpoint,
        # not the query. Fixes the defect found 2026-09-01: every prior
        # signal carried `FEED_URL + query`, identical across every
        # notice, which is both misleading to a human trying to open the
        # actual notice AND was the root cause of cycle 007's 96.4%
        # false-positive relevance failure (the query text contained the
        # CPV codes; a scorer reading source_ref matched the question
        # against itself). `item["url"]` is `_notice_url()`'s output --
        # never falls back to FEED_URL; "" is the honest fallback if a
        # notice genuinely had no derivable URL (see that function's
        # docstring for why that case cannot occur for pub-numbered
        # items in practice).
        source_ref=item.get("url", ""),
        target=target,
        kind="DEMAND",
        claim=claim,
        observed_at=observed_at,
        target_established_by="SOURCE_NATIVE",
        facts={
            "deadline": item.get("deadline", ""),
            # The notice's OWN CPV, so a relevance scorer matching CPV is
            # matching the notice rather than the query used to find it.
            "cpv": item.get("cpv", ""),
            # When TED published this notice (not when it closes) -- see
            # REQUEST_FIELDS's own comment for why this was added.
            "publication_date": item.get("publication_date", ""),
        },
        evidence=evidence,
        pressure_class="EXPLICIT_DEMAND",
        # blue-team pass 008, finding 1: this used to hardcode
        # EXPERT_QUERY's own CPV filter ("72000000/79000000/48000000")
        # verbatim into every signal's pressure_evidence, regardless of
        # what that specific notice's real `classification-cpv` was --
        # the exact defect class (fetch-query metadata read back as
        # evidence about notice content) that caused cycle 007's 96.4%
        # false-positive incident via `source_ref`. Currently inert
        # (`relevance._searchable_text()` does not read
        # `pressure_evidence`) but nothing stopped a future maintainer
        # from adding it, which would reopen the same bug on this field.
        # Fixed to name the NOTICE's own real CPV code(s) (`item["cpv"]`,
        # the same field `facts["cpv"]` already uses, populated from
        # `classification-cpv` in `parse_items()`) instead of the query
        # that found it -- observation about this notice, not a
        # restatement of the question that was asked.
        pressure_evidence=(
            f"TED notice with publication-number {safe_key!r} and a "
            f"deadline-receipt-request in the future at query time, "
            + (
                f"classified under CPV code(s) {item.get('cpv', '').strip()!r}"
                if item.get("cpv", "").strip()
                else "with no classification-cpv populated by TED for "
                     "this notice"
            )
            + " -- an EU contracting authority stating outright that it "
              "intends to purchase IT/software/business-consulting "
              "services"
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
    # Pagination accounting. Defaulted so sweep() (the existing
    # single-page path, unchanged) and every existing caller/test
    # constructing a TedRadarSweep by keyword continue to work
    # unmodified -- only sweep_paginated() below populates these with
    # real multi-page numbers.
    pages_requested: int = 1
    pages_fetched: int = 1
    partial: bool = False
    stop_reason: str = "single_page"

    def show_the_math(self) -> str:
        lines = [
            f"TED RADAR status={self.status} fetched={self.fetched_count} "
            f"signals={len(self.signals)}"
        ]
        if self.pages_requested > 1 or self.pages_fetched > 1:
            lines.append(
                f"  pages: {self.pages_fetched} fetched of "
                f"{self.pages_requested} requested "
                f"(stop_reason={self.stop_reason})"
            )
        if self.partial:
            lines.append(
                "  PARTIAL: this result does not cover every page "
                "authorized -- more open, matching notices likely exist "
                "beyond what this sweep read this cycle"
            )
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


# ── PAGINATION ──────────────────────────────────────────────────────
#
# Everything below is additive: sweep()/observe() above are completely
# unchanged, still single-page, still the default. This is a second,
# parallel path a caller opts into by naming `max_pages > 1` -- per
# `mouth_common.py`'s own docstring, which sanctions exactly this
# ("if a future source needs a different shape ... copy-and-adapt
# again rather than bending this module to fit"). No code in
# `mouth_common.py` is modified.


def _extract_page_meta(raw: bytes) -> tuple[object, Optional[int]]:
    """Best-effort read of TED's own `iterationNextToken` and
    `totalNoticeCount` fields from one page's raw response, for
    pagination-advancement detection and informational reporting only.

    Never raises and never used to decide whether a page's NOTICES are
    trustworthy -- `parse_items()`, called separately on the same
    bytes, is what surfaces a proper `FetchError` for genuinely
    malformed input. This exists only so `_pull_pages()` doesn't parse
    the same bytes twice for two different purposes inside one
    function, while still keeping `parse_items()`'s own contract
    (returns `tuple[dict, ...]`, nothing else) unchanged for every
    existing caller and test.
    """
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError, RecursionError):
        return None, None
    if not isinstance(payload, dict):
        return None, None
    token = payload.get("iterationNextToken")
    total = payload.get("totalNoticeCount")
    if not isinstance(total, int):
        total = None
    return token, total


def _pull_pages(
    max_pages: int,
    fetch_page_fn: Callable[[int], bytes],
    page_size: int = _REQUEST_LIMIT,
) -> tuple[list[dict], int, bool, Optional[str], int, str, Optional[int]]:
    """The paginated retrieval core: stitch, dedupe, detect when to
    stop. Performs no network I/O and enforces no budget itself --
    `fetch_page_fn(page)` is the caller's one fetch per page (in
    production, one `fetch_feed()` call, which charges the
    DiscoveryPolicy budget before its own socket opens); this function
    only decides how many times to call it and what to do with what
    comes back.

    Iterates `page` 1..max_pages (both the hard cap and the declared
    policy ceiling are already enforced by the caller before this runs
    -- see `observe_paginated()`), stopping earlier than that whenever
    any of these fire, each checked independently and each recorded as
    a distinct `stop_reason` so a caller can tell WHY the pull ended,
    not just that it did:

      - `fetch_error` / `parse_error` -- fetch_page_fn raised
        (FetchError, or CommunicationDenied -- which
        DiscoveryBudgetExhausted subclasses, so a mid-pull budget
        exhaustion lands here too) or parse_items() raised on a page
        that DID fetch. `partial=True`; everything collected on prior
        pages is still returned, never discarded.
      - `repeating_page` -- this page's publication-number set is
        identical to a page already seen this pull. A defensive check
        against a server that starts answering the same page twice,
        independent of any token.
      - `non_advancing_token` -- this page's `iterationNextToken`
        equals the PREVIOUS page's token, and neither is None. Kept
        defensively even though live TED (as of 2026-09-01) was never
        observed to populate this field at all for this query shape --
        see MAX_PAGES_HARD_CAP's own comment above.
      - `empty_page` -- zero notices on a page that fetched and parsed
        fine. A legitimate natural end, not a failure.
      - `no_new_items` -- every notice on this page was already seen on
        an earlier page (all duplicates). Another non-advancing
        signal, distinct from `repeating_page` (that catches an
        IDENTICAL set; this catches a page whose set differs but
        contributes nothing new -- e.g. a shuffled reorder of already-
        seen items).
      - `short_page_natural_end` -- fewer notices returned than
        `_REQUEST_LIMIT` requested. TED's own signal that this was the
        last real page (verified live: `page=29,limit=250` against
        `totalNoticeCount=7140` returned exactly 140, the true
        remainder -- not 250 padded with anything).
      - `page_ceiling_reached` -- `max_pages` pages were all fetched
        successfully with none of the above firing on the last one.
        More data likely exists beyond what was authorized/possible to
        read this pull.

    Returns `(items, pages_fetched, partial, error_message,
    duplicates_collapsed, stop_reason, reported_total_notice_count)`.
    `partial` here reflects only a fetch/parse FAILURE mid-pull --
    `observe_paginated()` additionally treats `page_ceiling_reached` as
    partial, since that distinction (authorized-but-incomplete vs.
    failed) matters to a caller deciding whether to retry.
    """
    seen_keys: set[str] = set()
    all_items: list[dict] = []
    duplicates = 0
    prior_pub_sets: list[frozenset] = []
    prev_token: object = None
    reported_total: Optional[int] = None
    pages_fetched = 0
    partial = False
    error_message: Optional[str] = None
    stop_reason = "natural_end"

    for page_num in range(1, max_pages + 1):
        try:
            raw = fetch_page_fn(page_num)
        except (FetchError, CommunicationDenied) as exc:
            partial = True
            error_message = str(exc)
            stop_reason = "fetch_error"
            break

        try:
            page_items = parse_items(raw)
        except FetchError as exc:
            partial = True
            error_message = str(exc)
            stop_reason = "parse_error"
            break

        token, total = _extract_page_meta(raw)
        if reported_total is None and total is not None:
            reported_total = total
        pages_fetched += 1

        pub_set = frozenset(i["key"] for i in page_items)
        if pub_set and pub_set in prior_pub_sets:
            stop_reason = "repeating_page"
            break
        prior_pub_sets.append(pub_set)

        non_advancing_token = token is not None and token == prev_token
        prev_token = token

        new_count = 0
        for item in page_items:
            if item["key"] in seen_keys:
                duplicates += 1
                continue
            seen_keys.add(item["key"])
            all_items.append(item)
            new_count += 1

        if non_advancing_token:
            stop_reason = "non_advancing_token"
            break
        if not page_items:
            stop_reason = "empty_page"
            break
        if new_count == 0:
            stop_reason = "no_new_items"
            break
        if len(page_items) < page_size:
            stop_reason = "short_page_natural_end"
            break
    else:
        stop_reason = "page_ceiling_reached"

    return (all_items, pages_fetched, partial, error_message, duplicates,
            stop_reason, reported_total)


def _default_paginated_policy(max_pages: int) -> DiscoveryPolicy:
    """A second, independently-declared DiscoveryPolicy for multi-page
    pulls -- not the module-level DISCOVERY_POLICY, which stays the
    single-page default so every existing caller/test referencing
    DISCOVERY_POLICY directly sees no behaviour change.

    `max_queries` is set to exactly `max_pages`: the policy's budget IS
    the declared page ceiling, per this function's whole reason for
    existing -- "how many pages" must be a bounded, authorized decision
    a caller states up front, not an open-ended loop that happens to
    stop whenever `DiscoveryBudgetExhausted` fires.
    """
    return DiscoveryPolicy(
        objective=DISCOVERY_POLICY.objective + f", paginated up to {max_pages} pages",
        requested_scope=DISCOVERY_POLICY.requested_scope,
        max_queries=max_pages,
    )


@dataclass(frozen=True)
class TedPaginatedObservation:
    """Same purpose as `mouth_common.MouthObservation`, plus the
    pagination accounting a single fetch has no use for. A distinct
    type rather than bolting optional fields onto `MouthObservation`
    that only this path populates -- `mouth_common.py`'s own docstring
    sanctions building a second, adapted shape for a paginated source."""

    mouth_id: str
    observed_at: str
    status: str  # FIRST_SEEN | UNCHANGED | CHANGED | UNAVAILABLE
    content_hash: Optional[str]
    item_count: int
    new_items: tuple[dict, ...]
    pages_requested: int
    pages_fetched: int
    partial: bool
    stop_reason: str
    duplicates_collapsed: int
    reported_total_notice_count: Optional[int]
    error: Optional[str] = None


def _load_paginated_state(state_path: Path) -> Optional[dict]:
    if not state_path.exists():
        return None
    try:
        return json.loads(state_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def observe_paginated(
    state_path: Path,
    max_pages: int = 1,
    fetch_page_fn: Optional[Callable[[int], bytes]] = None,
    policy: Optional[DiscoveryPolicy] = None,
    now: Optional[datetime] = None,
) -> TedPaginatedObservation:
    """Multi-page observation cycle. `max_pages=1` (the default)
    behaves like a single fetch -- more pages are an explicit caller
    choice, never the default this module reaches for on its own.

    Every page is a separate `fetch_feed()` call in the production
    path (the default `fetch_page_fn`), so every page independently
    charges the DiscoveryPolicy budget before its own socket opens --
    this function adds no second, ungated path around that control
    plane; it just calls the gated function more than once.

    `max_pages` is bounded twice, independently, both checked BEFORE
    any fetch happens (never discovered mid-pull by a page 6 failure):

      1. It must not exceed `MAX_PAGES_HARD_CAP` -- a hard ceiling this
         process enforces regardless of what any policy authorizes.
      2. The active DiscoveryPolicy's own `max_queries` must be >=
         `max_pages` -- the declared, authorized page ceiling. Passing
         a `policy` whose budget is smaller than what was asked for is
         refused outright rather than silently truncated or left to
         fail via `DiscoveryBudgetExhausted` on some later page.

    `fetch_page_fn(page: int) -> bytes` is injected in every test in
    `foundation/tests/test_mouth_ted.py` -- same discipline as
    `observe()`'s `fetch_fn`, generalised to take the page number the
    caller needs to embed in the request. When None, the default path
    issues `fetch_feed(..., json_body={..., "page": page})` against
    the live TED API's own `page` parameter -- see MAX_PAGES_HARD_CAP's
    comment above for what was verified live about it.

    A mid-sequence fetch/parse failure (including
    `DiscoveryBudgetExhausted`, a `CommunicationDenied` subclass)
    returns whatever pages completed before it, `partial=True`, and
    `error` naming what happened -- never a silently short result.
    Hitting the declared/hard ceiling before a natural end is also
    `partial=True`: more data likely exists beyond what this call was
    authorized to read. A partial result is never written as the new
    state baseline (see the write-guard below) -- a truncated pull
    must not be allowed to look, to the NEXT cycle's diff, like "the
    complete picture, unchanged".
    """
    if max_pages < 1:
        raise ValueError(f"max_pages must be >= 1, got {max_pages}")
    if max_pages > MAX_PAGES_HARD_CAP:
        raise ValueError(
            f"max_pages={max_pages} exceeds MAX_PAGES_HARD_CAP "
            f"({MAX_PAGES_HARD_CAP}) -- an unbounded pull against a "
            f"remote server that controls its own pagination is a "
            f"denial-of-service on this process, not a real safety "
            f"margin. Request fewer pages."
        )
    active_policy = policy or _default_paginated_policy(max_pages)
    if active_policy.max_queries < max_pages:
        raise ValueError(
            f"policy.max_queries ({active_policy.max_queries}) is below "
            f"max_pages requested ({max_pages}) -- the DiscoveryPolicy's "
            f"max_queries IS the authorized page ceiling for this "
            f"function; declare a policy whose budget actually covers "
            f"the pages being requested"
        )

    def _default_fetch_page(page: int) -> bytes:
        return fetch_feed(
            FEED_URL, policy=active_policy,
            json_body={
                "query": EXPERT_QUERY,
                "fields": list(REQUEST_FIELDS),
                "limit": _REQUEST_LIMIT,
                "page": page,
            },
        )

    fetch_page = fetch_page_fn or _default_fetch_page
    observed_at = (now or datetime.now(timezone.utc)).isoformat()

    (all_items, pages_fetched, fetch_partial, error_message, duplicates,
     stop_reason, reported_total) = _pull_pages(max_pages, fetch_page)

    if pages_fetched == 0:
        return TedPaginatedObservation(
            mouth_id=MOUTH_ID, observed_at=observed_at, status="UNAVAILABLE",
            content_hash=None, item_count=0, new_items=(),
            pages_requested=max_pages, pages_fetched=0, partial=True,
            stop_reason=stop_reason, duplicates_collapsed=0,
            reported_total_notice_count=reported_total, error=error_message,
        )

    items = tuple(all_items)
    content_hash = compute_state_hash(items)
    prior = _load_paginated_state(state_path)

    if prior is None:
        status = "FIRST_SEEN"
        new_items = items
    elif prior.get("content_hash") == content_hash:
        status = "UNCHANGED"
        new_items = ()
    else:
        status = "CHANGED"
        prior_keys = set(prior.get("keys", ()))
        new_items = tuple(i for i in items if i["key"] not in prior_keys)

    partial = fetch_partial or stop_reason == "page_ceiling_reached"

    # A partial pull is never persisted as the new baseline -- doing so
    # would let a truncated result masquerade as "the complete picture"
    # for the NEXT cycle's diff, the same silent-short-set failure this
    # function exists to prevent, just deferred one cycle instead of
    # surfacing immediately.
    if not partial and status in ("FIRST_SEEN", "CHANGED"):
        state_path.write_text(json.dumps({
            "content_hash": content_hash,
            "keys": sorted(i["key"] for i in items),
            "observed_at": observed_at,
            "item_count": len(items),
        }))

    return TedPaginatedObservation(
        mouth_id=MOUTH_ID, observed_at=observed_at, status=status,
        content_hash=content_hash, item_count=len(items), new_items=new_items,
        pages_requested=max_pages, pages_fetched=pages_fetched, partial=partial,
        stop_reason=stop_reason, duplicates_collapsed=duplicates,
        reported_total_notice_count=reported_total, error=error_message,
    )


def sweep_paginated(
    state_dir: Path,
    max_pages: int = 1,
    fetch_page_fn: Optional[Callable[[int], bytes]] = None,
    policy: Optional[DiscoveryPolicy] = None,
    now: Optional[datetime] = None,
) -> TedRadarSweep:
    """Multi-page counterpart to sweep(): observe_paginated() -> signal
    -> report. Same TedRadarSweep report shape sweep() returns, with
    the pagination fields populated for real instead of left at their
    single-page defaults. Uses its own state file
    (`{MOUTH_ID}_paginated.json`), distinct from sweep()'s
    (`{MOUTH_ID}.json`) -- a 1-page and an N-page pull of the same feed
    have different item sets by construction, and sharing one state
    file between them would make switching page counts look like a
    spurious CHANGED (or a false UNCHANGED) on the next run of whichever
    path runs second.
    """
    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / f"{MOUTH_ID}_paginated.json"
    observation = observe_paginated(
        state_path, max_pages=max_pages, fetch_page_fn=fetch_page_fn,
        policy=policy, now=now,
    )
    signals = tuple(ted_signal(item, now=now) for item in observation.new_items)
    targets = tuple(sorted({s.target for s in signals}))
    return TedRadarSweep(
        status=observation.status,
        fetched_count=observation.item_count,
        error=observation.error,
        signals=signals,
        targets=targets,
        pages_requested=observation.pages_requested,
        pages_fetched=observation.pages_fetched,
        partial=observation.partial,
        stop_reason=observation.stop_reason,
    )
