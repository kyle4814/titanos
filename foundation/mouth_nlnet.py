"""
Mouth: NLnet / NGI Zero — the first genuinely WINNABLE grant source for a solo
operator + automation.

Why this one, when grants.gov and gov tenders don't fit: NLnet's NGI Zero funds
are **open to individuals worldwide** (no US-entity wall, no corporate-reference
wall), give **€5,000–€50,000 R&D grants** on **rolling calls**, and fund
**open-source internet/security/privacy technology** — exactly the kind of thing
the system can help *build*. Verified live from nlnet.nl (2026-09-05): "Small
and medium-sized R&D grants between 5.000 and 50.000 euro ... Available to both
individuals and organisations."

This reads the public themes page (static HTML, not JS-gated, no WAF) through
the gated socket and extracts the next open-call deadline. Never fabricates: if
the deadline can't be parsed it returns None, and the caller treats that as
UNKNOWN, never a guess.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Callable, Optional

from foundation.mouth_common import fetch_feed
from foundation.discovery_authorization import DiscoveryPolicy

__all__ = ["NlnetCall", "fetch_open_call", "parse_deadline", "FEED_URL",
           "DISCOVERY_POLICY", "APPLY_URL", "GRANT_RANGE"]

FEED_URL = "https://nlnet.nl/themes/"
APPLY_URL = "https://nlnet.nl/propose/"
GRANT_RANGE = "€5,000–€50,000"  # verified quote from nlnet.nl/NGI0/

DISCOVERY_POLICY = DiscoveryPolicy(
    objective=("read NLnet's public themes page to extract the next NGI Zero "
               "open-call deadline for a globally-eligible grant opportunity"),
    requested_scope="READ_URL",
)

_MONTHS = {m.lower(): i for i, m in enumerate(
    ["", "January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"])}

# "Next deadline November 3. 2026" / "Next deadline November 3, 2026"
_DEADLINE_RE = re.compile(
    r"deadline\s+([A-Za-z]+)\s+(\d{1,2})[.,]?\s+(\d{4})", re.IGNORECASE)


def parse_deadline(text: str) -> Optional[date]:
    """The next open-call deadline as a date, or None if not present/parseable
    (UNKNOWN — never guessed)."""
    m = _DEADLINE_RE.search(text)
    if not m:
        return None
    month = _MONTHS.get(m.group(1).lower())
    if not month:
        return None
    try:
        return date(int(m.group(3)), month, int(m.group(2)))
    except ValueError:
        return None


@dataclass(frozen=True)
class NlnetCall:
    deadline: Optional[date]      # None => UNKNOWN, check the site
    grant_range: str
    apply_url: str
    eligibility: str


def fetch_open_call(fetch_fn: Optional[Callable[[], bytes]] = None) -> NlnetCall:
    """Fetch the themes page and return the current open call. `fetch_fn` is
    injected in tests — no test touches the network."""
    fetch = fetch_fn or (lambda: fetch_feed(FEED_URL, policy=DISCOVERY_POLICY))
    text = fetch().decode("utf-8", "replace")
    return NlnetCall(
        deadline=parse_deadline(text),
        grant_range=GRANT_RANGE,
        apply_url=APPLY_URL,
        eligibility="Open worldwide to individuals and organisations "
                    "(no US-entity or corporate-reference wall).",
    )
