"""A contract/freelance security gig mouth: watches Hacker News's monthly
"Who is hiring?" thread, via the Algolia HN Search API, for comments that
mention contract/freelance penetration-testing or security work.

WHY HN ALGOLIA AND NOT THE OTHER CANDIDATES THE TASK BRIEF NAMED

Six candidates were checked live, 2026-09-02, with this module's own
honest, non-spoofed User-Agent (`titanos-cosmic-library-mouth/1`), before
landing here:

  1. **RemoteOK** (`remoteok.com/api`) -- reachable, real JSON job data,
     confirmed live (200 OK, structured listings). NOT USED. Its own
     `robots.txt` names `ClaudeBot` and `anthropic-ai` explicitly, twice,
     in two separate rule groups: one Cloudflare-managed group states
     flatly `User-agent: ClaudeBot / Disallow: /`; a second, more
     specific "AI / LLM crawlers" group re-lists `ClaudeBot` and
     `anthropic-ai` with a narrower `Allow: /` restricted to citation/
     indexing use, explicitly excluding the kind of scheduled, recurring
     automated fetch this module performs. This module's own User-Agent
     string is not literally `ClaudeBot`, so a literal per-token robots
     parser would not block it -- but this repository is built and run
     by a Claude agent, and the operator's own file territory rule for
     this task is "never spoof a User-Agent or bypass a robots
     disallow." Fetching under a different name specifically to reach
     content the site operator has twice, explicitly, named Anthropic's
     own crawlers to restrict would be a bypass in substance even where
     it is not one in the literal string match. Declined on that
     judgment call, not on reachability -- recorded honestly rather than
     silently worked around.
  2. **We Work Remotely** (`weworkremotely.com/remote-jobs.rss`) --
     `robots.txt` permissive (only `/admin/`, `/account/`, profile/
     token-URL paths disallowed; the RSS path itself is untouched).
     Feed confirmed live: 91 real, current items, each with structured
     `region`/`country`/`state`/`skills`/`category`/`type` (Full-Time /
     Contract) fields -- the right shape. Genuinely searched for
     "penetration"/"pentest" in the current feed: **zero matches** this
     cycle. A real, honest negative result, not a build blocker -- this
     is exactly the kind of low-frequency lane a one-off read would
     never re-check, and a monitor exists precisely to keep checking.
     NOT built as a separate mouth this cycle: the category is right but
     the current content is empty, and HN Algolia (below) already gives
     a working, verified-non-empty-shape example of the same "watch a
     stream for security-contract keywords" pattern. Recorded as a
     genuine, reachable, permitted candidate for a second mouth the
     moment WWR's own content turns up a hit worth the second module --
     see `docs/DECISIONS/D-011-income-monitors.md`.
  3. **infosec-jobs.com** -- the domain now redirects (HTTP 301) entirely
     to `foorilla.com/hiring/infosec-privacy/`, which server-renders
     only a page shell; the actual job list loads via an htmx
     `hx-get="/hiring/jobs/"` fragment request that requires an
     `HX-Request` header AND a prior stateful `hx-post` to
     `/topics/hiring/` (body `{"topic": "102"}`) to select the InfoSec &
     Privacy category, with the selection held server-side against a
     session cookie between the two requests. `foorilla.com/robots.txt`
     is permissive for the paths involved (only `/hiring/companies/`,
     `/hiring/jobs/*/apply/` and a few others are disallowed), so this
     is not a robots refusal -- it is a real capability gap:
     `mouth_common.fetch_feed()` is a single stateless GET/POST with no
     cookie jar, by design (see its own docstring on why it stays
     narrow). Building session-cookie support into the repository's one
     socket for this one source would be exactly the kind of scope
     expansion Black Ice's "prefer the simpler solution" rule and this
     task's own file-territory limits both argue against. NOT USED --
     genuinely reachable by a browser, not by this fetcher's contract.
  4. **HN Algolia API** (`hn.algolia.com/api/v1/...`) -- the host serves
     no `robots.txt` at all (confirmed live: HTTP 404), and it is
     Algolia's own publicly documented API for Hacker News
     (`hn.algolia.com/api`), built for exactly this kind of programmatic
     use. USED.
  5. **Seek** (`seek.com.au/robots.txt`) -- explicitly disallows
     `*/job/`, `*?` (i.e. every query-string URL, which is how search
     results are addressed), `/graphql` and `/api/jobsearch/` for
     `User-agent: *`. BLOCKED outright, not attempted further.
  6. **Indeed** (`au.indeed.com/robots.txt`) -- explicitly disallows
     `/*?rss`, i.e. Indeed's own robots.txt forbids fetching its own RSS
     query parameter. BLOCKED outright, not attempted further.

WHAT THIS MODULE ACTUALLY DOES

Each observation cycle: (1) find the most recent "Ask HN: Who is hiring?"
story via `search_by_date` on `tags=story,author_whoishiring` (this
excludes that month's sibling "Who wants to be hired?" story, which
carries the same tag combination but a different title -- filtered
client-side on the title prefix, never trusted from tags alone); (2) run
a small, fixed set of keyword searches scoped to that story's comments
(`tags=comment,story_<id>`) for contract/freelance security-testing
terms; (3) merge and dedupe the results by comment `objectID`. This is
the same "narrow, fixed, explainable query set" discipline
`mouth_gets_nz.py` uses for its close-date regex -- not a general search
client, not an open-ended crawl of every comment in the thread.

Confirmed live 2026-09-02 against thread 49522897 ("Ask HN: Who is
hiring? (September 2026)"): the keyword set below returns real HN
comments, e.g. objectID 49528002, a ChainSecurity blockchain-security
posting -- full-time, not a contract lead, but proof the pipeline reaches
real current data. Zero genuinely contract-shaped pentest leads existed
in this specific month's thread at fetch time -- an honest negative
result from a real, live, permitted source, not a fabricated example.

WHAT THIS REUSES RATHER THAN DUPLICATES

  - `foundation/mouth_common.py::fetch_feed()` -- the one socket.
  - `foundation/discovery_authorization.py::DiscoveryPolicy` -- a fifth,
    independently-declared policy object.
  - `foundation/signal_spine.py::CanonicalSignal` -- the only signal
    shape.
  - `foundation/untrusted_text.py::describe()` -- every comment body
    (freely written by any HN user) goes through this before reaching
    `claim`/`evidence`.
  - `foundation/opportunity.py::SOURCE_TYPES` -- `"COMMUNITY"`: this is
    a public forum thread, self-posted by companies/individuals and
    aggregated by a community site, not an employer's own official
    listing (`OFFICIAL`) or a platform relaying declared terms
    (`PLATFORM`, used by `mouth_bounty.py`).

VALUE DISCIPLINE

HN hiring-thread comments are free-text job posts with no structured
rate/salary field at all. `money_state` is always `"NOT_OBSERVED"` here,
same reasoning as `mouth_gets_nz.py`'s GETS feed -- a poster may write
"$150/hr" in prose, and this module refuses to parse that into a
structured number. Inventing one would be exactly the fabrication this
repository's value discipline exists to prevent.

CANNOT

- Cannot search the full text of every comment in the thread -- only the
  fixed `GIG_KEYWORDS` list is queried, scoped to Algolia's own relevance
  match on that query string. A contract posting that never uses any of
  these exact words/phrases is invisible to this module. This is a real,
  named limitation, not a silent gap.
- Cannot see a company's contract posting on any hiring surface other
  than HN's monthly thread -- see item 3 above (infosec-jobs.com) for
  the nearest reachable-but-blocked-by-shape alternative.
- Cannot detect a posting edited after this module last observed it --
  `compute_state_hash` keys on comment `objectID` only, same limitation
  every other mouth in this repository carries for non-identity fields.
- Cannot tell full-time from genuinely-contract postings beyond what
  each comment's own free text says -- `job_type_guess` in the parsed
  item is a keyword-derived hint (`"contract"`/`"freelance"` appearing in
  the comment body), never a structured field, and is reported as a
  hint in `evidence`, never upgraded into a claim of certainty.
"""

from __future__ import annotations

import html
import json
import re
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from foundation.discovery_authorization import DiscoveryPolicy
from foundation.mouth_common import FetchError, MouthObservation, fetch_feed
from foundation.mouth_common import observe as _observe
from foundation.signal_spine import CanonicalSignal
from foundation.untrusted_text import describe

__all__ = [
    "MOUTH_ID", "API_BASE", "GIG_KEYWORDS", "DISCOVERY_POLICY", "FetchError",
    "MouthObservation", "parse_items", "observe", "gig_signal",
    "GigRadarSweep", "sweep",
]

MOUTH_ID = "mouth_gigs_hn_hiring"

# The one HN Algolia host this module ever calls. Confirmed live
# 2026-09-02: no robots.txt exists at this host at all (HTTP 404) --
# read as "nothing declared, nothing forbidden", same convention already
# applied to `api.yeswehack.com` in `mouth_bounty.py`. This is Algolia's
# own documented public HN Search API (see hn.algolia.com/api).
API_BASE = "https://hn.algolia.com/api/v1"

# Narrow, fixed, explainable -- never a general search client. Each term
# is run as its own scoped query against the current month's thread; see
# module docstring for why this stays a fixed list rather than an
# open-ended crawl of every comment.
GIG_KEYWORDS = (
    "penetration test",
    "penetration testing",
    "pentest",
    "security contract",
    "contract security",
)

# Client-side hint only (see module docstring's CANNOT section) -- never
# a structured field, never upgraded into a certainty claim.
_CONTRACT_HINT_RE = re.compile(r"\b(contract|freelance|contractor)\b", re.I)

DISCOVERY_POLICY = DiscoveryPolicy(
    objective=(
        "observe Hacker News's current monthly 'Who is hiring?' thread "
        "(via the Algolia HN Search API) for comments mentioning "
        "contract or freelance penetration-testing/security work -- see "
        "docs/DECISIONS/D-011-income-monitors.md for why this source was "
        "chosen over RemoteOK/WWR/infosec-jobs.com/Seek/Indeed"
    ),
    requested_scope="READ_URL",
    # One query to find the current thread, plus one per GIG_KEYWORDS
    # entry -- matches `mouth_ted.py`'s own precedent of setting
    # max_queries to exactly the real ceiling this module needs.
    max_queries=1 + len(GIG_KEYWORDS),
)


def _clean_str(value: object) -> str:
    return value if isinstance(value, str) else ""


def _find_current_thread(fetch_url: Callable[[str], bytes]) -> tuple[str, str]:
    """Return (story_id, story_title) for the most recent genuine
    "Who is hiring?" thread. Raises FetchError if none is found -- never
    guesses a story id."""
    url = (f"{API_BASE}/search_by_date?tags=story,author_whoishiring"
           f"&hitsPerPage=5")
    raw = fetch_url(url)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise FetchError(f"thread lookup did not parse as JSON: {exc}") from exc
    hits = data.get("hits") if isinstance(data, dict) else None
    if not isinstance(hits, list):
        raise FetchError("thread lookup response has no 'hits' list")
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        title = _clean_str(hit.get("title"))
        # "Who is hiring?" and "Who wants to be hired?" share the same
        # tags this month -- filtered on the title text itself, never
        # trusted from tags alone.
        if title.lower().startswith("ask hn: who is hiring"):
            story_id = _clean_str(hit.get("objectID")).strip()
            if story_id:
                return story_id, title
    raise FetchError(
        "no 'Ask HN: Who is hiring?' story found in the 5 most recent "
        "author_whoishiring stories")


def _default_fetch() -> bytes:
    """Find the current thread, then run each `GIG_KEYWORDS` query scoped
    to its comments, merge and dedupe by comment objectID. Every real
    fetch goes through `mouth_common.fetch_feed()`; this function opens
    no socket itself."""
    def fetch_url(url: str) -> bytes:
        return fetch_feed(url, policy=DISCOVERY_POLICY)

    story_id, story_title = _find_current_thread(fetch_url)

    seen_ids: set[str] = set()
    merged: list = []
    for keyword in GIG_KEYWORDS:
        url = (f"{API_BASE}/search_by_date?tags=comment,story_{story_id}"
               f"&query={urllib.parse.quote(keyword)}&hitsPerPage=50")
        raw = fetch_url(url)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise FetchError(
                f"keyword search for {keyword!r} did not parse as JSON: {exc}"
            ) from exc
        hits = data.get("hits") if isinstance(data, dict) else None
        if not isinstance(hits, list):
            continue
        for hit in hits:
            if not isinstance(hit, dict):
                continue
            object_id = _clean_str(hit.get("objectID")).strip()
            if not object_id or object_id in seen_ids:
                continue
            seen_ids.add(object_id)
            merged.append(hit)

    return json.dumps({
        "story_id": story_id,
        "story_title": story_title,
        "hits": merged,
    }).encode("utf-8")


def parse_items(raw: bytes) -> tuple[dict, ...]:
    """Parse the merged keyword-search result document into gig item
    dicts. `raw` is the single JSON document `_default_fetch()` builds;
    this parser stays a pure single-document parse, same as every other
    mouth in this repository."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise FetchError(f"response did not parse as JSON: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("hits"), list):
        raise FetchError("response has no top-level 'hits' list")

    story_id = _clean_str(data.get("story_id"))
    story_title = _clean_str(data.get("story_title"))

    items: list[dict] = []
    for hit in data["hits"]:
        if not isinstance(hit, dict):
            continue
        object_id = _clean_str(hit.get("objectID")).strip()
        if not object_id:
            # No stable identity to dedupe against -- dropped rather
            # than keyed on a guess, same discipline as every other
            # mouth's guid-less/slug-less item handling.
            continue
        comment_text = _clean_str(hit.get("comment_text"))
        # HN's own comment_text is HTML (real markup, e.g. "<p>", "<a>")
        # -- unescaped once for text recovery only, never rendered or
        # executed as markup, same discipline as
        # `mouth_gets_nz.py`'s description handling.
        unescaped_text = html.unescape(comment_text)

        job_type_guess = "contract" if _CONTRACT_HINT_RE.search(unescaped_text) else ""

        items.append({
            "key": object_id,
            "object_id": object_id,
            "author": _clean_str(hit.get("author")),
            "comment_text": unescaped_text,
            "created_at": _clean_str(hit.get("created_at")),
            "story_id": story_id,
            "story_title": story_title,
            "job_type_guess": job_type_guess,
        })
    return tuple(items)


def observe(
    state_path: Path,
    fetch_fn: Optional[Callable[[], bytes]] = None,
    now: Optional[datetime] = None,
) -> MouthObservation:
    """One observation cycle over the current HN 'Who is hiring?' thread.
    `fetch_fn` injected in every test in
    `foundation/tests/test_mouth_gigs.py` -- no test in this repository
    touches the real network, this module included. When `fetch_fn` is
    None the default path goes through `_default_fetch()`, which refuses
    without `DISCOVERY_POLICY` -- there is no second, ungated path here."""
    fetch = fetch_fn or _default_fetch
    return _observe(MOUTH_ID, state_path, fetch, parse_items, now=now)


def gig_signal(item: dict, now: Optional[datetime] = None) -> CanonicalSignal:
    """One matching HN comment -> one `CanonicalSignal`.

    The comment body and author are attacker-reachable free text (any HN
    user can post a comment) and are run through `untrusted_text.describe()`
    before anything derived from them reaches `claim`/`evidence`, same
    discipline as every other mouth."""
    observed_at = (now or datetime.now(timezone.utc)).isoformat()
    comment = describe(item.get("comment_text", ""))
    author = describe(item.get("author", ""))
    story_title = describe(item.get("story_title", ""))
    markers = tuple(sorted(
        set(comment.markers) | set(author.markers) | set(story_title.markers)))

    safe_object_id = describe(str(item.get("object_id", ""))).safe

    # A comment carries no structured "company"/"role" field -- the
    # author (an HN username, not a company name) is the closest stable
    # target this source offers, honestly labelled as such rather than
    # inventing a company name by parsing free text.
    target = author.safe or safe_object_id

    snippet = comment.safe[:160] + ("..." if len(comment.safe) > 160 else "")
    claim = f"HN 'Who is hiring?' comment mentioning security-contract work: {snippet}"

    evidence = {
        "object_id": safe_object_id,
        "author_safe": author.safe,
        "story_title_safe": story_title.safe,
        "comment_text_safe": comment.safe,
        "job_type_guess": item.get("job_type_guess", ""),
        "injection_markers": markers,
    }

    return CanonicalSignal(
        signal_id=f"gig:hn:{safe_object_id}",
        source_id=MOUTH_ID,
        source_type="COMMUNITY",
        source_ref=f"https://news.ycombinator.com/item?id={safe_object_id}",
        target=target,
        kind="DEMAND",
        claim=claim,
        observed_at=observed_at,
        target_established_by="ASSUMED",
        facts={
            "story_title": story_title.safe,
            "job_type_guess": item.get("job_type_guess", ""),
        },
        evidence=evidence,
        pressure_class="EXPLICIT_DEMAND",
        pressure_evidence=(
            "posted as a top-level reply in Hacker News's own monthly "
            "'Who is hiring?' thread, matched against a fixed contract/"
            "freelance security-testing keyword list -- a party stating "
            "outright that it is hiring for security-testing work"
        ),
        money_state="NOT_OBSERVED",
        money_observed="",
        **({"event_at": item["created_at"]} if item.get("created_at") else {}),
    )


@dataclass(frozen=True)
class GigRadarSweep:
    """One observation cycle, report only -- same discipline as every
    other mouth's sweep type: no ledger write, no promotion, no contact,
    no application."""

    status: str
    fetched_count: int
    error: Optional[str]
    signals: tuple[CanonicalSignal, ...]
    targets: tuple[str, ...]

    def show_the_math(self) -> str:
        lines = [
            f"HN HIRING GIG RADAR status={self.status} "
            f"fetched={self.fetched_count} signals={len(self.signals)}"
        ]
        if self.error:
            lines.append(f"  error: {self.error}")
        if self.status in ("FIRST_SEEN", "CHANGED") and not self.signals:
            lines.append(
                "  zero matching comments observed this cycle -- a "
                "valid, honest outcome, not an error"
            )
        for s in self.signals:
            lines.append(f"  OBSERVED  target={s.target!r}  {s.claim}")
        if self.signals:
            lines.append(
                "  every signal above is OBSERVED only (a live matching "
                "comment existed at fetch time) -- none is VERIFIED or "
                "REALIZED; no structured rate/salary field exists on "
                "this source, see module docstring's value discipline"
            )
        return "\n".join(lines)


def sweep(
    state_dir: Path,
    fetch_fn: Optional[Callable[[], bytes]] = None,
    now: Optional[datetime] = None,
) -> GigRadarSweep:
    """Run one HN-hiring gig-radar cycle: observe -> signal -> report."""
    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / f"{MOUTH_ID}.json"
    observation = observe(state_path, fetch_fn=fetch_fn, now=now)
    signals = tuple(gig_signal(item, now=now) for item in observation.new_items)
    targets = tuple(sorted({s.target for s in signals}))
    return GigRadarSweep(
        status=observation.status,
        fetched_count=observation.item_count,
        error=observation.error,
        signals=signals,
        targets=targets,
    )
