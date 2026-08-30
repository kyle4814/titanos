"""The second eye's npm window. Target-directed only.

WHY THIS MOUTH HAS NO FIXED FEED

`mouth_github_releases` and `mouth_pypi` each keep a standing watch on one
package they were built to follow. This one never had such a watch, and
inventing one would mean picking an arbitrary package to stare at forever.
It exists solely to be aimed at a target the demand eye discovered and the
identity bridge confirmed, so `target` is required rather than optional.

WHAT IT READS

The npm registry document for one package: `dist-tags.latest` and the
`time` map that says when each version was published. That is the whole
read -- one request, one package, no search, no crawl.

WHAT IT MUST NEVER DO

Fall back to another package, pick the "closest" name, or turn a lookup
failure into an empty version list. A package that does not exist and a
package that exists with no releases are different facts about the world,
and `foundation/target_mapping.py` keeps them apart before this mouth is
ever fired.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Optional

from foundation.mouth_common import (
    DEFAULT_TIMEOUT_SECONDS, fetch_feed, observe as _observe)

MOUTH_ID = "npm_releases"

REGISTRY_URL = "https://registry.npmjs.org/{name}"

# One package document can list hundreds of versions. The radar wants the
# current state of the target, not its whole history.
MAX_VERSIONS = 10


def feed_url_for(package: str) -> str:
    """The registry document for one package.

    A repository path is not a package name. Accepting one silently is how
    a wrong mapping becomes a wrong read, so it is refused here as well as
    at the mapping layer.
    """
    name = (package or "").strip()
    if not name:
        raise ValueError("this mouth must be aimed at a package")
    if name.startswith("@"):
        # Scoped packages are legal but their repository declarations are
        # not yet exercised by this bridge; refusing beats guessing.
        raise ValueError(
            f"scoped package {package!r} is not supported by this bridge yet")
    if "/" in name:
        raise ValueError(
            f"expected an npm package name, got {package!r}; a repository "
            f"path is not a package identity")
    return REGISTRY_URL.format(name=name)


def parse_items(raw: bytes) -> tuple[dict, ...]:
    """Versions newest-first, each carrying its own publication time.

    The publication time is the version's own, never the document's fetch
    time -- a registry read today says nothing about when the package last
    actually shipped.
    """
    try:
        payload = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        return ()
    times = payload.get("time") or {}
    latest = (payload.get("dist-tags") or {}).get("latest")
    versions = [(v, t) for v, t in times.items()
                if v not in ("created", "modified")]
    versions.sort(key=lambda vt: vt[1], reverse=True)
    name = payload.get("name", "")
    return tuple({
        "key": f"{name}@{version}",
        "package": name,
        "title": version,
        "published_at": published,
        "is_latest": version == latest,
        "link": f"https://www.npmjs.com/package/{name}/v/{version}",
    } for version, published in versions[:MAX_VERSIONS])


def observe(state_path: Path, target: str,
            fetch_fn: Optional[Callable[[], bytes]] = None,
            now=None):
    """Observe one package's releases. `target` is required, not optional."""
    url = feed_url_for(target)
    return _observe(
        mouth_id=f"{MOUTH_ID}:{target}", state_path=state_path,
        fetch_fn=fetch_fn or (lambda: fetch_feed(url, DEFAULT_TIMEOUT_SECONDS)),
        parse_fn=parse_items, now=now)
