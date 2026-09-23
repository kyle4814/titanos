"""Regime-aware utility restoration.

A recovered opportunity is no longer penalized; an actively shifted opportunity
retains the explicit caution penalty.
"""
from __future__ import annotations
from dataclasses import replace
from foundation.priority_scheduler import OpportunityPriority, prioritize
from foundation.regime_shift import RegimeShift
from foundation.regime_recovery import RegimeRecovery

def apply_regime_state(items: tuple[OpportunityPriority, ...],
                       shifts: tuple[RegimeShift, ...],
                       recoveries: tuple[RegimeRecovery, ...],
                       penalty: float = 0.0) -> tuple[OpportunityPriority, ...]:
    if penalty < 0:
        raise ValueError("penalty must be non-negative")
    flagged={s.opportunity_id for s in shifts if s.detected}
    recovered={r.opportunity_id for r in recoveries if r.recovered}
    return prioritize(tuple(
        replace(x, expected_value=x.expected_value-penalty)
        if x.opportunity_id in flagged and x.opportunity_id not in recovered else x
        for x in items
    ))

__all__=["apply_regime_state"]
