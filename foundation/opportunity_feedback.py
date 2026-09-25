"""Evidence-weighted, time-decayed outcome feedback."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import exp

@dataclass(frozen=True)
class OutcomeFeedback:
    opportunity_id: str
    expected_value: float
    realized_value: float
    completed: bool
    evidence_strength: float = 0.0
    observed_at: str | None = None

    def __post_init__(self) -> None:
        # Hold the declared types. The learning-store loader reads these back
        # with float()/bool(), so a record created with ints (10, 15) was
        # persisted as ints and reloaded as floats (10.0, 15.0): equal in
        # Python, different bytes in canonical JSON, so a learning receipt
        # built from a reloaded memory could never bind against the file it
        # was loaded from (2026-09-26, CI run 36188217313).
        object.__setattr__(self, "expected_value", float(self.expected_value))
        object.__setattr__(self, "realized_value", float(self.realized_value))
        object.__setattr__(self, "evidence_strength", float(self.evidence_strength))
        object.__setattr__(self, "completed", bool(self.completed))

    @property
    def value_error(self) -> float:
        return self.realized_value - self.expected_value

    @property
    def weight(self) -> float:
        return max(0.0, min(1.0, self.evidence_strength)) if self.completed else 0.0

    def decayed_weight(self, now: datetime | None = None, half_life_days: float = 30.0) -> float:
        if half_life_days <= 0:
            raise ValueError("half_life_days must be positive")
        if not self.observed_at:
            return self.weight
        now = now or datetime.now(timezone.utc)
        observed = datetime.fromisoformat(self.observed_at)
        age=max(0.0, (now-observed).total_seconds()/86400.0)
        return self.weight * exp(-0.6931471805599453 * age / half_life_days)

@dataclass
class OpportunityFeedbackBook:
    records: dict[str, tuple[OutcomeFeedback, ...]] = field(default_factory=dict)

    def record(self, feedback: OutcomeFeedback) -> None:
        self.records[feedback.opportunity_id] = (*self.records.get(feedback.opportunity_id, ()), feedback)

    def calibration(self, opportunity_id: str, *, now: datetime | None = None, half_life_days: float = 30.0) -> float:
        rows=self.records.get(opportunity_id, ())
        weighted=sum(x.value_error*x.decayed_weight(now,half_life_days) for x in rows)
        weight=sum(x.decayed_weight(now,half_life_days) for x in rows)
        return weighted/weight if weight else 0.0

    def adjusted_value(self, opportunity_id: str, expected_value: float, *, now: datetime | None = None, half_life_days: float = 30.0) -> float:
        return expected_value + self.calibration(opportunity_id,now=now,half_life_days=half_life_days)

__all__=["OutcomeFeedback","OpportunityFeedbackBook"]
