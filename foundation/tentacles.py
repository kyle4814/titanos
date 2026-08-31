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

from foundation.activity_shape import _is_bot
from foundation.demand_direction import classify_direction
from foundation.signal_spine import CanonicalSignal

__all__ = ["github_release_signal", "pypi_release_signal", "release_lineage",
           "github_issue_demand_signal", "demand_lineage",
           "directed_pypi_release_signal", "directed_npm_release_signal",
           "repository_activity_signal",
           "code_pressure_signal"]


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
    # An ask somebody has already taken is not open demand. Found by the
    # first killing experiment the radar ever ran: all five "help wanted"
    # issues on a LOCKED target were assigned, and the demand instrument
    # had counted every one of them as an open request.
    assignees = [a for a in (item.get("assignees") or ()) if a]

    # A third axis, orthogonal to human/bot and to assigned/unassigned:
    # which side of the transaction the asker is on. Found by the second
    # killing experiment -- two targets whose asks were unassigned and
    # written by real humans, but manufactured to be handed to a cohort
    # of contributors. Both prior gates passed them correctly and neither
    # could see it. See `foundation/demand_direction.py`.
    direction = classify_direction(
        item.get("labels", ()),
        sole_author_share=item.get("sole_author_share"))

    # A fourth gate, and the same failure family as the bot-commit lock
    # one layer up: `_is_bot` guarded commits and activity shape, but
    # nothing asked who WROTE the ask. Found in the first live fetch made
    # through the new control plane -- kubestellar/console#22495, a "Hive
    # Advisory Report" with 48 comments and no assignee, authored by
    # `kubestellar-hive[bot]`. Every prior gate passed it: unassigned,
    # no recruitment taxonomy, plenty of discussion. A machine filing a
    # report against its own project is not a human with a problem.
    author_is_bot = _is_bot(str(item.get("author_login", "")),
                            str(item.get("author_type", "")))

    # Deliberately EMPTY. An issue number, its state and its creation date
    # are properties of one ask, not claims about the target that another
    # source could confirm or deny. Putting them in `facts` made two
    # separate asks on one repository collide on a single key and read as
    # a contradiction -- issue #1 and issue #2 do not disagree, they are
    # two people asking. Caught by grouping the first live sweep by target.
    facts: dict = {}

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
                  "issue_number": number,
                  "issue_state": item.get("state", ""),
                  "first_expressed": item.get("created_at", ""),
                  "labels": tuple(item.get("labels", ())),
                  "comments": comments,
                  "assignees": tuple(assignees),
                  "claimed": bool(assignees),
                  "demand_direction": direction.direction,
                  "author_login": item.get("author_login", ""),
                  "author_is_bot": author_is_bot,
                  "direction_reasons": tuple(direction.reasons),
                  "raw_created_at": item.get("created_at", ""),
                  "raw_updated_at": item.get("updated_at", "")},
        pressure_class=("EXPLICIT_DEMAND"
                        if asked and not assignees and not author_is_bot
                        and direction.counts_as_demand() else "NONE"),
        pressure_evidence=(
            f"labelled {', '.join(asked)}; {comments} comments; unassigned; "
            f"no recruitment evidence; asked by a human"
            if asked and not assignees and not author_is_bot
            and direction.counts_as_demand()
            else ""),
        unknowns=(
            ("someone is assigned; this ask is already claimed"
             if assignees else "whether anyone is already working on it"),
            ("the ask was filed by a bot, not a person"
             if author_is_bot else
             "this ask is contributor-recruitment material, not a need"
             if direction.is_recruitment()
             else "whether a real need underlies this ask -- the absence "
                  "of recruitment markers is not evidence that one does"),
            "whether the project accepts outside contributions",
            "whether the underlying problem is reproducible"))


def directed_pypi_release_signal(item: dict, mapping, target: str,
                                 now: Optional[datetime] = None
                                 ) -> CanonicalSignal:
    """A release observed because a mapping said this package is that repo.

    The lineage stays the RELEASE event, not the mapping, so a directed
    read and a fixed-feed read of the same release still collapse into one
    fact. Steering the instrument changes what it looked at, never how
    many times the world happened.

    `target_established_by` is DECLARED_MATCH and the declaration travels
    in the evidence, so the reason this signal is allowed to be about this
    target is auditable rather than assumed.
    """
    if not mapping.is_conclusive():
        raise ValueError(
            f"refusing to build a signal on a {mapping.state} mapping; "
            f"a directed read without an established target is a guess "
            f"with a URL attached")
    version = str(item.get("title", "")).strip()
    package = mapping.candidate_identity
    return CanonicalSignal(
        signal_id=f"PYPI-DIRECTED-{package}-{version}",
        source_id="pypi_releases", source_type="PLATFORM",
        source_ref=str(item.get("link", "")),
        target=target, kind="RELEASE",
        claim=f"{package} {version} is listed on the package index",
        observed_at=_observed_now(now),
        event_at=_rfc2822(str(item.get("pub_date", ""))),
        source_lineage=release_lineage(package, version),
        target_established_by="DECLARED_MATCH",
        facts={"latest_version": version} if version else {},
        evidence={"feed": "pypi-releases-rss",
                  "directed": True,
                  "mapped_package": package,
                  "mapping_state": mapping.state,
                  "mapping_provenance": mapping.provenance,
                  "raw_pub_date": item.get("pub_date", "")},
        unknowns=("whether the index entry reflects a source release or a "
                  "re-upload",))


def directed_npm_release_signal(item: dict, mapping, target: str,
                                now: Optional[datetime] = None
                                ) -> CanonicalSignal:
    """A published npm version, observed because the package declared this
    repository as its own.

    Lineage is the RELEASE event keyed by package and version, exactly as
    for the other release adapters, so a GitHub release and its npm
    publication of the same version still collapse to one fact. Publishing
    to a registry is usually downstream of tagging a release; the radar
    must not count the same shipment twice because it was announced in two
    places.
    """
    if not mapping.is_conclusive():
        raise ValueError(
            f"refusing to build a signal on a {mapping.state} mapping; "
            f"a directed read without an established target is a guess "
            f"with a URL attached")
    version = str(item.get("title", "")).strip()
    package = mapping.candidate_identity
    return CanonicalSignal(
        signal_id=f"NPM-{package}-{version}",
        source_id="npm_releases", source_type="PLATFORM",
        source_ref=str(item.get("link", "")),
        target=target, kind="RELEASE",
        claim=f"{package} {version} is published on the npm registry",
        observed_at=_observed_now(now),
        event_at=_iso(str(item.get("published_at", ""))),
        source_lineage=release_lineage(package, version),
        target_established_by="DECLARED_MATCH",
        facts={"latest_version": version} if item.get("is_latest") else {},
        evidence={"registry": "npmjs",
                  "directed": True,
                  "mapped_package": package,
                  "is_latest": item.get("is_latest", False),
                  "mapping_state": mapping.state,
                  "mapping_provenance": mapping.provenance,
                  "raw_published_at": item.get("published_at", "")},
        unknowns=("whether the published artifact was built from the "
                  "declared repository at this version",))


def repository_activity_signal(item: dict, mapping, target: str,
                               now: Optional[datetime] = None
                               ) -> CanonicalSignal:
    """One commit: evidence the machine behind the ask is still moving.

    DIMENSION: repository-native execution activity. Not "GitHub" -- a
    platform is not a dimension. Someone asking for help and someone
    landing code are different acts, and that is what makes this a second
    dimension rather than a second view of the first one.

    `facts` is deliberately EMPTY. Two commits at different times are both
    true and are not disagreeing about anything; forcing a commit sha or a
    date into a single-valued fact key would recreate, exactly, the false
    contradiction that two help-wanted issue numbers already caused once.
    The sha, subject and authored time live in evidence.

    Lineage is the commit sha, because each commit is genuinely its own
    event. RESIDUAL RISK, stated rather than hidden: a commit that tags a
    release and the registry publication of that same version are one
    shipment, and this lineage does not currently collapse them. Observed
    live on copperheadhq/copperhead, whose "Release v0.10.0" commit and npm
    0.10.0 publish share a date.
    """
    if not mapping.is_conclusive():
        raise ValueError(
            f"refusing to build a signal on a {mapping.state} mapping; "
            f"an observation without an established target is a guess "
            f"with a URL attached")
    sha = str(item.get("sha", ""))[:12]
    subject = str(item.get("subject", ""))[:90]
    return CanonicalSignal(
        signal_id=f"COMMIT-{target}-{sha}",
        source_id="github_commits", source_type="PLATFORM",
        source_ref=str(item.get("link", "")),
        target=target, kind="ACTIVITY",
        claim=f"{target} commit {sha}: {subject}",
        observed_at=_observed_now(now),
        event_at=_iso(str(item.get("authored_at", ""))),
        source_lineage=f"{target.lower()}-commit-{sha}",
        target_established_by="SOURCE_NATIVE",
        facts={},
        evidence={"source": "github-commits",
                  "sha": item.get("sha", ""),
                  "subject": subject,
                  "authored_at": item.get("authored_at", ""),
                  "mapping_state": mapping.state,
                  "mapping_provenance": mapping.provenance},
        unknowns=("whether this commit relates to the open request at all",
                  "whether the committer is a maintainer or an outside "
                  "contributor"))


def code_pressure_signal(profile, mapping, target: str,
                         now: Optional[datetime] = None,
                         latest_event_at: str = "UNKNOWN"):
    """A CODE_PRESSURE signal -- but only when the window earned one.

    Returns None when the profile is not pressured. That is the whole
    discipline: an instrument that always emits its signal is not an
    instrument, it is a constant, and wiring a constant into `rank()`
    would be threshold-tuning through the back door.

    The claim is deliberately narrow: it reports a remediation SHARE over
    a stated window, never a defect. `event_at` is the newest commit in
    the window, so a pressured window from two years ago reads as stale
    rather than current.
    """
    from foundation.code_pressure import PressureIntegrityError
    if not mapping.is_conclusive():
        raise ValueError(
            f"refusing to build a signal on a {mapping.state} mapping")
    if not profile.is_pressured():
        return None
    share = profile.share()
    if share is None:                       # defensive: is_pressured implies it
        raise PressureIntegrityError("pressured profile with no share")
    return CanonicalSignal(
        signal_id=f"PRESSURE-{target}-{profile.classified()}",
        source_id="github_commits", source_type="PLATFORM",
        source_ref=f"https://github.com/{target}/commits",
        target=target, kind="CODE_PRESSURE",
        claim=(f"{share:.0%} of {profile.classified()} recent classified "
               f"commits on {target} are remediation"),
        observed_at=_observed_now(now),
        event_at=latest_event_at,
        source_lineage=f"{target.lower()}-pressure-window",
        target_established_by="SOURCE_NATIVE",
        facts={},                            # a window is not a target claim
        evidence={"source": "github-commit-subjects",
                  "remediation": profile.remediation,
                  "feature": profile.feature,
                  "maintenance": profile.maintenance,
                  "unclassified": profile.unclassified,
                  "classified": profile.classified(),
                  "share": round(share, 3),
                  "model_version": profile.model_version,
                  "samples": list(profile.evidence)},
        pressure_class="UNRESOLVED_PAIN",
        pressure_evidence=(f"{profile.remediation} of {profile.classified()} "
                           f"classified commits are remediation"),
        unknowns=("subject lines describe what commits say, not what they "
                  "changed",
                  "whether the remediation relates to any open request"))
