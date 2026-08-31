"""A bounded autonomous engineering window that survives its own death.

WHAT THIS IS FOR

The autonomy ramp asks for eight phases in order, and refuses to let
"the loop could run" substitute for "the loop ran":

    1 one offline radar sweep            -- radar_rail.sweep()
    2 radar -> tentacle -> signal        -- radar_rail.sweep()
    3 persist receipt + checkpoint       -- THIS MODULE
    4 restart the process                -- THIS MODULE (resume())
    5 recover from checkpoint            -- THIS MODULE (resume())
    6 run multiple cycles                -- THIS MODULE (run_window())
    7 run the declared window            -- THIS MODULE (run_window())
    8 measure actual autonomy            -- autonomy_metric.py

Phases 1 and 2 existed. Phase 3 did not: `radar_rail.sweep()` returns a
report and writes nothing durable, so an interrupted run left no trace
and a restarted one began from zero. That gap is what this closes.

WHY IT IS A WINDOW AND NOT A LOOP

`run_window()` takes a wall-clock budget and a cycle cap, and stops at
whichever arrives first. An unbounded `while True:` would be the
"autonomy theatre" every governing document here warns against -- a
process that cannot say why it is still running is not autonomous, it is
merely unsupervised. Every exit is a named reason, recorded.

WHAT IT DELIBERATELY DOES NOT DO

It does not fetch by default. The radar's real fetch path costs a live
GitHub request and is bounded by a budget that this module has no
authority to spend on its own, so `fetch_fn` is injected and the default
window runs offline against whatever the caller supplies. Enabling live
fetch is the caller's decision, made once, visibly.

It does not commit, push, promote, contact anyone, or write to the
outcome ledger. It observes, checkpoints, and reports. Escalation past
observation stays a decision made elsewhere -- that separation is why
this can be allowed to run unattended at all.

It does not claim its own success. `WindowResult` carries the counts and
the stop reason; whether that constitutes autonomy is measured by
`autonomy_metric.py`, which has no incentive to be kind about it.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from foundation.checkpoint import Checkpoint, CheckpointStore

__all__ = ["WindowResult", "CycleRecord", "STOP_REASONS", "run_window",
           "resume_or_start"]

# Every exit is one of these. A window that stops for a reason not on this
# list is a defect, not a surprise.
STOP_REASONS = (
    "BUDGET_EXHAUSTED",      # wall-clock budget reached -- the normal end
    "CYCLE_CAP_REACHED",     # max_cycles reached
    "NO_WORK",               # the source produced nothing to act on
    "SOURCE_FAILED",         # the sweep reported a failure; stop rather than spin
    "INTERRUPTED",           # a caller-supplied stop condition fired
)

DEFAULT_TASK_ID = "AUTONOMOUS_WINDOW"


@dataclass(frozen=True)
class CycleRecord:
    """One cycle's outcome. Deliberately small: this is the thing that has
    to survive a process death, so it holds counts and identifiers rather
    than object graphs."""

    cycle: int
    status: str
    fetched: int
    signals: int
    explicit_demand: int
    rejected: int
    targets: tuple = ()
    occurred_at: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {"cycle": self.cycle, "status": self.status,
                "fetched": self.fetched, "signals": self.signals,
                "explicit_demand": self.explicit_demand,
                "rejected": self.rejected, "targets": list(self.targets),
                "occurred_at": self.occurred_at}


@dataclass(frozen=True)
class WindowResult:
    task_id: str
    cycles_run: int
    cycles_resumed_from: int
    stop_reason: str
    elapsed_seconds: float
    records: tuple = ()
    checkpoint_id: Optional[str] = None
    notes: tuple = ()

    def total_explicit_demand(self) -> int:
        return sum(r.explicit_demand for r in self.records)

    def show_the_math(self) -> str:
        lines = [
            f"AUTONOMOUS WINDOW {self.task_id}",
            f"  resumed from cycle   {self.cycles_resumed_from}",
            f"  cycles run           {self.cycles_run}",
            f"  elapsed              {self.elapsed_seconds:.1f}s",
            f"  stop reason          {self.stop_reason}",
            f"  checkpoint           {self.checkpoint_id or 'NONE'}",
        ]
        for r in self.records:
            lines.append(
                f"    cycle {r.cycle}: {r.status} fetched={r.fetched} "
                f"signals={r.signals} demand={r.explicit_demand} "
                f"rejected={r.rejected}")
        lines.append(f"  total explicit demand {self.total_explicit_demand()}")
        for n in self.notes:
            lines.append(f"  NOTE: {n}")
        lines.append("  NOTE: this window observes and checkpoints only. It "
                     "does not commit, promote, contact anyone, or write to "
                     "the outcome ledger.")
        return "\n".join(lines)


def resume_or_start(store: CheckpointStore,
                    task_id: str = DEFAULT_TASK_ID) -> int:
    """The cycle number to begin at.

    Returns 0 when there is no checkpoint, which is the normal first-run
    case and must never be an error. A TAMPERED checkpoint is NOT resumed
    from -- the window restarts at 0 and says so, because continuing from
    state whose integrity failed would silently build on a lie.
    """
    cp = store.resume(task_id)
    if cp is None:
        return 0
    from foundation.checkpoint import CHECKPOINT_INTACT
    if store.verify(cp) != CHECKPOINT_INTACT:
        return 0
    return int(cp.payload.get("cycle", 0))


def run_window(state_dir: Path,
               *,
               fetch_fn: Optional[Callable[[], bytes]] = None,
               budget_seconds: float = 30.0,
               max_cycles: int = 5,
               per_page: int = 5,
               task_id: str = DEFAULT_TASK_ID,
               checkpoint_path: "str | Path | None" = None,
               should_stop: Optional[Callable[[], bool]] = None,
               now_fn: Callable[[], float] = time.monotonic,
               ) -> WindowResult:
    """Run bounded cycles, checkpointing after each one.

    Resumes from a prior checkpoint if one exists, so a window killed
    mid-run continues rather than repeating. That is the whole point of
    phases 4 and 5 -- a restart that starts over has not recovered, it has
    merely run again.
    """
    from foundation.radar_rail import sweep

    state_dir = Path(state_dir)
    # A first run has no state directory. A window that cannot start cold
    # is not autonomous -- found immediately on the first real run, where
    # sweep() raised FileNotFoundError and the window correctly reported
    # SOURCE_FAILED rather than pretending to have worked.
    state_dir.mkdir(parents=True, exist_ok=True)
    store = CheckpointStore(checkpoint_path)
    start_cycle = resume_or_start(store, task_id)
    started = now_fn()
    records: list[CycleRecord] = []
    notes: list[str] = []
    stop_reason = "CYCLE_CAP_REACHED"
    last_checkpoint: Optional[str] = None
    cycle = start_cycle

    if start_cycle:
        notes.append(f"resumed from checkpoint at cycle {start_cycle}")

    while cycle < max_cycles:
        if should_stop is not None and should_stop():
            stop_reason = "INTERRUPTED"
            break
        if now_fn() - started >= budget_seconds:
            stop_reason = "BUDGET_EXHAUSTED"
            break

        cycle += 1
        try:
            s = sweep(state_dir, per_page=per_page, fetch_fn=fetch_fn)
        except Exception as exc:                              # noqa: BLE001
            # A source failure stops the window rather than spinning on it.
            # A loop that retries a broken source until its budget expires
            # has converted a clear failure into an expensive silence.
            notes.append(f"sweep raised {type(exc).__name__}: {exc}")
            stop_reason = "SOURCE_FAILED"
            break

        rec = CycleRecord(
            cycle=cycle, status=s.status, fetched=s.fetched_count,
            signals=len(s.signals), explicit_demand=len(s.explicit_demand),
            rejected=len(s.rejected), targets=tuple(sorted(s.targets)),
            occurred_at=datetime.now(timezone.utc).isoformat())
        records.append(rec)

        cp = Checkpoint(
            task_id=task_id, phase="CYCLE_COMPLETE",
            repo_revision="", config_digest="", receipt_head=None,
            next_action=f"run cycle {cycle + 1}",
            payload=rec.to_payload())
        store.save(cp)
        last_checkpoint = cp.checkpoint_id

        if s.status in ("UNAVAILABLE", "FAILED"):
            stop_reason = "SOURCE_FAILED"
            break
        if s.fetched_count == 0:
            # UNCHANGED is the normal steady state once a feed has been
            # seen; there is nothing new to act on, so the window ends
            # rather than burning its budget re-observing the same items.
            stop_reason = "NO_WORK"
            break

    return WindowResult(
        task_id=task_id, cycles_run=len(records),
        cycles_resumed_from=start_cycle, stop_reason=stop_reason,
        elapsed_seconds=now_fn() - started, records=tuple(records),
        checkpoint_id=last_checkpoint, notes=tuple(notes))
