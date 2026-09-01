"""Make contract values comparable across currencies, honestly.

WHAT THIS IS NOT

This is a RANKING AID, not a financial calculation. It exists to answer
"which of these notices is roughly the biggest deal", nothing more.
Nobody should price a bid, book a receivable, or make a payment decision
off a number this module produces. The rates are a daily reference
snapshot from a central bank, not a tradable rate, not a spot rate, and
this module does not attempt to be either.

THE PROBLEM THIS CLOSES

`foundation/mouth_ted.py` extracts real `amount`/`currency` pairs from
TED notices -- 789 of 1,250 carry one, in EUR, DKK, SEK, NOK, HUF, RON
and others (see mouth_ted.py's own "REAL DISTRIBUTION" notes, which are
explicit that it "does not invent" a rate and reports every figure in
its native currency). Sorting those figures numerically without
converting them first is not a ranking, it is a coin flip that happens
to look authoritative: HUF 900,000,000 sorts above EUR 162,000,000 while
being worth roughly a fortieth as much.

THE SOURCE

The European Central Bank's daily reference-rate feed --
`https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml` -- is a
public XML feed, no key, no auth, intended for machine consumption
(it's the ECB's own published "euro foreign exchange reference rates"
feed, linked from ecb.europa.eu/stats/policy_and_exchange_rates).
Verified live 2026-09-01 with this repository's real User-Agent
(`foundation.mouth_common.DEFAULT_USER_AGENT`, no spoofing):
`robots.txt` on `www.ecb.europa.eu` has no `Disallow` rule matching
`/stats/eurofxref/` (its disallow list is all HTML content pages and a
few media directories; `Crawl-delay: 5` is honoured by fetching once
per run into a cache, never per-row -- see `_load_rate_table()`). The
feed itself returned HTTP 200 and parsed as well-formed XML with one
`<Cube time='YYYY-MM-DD'>` block of `<Cube currency='XXX' rate='N'/>`
children, EUR implicit as the 1.0 base (the ECB never emits an EUR
entry -- it IS the unit every other rate is quoted against).

WHAT EVERY CONVERTED FIGURE CARRIES

`to_eur()` never returns a bare number. It returns a `Conversion` that
keeps the ORIGINAL amount and currency next to the converted EUR value,
plus the exact rate used and the date that rate was published for. A
converted number without its rate and date is not auditable, and this
repository does not produce unauditable numbers (same discipline as
`mouth_ted.py`'s `value_detail` and `foundation/checkpoint.py`'s
content-hashed records). The original is never replaced, only
accompanied.

WHAT THIS REFUSES TO DO

- Never invents a rate. A currency absent from the table (e.g. it
  floated out of the ECB's ~30-currency reference set, or the feed
  itself failed) converts to `Conversion.unknown()` -- `eur_amount is
  None`, `status == STATUS_UNKNOWN` -- never a guess, never a silent
  pass-through of the raw number as if it were already EUR.
- Never hardcodes a rate as a fallback. A hardcoded rate is a number
  that will silently be wrong forever the moment real rates move; this
  module has exactly one source of rates, the fetched table, and no
  second path that produces a number.
- A malformed feed (bad XML, missing `Cube time`, empty rate table) is a
  structured `RateTableError`, caught at parse time -- never a crash
  that takes the caller down with it, and never silently treated as
  "zero rates available, proceed anyway".

STALENESS

The rate table has one publication date (`RateTable.date`, the
`Cube time='...'` attribute -- the ECB publishes once per TARGET
business day, around 16:00 CET). `RateTable.is_stale(today)` is true
once the table is more than `STALE_AFTER_DAYS` calendar days older than
`today` -- wide enough to cover an ordinary weekend/holiday gap without
flagging every Monday run as stale, narrow enough that a genuinely
abandoned cache (fetch has been failing silently for a week) gets
caught. A stale table is still USABLE for ranking -- the module does
not refuse to convert -- but `Conversion.stale` and `RateTable.is_stale`
are there precisely so a caller can print "as of 2026-08-24 (stale)"
next to the figure instead of presenting a week-old rate as today's.

CACHING

`load_rate_table()` fetches through `foundation.mouth_common.fetch_feed`
-- the only socket this repository opens, SSRF-gated, budget-gated by a
`DiscoveryPolicy` -- and caches the parsed table to disk with the same
atomic temp-file-then-`os.replace` discipline `foundation/checkpoint.py`
uses for its own durable writes, so a crash mid-write can never leave a
reader looking at a half-written cache file. A ranking run over
hundreds of rows calls `load_rate_table()` once, not once per row.
"""
from __future__ import annotations

import json
import math
import os
import tempfile
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Mapping, Optional
from xml.etree import ElementTree

from foundation.mouth_common import FetchError, fetch_feed
from foundation.discovery_authorization import DiscoveryPolicy

__all__ = [
    "RateTableError",
    "RateTable",
    "Conversion",
    "STATUS_OK",
    "STATUS_UNKNOWN",
    "STALE_AFTER_DAYS",
    "FEED_URL",
    "EUR",
    "DISCOVERY_POLICY",
    "parse_rate_table",
    "load_rate_table",
    "to_eur",
    "default_cache_path",
]

FEED_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
EUR = "EUR"

# The ECB publishes on TARGET business days -- weekends and a handful of
# bank holidays have no new table. 4 days covers an ordinary long
# weekend without flagging a normal Monday-morning run as stale, while
# still catching "the cache is a week old because fetches have been
# silently failing".
STALE_AFTER_DAYS = 4

STATUS_OK = "OK"
STATUS_UNKNOWN = "UNKNOWN"

DISCOVERY_POLICY = DiscoveryPolicy(
    objective="observe the ECB daily euro foreign exchange reference rates feed",
    requested_scope="READ_URL",
)


class RateTableError(Exception):
    """The rate table could not be fetched or parsed this attempt.
    Bounded, expected, non-fatal -- callers must treat this as
    UNAVAILABLE, never as 'zero rates' or 'use the last table forever'
    without saying so."""


@dataclass(frozen=True)
class RateTable:
    """One EUR-based reference rate table as published for `date_str`.

    `rates` maps ISO 4217 currency code -> "how many units of that
    currency equal 1 EUR" (the ECB's own convention). EUR itself is
    never a key -- it is the implicit 1.0 base -- `to_eur()` special-
    cases it rather than requiring every table to carry a redundant
    entry that could theoretically be tampered to something other than
    1.0.
    """

    date_str: str  # ISO date, e.g. "2026-08-31" -- the ECB's own Cube time
    rates: Mapping[str, float]
    fetched_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def is_stale(self, today: Optional[date] = None) -> bool:
        """True once this table is older than STALE_AFTER_DAYS relative
        to `today` (defaults to real today, UTC). A stale table is not
        refused -- it is flagged, see this module's STALENESS note."""
        ref = today or datetime.now(timezone.utc).date()
        try:
            table_date = date.fromisoformat(self.date_str)
        except ValueError:
            # A table whose own date doesn't parse cannot be dated at
            # all -- treat as stale rather than pretending freshness.
            return True
        return (ref - table_date).days > STALE_AFTER_DAYS

    def to_dict(self) -> dict:
        return {"date_str": self.date_str, "rates": dict(self.rates),
                "fetched_at": self.fetched_at}

    @classmethod
    def from_dict(cls, obj: Mapping) -> "RateTable":
        return cls(date_str=obj["date_str"], rates=dict(obj["rates"]),
                    fetched_at=obj.get("fetched_at", ""))


@dataclass(frozen=True)
class Conversion:
    """One converted figure -- and everything needed to audit it.

    The original amount/currency are ALWAYS present alongside the
    converted one; nothing here ever replaces the original. When
    `status == STATUS_UNKNOWN`, `eur_amount` and `rate_used` are both
    `None` -- an unconvertible value must be visibly unconvertible, not
    a guess and not a silent pass-through of `original_amount` relabeled
    as EUR.
    """

    original_amount: float
    original_currency: str
    status: str
    eur_amount: Optional[float]
    rate_used: Optional[float]
    rate_date: Optional[str]
    stale: bool

    def to_dict(self) -> dict:
        return {
            "original_amount": self.original_amount,
            "original_currency": self.original_currency,
            "status": self.status,
            "eur_amount": self.eur_amount,
            "rate_used": self.rate_used,
            "rate_date": self.rate_date,
            "stale": self.stale,
        }

    @classmethod
    def unknown(cls, amount: float, currency: str) -> "Conversion":
        return cls(original_amount=amount, original_currency=currency,
                    status=STATUS_UNKNOWN, eur_amount=None, rate_used=None,
                    rate_date=None, stale=False)


def _usable_rate(rate: object) -> bool:
    """True only for a rate that can safely divide a contract value.

    `rate <= 0` is not enough, and blue-team pass 014 proved it on the real
    parser. Every comparison involving NaN is False, so `NaN <= 0` is False
    and NaN sails through; Infinity is genuinely greater than zero and also
    passes. Both were accepted from a crafted ECB feed:

        rate NaN       -> status=OK, eur_amount=nan
        rate Infinity  -> status=OK, eur_amount=0.0

    The second is the worse one. A poisoned Infinity silently turns a
    million-euro contract into zero, which sorts quietly to the bottom of
    the operator's list rather than announcing itself. NaN at least looks
    wrong; a zero looks like a small contract.

    `math.isfinite` rejects NaN and both infinities in one check, and the
    type check keeps a string rate from a corrupted cache out of the
    arithmetic entirely -- that path raised an unhandled TypeError, which
    contradicts this module's own never-crash contract.
    """
    if not isinstance(rate, (int, float)) or isinstance(rate, bool):
        return False
    return math.isfinite(rate) and rate > 0


def parse_rate_table(xml_bytes: bytes) -> RateTable:
    """Parse the ECB daily feed's real shape:
    `<Cube><Cube time='...'><Cube currency='X' rate='N'/>...</Cube></Cube>`.

    Raises RateTableError on anything that doesn't match -- malformed
    XML, a missing `time` attribute, or a table with zero currencies
    (an empty table is indistinguishable from "the feed shape changed
    under us" and must not be treated as "EUR is the only currency
    today")."""
    try:
        root = ElementTree.fromstring(xml_bytes)
    except ElementTree.ParseError as exc:
        raise RateTableError(f"rate feed did not parse as XML: {exc}") from exc

    # Namespace-agnostic: match any element whose local tag is "Cube",
    # since the real feed's default namespace varies by how it's parsed.
    def _local(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]

    time_cube = None
    for elem in root.iter():
        if _local(elem.tag) == "Cube" and elem.get("time"):
            time_cube = elem
            break
    if time_cube is None:
        raise RateTableError(
            "rate feed parsed but no <Cube time='...'> block was found -- "
            "the feed's shape may have changed")

    date_str = time_cube.get("time", "").strip()
    if not date_str:
        raise RateTableError("rate feed's Cube time attribute is empty")

    rates: dict[str, float] = {}
    for child in time_cube:
        if _local(child.tag) != "Cube":
            continue
        currency = (child.get("currency") or "").strip().upper()
        raw_rate = child.get("rate")
        if not currency or raw_rate is None:
            continue
        try:
            rate = float(raw_rate)
        except ValueError:
            continue
        if not _usable_rate(rate):
            continue
        rates[currency] = rate

    if not rates:
        raise RateTableError(
            "rate feed parsed and had a Cube time block, but zero usable "
            "currency rates were found inside it")

    return RateTable(date_str=date_str, rates=rates)


def default_cache_path() -> Path:
    return Path(__file__).parent / "currency_rate_cache.json"


def _read_cache(path: Path) -> Optional[RateTable]:
    if not path.exists():
        return None
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return RateTable.from_dict(obj)
    except (json.JSONDecodeError, KeyError, OSError, TypeError):
        # A corrupt or half-written cache is not a fatal condition --
        # treated as "no cache", so the caller re-fetches.
        return None


def _write_cache_atomic(path: Path, table: RateTable) -> None:
    """Same discipline as foundation/checkpoint.py's save(): write to a
    temp file in the same directory, fsync, then os.replace -- a reader
    never observes a half-written cache file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=".tmp-currency-cache-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            json.dump(table.to_dict(), tmp, sort_keys=True)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_name, path)
    except Exception:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
        raise


def load_rate_table(
    cache_path: Optional[Path] = None,
    *,
    force_refresh: bool = False,
    fetch_fn=None,
) -> RateTable:
    """Return a RateTable, fetching at most once per call and caching to
    disk so a ranking run over many rows fetches once, not per row.

    `fetch_fn` overrides the network call entirely -- tests must inject
    it and never hit the real feed (see foundation/tests/test_currency.py).

    On fetch/parse failure with an existing cache present, the cache is
    returned (it will report its own staleness via `is_stale()`) rather
    than raising -- a transient network failure should degrade to "use
    the last known table, flagged as however stale it is", not abort a
    ranking run outright. With no cache and a failed fetch, this raises
    RateTableError -- there is genuinely nothing to return.
    """
    path = cache_path or default_cache_path()
    cached = None if force_refresh else _read_cache(path)
    if cached is not None and not force_refresh:
        return cached

    fetch = fetch_fn or (lambda: fetch_feed(FEED_URL, policy=DISCOVERY_POLICY))
    try:
        raw = fetch()
        table = parse_rate_table(raw)
    except (FetchError, RateTableError) as exc:
        if cached is not None:
            return cached
        fallback = _read_cache(path)
        if fallback is not None:
            return fallback
        raise RateTableError(
            f"rate table fetch failed and no cache exists at {path}: {exc}"
        ) from exc

    _write_cache_atomic(path, table)
    return table


def to_eur(amount: float, currency: str, rates: RateTable) -> Conversion:
    """Convert `amount` in `currency` to EUR using `rates`.

    Returns a Conversion carrying the original amount/currency, the EUR
    figure, the exact rate used, the rate's publication date, and
    whether that table is stale -- see this module's docstring for why
    every field is mandatory. A currency with no entry in `rates.rates`
    (and that isn't EUR) returns `Conversion.unknown()` -- never a
    guess, never the raw amount silently relabeled as EUR.
    """
    code = (currency or "").strip().upper()
    if not code:
        return Conversion.unknown(amount, currency or "")

    stale = rates.is_stale()

    if code == EUR:
        return Conversion(
            original_amount=amount, original_currency=code,
            status=STATUS_OK, eur_amount=amount, rate_used=1.0,
            rate_date=rates.date_str, stale=stale)

    rate = rates.rates.get(code)
    if not _usable_rate(rate):
        return Conversion.unknown(amount, code)

    eur_amount = amount / rate
    return Conversion(
        original_amount=amount, original_currency=code,
        status=STATUS_OK, eur_amount=eur_amount, rate_used=rate,
        rate_date=rates.date_str, stale=stale)
