"""Two thin adapters that turn real feed items into canonical signals.

WHAT THIS IS NOT

Not a scraper empire and not a fetcher. The fetching already exists in
`foundation/mouth_common.py` and the two real mouths built on it; these
functions take what a mouth already observed and express it in the one
shape `foundation/signal_spine.py` can fuse.

WHY THESE TWO SOURCE CLASSES

They are genuinely different instruments, not two queries against one
API. A GitHub release atom entry carries a tag URN and an ISO-8601
`updated` field. A PyPI RSS item carries an RFC-2822 `pub_date` and a
project-page link, and the feed is four times longer. Neither shape
survives being forced into the other -- so each adapter normalises only
the small `facts` mapping and preserves everything else as `evidence`.

THE POINT OF PICKING THESE TWO

They report the same underlying event. That makes them the honest test:
a fusion layer that reports "two independent sources agree" here is
lying, and this pair is what proves the layer does not.
"""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

from foundation.signal_spine import CanonicalSignal

__all__ = ["github_release_signal", "pypi_release_signal", "release_lineage",
           "github_issue_demand_signal", "demand_lineage"]


def release_lineage(package: str, version: str) -> str:
    """The upstream event both feeds are downstream of.

    Derived from package and version rather than from the feed, which is
    precisely why two feeds cannot pass themselves off as two facts.
    """
    return f"{package.lower()}-release-{version}"


def _iso(stamp: str) -> str:
    try:
        parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return "UNKNOWN"
    if not parsed.tzinfo:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.isoformat()


def _rfc2822(stamp: str) -> str:
    try:
        parsed = parsedate_to_datetime(stamp)
    except (TypeError, ValueError):
        return "UNKNOWN"
    if parsed is None:
        return "UNKNOWN"
    if not parsed.tzinfo:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.isoformat()


def _observed_now(now: Optional[datetime] = None) -> str:
    return (now or datetime.now(timezone.utc)).isoformat()


def github_release_signal(item: dict, package: str, target: str,
                          now: Optional[datetime] = None) -> CanonicalSignal:
    """One entry from a GitHub releases atom feed.

    `source_type` is PLATFORM, not OFFICIAL: the feed is GitHub's
    rendering of the project's act, not the project speaking. Nothing
    here upgrades that later.
    """
    version = str(item.get("title", "")).strip()
    return CanonicalSignal(
        signal_id=f"GH-{package}-{version}",
        source_id="github_releases", source_type="PLATFORM",
        source_ref=str(item.get("link", "")),
        target=target, kind="RELEASE",
        claim=f"{package} {version} appears as a GitHub release",
        observed_at=_observed_now(now),
        event_at=_iso(str(item.get("updated", ""))),
        source_lineage=release_lineage(package, version),
        facts={"latest_version": version} if version else {},
        evidence={"feed": "github-releases-atom",
                  "atom_key": item.get("key", ""),
                  "raw_updated": item.get("updated", "")},
        unknowns=("whether the tag corresponds to a published artifact",))


def pypi_release_signal(item: dict, package: str, target: str,
                        now: Optional[datetime] = None) -> CanonicalSignal:
    """One item from a PyPI project releases RSS feed.

    A different instrument: RFC-2822 timestamps, a project-page link, no
    tag identity at all. The evidence dict keeps that difference instead
    of pretending the two feeds are interchangeable.
    """
    version = str(item.get("title", "")).strip()
    return CanonicalSignal(
        signal_id=f"PYPI-{package}-{version}",
        source_id="pypi_releases", source_type="PLATFORM",
        source_ref=str(item.get("link", "")),
        target=target, kind="RELEASE",
        claim=f"{package} {version} is listed on the package index",
        observed_at=_observed_now(now),
        event_at=_rfc2822(str(item.get("pub_date", ""))),
        source_lineage=release_lineage(package, version),
        facts={"latest_version": version} if version else {},
        evidence={"feed": "pypi-releases-rss",
                  "guid": item.get("guid", ""),
                  "raw_pub_date": item.get("pub_date", "")},
        unknowns=("whether the index entry reflects a source release or a "
                  "re-upload",))


# A demand issue's lineage is the issue itself. Deliberately NOT the
# repository: two issues in one project are two separate expressions of
# need, but the same issue mirrored on a bounty board or an aggregator is
# one, and only an issue-scoped lineage gets both of those right.
def demand_lineage(repo: str, number) -> str:
    return f"{repo.lower()}-issue-{number}"


_HELP_WANTED = ("help wanted", "good first issue", "contributions welcome",
                "up for grabs")


def github_issue_demand_signal(item: dict, now: Optional[datetime] = None
                               ) -> CanonicalSignal:
    """One open issue where a human asked for help.

    `event_at` is `updated_at`, not `created_at`: demand is current if it
    is still being discussed. A 2021 request still argued about this week
    is live pressure, and a 2021 request untouched since 2021 is not --
    using creation time would get both backwards. `created_at` survives
    as a fact so the age of the ask stays visible.

    The pressure class is EXPLICIT_DEMAND only when a label actually says
    so. Inferring demand from a project being popular is exactly the
    hype-for-evidence substitution this whole spine exists to prevent.
    """
    repo = str(item.get("repo", ""))
    number = item.get("number")
    labels = [str(l).lower() for l in item.get("labels", ())]
    asked = [l for l in labels if l in _HELP_WANTED]
    comments = int(item.get("comments") or 0)

    facts = {"open_help_wanted_issue": str(number),
             "issue_state": str(item.get("state", ""))}
    if item.get("created_at"):
        facts["demand_first_expressed"] = str(item["created_at"])

    return CanonicalSignal(
        signal_id=f"ISSUE-{repo}-{number}",
        source_id="github_help_wanted_issues", source_type="PLATFORM",
        source_ref=str(item.get("html_url", "")),
        target=repo, kind="DEMAND",
        claim=(f"{repo}#{number} is open and labelled for help: "
               f"{str(item.get('title',''))[:90]}"),
        observed_at=_observed_now(now),
        event_at=_iso(str(item.get("updated_at", ""))),
        source_lineage=demand_lineage(repo, number),
        facts=facts,
        evidence={"source": "github-search-issues",
                  "labels": tuple(item.get("labels", ())),
                  "comments": comments,
                  "raw_created_at": item.get("created_at", ""),
                  "raw_updated_at": item.get("updated_at", "")},
        pressure_class="EXPLICIT_DEMAND" if asked else "NONE",
        pressure_evidence=(
            f"labelled {', '.join(asked)}; {comments} comments"
            if asked else ""),
        unknowns=(
            "whether anyone is already working on it",
            "whether the project accepts outside contributions",
            "whether the underlying problem is reproducible"))
