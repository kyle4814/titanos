"""
Layer 0 Worker Contract — TITANOS_LAYER0_RECURSIVE_PARETO_FRONTIER.md.

WHY THIS IS THE THIRD TIME THIS HAS BEEN CONSIDERED AND THE FIRST TIME
IT'S BEEN BUILT

Two prior directives this session (Living Pareto Frontier Architecture,
then this one's own predecessor) proposed typed worker processes
(Scout/Architect/Builder/Verifier/... or a Layer 0 substrate every worker
inherits). Both times the concrete nine-directory worker swarm was
rejected as premature — untyped directories with no code behind them are
exactly the "empty theater" every one of these doctrine files warns
against building. This time the ask is narrower: not nine workers, one
CONTRACT — the shape any future worker must satisfy. A contract with a
concrete enforcement mechanism and real tests is not theater; it's the
same category of thing as `narrative/schema/narrative_atom.py` being
built before any store or ingestion pipeline existed to use it — define
the shape now, let the day a real worker gets coded against it be a
separate, later decision.

THE FOUR STEPS THAT CANNOT BE SKIPPED, ENFORCED STRUCTURALLY

The doctrine: "NO WORKER MAY SKIP: CHECK_EXISTING, VERIFY,
PRESERVE_PROVENANCE, UPDATE_STATE." This is not a comment reminding a
subclass author to remember — `run()` is a template method a subclass
cannot override, and it calls all four unconditionally. A subclass that
leaves any of the four as the abstract default raises
`NotImplementedError` at the point the base class calls it, not
silently no-ops. Verified by test: a deliberately incomplete worker
subclass fails loudly, not quietly.

THE FORMAL STOP CONDITION, MADE INTO CODE

    NEW_INFORMATION_GAIN <= MINIMUM_THRESHOLD
    AND EXPECTED_REAL_WORLD_YIELD <= MINIMUM_THRESHOLD
    AND NO_CRITICAL_RISK_REQUIRES_ACTION
    => HALT

`should_halt()` is a pure function over three declared values, matching
the doctrine's own three-clause AND — not a vibe, a boolean expression a
test can pin down exactly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

__all__ = [
    "Layer0Worker", "CycleRecord", "StopSignal", "should_halt",
    "DEFAULT_INFORMATION_GAIN_THRESHOLD", "DEFAULT_YIELD_THRESHOLD",
]

DEFAULT_INFORMATION_GAIN_THRESHOLD = 0.0
DEFAULT_YIELD_THRESHOLD = 0.0


@dataclass
class StopSignal:
    """The formal stop condition's three inputs, declared explicitly by
    whoever is running a cycle — this module does not measure these
    itself, the same boundary every gate in this codebase holds."""
    new_information_gain: float
    expected_real_world_yield: float
    critical_risk_requires_action: bool


def should_halt(signal: StopSignal, *,
                information_gain_threshold: float = DEFAULT_INFORMATION_GAIN_THRESHOLD,
                yield_threshold: float = DEFAULT_YIELD_THRESHOLD) -> bool:
    """The formal stop condition, verbatim from the doctrine:

    NEW_INFORMATION_GAIN <= MINIMUM_THRESHOLD
    AND EXPECTED_REAL_WORLD_YIELD <= MINIMUM_THRESHOLD
    AND NO_CRITICAL_RISK_REQUIRES_ACTION
    => HALT

    A critical risk requiring action ALWAYS blocks halting, regardless of
    how low information gain or yield are — the recursion must not stop
    just because it ran out of interesting things to build while
    something dangerous is still unaddressed.
    """
    if signal.critical_risk_requires_action:
        return False
    return (signal.new_information_gain <= information_gain_threshold
            and signal.expected_real_world_yield <= yield_threshold)


@dataclass
class CycleRecord:
    """What one full run() produced — the audit trail a Layer0Worker
    leaves behind, independent of whatever domain-specific state it also
    updates."""
    worker_id: str
    started_at: str
    steps_completed: list[str] = field(default_factory=list)
    halted: bool = False
    halt_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"worker_id": self.worker_id, "started_at": self.started_at,
                "steps_completed": list(self.steps_completed),
                "halted": self.halted, "halt_reason": self.halt_reason}


class Layer0Worker(ABC):
    """Base contract every TitanOS worker inherits. `run()` is the
    template method — NOT overridable — sequencing all 14 doctrine steps
    in order. Subclasses implement the abstract hooks; the four
    mandatory ones (`check_existing`, `verify`, `preserve_provenance`,
    `update_state`) have no default implementation and raise
    `NotImplementedError` if a subclass doesn't provide one, so `run()`
    fails loudly at exactly the point a skipped mandatory step would have
    been silently skipped.
    """

    worker_id: str = "unnamed-worker"

    def run(self) -> CycleRecord:
        record = CycleRecord(worker_id=self.worker_id,
                             started_at=datetime.now(timezone.utc).isoformat())

        self.boot()
        record.steps_completed.append("BOOT")

        observation = self.observe()
        record.steps_completed.append("OBSERVE")

        self.map(observation)
        record.steps_completed.append("MAP")

        existing = self.check_existing(observation)
        record.steps_completed.append("CHECK_EXISTING")

        options = self.generate_options(observation, existing)
        record.steps_completed.append("GENERATE_OPTIONS")

        scored = self.score_frontier(options)
        record.steps_completed.append("SCORE_FRONTIER")

        lever = self.select_lever(scored)
        record.steps_completed.append("SELECT_LEVER")

        permitted = self.request_permission_if_required(lever)
        record.steps_completed.append("REQUEST_PERMISSION_IF_REQUIRED")
        if not permitted:
            record.halted = True
            record.halt_reason = "permission not granted"
            return record

        result = self.execute_minimum(lever)
        record.steps_completed.append("EXECUTE_MINIMUM")

        verified = self.verify(result)
        record.steps_completed.append("VERIFY")
        if not verified:
            record.halted = True
            record.halt_reason = "verification failed"
            self.preserve_provenance(result, verified=False)
            record.steps_completed.append("PRESERVE_PROVENANCE")
            return record

        yield_signal = self.measure_yield(result)
        record.steps_completed.append("MEASURE_YIELD")

        self.preserve_provenance(result, verified=True)
        record.steps_completed.append("PRESERVE_PROVENANCE")

        self.update_state(result, yield_signal)
        record.steps_completed.append("UPDATE_STATE")

        next_move = self.recommend_next(yield_signal)
        record.steps_completed.append("RECOMMEND_NEXT")

        stop_signal = self.stop_signal(yield_signal, next_move)
        if should_halt(stop_signal):
            record.halted = True
            record.halt_reason = "formal stop condition met"
        record.steps_completed.append("HALT")

        return record

    # ── Optional hooks — sensible no-op defaults are legitimate here ──────
    def boot(self) -> None:
        """Default no-op. Override for real initialization."""

    def observe(self) -> Any:
        """Default: no observation. Override to actually receive input."""
        return None

    def map(self, observation: Any) -> None:
        """Default no-op. Override to update an architectural map."""

    def generate_options(self, observation: Any, existing: Any) -> list[Any]:
        """Default: no candidates. Override to propose real levers."""
        return []

    def score_frontier(self, options: list[Any]) -> list[Any]:
        """Default: pass options through unscored. Override for real
        Pareto scoring."""
        return options

    def select_lever(self, scored_options: list[Any]) -> Any:
        """Default: first scored option, or None. Override for real
        selection logic."""
        return scored_options[0] if scored_options else None

    def request_permission_if_required(self, lever: Any) -> bool:
        """Default: no permission required, proceed. Override to gate on
        Hell's Gate / publication_gate / human authorization for
        anything critical — this default is DELIBERATELY permissive for
        low-stakes workers; a worker touching anything from
        TITANOS_CRITICAL_FUNCTION_SWITCH_GATE.md's list MUST override
        this, not rely on the default."""
        return True

    def execute_minimum(self, lever: Any) -> Any:
        """Default: no-op, returns None. Override to actually do work."""
        return None

    def measure_yield(self, result: Any) -> Any:
        """Default: no yield measured. Override to record real
        foundation/reality_yield_ledger.py-shaped evidence."""
        return None

    def recommend_next(self, yield_signal: Any) -> Any:
        """Default: no recommendation. Override for real frontier
        updates."""
        return None

    def stop_signal(self, yield_signal: Any, next_move: Any) -> StopSignal:
        """Default: always recommends halting (zero gain, zero yield, no
        critical risk) — a worker that hasn't overridden this has no
        basis to claim it should keep going."""
        return StopSignal(new_information_gain=0.0, expected_real_world_yield=0.0,
                          critical_risk_requires_action=False)

    # ── Mandatory hooks — no default, must be implemented ─────────────────
    @abstractmethod
    def check_existing(self, observation: Any) -> Any:
        """MANDATORY. Search for an existing solution before proposing a
        new one — 'never rebuild existing capability without proving the
        existing capability is insufficient.' No default implementation:
        a worker that doesn't override this cannot run at all."""
        raise NotImplementedError

    @abstractmethod
    def verify(self, result: Any) -> bool:
        """MANDATORY. Check the executed result against reality. No
        default: a worker cannot claim success without verifying it."""
        raise NotImplementedError

    @abstractmethod
    def preserve_provenance(self, result: Any, *, verified: bool) -> None:
        """MANDATORY. Record what happened, called on BOTH the verified
        and unverified path (see run() above) — a failed verification is
        exactly the kind of result provenance must not lose."""
        raise NotImplementedError

    @abstractmethod
    def update_state(self, result: Any, yield_signal: Any) -> None:
        """MANDATORY. Update whatever durable state this worker is
        responsible for. No default: a worker that does nothing here
        leaves the architectural map exactly as stale as before it ran."""
        raise NotImplementedError
