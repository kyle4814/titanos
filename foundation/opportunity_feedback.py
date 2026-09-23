"""Outcome feedback for opportunity utility scheduling."""
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

@dataclass
class OpportunityFeedbackBook:
    records: dict[str, tuple[OutcomeFeedback, ...]] = field(default_factory=dict)

    def record(self, feedback: OutcomeFeedback) -> None:
        self.records[feedback.opportunity_id] = (*self.records.get(feedback.opportunity_id, ()), feedback)

    def calibration(self, opportunity_id: str) -> float:
        rows=self.records.get(opportunity_id, ())
        return sum(x.value_error for x in rows) / len(rows) if rows else 0.0

    def adjusted_value(self, opportunity_id: str, expected_value: float) -> float:
        return expected_value + self.calibration(opportunity_id)

__all__=["OutcomeFeedback","OpportunityFeedbackBook"]
