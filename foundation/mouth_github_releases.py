"""Second mouth, adapted onto `foundation/mouth_common.py` after being
built and compared against `mouth_pypi.py` line-by-line (see that
module's docstring and this repo's history for the comparison result).

WHY THIS SOURCE

`https://github.com/yaml/pyyaml/releases.atom` — GitHub's public,
documented, no-auth Atom feed for the `yaml/pyyaml` repository. Same
real-world subject as `mouth_pypi.py` (PyYAML releases), but a
structurally different feed format (Atom `<entry>` + namespaced tags,
vs. PyPI's un-namespaced custom RSS with no `<guid>`) — a deliberate
contrast case that made the replication comparison mean something,
rather than two copies of the same shape.
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

MOUTH_ID = "github_pyyaml_releases"
FEED_URL = "https://github.com/yaml/pyyaml/releases.atom"

_ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def parse_items(xml_bytes: bytes) -> tuple[dict, ...]:
    """Parse Atom <entry> elements. GitHub's release Atom feed always
    provides a real, stable <id> per entry (verified against the live
    feed 2026-08-27) — unlike PyPI's RSS, which had none at all."""
    try:
        root = ElementTree.fromstring(xml_bytes)
    except ElementTree.ParseError as exc:
        raise FetchError(f"feed did not parse as XML: {exc}") from exc

    items = []
    for entry in root.findall("atom:entry", _ATOM_NS):
        entry_id = (entry.findtext("atom:id", namespaces=_ATOM_NS) or "").strip()
        title = (entry.findtext("atom:title", namespaces=_ATOM_NS) or "").strip()
        updated = (entry.findtext("atom:updated", namespaces=_ATOM_NS) or "").strip()
        link_el = entry.find("atom:link", _ATOM_NS)
        link = link_el.get("href", "") if link_el is not None else ""
        items.append({
            "title": title, "link": link, "updated": updated,
            "key": entry_id or link,
        })
    return tuple(items)


def observe(
    state_path: Path,
    fetch_fn: Optional[Callable[[], bytes]] = None,
    now=None,
) -> MouthObservation:
    fetch = fetch_fn or (lambda: fetch_feed(FEED_URL))
    return _observe(MOUTH_ID, state_path, fetch, parse_items, now=now)
