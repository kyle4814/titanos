"""Swarm Contract — the one entry point a Sonnet agent invokes instead of
calling `opportunity_cycle`, `tender_radar`, or `discovery_authorization`
directly.

WHY THIS EXISTS

`.claude/commands/next.md` states the constraint explicitly: "if a
capability can only be operated by the smartest available model, it is
not yet finished." `foundation/opportunity_cycle.py::run_cycle()` is
already safe in the sense that it never fabricates a qualified lead, a
contract, or cash -- but it is safe because of things a *caller* must
already know: which `fetch_fn` goes live vs. stays offline, that
`state_dir` and `ledger_path` are two different directories with two
different write disciplines, and that `discovery_authorization`'s
exceptions (`UnboundedDiscoveryObjective`, `CommunicationDenied`,
`DiscoveryBudgetExhausted`) can surface as raw Python exceptions through
`run_cycle()` if the live path is ever taken. A Sonnet agent reading
`opportunity_cycle.py` cold has no reason to know any of that. This
module is the difference between "an Opus operator who has read five
other files can drive this safely" and "the safe path is the only path
that exists."

DOES `layer0_worker.Layer0Worker` FIT? NO -- AND HERE IS THE EVIDENCE,
NOT AN ASSERTION.

`Layer0Worker` is a 14-step autonomous-worker lifecycle
(BOOT/OBSERVE/MAP/CHECK_EXISTING/GENERATE_OPTIONS/SCORE_FRONTIER/
SELECT_LEVER/REQUEST_PERMISSION_IF_REQUIRED/EXECUTE_MINIMUM/VERIFY/
MEASURE_YIELD/PRESERVE_PROVENANCE/UPDATE_STATE/RECOMMEND_NEXT/HALT) with
four MANDATORY abstract hooks (`check_existing`, `verify`,
`preserve_provenance`, `update_state`) a subclass must implement with
real domain logic before it can even be instantiated. What this task
needs is the opposite shape: one deterministic function, called once,
with an explicit typed input and a typed output -- no multi-option
generation, no `select_lever`, no `recommend_next`. Forcing this task
through `Layer0Worker` would mean inventing answers to questions that do
not apply here (what does "check_existing" mean for a single sweep
call? what "option" would `generate_options` produce when there is
exactly one action -- sweep or don't?) purely to satisfy an unrelated
contract shape. That is building the wrong abstraction to reuse a name,
which `TITANOS_GO_CYCLE_DOCTRINE.md` §V (verify *behavior*, not name)
and Beta's "never rebuild without proving insufficiency" standard both
argue against in the other direction -- the point here is a worker
contract does NOT fit a single stateless call/response envelope, not
that this module should be built as a competing worker type. Nothing in
`foundation/swarm_contract.py` inherits from or wraps `Layer0Worker`.
If a future cycle actually builds a scheduled, multi-cycle, option-
generating opportunity worker, THAT is where `Layer0Worker` belongs --
not here.

WHAT THIS REUSES RATHER THAN DUPLICATES

- `foundation.opportunity_cycle.run_cycle()` -- the one composed
  tender-radar -> pipeline chain. Not re-implemented.
- `foundation.discovery_authorization.DiscoveryPolicy` /
  `authorize_discovery()` -- objective validation and standing-scope
  checking, reused directly rather than re-deriving the same regexes.
- `foundation.outcome_ledger.OutcomeLedger` -- including its own
  documented `ledger_path=None` in-memory-only mode, which is what makes
  dry-run genuinely writeless rather than "writeless if you remember to
  delete the file after."

STRUCTURAL GUARANTEES (each is a property of the code, not a promise)

1. DRY-RUN BY DEFAULT. `SwarmTaskDescriptor.live` defaults to `False`.
   When `live` is `False`, `run_swarm_task()` never imports, constructs,
   or calls anything that touches a filesystem path or a socket -- it
   returns after validation. There is no code path from
   `live=False` to `tender_radar.sweep()`, `OutcomeLedger(...)` with a
   real path, or any `os`/`pathlib` write call. Verified by test:
   `state_dir` and `ledger_path` are asserted absent from disk after a
   dry run.
2. GOING LIVE REQUIRES TWO EXPLICIT SIGNALS, NOT ONE. `live=True` alone
   is refused -- `authorized_by` (a non-empty name) must also be set.
   A caller flipping one boolean by pattern-matching "the safe default
   is probably False, let me just set it True" still lands on a named
   refusal, not a live run.
3. NO OUTBOUND SEND, EVER. This module imports no networking, mail, or
   webhook library, directly or transitively beyond what
   `opportunity_cycle`/`tender_radar` already import (`urllib.request`,
   used only inside the discovery-gated fetch path this module never
   bypasses). There is no `send`, `notify`, `post`, or `webhook`
   function anywhere in this file's public surface.
4. NO WRITE OUTSIDE THE DECLARED LEDGER PATH. The only path this module
   ever opens for writing is `descriptor.ledger_path`, passed straight
   into `OutcomeLedger(ledger_path=...)` -- exactly the object that
   already refuses to write when constructed with `None`. This module
   constructs no ledger of its own and opens no second file handle
   anywhere in its own code.
5. BUDGET IS A NAMED CEILING, NOT A SUGGESTION. A descriptor requesting
   `max_queries`/`max_wall_clock_seconds`/`max_results` above this
   repository's own standing `discovery_authorization` defaults is
   refused before any action, naming the exact field that exceeded the
   ceiling. If the underlying fetch still exhausts its budget mid-sweep
   (`DiscoveryBudgetExhausted`, raised by `discovery_authorization.
   spend_query()` before a socket opens), this module catches it and
   returns a structured `BUDGET_EXHAUSTED` result -- it never lets that
   exception propagate as a bare traceback to the caller.
6. `qualified`, `contracts`, and `cash` ARE LITERAL ZEROS IN THIS
   MODULE'S OWN CODE, NOT COPIED FROM UPSTREAM. `opportunity_pipeline.
   PipelineReport` already hardcodes all three to `0` and this module
   trusts that -- but belt-and-suspenders: `SwarmTaskResult.__post_init__`
   raises `AssertionError` if any of the three is ever constructed
   non-zero, so even a future accidental change upstream cannot silently
   flow a nonzero value through this envelope's own output type.
7. EVERY REFUSAL NAMES THE CONSTRAINT. `SwarmTaskResult.status` is one
   of a fixed, named set (see `STATUSES` below); `refused_by` names
   exactly which check produced the refusal; `reason` is a human-
   readable sentence, never a raw exception repr. No bare exception ever
   crosses `run_swarm_task()`'s boundary -- the one outer `except
   Exception` clause exists specifically to make that a structural
   guarantee, not a best-effort one.

OPTIONAL SHORTLIST: THE GAP THIS CYCLE CLOSES

`foundation/shortlist.py` (`build_shortlist()` / `render_digest()`) was
IMPLEMENTED_UNWIRED -- an agent running a cycle through this module got
counts (`signal_count`, `controlling_party_count`, ...) but never the
one thing a human actually wants to read: a ranked, skimmable digest.
`SwarmTaskDescriptor.shortlist_profile` (optional, `None` by default)
and `.shortlist_limit` close that gap without changing anything about
guarantees 1-7 above:

- Supplying a profile changes NOTHING about whether a task goes live --
  `live`/`authorized_by` still gate that exactly as before. A dry run
  with a profile still performs zero sweeps and zero writes (guarantee
  1); it reports `shortlist_status=SHORTLIST_SKIPPED_DRY_RUN` rather
  than fabricating a digest from data that was never fetched.
- Not supplying a profile is the default and produces
  `shortlist_status=SHORTLIST_NOT_REQUESTED` with an empty digest --
  explicit, not an empty-looking-like-"nothing matched" digest (see
  `shortlist.py`'s own "MISSING FIELDS ARE UNKNOWN, NEVER A GUESS"
  discipline, restated here one level up).
- Only a `LIVE_OK` run with a profile produces
  `shortlist_status=SHORTLIST_PRODUCED` and a real `shortlist_digest`.
  `render_digest()` is called exactly once, its return value is stored
  as data on the result -- this module never calls `print()`.

OPTIONAL WATCH: "WHAT CHANGED SINCE LAST TIME" WITHOUT A SECOND TOOL

`foundation/opportunity_watch.py` (`new_since()` / `closing_within()` /
`watch_report()`) existed, was tested, and answered the two questions an
operator actually has -- what is NEW since the last run, and what is
CLOSING SOON -- but had no production caller. An operator running this
envelope daily re-read yesterday's full digest with no indication of
what changed. `SwarmTaskDescriptor.watch_state_path` (optional, `None`
by default) and `.watch_closing_within_days` close that gap without
changing anything about guarantees 1-7 above:

- Supplying `watch_state_path` changes NOTHING about whether a task goes
  live -- `live`/`authorized_by` still gate that exactly as before. A
  dry run with a watch state path still performs zero sweeps and zero
  writes (guarantee 1) -- it reports `watch_status=WATCH_SKIPPED_DRY_RUN`
  and, critically, never calls `opportunity_watch.new_since()`, so a dry
  run cannot advance the seen-set even accidentally. This is the single
  most important property this field adds: if a dry run ever marked a
  signal seen, the very next LIVE run would silently report it as not
  new, and an operator would never learn a real notice existed.
- Not supplying `watch_state_path` is the default and produces
  `watch_status=WATCH_NOT_REQUESTED` with every watch_* count at its
  honest zero -- explicit, not an empty-looking-like-"nothing changed"
  result. Watch-disabled behaviour is byte-identical to before this
  field existed.
- Only a `LIVE_OK` run with `watch_state_path` set produces
  `watch_status=WATCH_PRODUCED`. `watch_report()` -- which internally
  calls `new_since()` exactly once, which is the ONLY code in this
  module's transitive call graph that ever writes `watch_state_path` --
  runs from the SAME merged signal set the shortlist (if any) scores
  against; never a second sweep, same reasoning as the shortlist section
  above. EXPIRED and UNKNOWN-deadline counts are always populated from
  `watch_report()`'s own `expired`/`unknown_deadline` tuples -- never
  silently dropped, per `opportunity_watch.py`'s own module-level rule
  that "we do not know when this closes" is not the same claim as "this
  does not close."

WHY THIS MODULE SWEEPS ONCE, NOT TWICE, TO GET BOTH COUNTS AND SIGNALS

`opportunity_cycle.OpportunityCycleReport` (a file this agent does not
own this cycle) exposes only counts, never the merged
`CanonicalSignal` tuple `build_shortlist()` needs to score against a
profile. The tempting shortcut -- call `run_cycle()` once for the
report, then sweep every source a second time, separately, to get
signals for the digest -- was rejected after tracing what a second
sweep actually does: each source's own `sweep()` advances an on-disk
dedup cursor in `state_dir` and spends against that source's
module-level `DiscoveryPolicy` budget. A second sweep in the same task
would silently desync the digest from what the ledger actually
recorded (the cursor already moved past what the first sweep saw) and
spend real discovery budget twice for one task -- a live correctness
bug wearing a "just being thorough" costume.

`_sweep_all_with_signals()` below sweeps once. It reuses
`opportunity_cycle._sweep_one_source()` and `._summarize()` -- the
exact, already-tested per-source isolation and roll-up logic
`run_cycle()` itself calls -- and `opportunity_pipeline.run_pipeline()`,
unchanged, to build the identical `OpportunityCycleReport` shape
`run_cycle()` would have returned, while also handing back the merged
pre-pipeline signals `run_cycle()` throws away. This is reuse of
tested logic, not a re-derivation of it: the only lines that are new
are the loop and report-assembly `run_cycle()` itself already
contains, copied because this agent cannot add a `signals` field to
`opportunity_cycle.py` this cycle. When a profile is not supplied,
`run_swarm_task()` still calls `run_cycle()` directly, unchanged --
the mirrored path only runs when a shortlist is actually requested.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Union

from foundation.communication_gate import CommunicationDenied
from foundation.discovery_authorization import (
    DEFAULT_MAX_QUERIES,
    DEFAULT_MAX_RESULTS,
    DEFAULT_MAX_WALL_CLOCK_SECONDS,
    DiscoveryBudgetExhausted,
    DiscoveryPolicy,
    UnboundedDiscoveryObjective,
    authorize_discovery,
)
from foundation.opportunity_cycle import (
    OpportunityCycleReport,
    _sweep_one_source,
    _summarize,
    run_cycle,
)
from foundation.opportunity_pipeline import run_pipeline
from foundation.opportunity_watch import watch_report, render_watch
from foundation.outcome_ledger import OutcomeLedger
from foundation.relevance import CapabilityProfile
from foundation.shortlist import build_shortlist, render_digest
from foundation.signal_spine import CanonicalSignal
from foundation.tender_sources import list_sources

__all__ = [
    "STATUSES",
    "VALIDATION_REFUSED", "AUTHORITY_HOLD", "BUDGET_EXHAUSTED",
    "DRY_RUN_OK", "LIVE_OK", "INTERNAL_ERROR",
    "SHORTLIST_STATUSES",
    "SHORTLIST_NOT_REQUESTED", "SHORTLIST_SKIPPED_DRY_RUN",
    "SHORTLIST_PRODUCED",
    "WATCH_STATUSES",
    "WATCH_NOT_REQUESTED", "WATCH_SKIPPED_DRY_RUN", "WATCH_PRODUCED",
    "SwarmTaskDescriptor", "SwarmTaskResult", "run_swarm_task",
]

# Named, exhaustive result states. A Sonnet agent branches on this
# string, never on exception type or prose-parsing a message.
VALIDATION_REFUSED = "VALIDATION_REFUSED"   # malformed input, refused pre-action
AUTHORITY_HOLD = "AUTHORITY_HOLD"           # a real authority gate was hit
BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"       # discovery budget spent, not a crash
DRY_RUN_OK = "DRY_RUN_OK"                   # validated, nothing executed
LIVE_OK = "LIVE_OK"                         # sweep + pipeline actually ran
INTERNAL_ERROR = "INTERNAL_ERROR"           # last-resort catch, never a bare traceback

STATUSES = frozenset({
    VALIDATION_REFUSED, AUTHORITY_HOLD, BUDGET_EXHAUSTED, DRY_RUN_OK,
    LIVE_OK, INTERNAL_ERROR,
})

# Named, exhaustive shortlist states -- independent of `status` above.
# A Sonnet agent branches on this string to know whether
# `shortlist_digest` is meaningful, never on "is the string non-empty".
SHORTLIST_NOT_REQUESTED = "SHORTLIST_NOT_REQUESTED"   # descriptor carried no profile
SHORTLIST_SKIPPED_DRY_RUN = "SHORTLIST_SKIPPED_DRY_RUN"  # profile given, but dry-run never sweeps
SHORTLIST_PRODUCED = "SHORTLIST_PRODUCED"             # profile given, live sweep completed

SHORTLIST_STATUSES = frozenset({
    SHORTLIST_NOT_REQUESTED, SHORTLIST_SKIPPED_DRY_RUN, SHORTLIST_PRODUCED,
})

# Named, exhaustive watch states -- independent of `status` and of
# `shortlist_status`. A Sonnet agent branches on this string to know
# whether the watch_* count fields are meaningful, never on "is a count
# nonzero" (zero new signals is a legitimate, common, honest outcome).
WATCH_NOT_REQUESTED = "WATCH_NOT_REQUESTED"      # descriptor carried no watch_state_path
WATCH_SKIPPED_DRY_RUN = "WATCH_SKIPPED_DRY_RUN"  # requested, but dry-run never sweeps
                                                  # and -- just as importantly -- never
                                                  # advances the seen-set
WATCH_PRODUCED = "WATCH_PRODUCED"                # requested, live sweep completed

WATCH_STATUSES = frozenset({
    WATCH_NOT_REQUESTED, WATCH_SKIPPED_DRY_RUN, WATCH_PRODUCED,
})

# The one requested_scope this envelope will ever ask for. Fixed, not a
# descriptor field -- a Sonnet agent cannot request RECEIVE_WEBHOOK or any
# other scope through this module because there is no parameter that
# reaches one. `tender_radar.DISCOVERY_POLICY` (the module this envelope
# calls into) is independently fixed to the same scope.
_REQUESTED_SCOPE = "READ_API"


@dataclass(frozen=True)
class SwarmTaskDescriptor:
    """The one input `run_swarm_task()` accepts. Every field is required
    or has a safe, named default -- there is no way to construct a
    descriptor that goes live, spends more than the standing budget, or
    writes anywhere unnamed, without the constructor itself accepting
    values that later fail validation with a named reason."""

    objective: str
    state_dir: Union[str, Path]
    ledger_path: Union[str, Path]
    live: bool = False
    authorized_by: str = ""
    max_queries: int = DEFAULT_MAX_QUERIES
    max_wall_clock_seconds: int = DEFAULT_MAX_WALL_CLOCK_SECONDS
    max_results: int = DEFAULT_MAX_RESULTS
    now: Optional[datetime] = None
    # Optional -- `None` means "no shortlist wanted", not "empty profile".
    # See module docstring's OPTIONAL SHORTLIST section. A profile
    # requests nothing beyond scoring/rendering already-swept signals;
    # it cannot itself flip `live`, raise a budget ceiling, or open any
    # write path -- there is no code path from this field to `os`/
    # `pathlib`/socket I/O other than the sweep `live=True` already
    # authorizes.
    shortlist_profile: Optional[CapabilityProfile] = None
    shortlist_limit: int = 10
    # Optional -- `None` means "no watch behaviour wanted", not "watch
    # from an empty state". See module docstring's OPTIONAL WATCH
    # section. `watch_state_path` is the durable seen-set
    # `opportunity_watch.new_since()` reads and atomically rewrites;
    # `watch_closing_within_days` is the window `opportunity_watch.
    # closing_within()` scores against. Neither field can itself flip
    # `live`, raise a budget ceiling, or open any write path beyond the
    # one file `watch_state_path` names -- there is no code path from
    # these fields to any other write.
    watch_state_path: Optional[Union[str, Path]] = None
    watch_closing_within_days: int = 30

    def __post_init__(self) -> None:
        # Normalize path-like fields once, here, so every downstream
        # check and every downstream call sees a real Path -- never a
        # raw string compared inconsistently in different branches.
        object.__setattr__(self, "state_dir", Path(self.state_dir))
        object.__setattr__(self, "ledger_path", Path(self.ledger_path))
        if self.watch_state_path is not None:
            object.__setattr__(
                self, "watch_state_path", Path(self.watch_state_path))


@dataclass(frozen=True)
class SwarmTaskResult:
    """The one output type. `status` is always one of `STATUSES`.
    `requires_human` names any authority gate this run hit -- non-empty
    only on `AUTHORITY_HOLD`. `qualified`/`contracts`/`cash` cannot be
    constructed non-zero -- see module docstring guarantee 6."""

    status: str
    refused_by: str = ""
    reason: str = ""
    requires_human: tuple = ()
    sweep_status: str = ""
    sweep_error: Optional[str] = None
    signal_count: int = 0
    controlling_party_count: int = 0
    ledger_records_written: int = 0
    qualified: int = 0
    contracts: int = 0
    cash: int = 0
    # Independent of `status` -- see SHORTLIST_STATUSES above and the
    # module docstring's OPTIONAL SHORTLIST section. `shortlist_digest`
    # is data (the exact string `shortlist.render_digest()` returned),
    # never printed from inside this module.
    shortlist_status: str = SHORTLIST_NOT_REQUESTED
    shortlist_digest: str = ""
    shortlist_entry_count: int = 0
    # Independent of `status` and `shortlist_status` -- see
    # WATCH_STATUSES above and the module docstring's OPTIONAL WATCH
    # section. "What changed since last time" without a second tool:
    # these counts (and `watch_report_text`) are populated only on
    # `watch_status == WATCH_PRODUCED`; every other status leaves them
    # at their honest zero/empty default, never a fabricated number.
    watch_status: str = WATCH_NOT_REQUESTED
    watch_report_text: str = ""
    watch_new_count: int = 0
    watch_closing_count: int = 0
    watch_new_and_closing_count: int = 0
    watch_expired_count: int = 0
    watch_unknown_deadline_count: int = 0

    def __post_init__(self) -> None:
        if self.status not in STATUSES:
            raise AssertionError(
                f"SwarmTaskResult.status={self.status!r} is not one of "
                f"the named STATUSES {sorted(STATUSES)} -- an unnamed "
                f"status is exactly the 'bare traceback' outcome this "
                f"module exists to prevent")
        if self.shortlist_status not in SHORTLIST_STATUSES:
            raise AssertionError(
                f"SwarmTaskResult.shortlist_status="
                f"{self.shortlist_status!r} is not one of the named "
                f"SHORTLIST_STATUSES {sorted(SHORTLIST_STATUSES)}")
        if self.watch_status not in WATCH_STATUSES:
            raise AssertionError(
                f"SwarmTaskResult.watch_status={self.watch_status!r} is "
                f"not one of the named WATCH_STATUSES "
                f"{sorted(WATCH_STATUSES)}")
        if self.qualified != 0 or self.contracts != 0 or self.cash != 0:
            raise AssertionError(
                "SwarmTaskResult refuses to be constructed with "
                "qualified/contracts/cash != 0 -- no evidence for any "
                "of the three exists this far upstream of a real human "
                "response; see module docstring guarantee 6")

    def show_the_math(self) -> str:
        lines = [f"SWARM TASK status={self.status}"]
        if self.status in (VALIDATION_REFUSED, AUTHORITY_HOLD, BUDGET_EXHAUSTED, INTERNAL_ERROR):
            lines.append(f"  refused_by={self.refused_by!r} reason={self.reason}")
            if self.requires_human:
                lines.append(f"  requires_human={list(self.requires_human)}")
        else:
            lines.append(
                f"  sweep_status={self.sweep_status} signals={self.signal_count} "
                f"controlling_parties={self.controlling_party_count} "
                f"ledger_records={self.ledger_records_written} "
                f"qualified={self.qualified} contracts={self.contracts} "
                f"cash={self.cash}")
            if self.sweep_error:
                lines.append(f"  sweep_error={self.sweep_error}")
        lines.append(
            f"  shortlist_status={self.shortlist_status} "
            f"shortlist_entries={self.shortlist_entry_count}")
        lines.append(
            f"  watch_status={self.watch_status} "
            f"new={self.watch_new_count} "
            f"closing_soon={self.watch_closing_count} "
            f"new_and_closing={self.watch_new_and_closing_count} "
            f"expired={self.watch_expired_count} "
            f"unknown_deadline={self.watch_unknown_deadline_count}")
        return "\n".join(lines)


def _refused(status: str, refused_by: str, reason: str,
             requires_human: tuple = ()) -> SwarmTaskResult:
    return SwarmTaskResult(status=status, refused_by=refused_by,
                            reason=reason, requires_human=tuple(requires_human))


def _validate(descriptor: SwarmTaskDescriptor) -> Optional[SwarmTaskResult]:
    """Every check here runs before any action, in order, and returns on
    the first failure with a named constraint. Returns None when the
    descriptor is well-formed enough to proceed to objective/scope
    validation (still pre-action -- see `run_swarm_task`)."""

    if not str(descriptor.objective).strip():
        return _refused(VALIDATION_REFUSED, "OBJECTIVE_REQUIRED",
                         "descriptor.objective is empty -- a swarm task "
                         "must name a concrete objective")
    if str(descriptor.state_dir) in ("", "."):
        return _refused(VALIDATION_REFUSED, "STATE_DIR_REQUIRED",
                         "descriptor.state_dir must be a real declared path")
    if str(descriptor.ledger_path) in ("", "."):
        return _refused(VALIDATION_REFUSED, "LEDGER_PATH_REQUIRED",
                         "descriptor.ledger_path must be a real declared path")
    if descriptor.state_dir == descriptor.ledger_path:
        return _refused(VALIDATION_REFUSED, "STATE_DIR_EQUALS_LEDGER_PATH",
                         "state_dir and ledger_path must be distinct -- a "
                         "cursor cache file and the outcome ledger must "
                         "never collide on one path")
    if descriptor.max_queries > DEFAULT_MAX_QUERIES:
        return _refused(
            VALIDATION_REFUSED, "MAX_QUERIES_EXCEEDS_CEILING",
            f"max_queries={descriptor.max_queries} exceeds this "
            f"repository's standing DEFAULT_MAX_QUERIES="
            f"{DEFAULT_MAX_QUERIES} -- raising the ceiling is a human "
            f"decision, not a per-task one")
    if descriptor.max_wall_clock_seconds > DEFAULT_MAX_WALL_CLOCK_SECONDS:
        return _refused(
            VALIDATION_REFUSED, "MAX_WALL_CLOCK_EXCEEDS_CEILING",
            f"max_wall_clock_seconds={descriptor.max_wall_clock_seconds} "
            f"exceeds DEFAULT_MAX_WALL_CLOCK_SECONDS="
            f"{DEFAULT_MAX_WALL_CLOCK_SECONDS}")
    if descriptor.max_results > DEFAULT_MAX_RESULTS:
        return _refused(
            VALIDATION_REFUSED, "MAX_RESULTS_EXCEEDS_CEILING",
            f"max_results={descriptor.max_results} exceeds "
            f"DEFAULT_MAX_RESULTS={DEFAULT_MAX_RESULTS}")
    if descriptor.max_queries <= 0 or descriptor.max_wall_clock_seconds <= 0 \
            or descriptor.max_results <= 0:
        return _refused(VALIDATION_REFUSED, "BUDGET_MUST_BE_POSITIVE",
                         "max_queries, max_wall_clock_seconds and "
                         "max_results must all be positive integers")
    if descriptor.shortlist_limit < 0:
        return _refused(
            VALIDATION_REFUSED, "SHORTLIST_LIMIT_MUST_BE_NON_NEGATIVE",
            f"shortlist_limit={descriptor.shortlist_limit} must be >= 0")
    if descriptor.watch_closing_within_days < 0:
        return _refused(
            VALIDATION_REFUSED, "WATCH_CLOSING_WINDOW_MUST_BE_NON_NEGATIVE",
            f"watch_closing_within_days="
            f"{descriptor.watch_closing_within_days} must be >= 0")
    if descriptor.watch_state_path is not None and descriptor.watch_state_path in (
            descriptor.state_dir, descriptor.ledger_path):
        return _refused(
            VALIDATION_REFUSED, "WATCH_STATE_PATH_COLLIDES",
            "watch_state_path must be distinct from state_dir and "
            "ledger_path -- the watch seen-set, the dedup cursor cache, "
            "and the outcome ledger must never collide on one path")
    if descriptor.live and not str(descriptor.authorized_by).strip():
        # This is the authority gate, not a plain malformed-input
        # refusal: going live is a real action with real (if bounded)
        # consequences, so it names a human-facing gate rather than
        # just a validation field.
        return _refused(
            AUTHORITY_HOLD, "LIVE_REQUIRES_AUTHORIZED_BY",
            "descriptor.live=True but descriptor.authorized_by is "
            "empty -- going live requires an explicit named human "
            "authorization, not just a flipped boolean",
            requires_human=("LIVE_EXECUTION_AUTHORIZATION",))
    return None


def _sweep_all_with_signals(
    state_dir: Path,
    ledger: OutcomeLedger,
    fetch_fn: Optional[Callable[[], bytes]],
    now: Optional[datetime],
) -> "tuple[OpportunityCycleReport, tuple[CanonicalSignal, ...]]":
    """Exact mirror of `opportunity_cycle.run_cycle()`'s own body,
    extended to also return the merged pre-pipeline signal set a
    shortlist needs. See module docstring's "WHY THIS MODULE SWEEPS
    ONCE, NOT TWICE" section for why this exists instead of calling
    `run_cycle()` and then sweeping again -- a second sweep would desync
    each source's on-disk dedup cursor from what the ledger actually
    recorded and spend real discovery budget twice for one task.

    Reuses `opportunity_cycle._sweep_one_source()` / `._summarize()`
    and `opportunity_pipeline.run_pipeline()` unchanged -- the only new
    code here is the loop and report assembly `run_cycle()` itself
    already contains, copied because this module cannot add a `signals`
    field to `opportunity_cycle.OpportunityCycleReport` this cycle
    (that file belongs to a different agent this cycle). Only called
    when a shortlist is actually requested -- see `run_swarm_task()`,
    which still calls `run_cycle()` directly, unchanged, when no
    profile is supplied.
    """
    source_results = []
    merged_signals: "list[CanonicalSignal]" = []
    for source_id in list_sources():
        result, signals = _sweep_one_source(source_id, state_dir, fetch_fn, now)
        source_results.append(result)
        merged_signals.extend(signals)

    sweep_status, sweep_error = _summarize(tuple(source_results))

    pipeline_report = run_pipeline(tuple(merged_signals), ledger, now=now)

    report = OpportunityCycleReport(
        sweep_status=sweep_status,
        sweep_error=sweep_error,
        signal_count=pipeline_report.signal_count,
        controlling_party_count=pipeline_report.controlling_party_count,
        controlling_parties=tuple(
            sorted(o.controlling_party for o in pipeline_report.opportunities)),
        ledger_records_written=len(pipeline_report.opportunities),
        qualified=pipeline_report.qualified,
        contracts=pipeline_report.contracts,
        cash=pipeline_report.cash,
        source_results=tuple(source_results),
    )
    return report, tuple(merged_signals)


def run_swarm_task(
    descriptor: SwarmTaskDescriptor,
    *,
    _fetch_fn_for_tests: Optional[Callable[[], bytes]] = None,
) -> SwarmTaskResult:
    """The one entry point. Validates `descriptor` fully before any
    action; refuses with a structured, named reason on any failure;
    defaults to dry-run; requires two explicit signals (`live=True` AND
    a non-empty `authorized_by`) to go live; never lets a bare exception
    escape.

    `_fetch_fn_for_tests` is a TEST-ONLY seam, matching the identical
    injectable-`fetch_fn` pattern already used throughout this
    repository's mouths (`tender_radar.sweep`, `opportunity_cycle.
    run_cycle`) for offline determinism. It is not part of this
    function's documented production call surface -- `RUNBOOK_
    OPPORTUNITY.md` never tells a caller to pass it, and passing it does
    not change any validation or refusal behavior above, only which
    bytes a live run reads instead of opening a real socket.
    """
    try:
        refusal = _validate(descriptor)
        if refusal is not None:
            return refusal

        # Objective/scope validation is pure logic -- no I/O -- so it is
        # safe (and correct) to run it even in dry-run mode. Reuses
        # discovery_authorization's own regexes rather than re-deriving
        # them.
        policy = DiscoveryPolicy(
            objective=descriptor.objective,
            requested_scope=_REQUESTED_SCOPE,
            max_queries=descriptor.max_queries,
            max_wall_clock_seconds=descriptor.max_wall_clock_seconds,
            max_results=descriptor.max_results,
        )
        try:
            authorize_discovery(policy)
        except UnboundedDiscoveryObjective as exc:
            return _refused(VALIDATION_REFUSED, "OBJECTIVE_UNBOUNDED", str(exc))
        except DiscoveryBudgetExhausted as exc:
            # Order matters: DiscoveryBudgetExhausted subclasses
            # CommunicationDenied, so it must be caught first or the
            # broader except below would swallow it as a generic denial.
            return _refused(BUDGET_EXHAUSTED, "DISCOVERY_BUDGET_EXHAUSTED", str(exc))
        except CommunicationDenied as exc:
            return _refused(
                AUTHORITY_HOLD, "DISCOVERY_SCOPE_DENIED", str(exc),
                requires_human=("DISCOVERY_AUTHORIZATION_GATE",))

        if not descriptor.live:
            # DRY RUN: validated, nothing executed. No filesystem touch,
            # no ledger construction, no sweep call -- see module
            # docstring guarantee 1. A shortlist needs swept signals, so
            # a profile supplied on a dry run cannot produce one -- that
            # is reported explicitly (SHORTLIST_SKIPPED_DRY_RUN), never
            # as a silent empty digest.
            shortlist_status = (
                SHORTLIST_SKIPPED_DRY_RUN
                if descriptor.shortlist_profile is not None
                else SHORTLIST_NOT_REQUESTED)
            # Same discipline as the shortlist above, and the single
            # most important property this field adds: a dry run must
            # NEVER advance opportunity_watch's seen-set, or the next
            # live run would silently under-report "new" -- so a
            # requested watch is reported SKIPPED here, and
            # opportunity_watch.new_since() (the only code that ever
            # writes watch_state_path) is never called on this path.
            watch_status = (
                WATCH_SKIPPED_DRY_RUN
                if descriptor.watch_state_path is not None
                else WATCH_NOT_REQUESTED)
            return SwarmTaskResult(
                status=DRY_RUN_OK,
                reason=(
                    f"validated only -- would sweep objective="
                    f"{descriptor.objective!r} into state_dir="
                    f"{descriptor.state_dir} and ledger_path="
                    f"{descriptor.ledger_path}; set live=True and "
                    f"authorized_by to actually run"),
                shortlist_status=shortlist_status,
                watch_status=watch_status,
            )

        # LIVE: the only branch that touches disk or (via the real
        # fetch path inside tender_radar/mouth_common, when
        # _fetch_fn_for_tests is not supplied) a socket.
        needs_signals = (
            descriptor.shortlist_profile is not None
            or descriptor.watch_state_path is not None)
        try:
            ledger = OutcomeLedger(ledger_path=descriptor.ledger_path)
            if needs_signals:
                # Shortlist and/or watch requested -- sweep once,
                # keeping the merged signals, instead of run_cycle()'s
                # counts-only report. See _sweep_all_with_signals()'s
                # own docstring.
                report, merged_signals = _sweep_all_with_signals(
                    descriptor.state_dir, ledger,
                    _fetch_fn_for_tests, descriptor.now)
            else:
                report = run_cycle(
                    descriptor.state_dir, ledger,
                    fetch_fn=_fetch_fn_for_tests, now=descriptor.now)
                merged_signals = ()
        except DiscoveryBudgetExhausted as exc:
            return _refused(BUDGET_EXHAUSTED, "DISCOVERY_BUDGET_EXHAUSTED", str(exc))
        except CommunicationDenied as exc:
            return _refused(
                AUTHORITY_HOLD, "DISCOVERY_SCOPE_DENIED", str(exc),
                requires_human=("DISCOVERY_AUTHORIZATION_GATE",))
        except UnboundedDiscoveryObjective as exc:
            return _refused(VALIDATION_REFUSED, "OBJECTIVE_UNBOUNDED", str(exc))

        # A GATE REFUSAL IS STILL A GATE REFUSAL WHEN ONE SOURCE ABSORBS IT.
        #
        # `run_cycle` used to let a budget/authorization refusal propagate,
        # and the three `except` clauses above turned it into a structured
        # BUDGET_EXHAUSTED / AUTHORITY_HOLD. Cycle 008 stopped it
        # propagating, because doing so discarded every OTHER source's
        # already-fetched signals — the ledger ended with zero records.
        #
        # That fix would have silently removed this escalation: the cycle
        # would return LIVE_OK with a quietly smaller signal count, and an
        # agent would read a budget wall as an ordinary quiet day. So the
        # refusal is read back off the per-source results instead of off an
        # exception. The authority fact survives the isolation fix.
        refused = [r for r in getattr(report, "source_results", ())
                   if r.status == "REFUSED_BY_GATE"]
        if refused:
            detail = "; ".join(f"{r.source_id}: {r.error}" for r in refused)
            budget = [r for r in refused if "Budget" in (r.error or "")]
            if budget:
                return _refused(BUDGET_EXHAUSTED, "DISCOVERY_BUDGET_EXHAUSTED",
                                detail)
            return _refused(
                AUTHORITY_HOLD, "DISCOVERY_SCOPE_DENIED", detail,
                requires_human=("DISCOVERY_AUTHORIZATION_GATE",))

        # Shortlist, only when requested and only from the signals this
        # SAME sweep just produced -- never a second sweep. See
        # module docstring's OPTIONAL SHORTLIST section.
        shortlist_status = SHORTLIST_NOT_REQUESTED
        shortlist_digest = ""
        shortlist_entry_count = 0
        if descriptor.shortlist_profile is not None:
            shortlist = build_shortlist(
                merged_signals, descriptor.shortlist_profile,
                limit=descriptor.shortlist_limit)
            shortlist_digest = render_digest(shortlist)  # data, never printed
            shortlist_entry_count = len(shortlist)
            shortlist_status = SHORTLIST_PRODUCED

        # Watch, only when requested and only from the signals this SAME
        # sweep just produced -- never a second sweep, same discipline
        # as shortlist above. This is the ONLY call to
        # opportunity_watch.watch_report() -> new_since() anywhere in
        # this module, and it only happens once every other refusal
        # path above has already returned -- a budget/authority refusal
        # or an exception raised before this point leaves
        # watch_state_path completely untouched, which is exactly
        # opportunity_watch's own "a process killed before the atomic
        # publish leaves the previous state file untouched" guarantee,
        # inherited rather than re-implemented here.
        watch_status = WATCH_NOT_REQUESTED
        watch_report_text = ""
        watch_new_count = 0
        watch_closing_count = 0
        watch_new_and_closing_count = 0
        watch_expired_count = 0
        watch_unknown_deadline_count = 0
        if descriptor.watch_state_path is not None:
            w_report = watch_report(
                merged_signals, descriptor.watch_state_path,
                days=descriptor.watch_closing_within_days,
                now=descriptor.now)
            watch_report_text = render_watch(w_report)  # data, never printed
            watch_new_count = len(w_report.new)
            watch_closing_count = len(w_report.closing_soon)
            watch_new_and_closing_count = len(w_report.new_and_closing)
            watch_expired_count = len(w_report.expired)
            watch_unknown_deadline_count = len(w_report.unknown_deadline)
            watch_status = WATCH_PRODUCED

        return SwarmTaskResult(
            status=LIVE_OK,
            sweep_status=report.sweep_status,
            sweep_error=report.sweep_error,
            signal_count=report.signal_count,
            controlling_party_count=report.controlling_party_count,
            ledger_records_written=report.ledger_records_written,
            # Literal zeros, not `report.qualified`/`.contracts`/`.cash`
            # -- see module docstring guarantee 6. `report`'s own fields
            # are already always 0 (opportunity_pipeline hardcodes
            # them); this line does not trust that from a distance.
            qualified=0, contracts=0, cash=0,
            shortlist_status=shortlist_status,
            shortlist_digest=shortlist_digest,
            shortlist_entry_count=shortlist_entry_count,
            watch_status=watch_status,
            watch_report_text=watch_report_text,
            watch_new_count=watch_new_count,
            watch_closing_count=watch_closing_count,
            watch_new_and_closing_count=watch_new_and_closing_count,
            watch_expired_count=watch_expired_count,
            watch_unknown_deadline_count=watch_unknown_deadline_count,
        )
    except Exception as exc:  # last-resort structural guarantee, see (7)
        return _refused(
            INTERNAL_ERROR, "UNEXPECTED_EXCEPTION",
            f"{type(exc).__name__}: {exc}")


# ── COMMAND LINE ──────────────────────────────────────────────────────
#
# RUNBOOK_OPPORTUNITY.md calls itself "Sonnet-operable", and every step in
# it required writing and pasting a Python block. That is a higher bar
# than it looks: a paste is a place to make a mistake, and the mistake
# most available was constructing a descriptor with `live=True` while
# meaning to rehearse. A command with dry-run as its default removes that
# particular foot-gun by making the safe thing the shortest thing to type.
#
# The CLI adds no capability and relaxes no gate. It builds the same
# descriptor `run_swarm_task` already validates, so every refusal, the
# two-signal live requirement, and the structural zeros all still come
# from one place rather than being re-implemented here.

_DEFAULT_KEYWORDS = (
    "cyber security", "penetration testing", "security audit",
    "incident response", "soc", "it consulting", "software development",
)
_DEFAULT_EXCLUSIONS = (
    "construction", "catering", "cleaning", "vehicles", "medical supplies",
)


def _cli(argv: "list[str]") -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python3 -m foundation.swarm_contract",
        description="Run one opportunity cycle. Dry-run unless told otherwise.")
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--objective", required=True,
                        help="a concrete objective; vague ones are refused")
    parser.add_argument("--live", action="store_true",
                        help="actually fetch and write. Requires --authorised-by.")
    parser.add_argument("--authorised-by", default="",
                        help="who authorised a live run. Required with --live.")
    parser.add_argument("--shortlist", action="store_true",
                        help="also produce a ranked digest")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--watch-state",
                        help="path to the watch seen-set file. Supplying "
                             "this enables 'what's new since last run' / "
                             "'what's closing soon' reporting. A dry run "
                             "with this set NEVER advances the seen-set.")
    parser.add_argument("--closing-within-days", type=int, default=30,
                        help="window for the CLOSING SOON section "
                             "(default 30)")
    args = parser.parse_args(argv)

    profile = None
    if args.shortlist:
        profile = CapabilityProfile(
            name="operator-default", declared_by=args.authorised_by or "unattributed",
            keywords=_DEFAULT_KEYWORDS, cpv_codes=("72000000",),
            exclusions=_DEFAULT_EXCLUSIONS)

    result = run_swarm_task(SwarmTaskDescriptor(
        objective=args.objective,
        state_dir=Path(args.state_dir), ledger_path=Path(args.ledger),
        live=args.live, authorized_by=args.authorised_by,
        shortlist_profile=profile, shortlist_limit=args.limit,
        watch_state_path=(
            Path(args.watch_state) if args.watch_state else None),
        watch_closing_within_days=args.closing_within_days))

    print(f"status              {result.status}")
    if result.refused_by:
        print(f"refused_by          {result.refused_by}")
    if result.requires_human:
        print(f"requires_human      {', '.join(result.requires_human)}")
    print(f"signals             {result.signal_count}")
    print(f"controlling parties {result.controlling_party_count}")
    print(f"qualified/contracts/cash  {result.qualified}/"
          f"{result.contracts}/{result.cash}")
    if result.watch_status != WATCH_NOT_REQUESTED:
        print(f"watch_status        {result.watch_status}")
        print(f"  new={result.watch_new_count} "
              f"closing_soon={result.watch_closing_count} "
              f"new_and_closing={result.watch_new_and_closing_count} "
              f"expired={result.watch_expired_count} "
              f"unknown_deadline={result.watch_unknown_deadline_count}")
    if result.shortlist_digest:
        print()
        print(result.shortlist_digest)
    if result.watch_report_text:
        print()
        print(result.watch_report_text)
    # A refusal is a success state for this system, but it is not a
    # success for the shell that invoked it -- a script must be able to
    # branch on it without parsing prose.
    return 0 if result.status in (DRY_RUN_OK, LIVE_OK) else 1


if __name__ == "__main__":                                  # pragma: no cover
    import sys as _sys
    raise SystemExit(_cli(_sys.argv[1:]))
