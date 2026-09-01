"""The missing production caller for `tender_radar` and `opportunity_pipeline`.

WHY THIS EXISTS

Last cycle added two real modules, each individually tested, neither
with a production importer: `tender_radar.sweep()` produces real
`CanonicalSignal`s and then they evaporate (report-only, by that
module's own design); `opportunity_pipeline.run_pipeline()` takes
signals from ANY radar and records them into the outcome ledger, but
nothing in this repository ever called it with a real signal set.
`IMPLEMENTED_UNWIRED` went 28 -> 30 as a direct result: two more real,
tested capabilities that nothing outside their own tests reaches.

This module is the composed, runnable chain that actually calls both:

    tender_radar.sweep()  ->  opportunity_pipeline.run_pipeline()  ->  report

WHAT IT DOES NOT DO, ON PURPOSE

- Does not schedule itself. No cron entry, no loop, no `while True`. A
  scheduled entrypoint is a human decision recorded in
  `HUMAN_DECISIONS.md`, per this repo's own Critical Function
  Switch-Gate doctrine, and inventing one here would inflate
  `autonomy_metric.py`'s ratio dishonestly. `foundation/autonomy_window.py`
  already earns that comparison honestly by taking `budget_seconds`/
  `max_cycles` from its caller rather than assuming its own schedule;
  this module follows the identical discipline for a single cycle.
- Does not touch `autonomy_metric.py`.
- Does not fetch live by default. `fetch_fn` is injectable, exactly as
  `tender_radar.sweep()`, `radar_rail.sweep()`, and
  `autonomous_window.run_window()` already do -- the caller decides to
  go live, never this module on its own. When `fetch_fn` is None,
  `tender_radar.observe()` reaches its default fetcher, which goes
  through `mouth_common.fetch_feed()` and therefore through
  `discovery_authorization.authorize_discovery()`. No second, ungated
  path exists here.
- Does not write anything by default except through the `OutcomeLedger`
  the caller supplies. This module opens no ledger file of its own; the
  caller decides where records land (or hands in an in-memory-only
  ledger for a dry run), exactly the pattern `test_opportunity_pipeline.py`
  already uses.
- Cannot ever set `qualified`, `contracts`, or `cash` above zero.
  `opportunity_pipeline.PipelineReport` hardcodes all three to `0` and
  this module does not touch those fields at all -- it only reads them
  through to its own report. No code path here can change that, because
  no evidence for qualification, a contract, or cash exists anywhere in
  a `CanonicalSignal` this far upstream. See `opportunity_pipeline.py`'s
  own module docstring for the full argument; this module inherits it
  rather than re-arguing it.

WHAT THIS REUSES RATHER THAN DUPLICATES

- `foundation.tender_radar.sweep()` -- the one tender mouth, cold-start
  safe, offline-testable, gated at its one real fetch path.
- `foundation.opportunity_pipeline.run_pipeline()` -- the one signal ->
  ledger adapter, with its own idempotent `operation_id()` per collapsed
  opportunity+signal-set, reused here unchanged.
- `foundation.outcome_ledger.OutcomeLedger` -- passed in by the caller,
  never constructed by this module with an implicit default path (the
  same "caller decides where state lands" discipline
  `autonomous_window.py::run_window()` already applies to its
  `checkpoint_path`).

COLD START

`tender_radar.sweep()` already creates its own state directory
(`state_dir.mkdir(parents=True, exist_ok=True)`) -- the fix for the
real bug found on that module's own first live run. This module passes
`state_dir` straight through and adds no second directory of its own,
so a fresh machine with no prior state runs cleanly on the first call.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from foundation.opportunity_pipeline import PipelineReport, run_pipeline
from foundation.outcome_ledger import OutcomeLedger
from foundation.tender_radar import TenderRadarSweep, sweep as tender_sweep

__all__ = ["OpportunityCycleReport", "run_cycle"]


@dataclass(frozen=True)
class OpportunityCycleReport:
    """One composed cycle's outcome: what the radar saw, what the
    pipeline recorded, and the honest zeros. Never a claim about
    qualification, value, or contract state -- see module docstring."""

    sweep_status: str
    sweep_error: Optional[str]
    signal_count: int
    controlling_party_count: int
    controlling_parties: tuple = ()
    ledger_records_written: int = 0
    qualified: int = 0
    contracts: int = 0
    cash: int = 0

    def show_the_math(self) -> str:
        lines = [
            f"OPPORTUNITY CYCLE sweep_status={self.sweep_status} "
            f"signals={self.signal_count} "
            f"controlling_parties={self.controlling_party_count} "
            f"ledger_records={self.ledger_records_written} "
            f"qualified={self.qualified} contracts={self.contracts} "
            f"cash={self.cash}",
        ]
        if self.sweep_error:
            lines.append(f"  sweep error: {self.sweep_error}")
        if self.controlling_parties:
            lines.append(
                "  controlling parties: " + ", ".join(self.controlling_parties))
        if self.signal_count == 0:
            lines.append(
                "  zero signals this cycle -- a valid, honest outcome, not "
                "an error")
        else:
            lines.append(
                "  every party above is OBSERVED only: a discovered signal "
                "is demand, not a lead, not a qualified opportunity, not a "
                "contract, and not cash")
        return "\n".join(lines)


def run_cycle(
    state_dir: Path,
    ledger: OutcomeLedger,
    fetch_fn: Optional[Callable[[], bytes]] = None,
    now: Optional[datetime] = None,
) -> OpportunityCycleReport:
    """Run one tender sweep and feed its signals into the outcome
    pipeline. The real caller for both `tender_radar.sweep()` and
    `opportunity_pipeline.run_pipeline()` -- see module docstring for
    what it deliberately does not do.

    `state_dir` is handed straight to `tender_radar.sweep()`, which
    creates it if it does not exist (cold-start safe). `ledger` is the
    caller's own `OutcomeLedger` -- this function writes nothing
    durable except through it, and writes nothing at all when the
    sweep produces zero signals.

    A sweep in `UNAVAILABLE`/`FAILED` status still produces a structured
    report rather than raising: `sweep_error` is set, `signal_count` is
    0, and `run_pipeline()` is still called with an empty signal tuple
    so the report shape never depends on whether the fetch succeeded.
    """
    radar_sweep: TenderRadarSweep = tender_sweep(
        state_dir, fetch_fn=fetch_fn, now=now)

    pipeline_report: PipelineReport = run_pipeline(
        radar_sweep.signals, ledger, now=now)

    return OpportunityCycleReport(
        sweep_status=radar_sweep.status,
        sweep_error=radar_sweep.error,
        signal_count=pipeline_report.signal_count,
        controlling_party_count=pipeline_report.controlling_party_count,
        controlling_parties=tuple(
            sorted(o.controlling_party for o in pipeline_report.opportunities)),
        ledger_records_written=len(pipeline_report.opportunities),
        qualified=pipeline_report.qualified,
        contracts=pipeline_report.contracts,
        cash=pipeline_report.cash,
    )


if __name__ == "__main__":                                  # pragma: no cover
    import sys
    import tempfile

    repo_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo_root))

    # Runnable, offline by default -- no network fetch happens here unless
    # a caller edits this to inject one, matching the discipline every
    # other __main__ entrypoint in this repository (radar_rail, tender_radar)
    # follows: this is a demonstration harness, not a scheduled job.
    demo_state_dir = Path(tempfile.mkdtemp()) / "opportunity_cycle_state"
    demo_ledger = OutcomeLedger(ledger_path=Path(tempfile.mkdtemp()) / "demo_ledger.jsonl")
    report = run_cycle(
        demo_state_dir, demo_ledger, fetch_fn=lambda: b'{"releases": []}')
    print(report.show_the_math())
