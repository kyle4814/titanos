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
from foundation.opportunity_cycle import OpportunityCycleReport, run_cycle
from foundation.outcome_ledger import OutcomeLedger

__all__ = [
    "STATUSES",
    "VALIDATION_REFUSED", "AUTHORITY_HOLD", "BUDGET_EXHAUSTED",
    "DRY_RUN_OK", "LIVE_OK", "INTERNAL_ERROR",
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

    def __post_init__(self) -> None:
        # Normalize path-like fields once, here, so every downstream
        # check and every downstream call sees a real Path -- never a
        # raw string compared inconsistently in different branches.
        object.__setattr__(self, "state_dir", Path(self.state_dir))
        object.__setattr__(self, "ledger_path", Path(self.ledger_path))


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

    def __post_init__(self) -> None:
        if self.status not in STATUSES:
            raise AssertionError(
                f"SwarmTaskResult.status={self.status!r} is not one of "
                f"the named STATUSES {sorted(STATUSES)} -- an unnamed "
                f"status is exactly the 'bare traceback' outcome this "
                f"module exists to prevent")
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
            # docstring guarantee 1.
            return SwarmTaskResult(
                status=DRY_RUN_OK,
                reason=(
                    f"validated only -- would sweep objective="
                    f"{descriptor.objective!r} into state_dir="
                    f"{descriptor.state_dir} and ledger_path="
                    f"{descriptor.ledger_path}; set live=True and "
                    f"authorized_by to actually run"),
            )

        # LIVE: the only branch that touches disk or (via the real
        # fetch path inside tender_radar/mouth_common, when
        # _fetch_fn_for_tests is not supplied) a socket.
        try:
            ledger = OutcomeLedger(ledger_path=descriptor.ledger_path)
            report: OpportunityCycleReport = run_cycle(
                descriptor.state_dir, ledger,
                fetch_fn=_fetch_fn_for_tests, now=descriptor.now)
        except DiscoveryBudgetExhausted as exc:
            return _refused(BUDGET_EXHAUSTED, "DISCOVERY_BUDGET_EXHAUSTED", str(exc))
        except CommunicationDenied as exc:
            return _refused(
                AUTHORITY_HOLD, "DISCOVERY_SCOPE_DENIED", str(exc),
                requires_human=("DISCOVERY_AUTHORIZATION_GATE",))
        except UnboundedDiscoveryObjective as exc:
            return _refused(VALIDATION_REFUSED, "OBJECTIVE_UNBOUNDED", str(exc))

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
        )
    except Exception as exc:  # last-resort structural guarantee, see (7)
        return _refused(
            INTERNAL_ERROR, "UNEXPECTED_EXCEPTION",
            f"{type(exc).__name__}: {exc}")
