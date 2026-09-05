"""
Lead Source — extract business domains from a lead CSV to feed the lead engine.

Kyle has a large CSV of real businesses (columns like business_name, email,
website, category, suburb, state). This pulls the domains out of it so
`lead_engine` can triage them by email-security weakness and surface the hottest
(most spoofable) ones to call first.

Pure parsing — no network. It reads the operator's own lead file (his data),
extracts and normalises domains, drops free-mail providers (gmail/outlook/etc.
are not a business's own domain), and de-dupes. A `limit` keeps a batch polite:
triaging tens of thousands of domains live would be a lot of DNS lookups, so
callers take a bounded slice.
"""

from __future__ import annotations

import csv
import io
import re
from typing import Iterable, List, Optional

__all__ = ["domains_from_csv", "FREE_EMAIL_PROVIDERS"]

# Free/consumer mail hosts — an address here is NOT the business's own domain.
FREE_EMAIL_PROVIDERS = frozenset({
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com",
    "yahoo.com", "yahoo.com.au", "ymail.com", "icloud.com", "me.com",
    "bigpond.com", "bigpond.net.au", "optusnet.com.au", "iinet.net.au",
    "tpg.com.au", "aol.com", "proton.me", "protonmail.com", "gmx.com",
    "msn.com", "internode.on.net", "westnet.com.au", "dodo.com.au",
})

# Columns we'll look at, in preference order.
_WEBSITE_COLS = ("website", "url", "domain", "web", "site")
_EMAIL_COLS = ("email", "e-mail", "email_address", "contact_email")

_DOMAIN_RE = re.compile(r"^[a-z0-9.-]+\.[a-z]{2,}$")


def _norm_domain(raw: str) -> Optional[str]:
    """Normalise a website/URL/host to a bare domain, or None if not usable."""
    s = str(raw or "").strip().lower()
    if not s:
        return None
    s = re.sub(r"^https?://", "", s)
    s = re.sub(r"^www\.", "", s)
    s = s.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
    s = s.split(":", 1)[0]  # strip any port
    s = s.strip(". ")
    if not s or not _DOMAIN_RE.match(s):
        return None
    return s


def _domain_from_email(raw: str) -> Optional[str]:
    s = str(raw or "").strip().lower()
    if "@" not in s:
        return None
    dom = s.rsplit("@", 1)[1].strip()
    if dom in FREE_EMAIL_PROVIDERS:
        return None
    return _norm_domain(dom)


def _pick(fieldnames: Iterable[str], candidates) -> Optional[str]:
    lower = {str(f).strip().lower(): f for f in (fieldnames or [])}
    for c in candidates:
        if c in lower:
            return lower[c]
    return None


def domains_from_csv(csv_text: str, limit: Optional[int] = None) -> List[str]:
    """Extract de-duplicated business domains from a lead CSV.

    Prefers a website-style column; falls back to the email column (dropping
    free-mail providers). Order is preserved (first occurrence wins). `limit`
    truncates to a polite batch."""
    reader = csv.DictReader(io.StringIO(csv_text))
    web_col = _pick(reader.fieldnames, _WEBSITE_COLS)
    email_col = _pick(reader.fieldnames, _EMAIL_COLS)
    seen = set()
    out: List[str] = []
    for row in reader:
        dom = None
        if web_col:
            dom = _norm_domain(row.get(web_col, ""))
        if dom is None and email_col:
            dom = _domain_from_email(row.get(email_col, ""))
        if dom and dom not in seen:
            seen.add(dom)
            out.append(dom)
            if limit is not None and len(out) >= limit:
                break
    return out
