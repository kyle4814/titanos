"""A demand mouth: reads issues where a human explicitly asked for help.

The two existing mouths answer "did something happen?" -- a release was
published. This one helps answer a different question: "does anyone
care?" A release is an act by a maintainer. An open `help wanted` issue
with real discussion on it is an act by someone with a problem.

Those are different causal events, which is the entire reason this
source class is worth adding. Reading the same release through a third
feed would have added data and no information.

BOUNDED BY CONSTRUCTION

One request, `per_page` capped, no pagination, no crawling. The GitHub
search API is public and this endpoint is read unauthenticated -- no
credentials, no token, no account action. `mouth_common.observe()` does
the fetching, hashing and change detection exactly as it does for the
release mouths; nothing here is a second fetch stack.

WHAT THIS MOUTH DOES NOT KNOW

It sees that a request exists and that people have replied to it. It
does not know whether the request is still wanted, whether anyone is
already working on it, whether the project accepts outside patches, or
whether the problem is real. Those are recorded as unknowns, not guessed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Optional

from foundation.mouth_common import DEFAULT_TIMEOUT_SECONDS, fetch_feed, observe as _observe

MOUTH_ID = "github_help_wanted_issues"

# Open, explicitly labelled as wanting help, with enough discussion that
from foundation.discovery_authorization import DiscoveryPolicy

# The concrete objective this module fetches for. `fetch_feed()`
# refuses to open a socket without one -- see its docstring for why
# the gate lives at the socket rather than above it.
DISCOVERY_POLICY = DiscoveryPolicy(
    objective="observe open GitHub issues labelled for help on public repositories",
    requested_scope="READ_API")
# at least a few humans engaged. `comments:>2` is the cheapest available
# filter against a label nobody ever answered.
SEARCH_URL = (
    "https://api.github.com/search/issues"
    "?q=label:%22help+wanted%22+state:open+comments:%3E2"
    "&sort=updated&order=desc&per_page={per_page}"
)

MAX_PER_PAGE = 10


def build_url(per_page: int = 5) -> str:
    if not 1 <= per_page <= MAX_PER_PAGE:
        raise ValueError(
            f"per_page must be 1..{MAX_PER_PAGE}; this mouth observes, it "
            f"does not harvest")
    return SEARCH_URL.format(per_page=per_page)


def parse_items(raw: bytes) -> tuple[dict, ...]:
    """Keep only the fields a signal will actually stand on.

    `created_at` and `updated_at` are both kept because they mean
    different things for demand: when it was first expressed, and when it
    was last alive. Collapsing them would erase the difference between a
    fresh request and a four-year-old one still being argued about.
    """
    try:
        payload = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        return ()
    items = []
    for it in payload.get("items", ()):
        if not isinstance(it, dict) or "html_url" not in it:
            continue
        repo = str(it.get("repository_url", "")).split("/repos/")[-1]
        items.append({
            "key": it["html_url"],
            "repo": repo,
            "number": it.get("number"),
            "title": it.get("title", ""),
            "labels": [l.get("name", "") for l in it.get("labels", ())
                       if isinstance(l, dict)],
            "comments": it.get("comments", 0),
            # Assignment was always in the response and was discarded. A
            # "help wanted" issue with an assignee is not an open ask, and
            # counting it as one overstates demand -- it cost a whole
            # locked target before this was noticed.
            "assignees": [a.get("login", "") for a in it.get("assignees", ())
                          if isinstance(a, dict)],
            # Who wrote the ask. Third field in this parser found to
            # matter after being discarded: one account authoring every
            # ask in a repository is a contributor programme, not a
            # community. Kept so `demand_direction` can corroborate a
            # lone teaching label without an extra API request.
            "author_login": (it.get("user") or {}).get("login", ""),
            "created_at": it.get("created_at", ""),
            "updated_at": it.get("updated_at", ""),
            "state": it.get("state", ""),
            "html_url": it["html_url"],
        })
    return tuple(items)


def observe(state_path: Path, per_page: int = 5,
            fetch_fn: Optional[Callable[[], bytes]] = None,
            now=None):
    url = build_url(per_page)
    return _observe(
        mouth_id=MOUTH_ID, state_path=state_path,
        fetch_fn=fetch_fn or (lambda: fetch_feed(url, DEFAULT_TIMEOUT_SECONDS, policy=DISCOVERY_POLICY)),
        parse_fn=parse_items, now=now)
