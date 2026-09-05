"""operator_cli.py -- the one command an operator actually runs.

WHY THIS EXISTS
----------------
Every piece of the hunt chain (`hunt.py`, `sources.py`, `hunt_loop.py`,
`brief.py`, `dossier.py`, `qualification.py`) already worked and none of
them had a door a non-developer could walk through. Using any of it meant
opening a Python shell, constructing an `OperatorProfile`, constructing a
`DiscoveryPolicy`, and calling a function by hand -- which means the
system did not actually run for anyone who cannot write Python. This
module is that door: one command, five subcommands, real defaults,
nothing to import.

WHAT THIS REUSES RATHER THAN DUPLICATES
-----------------------------------------
  - `foundation.hunt.hunt_multi()` / `hunt()` -- the actual fetch/assess/
    band chain. Never re-implemented.
  - `foundation.sources.sources_for_query()` -- the full source
    registry. Never a hand-written subset: this file printed a frozen
    three-name list for several cycles after the registry grew to
    seven, telling the operator which sources were swept and being
    wrong about it.
  - `foundation.hunt_loop.run_hunt_loop()` -- the unattended cycle, kill
    switch and receipt log included.
  - `foundation.brief.build_brief()` / `render_brief()` -- the morning
    brief.
  - `foundation.dossier.render_dossier()` / `missing_facts_for_scheme()`.
  - `foundation.qualification.OperatorProfile` -- read from a config
    file here, never redefined.
  - `foundation.swarm_contract._cli()`'s own shape: dry-run is the
    default for anything that touches the network, going live requires
    an explicit `--live` flag, and every refusal is a named, printed
    reason rather than a bare traceback. This module does not invent a
    new CLI convention.

OPERATOR PROFILE
-----------------
`operator_profile.json` at the repository root, if present, is read as
the real operator's real, self-declared data. If it is absent, this
module falls back to `operator_profile.example.json` and prints an
unmissable notice that the numbers shown are NOT the real operator's --
it never silently pretends the example data is real.

NETWORK
--------
Every command that can reach the network builds a real `DiscoveryPolicy`
naming a concrete objective and a bounded budget before it is used --
there is no code path here that opens a socket without one. `--dry-run`
is the default: `hunt`, `brief`, and `loop` describe what they would do
and touch nothing until `--live` is passed explicitly. `dossier` and
`profile` never touch the network at all, live or not.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

from foundation.brief import build_brief, render_brief
from foundation.discovery_authorization import (
    DEFAULT_MAX_QUERIES,
    DEFAULT_MAX_RESULTS,
    DEFAULT_MAX_WALL_CLOCK_SECONDS,
    DiscoveryPolicy,
)
from foundation.access_barriers import assess_access, format_access
from foundation.entry_gate import assess_entry, format_entry
from foundation.partner_network import derive_partner_needs, format_partner_needs
from foundation.reachability import format_reachability, scan_reachability
from foundation.pit_report import format_pit_summary, summarise_pit_report
from foundation.corpus_triage import triage as triage_corpus
from foundation import mouth_find_a_tender_uk
from foundation.spec_crossref import (
    crossref,
    format_crossref,
    format_term_coverage,
    trace_term,
)
from foundation.deal_pipeline import (
    DealBoard,
    DealError,
    append_deal_event,
    load_deals,
    render_pipeline,
)
from foundation.dossier import (
    BusinessFacts,
    Referee,
    SCHEMES,
    SupplierDossier,
    missing_facts_for_scheme,
    render_dossier,
)
from foundation.hunt import (
    HuntIntegrityError,
    HuntReport,
    hunt_multi,
    render_hunt,
    with_recency,
)
from foundation.hunt_loop import HUNT_STOP_FILENAME, render_hunt_cycle, run_hunt_loop
from foundation import mouth_etenders_ie
from foundation import income_watch
from foundation.qualification import OperatorProfile
from foundation.relevance import CapabilityProfile
from foundation.sources import sources_for_query

__all__ = [
    "REPO_ROOT",
    "PROFILE_PATH",
    "PROFILE_EXAMPLE_PATH",
    "load_operator_profile",
    "main",
]

REPO_ROOT = Path(__file__).resolve().parent.parent
PROFILE_PATH = REPO_ROOT / "operator_profile.json"
PROFILE_EXAMPLE_PATH = REPO_ROOT / "operator_profile.example.json"

_DEFAULT_KEYWORD = "cyber security"

# A LIVE SWEEP ON 2026-09-03 ASSESSED 120 NOTICES AND 100 OF THEM WERE
# PUBLISHED IN 2016 AND 2017.
#
# Nothing was broken. The CLI simply never bounded TED by date, so every
# sweep spent its whole budget re-reading notices that closed years ago,
# banded them, printed them, and looked exactly like a working hunt. A
# closed notice is not an opportunity, and a report full of them is
# worse than an empty one -- it costs the operator's attention to
# discover that for himself, item by item.
#
# The honest bound is publication date, NOT deadline. `deadline-receipt-
# request >= today()` is the filter that actually means "still accepting
# tenders", and `hunt.with_open_deadline()` implements it -- but it is
# measured to return ZERO results when combined with an `FT ~ (...)`
# clause, which is what a keyword hunt is. So this is a proxy: recently
# published, not provably open. A notice published inside this window
# may still have closed. That is a weaker claim and it is the strongest
# one available on a full-text query -- see `with_recency()`'s and
# `with_open_deadline()`'s own docstrings for the measurements.
_DEFAULT_PUBLISHED_WITHIN_DAYS = 365
_DEFAULT_EXCLUSIONS = (
    "construction", "catering", "cleaning", "vehicles", "medical supplies",
)


class ProfileLoadError(ValueError):
    """Raised when neither a real nor an example operator profile could
    be read and parsed -- this CLI refuses to guess at operator data."""


@dataclass(frozen=True)
class LoadedProfile:
    operator: OperatorProfile
    business_facts: BusinessFacts
    source_path: Path
    is_example: bool


def _strip_doc_keys(d: dict) -> dict:
    """Drop every `_`-prefixed documentation key
    (`operator_profile.example.json` carries `_comment`/`_name`/... next
    to each real field so the file is self-documenting) -- never read as
    data."""
    return {k: v for k, v in d.items() if not k.startswith("_")}


def _business_facts_from_json(raw: Optional[dict]) -> BusinessFacts:
    if not raw:
        return BusinessFacts()
    raw = _strip_doc_keys(raw)
    referees = tuple(
        Referee(
            name=r.get("name", ""),
            organisation=r.get("organisation", ""),
            contact=r.get("contact", ""),
        )
        for r in raw.get("referees", []) or ()
    )
    return BusinessFacts(
        abn=raw.get("abn"),
        acn=raw.get("acn"),
        business_address=raw.get("business_address"),
        licence_number=raw.get("licence_number"),
        registration_number=raw.get("registration_number"),
        insurance_policy_number=raw.get("insurance_policy_number"),
        insurance_pi_cover_aud=raw.get("insurance_pi_cover_aud"),
        insurance_pl_cover_aud=raw.get("insurance_pl_cover_aud"),
        years_experience=raw.get("years_experience"),
        revenue_band=raw.get("revenue_band"),
        skills=tuple(raw.get("skills", []) or ()),
        referees=referees,
    )


def load_operator_profile(path: Optional[Path] = None) -> LoadedProfile:
    """Read the operator profile from `path` (default: `operator_profile
    .json` at the repo root), falling back to `operator_profile.example
    .json` if it is absent. Never fabricates a value -- a malformed file
    raises `ProfileLoadError` naming exactly what is wrong rather than
    silently substituting a default field by field.
    """
    real_path = path or PROFILE_PATH
    is_example = False
    use_path = real_path
    if not use_path.exists():
        use_path = PROFILE_EXAMPLE_PATH
        is_example = True
    if not use_path.exists():
        raise ProfileLoadError(
            f"no operator profile found -- neither {real_path} nor "
            f"{PROFILE_EXAMPLE_PATH} exists")

    try:
        raw = json.loads(use_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProfileLoadError(f"could not read/parse {use_path}: {exc}") from exc

    fields = _strip_doc_keys(raw)
    try:
        operator = OperatorProfile(
            name=fields["name"],
            staff_count=fields["staff_count"],
            certifications=frozenset(fields.get("certifications", []) or ()),
            insurance_cover_eur=fields.get("insurance_cover_eur"),
            corporate_references=tuple(fields.get("corporate_references", []) or ()),
            languages=frozenset(fields.get("languages", []) or ()),
        )
    except KeyError as exc:
        raise ProfileLoadError(
            f"{use_path} is missing required field {exc}") from exc
    except ValueError as exc:
        raise ProfileLoadError(f"{use_path} is invalid: {exc}") from exc

    facts = _business_facts_from_json(fields.get("business_facts"))
    return LoadedProfile(
        operator=operator, business_facts=facts,
        source_path=use_path, is_example=is_example,
    )


def _print_profile_notice(loaded: LoadedProfile) -> None:
    if loaded.is_example:
        print(
            "NOTICE: no operator_profile.json found at the repository "
            f"root -- using DEFAULT/EXAMPLE data from "
            f"{loaded.source_path.name}. This is NOT your real operator "
            "profile. Copy operator_profile.example.json to "
            "operator_profile.json and edit it before trusting any "
            "result below.", file=sys.stderr,
        )
    else:
        print(f"operator profile: {loaded.source_path}", file=sys.stderr)


def _default_capability_profile(keyword: str, authorized_by: str) -> CapabilityProfile:
    return CapabilityProfile(
        name="operator-default",
        declared_by=authorized_by or "unattributed",
        keywords=frozenset({keyword.lower()}),
        cpv_codes=frozenset({"72000000"}),
        exclusions=frozenset(_DEFAULT_EXCLUSIONS),
    )


def _registered_source_ids() -> str:
    """Read the source ids out of the registry itself. Never a literal
    list typed into this file -- see the module docstring."""
    from foundation.sources import ALL_SOURCES
    return ", ".join(s.source_id for s in ALL_SOURCES)


def _derive_ted_query(args) -> str:
    """The ONE place a TED query is built, for every subcommand.

    It was three places, each repeating
    `args.ted_query or f'FT ~ ("{keyword}")'` -- so a date bound added
    to one of them would have silently left the other two sweeping the
    entire archive. Same drift class as `sources_for_query()` naming
    three of five sources.

    An explicit `--ted-query` is passed through UNTOUCHED, including
    its date handling or lack of one: a caller who writes their own
    expert query is the authority on it. `--published-within-days 0`
    disables the bound and sweeps the whole archive deliberately.
    """
    if args.ted_query:
        return args.ted_query
    query = f'FT ~ ("{args.keyword}")'
    days = getattr(args, "published_within_days", _DEFAULT_PUBLISHED_WITHIN_DAYS)
    if not days:
        return query
    try:
        return with_recency(query, days)
    except HuntIntegrityError:
        # An out-of-range window is the caller's error, not a reason to
        # silently fall back to an unbounded archive sweep -- the exact
        # behaviour this function exists to stop.
        raise


def _build_policy(objective: str, max_queries: int, max_wall_clock_seconds: int,
                   max_results: int) -> DiscoveryPolicy:
    return DiscoveryPolicy(
        objective=objective,
        requested_scope="READ_API",
        max_queries=max_queries,
        max_wall_clock_seconds=max_wall_clock_seconds,
        max_results=max_results,
    )


def _run_hunt(args, loaded: LoadedProfile) -> Tuple[Optional[HuntReport], int]:
    """Shared by `hunt` and `brief`: dry-run by default, prints what it
    would fetch and touches nothing; `--live` performs one real
    multi-source hunt and returns the report. Returns (report, exit_code)
    -- `report` is `None` whenever no network call was made."""
    keyword = args.keyword
    ted_query = _derive_ted_query(args)
    objective = args.objective or (
        f"observe public procurement notices matching keyword "
        f"{keyword!r} across every registered source "
        f"({_registered_source_ids()}) for "
        f"operator {loaded.operator.name!r}")

    if not args.live:
        print("DRY RUN (default) -- no network request will be made.")
        print(f"  objective   : {objective}")
        print(f"  keyword     : {keyword}")
        print(f"  TED query   : {ted_query}")
        print(f"  sources     : {_registered_source_ids()}")
        print(
            f"  budget      : max_queries={args.max_queries} "
            f"max_wall_clock_seconds={args.max_wall_clock_seconds} "
            f"max_results={args.max_results}")
        print("Pass --live to actually fetch.")
        return None, 0

    try:
        policy = _build_policy(
            objective, args.max_queries, args.max_wall_clock_seconds,
            args.max_results)
    except Exception as exc:  # noqa: BLE001 -- a bad --objective is a real, named failure
        print(f"REFUSED: could not build a discovery policy: {exc}", file=sys.stderr)
        return None, 1

    capability = _default_capability_profile(keyword, args.authorised_by)
    now = datetime.now(timezone.utc)
    try:
        sources = sources_for_query(ted_query, ted_limit=args.limit, ted_policy=policy)
        report = hunt_multi(
            keyword, loaded.operator, sources, capability=capability, now=now)
    except Exception as exc:  # noqa: BLE001 -- never a bare traceback to the operator
        print(f"HUNT FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return None, 1
    return report, 0


def cmd_hunt(args) -> int:
    loaded = load_operator_profile()
    _print_profile_notice(loaded)
    report, code = _run_hunt(args, loaded)
    if report is None:
        return code
    print()
    print(render_hunt(report, limit=args.print_limit))
    # A hunt that legitimately finds nothing is success, not failure.
    return 0


def cmd_brief(args) -> int:
    loaded = load_operator_profile()
    _print_profile_notice(loaded)
    report, code = _run_hunt(args, loaded)
    if report is None:
        return code
    brief = build_brief(
        report, now=datetime.now(timezone.utc),
        closing_within_days=args.closing_within_days,
    )
    print()
    print(render_brief(brief))
    return 0


def cmd_loop(args) -> int:
    loaded = load_operator_profile()
    _print_profile_notice(loaded)
    keyword = args.keyword
    ted_query = _derive_ted_query(args)
    objective = args.objective or (
        f"unattended repeated hunt for keyword {keyword!r} against TED "
        f"for operator {loaded.operator.name!r}")

    stop_file = REPO_ROOT / HUNT_STOP_FILENAME
    if not args.live:
        print("DRY RUN (default) -- no network request will be made, no loop started.")
        print(f"  objective     : {objective}")
        print(f"  TED query     : {ted_query}")
        print(f"  interval secs : {args.interval}")
        print(f"  max cycles    : {args.max_cycles if args.max_cycles else 'unbounded'}")
        print(f"  kill switch   : drop a file at {stop_file} to stop a live loop")
        print("Pass --live to actually run.")
        return 0

    try:
        policy = _build_policy(
            objective, args.max_queries, args.max_wall_clock_seconds,
            args.max_results)
    except Exception as exc:  # noqa: BLE001
        print(f"REFUSED: could not build a discovery policy: {exc}", file=sys.stderr)
        return 1

    capability = _default_capability_profile(keyword, args.authorised_by)
    results = run_hunt_loop(
        REPO_ROOT, ted_query, loaded.operator,
        policy=policy, capability=capability, limit=args.limit,
        sleep_seconds=args.interval, max_cycles=args.max_cycles,
    )
    for result in results:
        print(render_hunt_cycle(result))
        print()
    if not results:
        print("Loop produced no cycles.")
        return 0
    last = results[-1]
    # STOPPED_HUNT_ERROR is a real failure; every other stop (including
    # the kill switch and a clean empty run) is a legitimate outcome.
    return 1 if last.action == "STOPPED_HUNT_ERROR" else 0


def cmd_income(args) -> int:
    """Watch the non-procurement income mouths (`mouth_bounty.py`'s
    YesWeHack programs, `mouth_gigs.py`'s HN 'Who is hiring?' contract
    matches) and print what's new. See `foundation/income_watch.py` for
    why this is a separate report type from `hunt`/`brief`: a bug bounty
    program was never issued by a buyer running a procurement process,
    and `HuntReport`'s whole vocabulary is buyer selection criteria that
    simply do not apply here."""
    objective = args.objective or (
        "observe YesWeHack's public bug bounty program directory and "
        "Hacker News's monthly 'Who is hiring?' thread for new "
        "contract/freelance security-testing opportunities -- "
        "non-procurement income mouths, see foundation/income_watch.py")

    if not args.live:
        print("DRY RUN (default) -- no network request will be made.")
        print(f"  objective   : {objective}")
        print("  sources     : mouth_bounty (YesWeHack programs), "
              "mouth_gigs (HN 'Who is hiring?')")
        print(
            f"  budget      : max_queries={args.max_queries} "
            f"max_wall_clock_seconds={args.max_wall_clock_seconds} "
            f"max_results={args.max_results}")
        print("Pass --live to actually fetch.")
        return 0

    # Unlike `hunt`/`brief`/`loop`, `--objective`/`--max-*` are not
    # forwarded into a policy consumed here: each income source builds
    # and enforces its own DiscoveryPolicy internally (mouth_bounty.
    # DISCOVERY_POLICY / mouth_gigs.DISCOVERY_POLICY), checked inside
    # `mouth_common.fetch_feed()` before any socket opens regardless of
    # what this CLI does. Constructing a second, unconsumed policy here
    # would be exactly the decorative-gate pattern Black Ice forbids --
    # the printed objective above documents intent for the operator, it
    # does not additionally gate anything.
    state_path = REPO_ROOT / "income_watch_state.jsonl"
    try:
        sources = income_watch.default_sources()
        report = income_watch.watch(
            sources, state_path, now=datetime.now(timezone.utc))
    except Exception as exc:  # noqa: BLE001 -- never a bare traceback to the operator
        print(f"INCOME WATCH FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print()
    print(income_watch.render_income_watch(report, limit=args.print_limit))
    # Zero new programs/gigs this cycle is success, not failure -- same
    # discipline as cmd_hunt's own empty-result handling.
    return 0


def cmd_dossier(args) -> int:
    loaded = load_operator_profile()
    _print_profile_notice(loaded)
    dossier = SupplierDossier(profile=loaded.operator, facts=loaded.business_facts)
    print(render_dossier(dossier))
    print()
    print("=" * 72)
    print("MISSING FACTS BY SCHEME")
    print("=" * 72)
    for scheme in SCHEMES:
        missing = missing_facts_for_scheme(dossier, scheme)
        print(f"\n{scheme} ({len(missing)} missing):")
        if not missing:
            print("  none identified by this checklist")
        for m in missing:
            print(f"  - {m.fact}: {m.why_needed}")
    return 0


def cmd_digest(args) -> int:
    """The end-of-run operator digest, as ONE command.

    `next.md` mandates that every cycle produces the phone money-printer
    digest; before this command that was a remembered sequence of steps.
    This is the single reproducible entry point a Sonnet swarm or a future
    session runs: it renders the phone dashboard HTML, pushes the digest
    (dry-run without a token, live with one), and prints the top DO-NOW
    moves as text. Touches the network ONLY when TELEGRAM creds are set
    (operator self-notification, gated on NOTIFY_OPERATOR); otherwise it
    writes the messages to a file and stays entirely offline."""
    from foundation.ops_digest import live_opportunities
    from foundation.telegram_notify import send_digest

    now = datetime.now(timezone.utc)
    opps = live_opportunities(now)

    # 1. Phone dashboard HTML (self-contained, for Artifact / SendUserFile).
    html_path = Path(args.html_out) if args.html_out else (
        Path(__file__).resolve().parent.parent / "digest_out" / "ops_digest.html")
    html_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import subprocess
        subprocess.run(
            [sys.executable, "scripts/build_digest_artifact.py", str(html_path)],
            cwd=str(Path(__file__).resolve().parent.parent), check=True,
            capture_output=True, timeout=60)
        html_state = f"written -> {html_path}"
    except Exception as exc:  # pragma: no cover - build-script shape
        html_state = f"NOT written ({type(exc).__name__})"

    # 2. Telegram push (dry-run unless creds present). send_digest is gated.
    result = send_digest(now=now)

    # 3. The operator-facing summary: top DO-NOW moves.
    live = [o for o in opps if not o.is_expired(now)]
    do_now = [o for o in live if o.effective_status(now) == "ACTIONABLE_NOW"]
    act_soon = [o for o in live if o.effective_status(now) == "ACT_SOON"]

    print("=" * 72)
    print("OPERATOR DIGEST")
    print("=" * 72)
    print(f"generated : {now.strftime('%a %d %b %Y %H:%M UTC')}")
    print(f"dashboard : {html_state}")
    print(f"telegram  : {result.mode}"
          + (f" ({result.dry_run_path})" if result.dry_run_path else
             f" delivered {result.delivered}/{result.total}"))
    print(f"live ops  : {len(live)}  (DO NOW {len(do_now)}, ACT SOON {len(act_soon)})")
    print()
    print("TOP MOVES (act on these first):")
    for o in (do_now + act_soon)[:5]:
        print(f"  {o.badge(now)}  {o.title}")
        print(f"     value: {o.value}")
        print(f"     step : {o.actions[0]}")
        print(f"     link : {o.link}")
    if result.errors and result.mode == "DRY_RUN":
        print()
        print("note: Telegram not armed — set TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID "
              "to push (see HUMAN_DECISIONS.md). The dashboard covers you meanwhile.")
    return 0


def cmd_portfolio(args) -> int:
    """Assemble the WHOLE tendering portfolio (live opps + drafts + full
    intelligence + archive) into one folder, fresh. Optionally zip it."""
    from foundation.portfolio_bundle import build_portfolio_bundle
    import zipfile
    dest = Path(args.out).expanduser()
    written = build_portfolio_bundle(dest)
    print(f"portfolio assembled at {dest}  ({len(written)} files)")
    if args.zip:
        zpath = dest.with_suffix(".zip")
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for f in written:
                z.write(f, f.relative_to(dest.parent))
        print(f"zipped -> {zpath}  ({zpath.stat().st_size // 1024} KB)")
    print("open START_HERE.md first — it is the map and the do-first order.")
    return 0


def cmd_team_payload(args) -> int:
    """Build the end-of-cycle ZIP payload for Kyle's team to submit: the
    full portfolio plus TEAM_TARGETS (the credential-walled contracts a team
    can win). Same bundle as `portfolio`, framed for the team."""
    from foundation.portfolio_bundle import build_portfolio_bundle
    from foundation.team_targets import live_team_targets
    import zipfile
    dest = Path(args.out).expanduser()
    written = build_portfolio_bundle(dest)
    tt = live_team_targets()
    print(f"team payload assembled at {dest}  ({len(written)} files, "
          f"{len(tt)} team targets)")
    if args.zip:
        zpath = dest.with_suffix(".zip")
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for f in written:
                z.write(f, f.relative_to(dest.parent))
        print(f"zipped -> {zpath}  ({zpath.stat().st_size // 1024} KB)")
    print("hand 01_PORTFOLIO/TEAM_TARGETS.md to the team — dated Irish tenders first.")
    return 0


def cmd_team_fit(args) -> int:
    """Rank the live team targets by winnability against a declared team
    capability profile. Honest: an undeclared capability or an unparseable
    requirement is UNKNOWN (needs a human read), never a silent pass. With
    no flags, every target shows its gaps against a zero profile — which is
    itself a useful checklist of exactly what the team must bring."""
    from foundation.team_fit import TeamCapability, render_fit_md
    langs = tuple(l.strip().lower() for l in (args.languages or "").split(",")
                  if l.strip())
    caps = tuple(c.strip().lower() for c in (args.capabilities or "").split(",")
                 if c.strip())
    cap = TeamCapability(
        annual_turnover_eur=args.turnover,
        max_insurance_eur=args.insurance,
        can_obtain_higher_insurance=args.can_raise_insurance,
        reference_contracts=args.references,
        largest_reference_eur=args.largest_reference,
        languages=langs,
        has_247_soc=args.soc,
        capabilities=caps,
        named_testers=args.named_testers,
    )
    md = render_fit_md(cap)
    if getattr(args, "out", None):
        Path(args.out).expanduser().write_text(md, encoding="utf-8")
        print(f"team-fit report written -> {args.out}")
    else:
        print(md)
    return 0


def cmd_security_report(args) -> int:
    """Produce an automated email-security report for a domain — SPF, DMARC,
    DKIM, DNSSEC, MX, MTA-STS — from public DNS only. The first sellable,
    fully-automated deliverable: the system runs it, the operator sells and
    delivers it. Reads public records only; no credentials, no intrusion."""
    from foundation.email_security_report import (
        assess_email_security, render_report_md)
    report = assess_email_security(args.domain)
    md = render_report_md(report)
    if getattr(args, "out", None):
        Path(args.out).expanduser().write_text(md, encoding="utf-8")
        print(f"email-security report written -> {args.out}  (grade {report.grade})")
    else:
        print(md)
    return 0


def cmd_submission_prep(args) -> int:
    """Assemble a ready-to-file submission pack for one target: portal + login
    URL, the step sequence (stopping at the human Submit), the upload checklist
    from the notice's quoted requirements, and a qualification/ESPD answer
    sheet filled from the team profile. Unsupplied facts are UNKNOWN and listed
    under MISSING — never invented. Offline; files nothing, submits nothing."""
    import json
    from foundation.submission_pack import (
        TeamProfile, build_submission_pack, render_pack_md)
    from foundation.team_targets import TEAM_TARGETS
    target = next((t for t in TEAM_TARGETS if t.target_id == args.target), None)
    if target is None:
        ids = ", ".join(sorted(t.target_id for t in TEAM_TARGETS))
        print(f"unknown target {args.target!r}. known: {ids}")
        return 2
    profile = TeamProfile()
    if args.profile:
        raw = json.loads(Path(args.profile).expanduser().read_text(encoding="utf-8"))
        profile = TeamProfile(
            legal_name=raw.get("legal_name", ""),
            registration=raw.get("registration", ""),
            contact_name=raw.get("contact_name", ""),
            contact_email=raw.get("contact_email", ""),
            address=raw.get("address", ""),
            annual_turnover_eur=float(raw.get("annual_turnover_eur", 0) or 0),
            insurance_cover={k: float(v) for k, v in
                             (raw.get("insurance_cover", {}) or {}).items()},
            references=tuple(raw.get("references", []) or ()),
            certifications=tuple(raw.get("certifications", []) or ()),
            languages=tuple(raw.get("languages", []) or ()),
            has_247_soc=bool(raw.get("has_247_soc", False)),
        )
    pack = build_submission_pack(target, profile)
    md = render_pack_md(pack)
    if getattr(args, "out", None):
        Path(args.out).expanduser().write_text(md, encoding="utf-8")
        print(f"submission pack written -> {args.out}"
              + (f"  ({len(pack.missing)} facts still MISSING)"
                 if pack.missing else "  (profile complete)"))
    else:
        print(md)
    return 0


def cmd_situation(args) -> int:
    """Print the ops bottleneck analysis, computed by situation_analysis
    (the repo's largest capability, previously reachable from nothing) over
    the real income situation. The engine derives the bottleneck from
    dependency structure — it is not told the answer."""
    from foundation.ops_situation import analyse_ops_bottleneck, render_bottleneck
    print(render_bottleneck(analyse_ops_bottleneck()))
    return 0


def cmd_close_pack(args) -> int:
    """Print the close pack: every live deal at its submit line, the wall
    it stops at, the facts still needed from Kyle, and the ready-to-send
    drafts for the pure-inquiry ones. Offline; drafts nothing that asserts
    an unverified capability."""
    from foundation.close_pack import render_close_pack
    now = datetime.now(timezone.utc).strftime("%a %d %b %Y %H:%M UTC")
    print(render_close_pack(now_line=now))
    return 0


# The pipeline lives beside the other durable ledgers, and is gitignored
# for the same reason they are: it names counterparties the operator
# intends to approach, and this repository is public.
DEAL_LOG = Path(__file__).resolve().parent / "deal_pipeline_log.jsonl"


def cmd_deals(args) -> int:
    """Show the deal pipeline, or move one deal forward.

    Wired because `deal_pipeline.py` was built, seeded with twelve real
    positions, tested at 33 cases -- and reachable only by someone who
    knew to import it. This repository has already documented four
    mouths and one classifier that reached exactly that state, and the
    audit that found them called it the highest-severity finding of the
    session.
    """
    if getattr(args, "move", None):
        try:
            deal_id, stage = args.move.split(":", 1)
        except ValueError:
            print("REFUSED: --move expects DEAL_ID:STAGE, e.g. "
                  "pulse-security:APPROACHED", file=sys.stderr)
            return 1
        known = load_deals(DEAL_LOG)
        prior = known.get(deal_id.strip())
        if prior is None:
            print(f"REFUSED: no deal with id {deal_id.strip()!r}. Run "
                  "`deals` with no arguments to see the ids.",
                  file=sys.stderr)
            return 1
        next_action = args.next_action or prior.next_action
        if stage.strip() not in ("WON", "LOST", "PARKED") and not next_action.strip():
            print("REFUSED: a live deal needs a next action. Pass "
                  "--next-action.", file=sys.stderr)
            return 1
        try:
            moved = append_deal_event(
                DEAL_LOG, deal_id=prior.deal_id, counterparty=prior.counterparty,
                lane=prior.lane, stage=stage.strip(), next_action=next_action,
                money_observed=args.money or prior.money_observed,
                notes=prior.notes)
        except DealError as exc:
            print(f"REFUSED: {exc}", file=sys.stderr)
            return 1
        print(f"{moved.counterparty}: {prior.stage} -> {moved.stage}")
        return 0

    deals = load_deals(DEAL_LOG)
    board = DealBoard(deals=tuple(deals.values()))
    print(render_pipeline(board, stale_after_days=args.stale_after_days))
    return 0


def _looks_like_text(candidate: str) -> bool:
    """Is this actually readable text, or bytes that happened to decode?

    Judged on the share of printable characters, not on length: a caller
    may legitimately pass one real sentence, and refusing that would
    break the honest short-snippet case to catch the binary one.
    """
    if not candidate.strip():
        return False
    printable = sum(1 for ch in candidate if ch.isprintable() or ch.isspace())
    return printable / len(candidate) >= 0.85


def _rtf_to_text(raw: bytes) -> str:
    """Minimal RTF-to-text. Not a general RTF renderer -- enough to read
    a procurement document's words.

    WHY THIS EXISTS. Ireland's eTenders serves Irish Rail's CIE 7289
    penetration-testing qualification documents as RTF. Before this,
    RTF fell through to the plain-text branch, which returned 2.7
    MILLION characters of `\\rtlch\\fcs1\\af0\\afs20` control words and
    handed them to `assess_access()` as document text. That is the same
    failure as the .docx-named-.bin case this function's magic-byte
    check already exists to stop -- confident output over markup -- and
    it was sitting in front of the narrowest, most solo-operator-shaped
    cyber instrument found anywhere in the Irish register.

    Groups whose control word is in `_RTF_SKIP_GROUPS` are dropped
    entirely, contents included: `\\fonttbl`, `\\stylesheet` and friends
    hold hundreds of font and style NAMES which are otherwise
    indistinguishable from prose and would flood the result.
    """
    text = raw.decode("cp1252", errors="ignore")
    out: list[str] = []
    skip_depth = 0          # brace depth at which a skipped group began
    depth = 0
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "{":
            depth += 1
            i += 1
            continue
        if ch == "}":
            if skip_depth and depth <= skip_depth:
                skip_depth = 0
            depth -= 1
            i += 1
            continue
        if ch == "\\":
            m = _RTF_CONTROL.match(text, i)
            if not m:
                # An escaped literal: \{ \} \\
                if i + 1 < n and text[i + 1] in "{}\\":
                    if not skip_depth:
                        out.append(text[i + 1])
                    i += 2
                    continue
                i += 1
                continue
            word, arg = m.group(1), m.group(2)
            i = m.end()
            if i < n and text[i] == " ":
                i += 1          # a single trailing space delimits, not text
            if word == "'":
                pass            # handled below via _RTF_HEX
            if word in _RTF_SKIP_GROUPS and not skip_depth:
                skip_depth = depth
                continue
            if skip_depth:
                continue
            if word in ("par", "line", "row", "sect"):
                out.append("\n")
            elif word in ("tab", "cell"):
                out.append("\t")
            continue
        if not skip_depth:
            out.append(ch)
        i += 1
    joined = "".join(out)
    # \'xx is a single cp1252 byte written as hex -- decode it rather
    # than leaving `\'93` visible in the middle of a quoted clause.
    joined = _RTF_HEX.sub(
        lambda m: bytes([int(m.group(1), 16)]).decode("cp1252", "ignore"),
        joined)
    return joined


# Control-word groups whose CONTENTS are metadata, not prose. Dropped
# whole; keeping them buries the document in font and style names.
_RTF_SKIP_GROUPS = frozenset({
    "fonttbl", "colortbl", "stylesheet", "info", "listtable",
    "listoverridetable", "rsidtbl", "generator", "themedata",
    "colorschememapping", "latentstyles", "datastore", "pict",
    "xmlnstbl", "filetbl", "revtbl", "background", "shppict",
    "nonshppict", "objdata", "fchars", "lchars", "upr",
})
_RTF_CONTROL = re.compile(r"\\([a-zA-Z]+|')(-?\d+)?")
_RTF_HEX = re.compile(r"\\?'([0-9a-fA-F]{2})")


def _read_document_text(path: Path) -> str:
    """Extract text from a tender document.

    Handles the three shapes real tender packs actually arrive in --
    .docx, .pdf and plain text -- because those are what the Irish and
    PNG documents were, and a tool that only reads .txt would not have
    read any of them.

    Returns "" when nothing can be extracted, which `assess_access()`
    reports as NOT_ASSESSED rather than as a clean bill of health. That
    distinction matters here: PNG's own addendum is a scanned image with
    no extractable text, and a scanned page must never be mistaken for a
    page with no barriers on it.
    """
    # DETECT BY CONTENT, NOT BY EXTENSION.
    #
    # A real tender .docx handed over with a .bin extension fell through
    # to the plain-text branch, which read 752,954 characters of raw ZIP
    # bytes and reported NONE_DETECTED -- a confident clean verdict on
    # binary noise. Tender packs arrive from portals with whatever name
    # the download gave them, so extension is not something to trust.
    #
    # Magic bytes: "PK\x03\x04" is a ZIP, which is what a .docx is;
    # "%PDF" is a PDF.
    try:
        with path.open("rb") as fh:
            # Eight, not four: `{\rtf` is five bytes and a four-byte
            # read silently never matched it.
            head = fh.read(8)
    except OSError:
        return ""
    if head[:4] == b"PK\x03\x04":
        suffix = ".docx"
    elif head[:4] == b"%PDF":
        suffix = ".pdf"
    elif head[:5] == b"{\\rtf":
        suffix = ".rtf"
    else:
        suffix = path.suffix.lower()
    if suffix == ".docx":
        import zipfile
        try:
            xml = zipfile.ZipFile(path).read("word/document.xml").decode(
                "utf-8", errors="ignore")
        except (KeyError, zipfile.BadZipFile):
            return ""
        # PARAGRAPH BREAKS COME FROM THE CLOSING TAG, NOT THE OPENING
        # ONE. This previously substituted `<w:p[ >]` -- which eats the
        # `<` and the first character, leaving the REST of the opening
        # tag (`w14:paraId="672A6659" w:rsidR="006D172B" ...>`) as
        # ordinary text that the following tag-strip can no longer
        # match, because it no longer begins with `<`.
        #
        # Measured on RTE's real 25P041 Cyber Security DPS document,
        # 2026-09-03: 191,868 characters extracted, opening with
        # `w14:paraId=` and carrying Word revision-id attributes
        # throughout. `assess_access()` then scans that noise and counts
        # it as document text -- a barrier assessment run over markup.
        #
        # `</w:p>` has no attributes, so replacing it is unambiguous.
        text = xml.replace("</w:p>", "\n")
        return re.sub(r"<[^>]+>", "", text)
    if suffix == ".rtf":
        return _rtf_to_text(path.read_bytes())
    if suffix == ".pdf":
        try:
            import pypdf
        except ImportError:
            print("REFUSED: reading a PDF needs pypdf (pip install pypdf).",
                  file=sys.stderr)
            return ""
        try:
            reader = pypdf.PdfReader(str(path))
        except Exception:  # noqa: BLE001 - a malformed PDF is not a crash
            return ""
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    try:
        raw_text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    # A FILE THAT IS NOT TEXT MUST READ AS UNREADABLE, NOT AS PERMISSIVE.
    #
    # Eight bytes of binary decode under errors="ignore" to a short
    # non-empty string, which is truthy, which made `assess_entry()`
    # report NO_GATE_STATED -- a confident "this document states no
    # entry requirement" computed over noise. `assess_access()` had the
    # identical hole. Both callers already handle "" correctly as
    # NOT_ASSESSED; the fix belongs here, once, rather than as a length
    # check in each of them.
    #
    # Same failure family as the .docx attribute leak and the unparsed
    # .rtf above: output that looks like a verdict, computed over
    # something that was never read.
    if not _looks_like_text(raw_text):
        return ""
    return raw_text


def cmd_access(args) -> int:
    """Scan a tender document for barriers that have nothing to do with
    whether the operator qualifies.

    Wired as a document command rather than folded into `hunt`, because
    this module needs the tender DOCUMENT and a hunt only ever has the
    notice metadata. Running it over notice summaries would return
    NOT_ASSESSED on every entry and teach the operator to ignore it --
    which is how a real signal becomes noise.

    PNG's NPC/2026-26 is why this exists: zero eligibility criteria, and
    still unreachable behind a PGK5,000 document fee and a paper-only
    submission rule.
    """
    path = Path(args.document).expanduser()
    if not path.exists():
        print(f"REFUSED: no such file: {path}", file=sys.stderr)
        return 1
    text = _read_document_text(path)
    assessment = assess_access(text)
    print(f"document : {path.name}")
    print(f"extracted: {len(text)} characters")
    if not text.strip():
        print("NOTE     : nothing extractable. A scanned image reads the "
              "same as a clean document from here -- open it yourself.")
    print()
    print(format_access(assessment))
    return 0


def cmd_deep_ireland(args) -> int:
    """Walk Ireland's whole open register rather than its first 200 rows.

    WHY THIS IS A SEPARATE COMMAND AND NOT A `hunt` FLAG. A routine hunt
    is seven sources and finishes in seconds. This is ~293 sequential
    requests against one public government server and takes ten minutes.
    Folding it into `hunt` would put that load on every sweep, including
    every cron tick -- so it is deliberately a thing the operator asks
    for.

    It exists because the 20-page routine sweep reaches 7% of the
    register, and on 2026-09-03 the other 93% held nine cyber
    qualification systems with no closing date, every one of them
    invisible to this project for its whole campaign.
    """
    if not args.live:
        print("DRY RUN (default) -- no network request will be made.")
        print(f"  target      : {mouth_etenders_ie.RESULTS_URL}")
        print(f"  order       : stable title sort (not recency -- a "
              f"ten-minute walk in recency order loses rows across page "
              f"boundaries it has already passed)")
        print(f"  max pages   : {args.max_pages}  "
              f"({args.max_pages * 10} notices at 10 rows/page)")
        print(f"  throttle    : {args.throttle_seconds}s between pages")
        print(f"  estimated   : ~{int(args.max_pages * (args.throttle_seconds + 1) / 60)} minutes")
        print("Pass --live to actually fetch.")
        return 0

    walk = mouth_etenders_ie.deep_sweep(
        max_pages=args.max_pages, throttle_seconds=args.throttle_seconds)

    print(f"pages fetched : {walk.pages_walked}")
    print(f"notices       : {len(walk.items)}")
    print(f"complete      : {walk.complete}")
    print(f"stopped       : {walk.stopped_because}")
    if not walk.complete:
        # The load-bearing line. A truncated walk that reads as a whole
        # one turns "Ireland has no security tender" into a conclusion
        # drawn from the part that happened to be read.
        print()
        print("WARNING: this walk did NOT reach the end of the register. "
              "The notices below are a PREFIX of it, not the whole thing "
              "-- do not read an absence here as an absence in Ireland.")

    shown = walk.items if args.all else walk.security_relevant
    print()
    print(f"showing {len(shown)} "
          f"{'notices' if args.all else 'security-relevant notices'}")
    print()
    for item in sorted(shown, key=lambda i: i.get("deadline", "") or "zzz"):
        deadline = item.get("deadline", "").strip()
        # An empty deadline is not missing data on this source: it is
        # the defining property of a Dynamic Purchasing / Qualification
        # System, which never closes. Say so rather than printing a gap.
        marker = deadline if deadline else "NO CLOSING DATE (rolling admission)"
        print(f"  {marker}")
        print(f"    {item.get('title', '')[:100]}")
        print(f"    {item.get('organisation', '')[:70]}  "
              f"value={item.get('value_text', '') or 'UNKNOWN'}")
        print(f"    {item.get('link', '')}")
    return 0


def cmd_partner_needs(args) -> int:
    """Given a tender document, print exactly what a delivery partner
    would have to supply to make it winnable -- the capability gaps the
    operator cannot clear himself.

    The commercial thesis in one command: every opportunity gated on a
    held credential, a turnover figure, references, or local staffing is
    a partner-shaped opportunity. This reuses entry_gate; it invents no
    requirement the document did not state. It is NOT a matched partner
    and NOT authority to contact anyone.
    """
    path = Path(args.document)
    if not path.exists():
        print(f"REFUSED: no such document: {path}", file=sys.stderr)
        return 1
    text = _read_document_text(path)
    print(f"document : {path.name}")
    if not text.strip():
        print("NOTE     : nothing extractable -- a scanned image reads the "
              "same as a permissive document from here.")
    print()
    print(format_partner_needs(derive_partner_needs(assess_entry(text))))
    return 0


def cmd_gates(args) -> int:
    """Read a tender document for what it costs the OPERATOR to start.

    Separate from `access` on purpose. `access` answers "can this notice
    be reached at all" -- fees, paper-only submission, site visits.
    This answers a different question that no other surface in this
    repository answers: which requirements need Kyle personally, which
    close by doing work or partnering, and which the document itself
    defers until after admission.

    That last column is the one worth having. Iarnrod Eireann and RTE
    make the identical insurance demand; one is a Pass/Fail gate at
    admission and the other applies only once you have been selected to
    call-off. A tool that reports both as "insurance required" throws
    away the difference between a wall and a later errand.
    """
    path = Path(args.document)
    if not path.exists():
        print(f"REFUSED: no such document: {path}", file=sys.stderr)
        return 1
    text = _read_document_text(path)
    print(f"document : {path.name}")
    print(f"extracted: {len(text)} characters")
    if not text.strip():
        print("NOTE     : nothing extractable. A scanned image reads the "
              "same as a permissive document from here -- open it yourself.")
    print()
    print(format_entry(assess_entry(text)))
    return 0


# Tuned to Swiss Post's e-voting specifications, which is the only real
# corpus this has been run against. Exposed as flags rather than frozen,
# because a different specification numbers its algorithms differently
# and a checker that silently finds nothing is worse than one that
# refuses.
_DEFAULT_DEFINITION_PATTERN = r"Algorithm\s+(\d+\.\d+)\s+([A-Z][A-Za-z0-9]{3,60})"
_DEFAULT_REFERENCE_PATTERN = r"[Aa]lgorithm\s+(\d+\.\d+)"


def cmd_spec(args) -> int:
    """Cross-reference a specification, and optionally trace a term
    across several of them.

    WHY THIS COMMAND EXISTS. `spec_crossref.py` was built with 39 tests
    and reachable only from a Python shell -- the third time in three
    days a capability in this repository has been finished and left
    unwired (the Denmark and Netherlands mouths sat outside the source
    registry; `deep_sweep()` sat outside the CLI). A capability nobody
    can invoke is not a capability.

    It found the SGSP documentation candidate on Swiss Post's e-voting
    corpus: 'SGSP' appears 43 times in the computational proof and zero
    times in the two specifications that implement the control
    protecting it.
    """
    docs: dict = {}
    for raw_path in args.documents:
        path = Path(raw_path)
        if not path.exists():
            print(f"REFUSED: no such document: {path}", file=sys.stderr)
            return 1
        text = _read_document_text(path)
        if not text.strip():
            # Never silently treat an unreadable file as an empty one --
            # a scanned PDF and a clean one look identical from here.
            print(f"NOTE: nothing extractable from {path.name} -- it is "
                  f"counted as read with zero content, which is why the "
                  f"renders below say so rather than implying absence.",
                  file=sys.stderr)
        docs[path.name] = text

    if args.trace:
        print(format_term_coverage(trace_term(
            args.trace, docs,
            aliases=tuple(args.alias) if args.alias else None)))
        print()

    for name, text in docs.items():
        report = crossref(
            text,
            definition_pattern=args.definition_pattern,
            reference_pattern=args.reference_pattern,
            report_unreferenced=args.unreferenced,
        )
        print(f"--- {name} ({len(text):,} chars)")
        print(format_crossref(report))
        print()
    return 0


def cmd_fat_notice(args) -> int:
    """Read a UK Find a Tender notice's REAL bidder criteria by OCID and
    run them through the entry-gate barrier analysis.

    The free-text UK feed carries no criteria, so every UK notice comes
    back INSUFFICIENT_DATA. The public keyless OCDS release endpoint
    carries the authoritative selection criteria. This resolved a real
    question 2026-09-05: the City of Bradford penetration-testing
    framework (ocds-h6vhtk-06e59c) shows ZERO stated barriers.
    """
    ocid = args.ocid.strip()
    objective = (f"read one named OCDS release, {ocid}, to assess the "
                 f"bidder qualification barriers stated on a UK Find a "
                 f"Tender notice")
    if not args.live:
        print("DRY RUN (default) -- no network request will be made.")
        print(f"  ocid      : {ocid}")
        print(f"  endpoint  : {mouth_find_a_tender_uk.OCDS_RELEASE_URL.format(ocid=ocid)}")
        print("Pass --live to actually fetch.")
        return 0
    policy = _build_policy(objective, args.max_queries,
                           args.max_wall_clock_seconds, args.max_results)
    try:
        release = mouth_find_a_tender_uk.fetch_release(ocid, policy)
    except Exception as exc:  # noqa: BLE001 -- named refusal, never a traceback
        print(f"FETCH FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    text = mouth_find_a_tender_uk.release_assessable_text(release)
    tender = release.get("tender", {})
    print(f"notice : {tender.get('title', ocid)}")
    val = tender.get("value") or {}
    print(f"value  : {val.get('amountGross')} {val.get('currency','')}"
          f"   status: {tender.get('status')}"
          f"   closes: {(tender.get('tenderPeriod') or {}).get('endDate')}")
    print(f"criteria text: {len(text)} characters")
    print()
    print(format_entry(assess_entry(text)))
    return 0


def cmd_triage(args) -> int:
    """Measure whether a delivered corpus contains buildable substance or
    is descriptive scaffolding.

    The question performed by hand on every corpus delivered this session
    (the Swiss Post e-voting docs, the specs). It reports measured facts
    and one routing verdict -- IMPLEMENTABLE / MIXED / SCAFFOLD_ONLY /
    UNASSESSED_CODE / EMPTY -- and never decides worth: a human decides
    what to do with the verdict.

    UNASSESSED_CODE is the honest answer for source in a language the
    triage cannot parse (Java, Rust, Go...): it will not call code it
    cannot read scaffolding.
    """
    root = Path(args.directory)
    if not root.is_dir():
        print(f"REFUSED: not a directory: {root}", file=sys.stderr)
        return 1
    report = triage_corpus(root)
    print(report.show_the_measurements())
    return 0


def cmd_pit(args) -> int:
    """Read a Public Intrusion Test / bounty final report for how
    contested its target already is: acceptance rate, duplicate rate,
    and the confirmed findings that actually paid.

    Answers the question mouth_bounty and income_watch cannot: not "does
    this programme exist" but "is there anything left in it". The 2026
    Swiss Post report reads 85 submitted, 6 confirmed (7%), 23
    duplicates (27%) -- the obvious findings are gone, and both paying
    ones came from the invitation-only tier.
    """
    path = Path(args.report)
    if not path.exists():
        print(f"REFUSED: no such report: {path}", file=sys.stderr)
        return 1
    text = _read_document_text(path)
    if not text.strip():
        print(f"NOTE: nothing extractable from {path.name}.", file=sys.stderr)
    print(f"report: {path.name}")
    print()
    print(format_pit_summary(summarise_pit_report(text)))
    return 0


def cmd_reachability(args) -> int:
    """Report which capabilities can actually be invoked.

    Built after the third module in three days was finished, tested and
    left unreachable. Deliberately a report and not a gate: 23 of 90
    tested modules were unreachable when first measured, and a check
    that fires 23 times on every sweep is one people learn to scroll
    past.
    """
    print(format_reachability(
        scan_reachability(REPO_ROOT, package=args.package),
        verbose=args.verbose))
    return 0


def cmd_profile(args) -> int:
    try:
        loaded = load_operator_profile()
    except ProfileLoadError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1
    _print_profile_notice(loaded)
    p = loaded.operator
    print(f"name                 : {p.name}")
    print(f"staff_count          : {p.staff_count}")
    print(f"certifications       : {sorted(p.certifications) or '(none declared)'}")
    print(f"insurance_cover_eur  : {p.insurance_cover_eur}")
    print(f"corporate_references : {list(p.corporate_references) or '(none declared)'}")
    print(f"languages            : {sorted(p.languages)}")
    f = loaded.business_facts
    print()
    print("business_facts (used by 'dossier'):")
    print(f"  abn                    : {f.abn}")
    print(f"  acn                    : {f.acn}")
    print(f"  business_address       : {f.business_address}")
    print(f"  licence_number         : {f.licence_number}")
    print(f"  registration_number    : {f.registration_number}")
    print(f"  insurance_policy_number: {f.insurance_policy_number}")
    print(f"  insurance_pi_cover_aud : {f.insurance_pi_cover_aud}")
    print(f"  insurance_pl_cover_aud : {f.insurance_pl_cover_aud}")
    print(f"  years_experience       : {f.years_experience}")
    print(f"  revenue_band           : {f.revenue_band}")
    print(f"  skills                 : {list(f.skills) or '(none declared)'}")
    print(f"  referees               : {len(f.referees)} declared")
    return 0


def _add_hunt_style_args(sp, default_limit: int = 50) -> None:
    sp.add_argument("--keyword", default=_DEFAULT_KEYWORD,
                     help=f"plain keyword to hunt for (default: {_DEFAULT_KEYWORD!r})")
    sp.add_argument("--ted-query", default=None,
                     help='TED expert-query override, e.g. \'FT ~ ("penetration testing")\'. '
                          "Default is derived from --keyword.")
    sp.add_argument("--objective", default=None,
                     help="override the discovery objective text recorded on the policy")
    sp.add_argument("--live", action="store_true",
                     help="actually fetch over the network. Default is dry-run.")
    sp.add_argument("--authorised-by", default="",
                     help="who authorised this run (recorded, not enforced)")
    sp.add_argument("--limit", type=int, default=default_limit,
                     help="max notices to request from TED (default: 50)")
    sp.add_argument("--published-within-days", type=int,
                     default=_DEFAULT_PUBLISHED_WITHIN_DAYS,
                     help="bound the TED query to notices published in the "
                          f"last N days (default: {_DEFAULT_PUBLISHED_WITHIN_DAYS}). "
                          "0 sweeps the entire archive, including notices "
                          "that closed years ago. Ignored when --ted-query "
                          "is given.")
    sp.add_argument("--max-queries", type=int, default=DEFAULT_MAX_QUERIES)
    sp.add_argument("--max-wall-clock-seconds", type=int,
                     default=DEFAULT_MAX_WALL_CLOCK_SECONDS)
    sp.add_argument("--max-results", type=int, default=DEFAULT_MAX_RESULTS)


def build_parser() -> "object":
    import argparse

    parser = argparse.ArgumentParser(
        prog="python3 -m foundation.operator_cli",
        description="Run the procurement-hunt chain from the command line. "
                     "Dry-run by default for anything that touches the network.")
    sub = parser.add_subparsers(dest="command")

    p_hunt = sub.add_parser("hunt", help="run one multi-source hunt, print the ranked report")
    _add_hunt_style_args(p_hunt)
    p_hunt.add_argument("--print-limit", type=int, default=None,
                         help="only print the first N entries (default: all)")
    p_hunt.set_defaults(func=cmd_hunt)

    p_brief = sub.add_parser("brief", help="run a hunt, print the morning brief")
    _add_hunt_style_args(p_brief)
    p_brief.add_argument("--closing-within-days", type=int, default=14,
                          help="ACTION REQUIRED window in days (default: 14)")
    p_brief.set_defaults(func=cmd_brief)

    p_loop = sub.add_parser("loop", help="run the unattended hunt loop")
    _add_hunt_style_args(p_loop, default_limit=50)
    p_loop.add_argument("--interval", type=int, default=3600,
                         help="seconds to sleep between cycles (default: 3600)")
    p_loop.add_argument("--max-cycles", type=int, default=None,
                         help="stop after N cycles (default: run until killed/stopped)")
    p_loop.set_defaults(func=cmd_loop)

    p_income = sub.add_parser(
        "income", help="watch non-procurement income sources (bug bounty "
                        "programs, HN contract-security gigs) for new listings")
    p_income.add_argument("--objective", default=None,
                           help="override the discovery objective text recorded on the policy")
    p_income.add_argument("--live", action="store_true",
                           help="actually fetch over the network. Default is dry-run.")
    p_income.add_argument("--max-queries", type=int, default=DEFAULT_MAX_QUERIES)
    p_income.add_argument("--max-wall-clock-seconds", type=int,
                           default=DEFAULT_MAX_WALL_CLOCK_SECONDS)
    p_income.add_argument("--max-results", type=int, default=DEFAULT_MAX_RESULTS)
    p_income.add_argument("--print-limit", type=int, default=None,
                           help="only print the first N entries (default: all)")
    p_income.set_defaults(func=cmd_income)

    p_dossier = sub.add_parser(
        "dossier", help="render the supplier dossier and missing-facts list")
    p_dossier.set_defaults(func=cmd_dossier)

    p_deals = sub.add_parser(
        "deals", help="show the deal pipeline, or move a deal forward")
    p_deals.add_argument(
        "--move", metavar="DEAL_ID:STAGE",
        help="move one deal to a new stage, e.g. pulse-security:APPROACHED")
    p_deals.add_argument(
        "--next-action", default="",
        help="the next action after the move (required unless terminal)")
    p_deals.add_argument(
        "--money", default="",
        help="observed money, only valid on a WON deal, e.g. '2500 AUD'")
    p_deals.add_argument(
        "--stale-after-days", type=int, default=7,
        help="flag live deals untouched this long (default 7)")
    p_deals.set_defaults(func=cmd_deals)

    p_access = sub.add_parser(
        "access",
        help="scan a tender document for fees, paper-only submission and "
             "other barriers unrelated to qualification")
    p_access.add_argument("document",
                          help="path to a .pdf, .docx or text tender document")
    p_access.set_defaults(func=cmd_access)

    p_deep = sub.add_parser(
        "deep-ireland",
        help="walk Ireland's ENTIRE open tender register (~2,900 notices, "
             "~293 pages, ~10 minutes) instead of the 200 rows a routine "
             "hunt reaches")
    p_deep.add_argument("--live", action="store_true",
                        help="actually fetch over the network. Default is dry-run.")
    p_deep.add_argument("--max-pages", type=int,
                        default=mouth_etenders_ie.DEEP_MAX_PAGES,
                        help="stop after N pages (default: "
                             f"{mouth_etenders_ie.DEEP_MAX_PAGES}). A walk that "
                             "stops here is reported as INCOMPLETE.")
    p_deep.add_argument("--throttle-seconds", type=float,
                        default=mouth_etenders_ie.DEEP_THROTTLE_SECONDS,
                        help="courtesy pause between page fetches against a "
                             "public government server (default: "
                             f"{mouth_etenders_ie.DEEP_THROTTLE_SECONDS})")
    p_deep.add_argument("--all", action="store_true",
                        help="print every notice, not only the "
                             "security-relevant ones")
    p_deep.set_defaults(func=cmd_deep_ireland)

    p_pneeds = sub.add_parser(
        "partner-needs",
        help="given a tender document, print what a delivery partner would "
             "have to supply to make it winnable (the gaps you cannot clear "
             "yourself)")
    p_pneeds.add_argument("document",
                          help="path to a .pdf/.docx/.rtf/text tender document")
    p_pneeds.set_defaults(func=cmd_partner_needs)

    p_gates = sub.add_parser(
        "gates",
        help="read a tender document for what it costs YOU to start: which "
             "requirements need you personally, which close by doing the "
             "work, and which the document defers until after admission")
    p_gates.add_argument("document",
                         help="path to a .pdf, .docx, .rtf or text document")
    p_gates.set_defaults(func=cmd_gates)

    p_spec = sub.add_parser(
        "spec",
        help="cross-reference a technical specification against itself, and "
             "trace whether a named assumption is mentioned in the documents "
             "that implement it")
    p_spec.add_argument("documents", nargs="+",
                        help="one or more .pdf/.docx/.rtf/text specifications")
    p_spec.add_argument("--trace", default=None, metavar="TERM",
                        help="report which documents mention TERM and which "
                             "do not (e.g. --trace SGSP)")
    p_spec.add_argument("--alias", action="append", default=None,
                        help="another spelling of --trace TERM; repeatable")
    p_spec.add_argument("--definition-pattern",
                        default=_DEFAULT_DEFINITION_PATTERN,
                        help="regex capturing (identifier, name) at a "
                             "definition site")
    p_spec.add_argument("--reference-pattern",
                        default=_DEFAULT_REFERENCE_PATTERN,
                        help="regex capturing (identifier) at a citation")
    p_spec.add_argument("--unreferenced", action="store_true",
                        help="also report identifiers cited neither by "
                             "number nor by name anywhere")
    p_spec.set_defaults(func=cmd_spec)

    p_fat = sub.add_parser(
        "fat-notice",
        help="read a UK Find a Tender notice's real bidder criteria by OCID "
             "(via the public OCDS release API) and analyse its entry gates")
    p_fat.add_argument("ocid", help="the OCDS id, e.g. ocds-h6vhtk-06e59c")
    p_fat.add_argument("--live", action="store_true",
                       help="actually fetch. Default is dry-run.")
    p_fat.add_argument("--max-queries", type=int, default=DEFAULT_MAX_QUERIES)
    p_fat.add_argument("--max-wall-clock-seconds", type=int,
                       default=DEFAULT_MAX_WALL_CLOCK_SECONDS)
    p_fat.add_argument("--max-results", type=int, default=DEFAULT_MAX_RESULTS)
    p_fat.set_defaults(func=cmd_fat_notice)

    p_triage = sub.add_parser(
        "triage",
        help="measure whether a delivered corpus is buildable substance or "
             "descriptive scaffolding (structural template ratio, real vs "
             "constant-return code, unparsed-language honesty)")
    p_triage.add_argument("directory", help="path to the corpus directory")
    p_triage.set_defaults(func=cmd_triage)

    p_pit = sub.add_parser(
        "pit",
        help="read a public-intrusion-test / bounty final report for how "
             "contested a target already is (acceptance rate, duplicates, "
             "what paid)")
    p_pit.add_argument("report", help="path to a PIT final report (.pdf/.txt)")
    p_pit.set_defaults(func=cmd_pit)

    p_reach = sub.add_parser(
        "reachability",
        help="report which tested modules can actually be invoked, and "
             "which exist only in their own test file")
    p_reach.add_argument("--package", default="foundation",
                         help="package directory to scan (default: foundation)")
    p_reach.add_argument("--verbose", action="store_true",
                         help="also list the reached modules and their importers")
    p_reach.set_defaults(func=cmd_reachability)

    p_profile = sub.add_parser(
        "profile", help="show the currently configured operator profile")
    p_profile.set_defaults(func=cmd_profile)

    p_digest = sub.add_parser(
        "digest",
        help="produce the end-of-run operator digest (dashboard + telegram "
             "dry-run/send + top moves) in one command")
    p_digest.add_argument(
        "--html-out", default=None,
        help="where to write the phone dashboard HTML "
             "(default: digest_out/ops_digest.html)")
    p_digest.set_defaults(func=cmd_digest)

    p_close = sub.add_parser(
        "close-pack",
        help="every live deal at its submit line: the wall, the facts still "
             "needed from Kyle, and ready-to-send inquiry drafts")
    p_close.set_defaults(func=cmd_close_pack)

    p_situation = sub.add_parser(
        "situation",
        help="bottleneck analysis over the real income situation, computed by "
             "situation_analysis (not asserted)")
    p_situation.set_defaults(func=cmd_situation)

    p_portfolio = sub.add_parser(
        "portfolio",
        help="assemble the WHOLE tendering portfolio (opps + drafts + full "
             "intelligence + archive) into one folder, fresh")
    p_portfolio.add_argument("--out", required=True,
                             help="destination folder for the bundle")
    p_portfolio.add_argument("--zip", action="store_true",
                             help="also write <out>.zip")
    p_portfolio.set_defaults(func=cmd_portfolio)

    p_team = sub.add_parser(
        "team-payload",
        help="build the end-of-cycle ZIP payload for Kyle's team (portfolio + "
             "TEAM_TARGETS — the contracts a team can win)")
    p_team.add_argument("--out", required=True, help="destination folder")
    p_team.add_argument("--zip", action="store_true", help="also write <out>.zip")
    p_team.set_defaults(func=cmd_team_payload)

    p_fit = sub.add_parser(
        "team-fit",
        help="rank the live team targets by winnability against a declared "
             "team capability profile (honest: undeclared = UNKNOWN, never a pass)")
    p_fit.add_argument("--turnover", type=float, default=0.0,
                       help="team annual turnover in EUR")
    p_fit.add_argument("--insurance", type=float, default=0.0,
                       help="highest single insurance cover the team holds, EUR")
    p_fit.add_argument("--can-raise-insurance", action="store_true",
                       help="team is willing/able to raise cover if awarded")
    p_fit.add_argument("--references", type=int, default=0,
                       help="number of deliverable corporate reference contracts")
    p_fit.add_argument("--largest-reference", type=float, default=0.0,
                       help="value of the largest single reference, EUR")
    p_fit.add_argument("--languages", default="",
                       help="comma-separated languages, e.g. english,german")
    p_fit.add_argument("--soc", action="store_true",
                       help="team delivers 24x7x365 SOC / incident response")
    p_fit.add_argument("--capabilities", default="",
                       help="comma-separated capability tags, e.g. soc,mdr,siem")
    p_fit.add_argument("--named-testers", type=int, default=0,
                       help="number of named pen-testers (for tester-count reqs)")
    p_fit.add_argument("--out", help="write the report to this file instead of stdout")
    p_fit.set_defaults(func=cmd_team_fit)

    p_sub = sub.add_parser(
        "submission-prep",
        help="assemble a ready-to-file submission pack for one target "
             "(portal, checklist, ESPD answers) — stops at the human Submit")
    p_sub.add_argument("--target", required=True,
                       help="target id, e.g. IE_HSA (see team-payload / OPS_BOARD)")
    p_sub.add_argument("--profile",
                       help="path to a team profile JSON (legal_name, registration, "
                            "annual_turnover_eur, insurance_cover, references, ...)")
    p_sub.add_argument("--out", help="write the pack to this file instead of stdout")
    p_sub.set_defaults(func=cmd_submission_prep)

    p_sec = sub.add_parser(
        "security-report",
        help="automated email-security report for a domain (SPF/DMARC/DKIM/"
             "DNSSEC/MX) from public DNS — the first sellable deliverable")
    p_sec.add_argument("--domain", required=True, help="domain to check, e.g. acme.com")
    p_sec.add_argument("--out", help="write the report to this file instead of stdout")
    p_sec.set_defaults(func=cmd_security_report)

    return parser


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        # No arguments at all must still print something useful.
        parser.print_help()
        print()
        try:
            loaded = load_operator_profile()
            _print_profile_notice(loaded)
        except ProfileLoadError as exc:
            print(f"NOTE: {exc}", file=sys.stderr)
        return 0
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    try:
        return args.func(args)
    except ProfileLoadError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
