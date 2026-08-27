"""
Authority Runtime — the smallest real persistent-tick proof, gated end to
end by `authority_sigil.py`. Built 2026-08-27 as the one proof cycle
Kyle's authorization asked for: "Start with one persistent minimal
runtime and one zero-spend or explicitly bounded authority class. Prove
the full cycle. No fake worker army, no speculative mall."

THE ONE CAPABILITY THIS PROVES: "RUN_PULSE_SWEEP"

Not a new capability -- `foundation.sentinel.pulse_sweep()` already
exists, is already fully tested, is read-only (no writes, no network, no
subprocess -- structurally enforced by `TestSentinelCannotExecute` in
that module's own test file), and costs nothing. This module adds no new
work; it adds the authority wrapper and the tick/receipt loop around
already-existing, already-safe work, so the proof is about the envelope
mechanics (expiry, revocation, budget, fail-closed-outside-scope), not
about a new risky action.

THE TICK

    evaluate() [foundation.authority_sigil, check-only, no write]
        -> DENY:    record a DENY ActionRecord, write a HOLD receipt
        -> ADMITTED: execute pulse_sweep()
            -> SUCCEEDS: record an ADMIT ActionRecord (consumes budget),
                          write a SUCCESS receipt
            -> RAISES:   record an ERROR ActionRecord (does NOT consume
                          budget), write a FAILURE receipt naming the
                          exception -- never propagates uncaught

Every tick, whatever the outcome, produces exactly one durable
ActionRecord and one tick-log receipt. Budget is consumed only on
confirmed successful execution -- never on the mere intent to attempt
one. Found and fixed 2026-08-28: the original version called the
combined authorize_action() (evaluate + record) *before* running
pulse_sweep(), so a crash or exception during execution left a durable
ADMIT record with no completed work and no receipt behind it -- directly
reproduced by mocking pulse_sweep() to raise mid-call. This ordering
closes that gap; see foundation/tests/test_authority_runtime.py's
TestExecutionFailureDoesNotPhantomConsumeBudget for the reproduction.

WHAT THIS FILE DOES NOT DO

No process supervisor, no daemon installation, no systemd unit, no
concurrency, no second authority class. `run_loop()` is a bounded
Python loop (a caller-supplied `max_ticks`, never literally infinite in
a test) -- exactly enough to prove multiple ticks against real time
without standing up new operational infrastructure this repository has
no precedent for. Real recurring invocation, if ever authorized, reuses
the exact same mechanism `foundation/cron_pulse.py` already uses live:
one cron entry calling `tick()` once per invocation.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from foundation.authority_sigil import ActionRecord, ReleaseLedger, evaluate
from foundation.sentinel import pulse_sweep

__all__ = ["CAPABILITY_RUN_PULSE_SWEEP", "TickResult", "tick", "run_loop", "read_tick_log"]

CAPABILITY_RUN_PULSE_SWEEP = "RUN_PULSE_SWEEP"

_DEFAULT_TICK_LOG = Path(__file__).resolve().parent / "authority_runtime_tick_log.jsonl"


@dataclass(frozen=True)
class TickResult:
    tick_at: str
    release_id: str
    target: str
    admitted: bool
    reasons: tuple[str, ...]
    raw_finding_count: Optional[int] = None
    compacted: Optional[bool] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _append_receipt(log_path: Optional[Path], result: TickResult) -> None:
    if not log_path:
        return
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(result.to_dict(), sort_keys=True))
        fh.write("\n")


def tick(
    ledger: ReleaseLedger,
    release_id: str,
    target: str,
    *,
    log_path: Optional[Path] = _DEFAULT_TICK_LOG,
    now: Optional[datetime] = None,
) -> TickResult:
    """One bounded, receipted unit of work. `target` must match a real
    path in the release's allowed_targets -- pulse_sweep(target) is the
    only action this function will ever perform, and only if the sigil
    admits it.

    Budget is consumed only on confirmed successful execution (see this
    module's docstring) -- `evaluate()` is a pure check, never a write;
    the ActionRecord recording actual consumption is written after
    pulse_sweep() returns, not before it runs."""
    current = now or datetime.now(timezone.utc)
    occurred_at = current.isoformat()
    decision = evaluate(ledger, release_id, CAPABILITY_RUN_PULSE_SWEEP, target, now=current)

    if not decision.admitted:
        ledger.record_action(ActionRecord(
            release_id=release_id, capability=CAPABILITY_RUN_PULSE_SWEEP,
            target=target, occurred_at=occurred_at, result="DENY",
        ))
        result = TickResult(
            tick_at=occurred_at, release_id=release_id, target=target,
            admitted=False, reasons=tuple(decision.reasons),
        )
        _append_receipt(log_path, result)
        return result

    try:
        report = pulse_sweep(Path(target))
    except Exception as exc:  # noqa: BLE001 -- an authorized capability's
        # own failure must never crash the caller or phantom-consume
        # budget; it becomes a receipted, non-budget-consuming ERROR.
        ledger.record_action(ActionRecord(
            release_id=release_id, capability=CAPABILITY_RUN_PULSE_SWEEP,
            target=target, occurred_at=occurred_at, result="ERROR",
        ))
        result = TickResult(
            tick_at=occurred_at, release_id=release_id, target=target,
            admitted=False,
            reasons=(f"authorized but capability execution failed: {exc}",),
        )
        _append_receipt(log_path, result)
        return result

    ledger.record_action(ActionRecord(
        release_id=release_id, capability=CAPABILITY_RUN_PULSE_SWEEP,
        target=target, occurred_at=occurred_at, result="ADMIT",
    ))
    result = TickResult(
        tick_at=occurred_at, release_id=release_id, target=target,
        admitted=True, reasons=tuple(decision.reasons),
        raw_finding_count=report.raw_finding_count, compacted=report.compacted,
    )
    _append_receipt(log_path, result)
    return result


def run_loop(
    ledger: ReleaseLedger,
    release_id: str,
    target: str,
    *,
    max_ticks: int,
    interval_seconds: float,
    log_path: Optional[Path] = _DEFAULT_TICK_LOG,
) -> tuple[TickResult, ...]:
    """Bounded soak loop -- `max_ticks` is always required and finite;
    there is no code path in this module that loops without a caller-set
    bound. Real unattended recurrence, if ever authorized, is a cron
    entry calling tick() once, not this function running forever."""
    if max_ticks <= 0:
        raise ValueError("max_ticks must be positive -- this function never loops unbounded")
    results = []
    for i in range(max_ticks):
        results.append(tick(ledger, release_id, target, log_path=log_path))
        if i < max_ticks - 1:
            time.sleep(interval_seconds)
    return tuple(results)


def read_tick_log(log_path: Path = _DEFAULT_TICK_LOG) -> tuple[dict[str, Any], ...]:
    """Read-only, bounded, fail-soft -- same discipline as
    foundation.sentinel.read_pulse_continuity(). A missing log is a
    valid, non-fatal state (never fired yet)."""
    if not log_path.exists():
        return ()
    records = []
    for line in log_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return tuple(records)
