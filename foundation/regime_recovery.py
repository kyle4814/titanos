"""Fresh-evidence recovery for regime-shifted opportunities."""
from __future__ import annotations
from dataclasses import dataclass
from foundation.opportunity_feedback import OpportunityFeedbackBook
from foundation.regime_shift import RegimeShift, detect_shift

@dataclass(frozen=True)
class RegimeRecovery:
    opportunity_id: str
    shift: RegimeShift
    recovered: bool
    fresh_evidence_count: int

def assess_recovery(book: OpportunityFeedbackBook, opportunity_id: str, *,
                    now=None, half_life_days: float = 30.0,
                    recent_window: int = 3, threshold: float = 10.0,
                    recovery_window: int = 3) -> RegimeRecovery:
    rows=book.records.get(opportunity_id, ())
    shift=detect_shift(book, opportunity_id, now=now,
                       half_life_days=half_life_days,
                       recent_window=recent_window, threshold=threshold)
    fresh=max(1,recovery_window)
    recent=rows[-fresh:]
    # Recovery requires enough fresh completed evidence and no current shift.
    valid=[x for x in recent if x.completed and x.weight > 0]
    recovered=len(valid) >= fresh and not shift.detected
    return RegimeRecovery(opportunity_id,shift,recovered,len(valid))

__all__=["RegimeRecovery","assess_recovery"]
