"""The repository's own execution activity. No package required.

WHY THIS SURFACE

Publication-based observation reached 1 in 18 of the discovered population,
because language is not the same fact as published package and most
repositories people ask for help on are applications, not libraries. This
mouth asks a question whose eligibility set is every repository target:
what has this repository itself actually done, and when?

WHY COMMITS AND NOT THE ALTERNATIVES, MEASURED

    commits                 200 on 5/5 sampled, per-commit author dates
    events                  200 on 5/5, but a 90-day ephemeral window and
                            heterogeneous types -- a quiet repository and an
                            aged-out one look identical
    stats/commit_activity   202 NOT_READY on 4/5 sampled -- GitHub computes
                            it lazily, so the honest reading is "come back
                            later", and the tempting wrong reading is "zero
                            activity"
    metadata pushed_at      200 on 5/5, but one scalar with no per-event time,
                            moved by any branch and by bots

Commits won on coverage and on carrying their own event time.

WHAT THIS IS NOT

Not a popularity scanner. It does not read stars, forks or watchers, and it
computes no score. Commit count is not value, recent activity is not demand,
and an active repository is not a high-value target. This mouth observes;
the spine classifies; gravity weighs; the lock refuses.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Optional

from foundation.mouth_common import (
    DEFAULT_TIMEOUT_SECONDS, fetch_feed, observe as _observe)

MOUTH_ID = "github_commits"

COMMITS_URL = "https://api.github.com/repos/{repo}/commits?per_page={n}"

# The radar wants the current state of the machine, not its whole history.
from foundation.discovery_authorization import DiscoveryPolicy

# The concrete objective this module fetches for. `fetch_feed()`
# refuses to open a socket without one -- see its docstring for why
# the gate lives at the socket rather than above it.
DISCOVERY_POLICY = DiscoveryPolicy(
    objective="observe the recent commit list for one named GitHub repository",
    requested_scope="READ_API")
MAX_COMMITS = 10


def feed_url_for(repo: str, n: int = MAX_COMMITS) -> str:
    """The commit list for one repository.

    The repository path IS the identity here, so there is nothing to
    resolve -- but there is still something to refuse: anything that is not
    an owner/name path, so this mouth can never be aimed at an address
    somebody assembled by hand.
    """
    if repo.count("/") != 1 or not all(p.strip() for p in repo.split("/")):
        raise ValueError(
            f"expected owner/name, got {repo!r}; this mouth is aimed at a "
            f"repository, not at an arbitrary address")
    if not 1 <= n <= MAX_COMMITS:
        raise ValueError(
            f"n must be 1..{MAX_COMMITS}; this mouth observes, it does not "
            f"clone history")
    return COMMITS_URL.format(repo=repo, n=n)


def parse_items(raw: bytes) -> tuple[dict, ...]:
    """One item per commit, each carrying its OWN authored time.

    The author date is when the work happened. Reading it today says
    nothing about when it happened, and this mouth never lets the read time
    stand in for the event time.
    """
    try:
        payload = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        return ()
    if not isinstance(payload, list):
        # An error document is not an empty repository.
        return ()
    items = []
    for c in payload:
        if not isinstance(c, dict) or "sha" not in c:
            continue
        commit = c.get("commit") or {}
        author = commit.get("author") or {}
        account = c.get("author") or {}
        message = str(commit.get("message", ""))
        # Authorship was already in every response and was being discarded.
        # Two identities are kept because they answer different questions:
        # the account is who pushed, the email is who wrote, and a repo
        # where those diverge is not the same shape as one where they don't.
        items.append({
            "key": c["sha"],
            "sha": c["sha"],
            "authored_at": author.get("date", ""),
            "subject": message.splitlines()[0] if message else "",
            "author_login": account.get("login", ""),
            "author_type": account.get("type", ""),
            "author_email": author.get("email", ""),
            "link": c.get("html_url", ""),
        })
    return tuple(items)


def observe(state_path: Path, target: str,
            fetch_fn: Optional[Callable[[], bytes]] = None,
            n: int = MAX_COMMITS, now=None):
    """Observe one repository's recent commits. `target` is required.

    Like the npm mouth, this one keeps no standing watch -- it exists to be
    aimed at a repository the demand eye already found.
    """
    url = feed_url_for(target, n)
    return _observe(
        mouth_id=f"{MOUTH_ID}:{target}", state_path=state_path,
        fetch_fn=fetch_fn or (lambda: fetch_feed(url, DEFAULT_TIMEOUT_SECONDS, policy=DISCOVERY_POLICY)),
        parse_fn=parse_items, now=now)
