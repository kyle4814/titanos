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
  - `foundation.sources.sources_for_query()` -- the standard three-source
    registry.
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
from foundation.hunt import HuntReport, hunt_multi, render_hunt
from foundation.hunt_loop import HUNT_STOP_FILENAME, render_hunt_cycle, run_hunt_loop
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
    ted_query = args.ted_query or f'FT ~ ("{keyword}")'
    objective = args.objective or (
        f"observe public procurement notices matching keyword "
        f"{keyword!r} across TED, NZ GETS and UK Contracts Finder for "
        f"operator {loaded.operator.name!r}")

    if not args.live:
        print("DRY RUN (default) -- no network request will be made.")
        print(f"  objective   : {objective}")
        print(f"  keyword     : {keyword}")
        print(f"  TED query   : {ted_query}")
        print("  sources     : TED, NZ_GETS, UK_CONTRACTS_FINDER")
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
    ted_query = args.ted_query or f'FT ~ ("{keyword}")'
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

    p_profile = sub.add_parser(
        "profile", help="show the currently configured operator profile")
    p_profile.set_defaults(func=cmd_profile)

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
