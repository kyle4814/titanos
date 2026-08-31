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
from foundation.discovery_authorization import DiscoveryPolicy

__all__ = [
    "MOUTH_ID", "FEED_URL", "FetchError", "MouthObservation",
    "fetch_feed", "parse_items", "observe",
]

# The concrete objective this module fetches for. `fetch_feed()`
# refuses to open a socket without one -- see its docstring for why
# the gate lives at the socket rather than above it.
DISCOVERY_POLICY = DiscoveryPolicy(
    objective="observe the PyPI releases RSS feed for one named package",
    requested_scope="READ_URL")

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


def feed_url_for(project: str) -> str:
    """The releases RSS feed for a PyPI project."""
    name = (project or "").strip()
    if not name or "/" in name:
        raise ValueError(
            f"expected a PyPI project name, got {project!r}; a repository "
            f"path is not a package identity")
    return f"https://pypi.org/rss/project/{name}/releases.xml"


def observe(
    state_path: Path,
    fetch_fn: Optional[Callable[[], bytes]] = None,
    now=None,
    target: Optional[str] = None,
) -> MouthObservation:
    """Observe releases -- from the fixed feed, or from a named project.

    `target` here is a PACKAGE name, never a repository path. The two are
    different identities and the mapping between them is established by
    `foundation/target_mapping.py`, not by this mouth guessing.
    """
    url = feed_url_for(target) if target else FEED_URL
    mouth_id = f"{MOUTH_ID}:{target}" if target else MOUTH_ID
    fetch = fetch_fn or (lambda: fetch_feed(url, policy=DISCOVERY_POLICY))
    return _observe(mouth_id, state_path, fetch, parse_items, now=now)
