"""Evidence-weighted outcome feedback for opportunity scheduling."""
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(frozen=True)
class OutcomeFeedback:
    opportunity_id: str
    expected_value: float
    realized_value: float
    completed: bool
    evidence_strength: float = 0.0

    @property
    def value_error(self) -> float:
        return self.realized_value - self.expected_value

    @property
    def weight(self) -> float:
        return max(0.0, min(1.0, self.evidence_strength)) if self.completed else 0.0

@dataclass
class OpportunityFeedbackBook:
    records: dict[str, tuple[OutcomeFeedback, ...]] = field(default_factory=dict)

    def record(self, feedback: OutcomeFeedback) -> None:
        self.records[feedback.opportunity_id] = (*self.records.get(feedback.opportunity_id, ()), feedback)

    def calibration(self, opportunity_id: str) -> float:
        rows=self.records.get(opportunity_id, ())
        weighted=sum(x.value_error*x.weight for x in rows)
        weight=sum(x.weight for x in rows)
        return weighted/weight if weight else 0.0

    def adjusted_value(self, opportunity_id: str, expected_value: float) -> float:
        return expected_value + self.calibration(opportunity_id)

__all__=["OutcomeFeedback","OpportunityFeedbackBook"]
