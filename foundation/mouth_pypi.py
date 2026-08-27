"""The first real mouth: legitimate, public, machine-readable PyPI RSS.

WHY THIS SOURCE

`PyYAML` is this repository's one real third-party dependency (see
`TITANOS_OBELISK_ZERO_DEPENDENCY_DOCTRINE.md`). PyPI publishes a public,
documented, intended-for-consumption RSS feed of a project's releases at
`https://pypi.org/rss/project/<name>/releases.xml` — no authentication,
no rate-limit-defeating behaviour needed (one small GET per invocation),
nothing scraped that wasn't built to be machine-read.

THIS WAS THIS REPOSITORY'S FIRST NETWORK CALL, ANYWHERE, EVER (see
`SIGIL.md`'s honest T7->T3 tier note). Only after explicit confirmation
from the repository owner — not built speculatively.

WHAT THIS DOES

`observe()` (from `foundation.mouth_common`, shared with
`mouth_github_releases.py` after those two real mouths were compared
line-by-line and found to duplicate their fetch/hash/compare/receipt
logic exactly): fetch the feed, parse items, compute a content hash,
compare against last known state, return FIRST_SEEN / UNCHANGED /
CHANGED / UNAVAILABLE. This module supplies only what's genuinely
source-specific: the feed URL and how to parse PyPI's particular RSS
shape.

THE REAL BUG THIS MODULE ONCE HAD, FIXED

PyPI's real feed (verified 2026-08-27 against the live source, not
assumed from documentation) has no `<guid>` element at all — `<link>`
is the only stable per-item identifier it actually emits. `key` falls
back to `link` when `guid` is absent, so this stays correct against a
feed that *does* emit real guids too.

WIRING NOTE (2026-08-27, re-examined the same day this module was
built): `foundation/contract_compat.py`'s `check_compatible()` was
considered for wiring into `rpa.gates.human_jurisdiction.authorize_
pilot()` and rejected — that gate already independently guards against
the exact shape mismatch it demonstrates, more strongly. Unrelated to
this module; noted here only because both live in `foundation/` and a
future reader might otherwise wonder whether they connect.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional
from xml.etree import ElementTree

from foundation.mouth_common import FetchError, MouthObservation, fetch_feed, observe as _observe

__all__ = [
    "MOUTH_ID", "FEED_URL", "FetchError", "MouthObservation",
    "fetch_feed", "parse_items", "observe",
]

MOUTH_ID = "pypi_pyyaml_releases"
FEED_URL = "https://pypi.org/rss/project/PyYAML/releases.xml"


def parse_items(xml_bytes: bytes) -> tuple[dict, ...]:
    """Parse RSS <item> elements. `key` is `guid` if present, else
    `link` — PyPI's real feed only ever emits the latter."""
    try:
        root = ElementTree.fromstring(xml_bytes)
    except ElementTree.ParseError as exc:
        raise FetchError(f"feed did not parse as XML: {exc}") from exc

    items = []
    for item in root.findall(".//item"):
        link = (item.findtext("link") or "").strip()
        guid = (item.findtext("guid") or "").strip()
        items.append({
            "title": (item.findtext("title") or "").strip(),
            "link": link,
            "guid": guid,
            "pub_date": (item.findtext("pubDate") or "").strip(),
            "key": guid or link,
        })
    return tuple(items)


def observe(
    state_path: Path,
    fetch_fn: Optional[Callable[[], bytes]] = None,
    now=None,
) -> MouthObservation:
    fetch = fetch_fn or (lambda: fetch_feed(FEED_URL))
    return _observe(MOUTH_ID, state_path, fetch, parse_items, now=now)
