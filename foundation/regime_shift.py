"""Detect material regime shifts in opportunity outcomes."""
from __future__ import annotations
from dataclasses import dataclass
from foundation.opportunity_feedback import OpportunityFeedbackBook

@dataclass(frozen=True)
class RegimeShift:
    opportunity_id: str
    historical_calibration: float
    recent_calibration: float
    delta: float
    detected: bool

def detect_shift(book: OpportunityFeedbackBook, opportunity_id: str, *,
                 now=None, half_life_days: float = 30.0,
                 recent_window: int = 3, threshold: float = 10.0) -> RegimeShift:
    rows=book.records.get(opportunity_id, ())
    historical=book.calibration(opportunity_id, now=now, half_life_days=half_life_days)
    recent_rows=rows[-max(1,recent_window):]
    if not recent_rows:
        recent=0.0
    else:
        weighted=sum(x.value_error*x.decayed_weight(now,half_life_days) for x in recent_rows)
        weight=sum(x.decayed_weight(now,half_life_days) for x in recent_rows)
        recent=weighted/weight if weight else 0.0
    delta=recent-historical
    return RegimeShift(opportunity_id,historical,recent,delta,abs(delta)>=threshold)

__all__=["RegimeShift","detect_shift"]
