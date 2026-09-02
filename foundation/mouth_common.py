"""Shared shape extracted from two real mouths (`mouth_pypi.py`,
`mouth_github_releases.py`) after comparing them line-by-line, per the
Inspector Swarm directive's own replication test: `fetch_feed()`,
`compute_state_hash()`, `MouthObservation`, `_load_state()`, and
`observe()`'s control flow were byte-for-byte duplicated across both —
not "philosophically similar," not speculative future-proofing. This is
that duplication, extracted once, parameterized by the one thing that
was genuinely source-specific: how to parse the fetched bytes into a
tuple of `{"key": ..., ...}` dicts.

WHAT THIS IS NOT: not a source registry, not an agent framework, not a
scheduler — the existing `foundation/cron_pulse.py` cron entry remains
the only clock. A third mouth reuses this module only if its `observe()`
shape genuinely matches (fetch bytes -> parse to keyed items -> hash ->
compare -> receipt); if a future source needs a different shape (e.g. a
paginated API, not a single feed fetch), copy-and-adapt again rather
than bending this module to fit — same discipline this module itself
was built under.
"""
from __future__ import annotations

import hashlib
import json
import urllib.error
import ipaddress
import socket
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Mapping
from typing import Callable, Optional

# Imported at module level so the gate's own exception type is part of
# this module's contract rather than something a caller discovers only
# at call time. discovery_authorization is imported lazily inside
# fetch_feed() to keep the dependency one-directional.
from foundation.communication_gate import CommunicationDenied

__all__ = [
    "FetchError",
    "CommunicationDenied",
    "MouthObservation",
    "fetch_feed",
    "MAX_FEED_BYTES",
    "compute_state_hash",
    "observe",
    "MouthLogContinuity",
    "read_mouth_log_continuity",
]

DEFAULT_TIMEOUT_SECONDS = 10

# Hard ceiling on a single feed response. The two real feeds are a few
# kilobytes; 5 MB is ~1000x headroom while still bounding memory. See
# fetch_feed()'s docstring for why a timeout alone does not bound this.
MAX_FEED_BYTES = 5 * 1024 * 1024
# Bounds the REQUEST body. MAX_FEED_BYTES bounds the response; an
# unbounded request is the same class of problem in the other direction.
MAX_REQUEST_BYTES = 64 * 1024
DEFAULT_USER_AGENT = "titanos-cosmic-library-mouth/1 (+https://github.com/kyle4814/titanos)"

# Same cadence/threshold policy as foundation/sentinel.py's read_pulse_continuity —
# both clocks are hourly cron entries. Not shared code (different payload
# shapes: Finding vs MouthObservation/dependency-pressure records); same
# policy number, independently declared.
LOG_MAX_RECORDS = 20
LOG_STALE_AFTER_SECONDS = 3 * 3600


class FetchError(Exception):
    """The feed could not be retrieved or parsed this attempt. Bounded,
    expected, non-fatal — callers must treat this as UNAVAILABLE, never
    as 'zero items' or 'no change'."""


# ── SSRF GUARD ────────────────────────────────────────────────────────
#
# THE DEFECT THIS CLOSES (blue-team pass 006, confirmed statically):
# `url` is caller-supplied and was passed straight into
# `urllib.request.Request` with no validation of any kind. Grepping the
# whole control plane -- mouth_common, discovery_authorization,
# communication_gate -- for a scheme, host or IP check returned nothing.
# So `file:///etc/passwd`, `http://169.254.169.254/` (cloud metadata),
# `http://localhost:8080/`, and every RFC1918 address were reachable by
# any validly-authorized policy.
#
# Authorization answered "may this caller fetch?" and nothing answered
# "fetch WHAT?". Adding POST made that worse: a request that can carry a
# body to an internal address is a considerably more useful weapon than
# one that can only GET.
#
# WHAT THIS DOES NOT DO. It resolves the hostname and rejects private
# destinations, but resolution here and connection inside urllib are two
# separate lookups -- a DNS entry that changes between them (rebinding)
# is not caught. Closing that needs connection-level pinning, which
# urllib does not expose. This raises the cost of the attack
# substantially; it does not reduce it to zero, and saying so is the
# point.
_ALLOWED_SCHEMES = frozenset({"https"})


def _reject_unsafe_url(url: str) -> None:
    """Raise CommunicationDenied unless `url` is a public https endpoint."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise CommunicationDenied(
            f"refusing to fetch {url!r}: scheme {parsed.scheme!r} is not "
            f"allowed. Only {sorted(_ALLOWED_SCHEMES)} may be fetched -- "
            f"file://, ftp:// and plaintext http:// are refused outright"
        )
    host = parsed.hostname
    if not host:
        raise CommunicationDenied(f"refusing to fetch {url!r}: no host")
    try:
        infos = socket.getaddrinfo(host, parsed.port or 443,
                                   proto=socket.IPPROTO_TCP)
    except OSError as exc:
        raise CommunicationDenied(
            f"refusing to fetch {url!r}: host {host!r} did not resolve "
            f"({exc.__class__.__name__}); an unresolvable host cannot be "
            f"shown to be public"
        ) from exc
    for info in infos:
        addr = ipaddress.ip_address(info[4][0])
        if (addr.is_private or addr.is_loopback or addr.is_link_local
                or addr.is_reserved or addr.is_multicast
                or addr.is_unspecified):
            raise CommunicationDenied(
                f"refusing to fetch {url!r}: host {host!r} resolves to "
                f"{addr}, which is not a public address. Cloud metadata "
                f"services, loopback and RFC1918 ranges are refused -- "
                f"this fetcher exists to read public feeds"
            )


def fetch_feed(url: str, timeout: int = DEFAULT_TIMEOUT_SECONDS,
                user_agent: str = DEFAULT_USER_AGENT,
                *, policy: "DiscoveryPolicy | None" = None,
                json_body: "Mapping[str, Any] | None" = None,
                form_body: "Mapping[str, Any] | None" = None) -> bytes:
    """One GET request, real network I/O, no retry loop here — the
    caller's own schedule (cron) is the backoff policy.

    THE CONTROL PLANE IS ENFORCED HERE, NOT ABOVE HERE

    `policy` is required and has no usable default. This function is the
    only place in the repository that opens a socket, so it is the only
    place where the authorization check cannot be routed around: a
    caller that reaches for a mouth, an adapter, or this function
    directly hits the same gate. Enforcing in a CLI or an orchestrator
    instead would leave `fetch_feed(url)` as an open door beside it.

    Found by auditing the switch estate against its own claim.
    `communication_gate.py` was built, tested and armed, and
    `discovery_authorization.authorize_discovery()` describes itself as
    "the one real entry point a future discovery adapter must call
    before doing anything." Five mouths and `target_mapping` fetch. None
    of them called it. The gate had no consumer, which makes it a
    reminder rather than an enforcement point -- exactly the failure the
    switch-gate doctrine exists to prevent.

    Passing `policy=None` raises rather than defaulting to a permissive
    standing grant. A default would reintroduce the bypass in one line:
    the point is that every fetch names a concrete objective and a
    budget, which is what the standing authorization actually requires.

    THE BYTE CAP (retained from the 2026-08-28 adversarial review)

    Hard byte cap added after adversarial review. The previous
    `response.read()` was unbounded: `timeout` bounds a single stalled
    socket operation, NOT total transfer size or total transfer time, so
    a source that trickles bytes just under the idle timeout can stream
    indefinitely, and any large response is read fully into memory
    regardless of size. TLS certificate validation (urllib's default)
    makes a classic MITM hard but does nothing to bound what a
    legitimate-but-compromised endpoint returns. These are release feeds
    measured in kilobytes; a cap of `MAX_FEED_BYTES` is far above any
    honest response and turns a memory-exhaustion vector into an
    ordinary, receipted `FetchError` -> `UNAVAILABLE`, which `observe()`
    already handles without touching prior state.

    Reads one byte past the cap specifically so exceeding it is
    detectable rather than silently truncating a feed into a corrupt
    parse -- a truncated feed would look like "items disappeared," which
    `observe()` could otherwise record as a real CHANGED observation.
    """
    from foundation.discovery_authorization import (
        DiscoveryPolicy, authorize_discovery, spend_query)
    if policy is None:
        raise CommunicationDenied(
            f"refusing to fetch {url!r}: no DiscoveryPolicy supplied. "
            f"Network access in this repository is gated by "
            f"foundation/communication_gate.py via authorize_discovery(); "
            f"a caller must name a concrete objective and budget. There is "
            f"deliberately no permissive default -- see this function's "
            f"docstring."
        )
    if not isinstance(policy, DiscoveryPolicy):
        raise CommunicationDenied(
            f"refusing to fetch {url!r}: policy must be a DiscoveryPolicy, "
            f"not {type(policy).__name__} -- a caller cannot substitute an "
            f"object that merely claims to be authorized"
        )
    # Raises UnboundedDiscoveryObjective or CommunicationDenied. Never
    # returns False silently, so "did not check" cannot be mistaken for
    # "checked and it was fine".
    authorize_discovery(policy)
    # And charge the request against the policy's declared budget BEFORE
    # the socket opens, so an exhausted budget costs nothing. Until
    # 2026-09-01 `max_queries` was a decorative field read by no code
    # anywhere, while this docstring told callers a policy names a
    # budget -- the gate advertised a limit it did not have.
    spend_query(policy)
    # A DECLARED JSON BODY, NOT AN ARBITRARY REQUEST BUILDER.
    #
    # EU TED publishes ~397,000 open notices under CC BY 4.0, needs no key,
    # and answers this fetcher's honest User-Agent -- and its search
    # endpoint is POST-only (GET returns 405, verified live 2026-09-01).
    # So the largest lawful source of real demand this system has found was
    # unreachable because of a constraint we imposed on ourselves, not one
    # anybody imposed on us.
    #
    # This stays deliberately narrow rather than becoming a general HTTP
    # client, because this function is the only socket in the repository
    # and every widening of it widens the whole attack surface:
    #
    #   - the body must be a mapping, serialised to JSON here. A caller
    #     cannot hand over raw bytes, so it cannot smuggle a different
    #     content type or a chunked/multipart shape through this door.
    #   - only POST is reachable, and only by supplying a body. There is
    #     no `method` parameter, so PUT/DELETE/PATCH remain unreachable
    #     by construction rather than by validation.
    #   - the serialised body is capped. An unbounded request body is a
    #     memory and egress problem in the one direction this function's
    #     existing cap does not cover -- MAX_FEED_BYTES bounds what comes
    #     back, and bounded a request is not the same thing.
    #   - every gate above still ran first. Authorization and budget are
    #     charged before this point regardless of method, so POST is not
    #     a second path around the control plane. That is the property
    #     the tests pin.
    _reject_unsafe_url(url)
    data = None
    headers = {"User-Agent": user_agent}
    if json_body is not None and form_body is not None:
        raise CommunicationDenied(
            f"refusing to fetch {url!r}: json_body and form_body are "
            f"mutually exclusive -- a request carries one body with one "
            f"content type, and a caller that supplied both has not "
            f"decided which request it is making"
        )
    body = json_body if json_body is not None else form_body
    if body is not None:
        kind = "json_body" if json_body is not None else "form_body"
        if not isinstance(body, Mapping):
            raise CommunicationDenied(
                f"refusing to fetch {url!r}: {kind} must be a mapping, "
                f"not {type(body).__name__} -- raw bytes would let a "
                f"caller choose its own content type through the only "
                f"socket in this repository"
            )
        if json_body is not None:
            data = json.dumps(body, sort_keys=True).encode("utf-8")
            content_type = "application/json"
        else:
            # FORM-ENCODED POST -- added 2026-09-02 for one real,
            # measured reason, not for generality.
            #
            # Ireland's eTenders export endpoint (viewCFTSAction.do) is a
            # Struts-era form handler. It ignores a JSON body entirely,
            # so the 10,000-row CSV carrying 232 live security notices --
            # the largest concentration of English-language procurement
            # this project has found -- was unreachable purely because
            # this function could only serialise one content type.
            #
            # Every constraint the JSON path carries applies here
            # unchanged, deliberately: Mapping only (so a caller can
            # never hand over raw bytes and pick its own content type),
            # the same MAX_REQUEST_BYTES cap, the same READ_URL refusal
            # below, and the same authorization and budget already
            # charged before this point. There is still no `method`
            # parameter, so PUT/DELETE/PATCH remain unreachable by
            # construction.
            #
            # This widens what may be SENT, never who may send it.
            data = urllib.parse.urlencode(
                sorted((str(k), str(v)) for k, v in body.items())
            ).encode("utf-8")
            content_type = "application/x-www-form-urlencoded"
        if len(data) > MAX_REQUEST_BYTES:
            raise CommunicationDenied(
                f"refusing to fetch {url!r}: request body is {len(data)} "
                f"bytes, over MAX_REQUEST_BYTES ({MAX_REQUEST_BYTES})"
            )
        headers["Content-Type"] = content_type
        # SCOPE IS NOT DECORATIVE. Blue-team pass 006 found READ_URL and
        # READ_API were only ever checked for set-membership -- nothing
        # compared the declared scope against what the request actually
        # does, so a READ_URL policy could drive a POST with a
        # caller-controlled body. A scope that does not constrain
        # anything is a label, and this repository's whole argument is
        # that a label is not a control.
        if getattr(policy, "requested_scope", None) == "READ_URL":
            raise CommunicationDenied(
                f"refusing to fetch {url!r}: policy scope is READ_URL, "
                f"which authorises reading a URL, not sending a request "
                f"body. Declare READ_API to POST."
            )
    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read(MAX_FEED_BYTES + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise FetchError(f"could not fetch {url!r}: {exc}") from exc
    if len(payload) > MAX_FEED_BYTES:
        raise FetchError(
            f"response from {url!r} exceeds MAX_FEED_BYTES ({MAX_FEED_BYTES}) "
            f"— refusing to buffer an unbounded remote response; treated as "
            f"UNAVAILABLE, prior state left untouched"
        )
    return payload


def compute_state_hash(items: tuple[dict, ...]) -> str:
    """Deterministic hash over the item set — order-independent (keys
    sorted) so feed re-ordering alone never looks like a change."""
    canonical = sorted(item["key"] for item in items)
    payload = json.dumps(canonical, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class MouthObservation:
    mouth_id: str
    observed_at: str
    status: str  # FIRST_SEEN | UNCHANGED | CHANGED | UNAVAILABLE
    content_hash: Optional[str]
    item_count: int
    new_items: tuple[dict, ...]
    error: Optional[str] = None


def _load_state(state_path: Path) -> Optional[dict]:
    if not state_path.exists():
        return None
    try:
        return json.loads(state_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def observe(
    mouth_id: str,
    state_path: Path,
    fetch_fn: Callable[[], bytes],
    parse_fn: Callable[[bytes], tuple[dict, ...]],
    now: Optional[datetime] = None,
) -> MouthObservation:
    """Run one observation cycle: fetch, parse (source-specific), hash,
    compare, persist. `fetch_fn`/`parse_fn` are injectable so tests never
    need real network I/O. A failed fetch or parse leaves `state_path`
    untouched — the last known good baseline survives an outage."""
    observed_at = (now or datetime.now(timezone.utc)).isoformat()
    prior = _load_state(state_path)

    try:
        raw = fetch_fn()
        items = parse_fn(raw)
    except FetchError as exc:
        return MouthObservation(
            mouth_id=mouth_id, observed_at=observed_at, status="UNAVAILABLE",
            content_hash=None, item_count=0, new_items=(), error=str(exc),
        )

    content_hash = compute_state_hash(items)

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

    if status in ("FIRST_SEEN", "CHANGED"):
        state_path.write_text(json.dumps({
            "content_hash": content_hash,
            "keys": sorted(i["key"] for i in items),
            "observed_at": observed_at,
            "item_count": len(items),
        }))

    return MouthObservation(
        mouth_id=mouth_id, observed_at=observed_at, status=status,
        content_hash=content_hash, item_count=len(items), new_items=new_items,
    )


@dataclass(frozen=True)
class MouthLogContinuity:
    """Bounded, read-only view of a receipt log's tail — the same
    question `sentinel.read_pulse_continuity()` answers for
    `pulse_log.jsonl`, asked here for any jsonl receipt stream that
    records an `observed_at` (or `timestamp`) field per line: mouth
    observation logs, `dependency_pressure_log.jsonl`. `stale=True`
    means the clock that's supposed to write this log may have stopped
    — check is never automated into action, same as every other
    Finding-adjacent primitive in this repository."""

    available: bool
    latest_timestamp: Optional[str]
    latest_status: Optional[str]
    records_considered: int
    stale: bool
    warnings: tuple[str, ...]
    source: str


MOUTH_STATUSES = ("FIRST_SEEN", "UNCHANGED", "CHANGED", "UNAVAILABLE")


def read_mouth_log_continuity(
    log_path: Path,
    max_records: int = LOG_MAX_RECORDS,
    now: Optional[datetime] = None,
) -> MouthLogContinuity:
    """Read the tail of a jsonl receipt log and report its freshness.

    Read-only, bounded, fails soft: a missing file, an empty file, and
    malformed lines are all reported as `warnings`, never raised.
    """
    source = str(log_path)
    if not log_path.exists():
        return MouthLogContinuity(
            available=False, latest_timestamp=None, latest_status=None,
            records_considered=0,
            warnings=(f"{log_path.name} does not exist yet — this clock has never fired",),
            source=source, stale=False,
        )

    all_lines = [line for line in log_path.read_text().splitlines() if line.strip()]
    tail = all_lines[-max_records:] if max_records > 0 else []

    records: list[dict] = []
    warnings: list[str] = []
    for line in tail:
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            warnings.append(f"skipped malformed JSON line: {exc}")
            continue
        # Same fix as sentinel.py::read_pulse_continuity() -- a valid-JSON
        # non-dict line (bare number/string/array from a truncated write)
        # crashed `.get()` two lines below. Found by systemic hunt 2026-08-28.
        if not isinstance(obj, dict):
            warnings.append(f"skipped non-record JSON line (not an object): {obj!r}"[:200])
            continue
        records.append(obj)

    if not records:
        return MouthLogContinuity(
            available=True, latest_timestamp=None, latest_status=None,
            records_considered=0,
            warnings=tuple(warnings) or ("no records in the bounded window",),
            source=source, stale=False,
        )

    latest = records[-1]
    latest_timestamp = latest.get("observed_at") or latest.get("timestamp")
    latest_status = latest.get("status")

    # THE COLLAPSE THIS CLOSES (reproduced 2026-08-29, no mutation
    # required -- both worlds are ordinary shipped behaviour):
    #
    #   5 observations, all UNCHANGED  -> available=True stale=False warnings=()
    #   5 observations, all UNAVAILABLE-> available=True stale=False warnings=()
    #
    # A mouth whose every observation has failed was indistinguishable
    # from a perfectly healthy one on `available`/`stale`/`warnings` --
    # and those three are exactly the fields `.claude/commands/boot.md`
    # step 4b teaches the operator to read as "the normal state". Step 4c
    # routes this function without enumerating its states at all, so
    # nothing told the operator to also inspect `latest_status`.
    # `available` means "the log file could be read", never "the mouth is
    # available"; the name invites precisely that misreading.
    #
    # NO THRESHOLD IS CHOSEN HERE, deliberately. This looks only at the
    # single most recent observation -- no window, no rate, no tolerance.
    # The neighbouring question of how much INTERMITTENT failure deserves
    # an alarm is a human judgment and stays open as HUMAN_DECISIONS item
    # 15; it is not smuggled in here as a constant. A mouth that failed
    # and recovered still returns silently from this reader, which is the
    # same deliberate noise-suppression choice
    # `sentinel.py::check_mouth_health()`'s own tests already encode.
    if latest_status == "UNAVAILABLE":
        warnings.append(
            "most recent observation FAILED (status=UNAVAILABLE) -- "
            "`available=True` here means the log was readable, not that "
            "the mouth is reachable"
        )

    stale = False
    if latest_timestamp:
        try:
            parsed = datetime.fromisoformat(latest_timestamp)
        except (ValueError, TypeError):
            parsed = None
            warnings.append(f"latest timestamp {latest_timestamp!r} could not be parsed as ISO-8601")
        if parsed is not None:
            current = now if now is not None else datetime.now(timezone.utc)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            if current.tzinfo is None:
                current = current.replace(tzinfo=timezone.utc)
            # abs(): a FUTURE-dated record must be flagged too. A one-way
            # comparison goes negative and never exceeds the threshold,
            # so a log stamped ahead of now reads as permanently fresh --
            # exactly what a stopped or wrong clock produces.
            age_seconds = abs((current - parsed).total_seconds())
            if age_seconds > LOG_STALE_AFTER_SECONDS:
                stale = True
                warnings.append(
                    f"log appears stale — last record {age_seconds / 3600:.1f}h ago "
                    f"(threshold {LOG_STALE_AFTER_SECONDS / 3600:.0f}h)"
                )

    return MouthLogContinuity(
        available=True, latest_timestamp=latest_timestamp, latest_status=latest_status,
        records_considered=len(records), warnings=tuple(warnings), source=source,
        stale=stale,
    )
