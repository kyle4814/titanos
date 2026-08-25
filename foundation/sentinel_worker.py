"""
SentinelSweepWorker — the first real (non-test-double) Layer0Worker.

WHY THIS FILE EXISTS

Every prior test of the queue<->worker seam (`test_queue_worker_adapter.py`)
used a synthetic `_SucceedingWorker`/`_ExplodingWorker` test double whose
`execute_minimum` did nothing but return a string. That proves the
*wiring* is correct; it does not prove a real worker doing real,
already-existing repository work can traverse the same path. This module
is that real worker: its unit of work is `foundation/sentinel.py::
pulse_sweep()` — an existing, already-tested, read-only, no-network,
no-new-permission operation — and its `update_state` writes a real
`foundation/crystal.py::Crystal` into a real `CrystalStore`, not a mock.

WHAT IT DOES, END TO END

`execute_minimum` runs `pulse_sweep(repo_root)` (the actual function,
unmodified). `verify` checks the returned `HealthReport` is
well-formed (a `HealthReport` instance with a non-negative finding
count) — a real check against the real contract, not a tautology.
`update_state` records one `Crystal` per completed sweep, summarizing
what was found, with `reusable_abstraction` derived from the actual
finding count so the crystal is never a content-free stub.

WHAT IT DELIBERATELY DOES NOT DO

It does not write anything to disk, does not fix any finding it
discovers, does not schedule itself again, and does not gain any
permission beyond what `pulse_sweep()` already had (filesystem read
only). `preserve_provenance` records into an in-memory list on the
worker instance — the same "no persistence subsystem invented for this
demonstration" boundary this repo's stores have always operated under.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from foundation.crystal import CrystalStore
from foundation.layer0_worker import Layer0Worker
from foundation.sentinel import HealthReport, pulse_sweep

__all__ = ["SentinelSweepWorker"]


@dataclass
class _ProvenanceRecord:
    verified: bool
    raw_finding_count: int
    compacted: bool


class SentinelSweepWorker(Layer0Worker):
    """Runs one real `pulse_sweep()` against `repo_root` and records a
    real `Crystal` for it. One worker instance performs exactly one
    sweep — construct a fresh instance per task, per `Layer0Worker`'s own
    documented pattern (workers are not reused across cycles)."""

    worker_id = "sentinel-sweep-worker"

    def __init__(self, repo_root: Path, crystal_store: CrystalStore,
                 recorded_by: str, crystal_id: str):
        self.repo_root = repo_root
        self.crystal_store = crystal_store
        self.recorded_by = recorded_by
        self.crystal_id = crystal_id
        self.provenance: list[_ProvenanceRecord] = []

    def observe(self) -> Any:
        return self.repo_root

    def check_existing(self, observation: Any) -> Any:
        # A sweep is idempotent and cheap to rerun — there is no prior
        # "existing solution" to search for here (unlike a build task),
        # so this mandatory hook honestly reports there is nothing to
        # reuse rather than fabricating a check.
        return None

    def execute_minimum(self, lever: Any) -> HealthReport:
        return pulse_sweep(self.repo_root)

    def verify(self, result: Any) -> bool:
        return isinstance(result, HealthReport) and result.raw_finding_count >= 0

    def preserve_provenance(self, result: Any, *, verified: bool) -> None:
        report: HealthReport = result if isinstance(result, HealthReport) else None
        self.provenance.append(_ProvenanceRecord(
            verified=verified,
            raw_finding_count=report.raw_finding_count if report else -1,
            compacted=report.compacted if report else False,
        ))

    def update_state(self, result: HealthReport, yield_signal: Any) -> None:
        finding_summary = "; ".join(f.observation for f in result.findings) or "no findings"
        self.crystal_store.record(
            self.crystal_id,
            problem="is the repository's boot/state/test integrity currently intact?",
            context=f"pulse sweep of {self.repo_root}",
            hypothesis="deterministic Level-1 checks will surface any drifted invariant",
            action="ran foundation.sentinel.pulse_sweep() via SentinelSweepWorker",
            evidence=f"{result.raw_finding_count} raw findings, compacted={result.compacted}",
            result=finding_summary,
            provenance="foundation/sentinel_worker.py::SentinelSweepWorker",
            reusable_abstraction=(
                "zero findings" if result.raw_finding_count == 0
                else f"{result.raw_finding_count} finding(s) open: {finding_summary}"
            ),
            regression_test_ref="foundation/tests/test_closed_loop_reality.py",
            epistemic_status="VERIFIED_FACT",
            recorded_by=self.recorded_by,
        )
