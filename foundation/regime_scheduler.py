"""Regime-aware priority scheduling.

A detected regime shift applies a deterministic caution penalty until fresh
evidence is gathered. It does not override authority or hard constraints.
"""
from __future__ import annotations
from dataclasses import replace
from foundation.priority_scheduler import OpportunityPriority, prioritize
from foundation.regime_shift import RegimeShift

def apply_regime_flags(items: tuple[OpportunityPriority, ...],
                       shifts: tuple[RegimeShift, ...],
                       penalty: float = 0.0) -> tuple[OpportunityPriority, ...]:
    if penalty < 0: raise ValueError("penalty must be non-negative")
    flagged={s.opportunity_id for s in shifts if s.detected}
    return prioritize(tuple(
        replace(x, expected_value=x.expected_value-penalty) if x.opportunity_id in flagged else x
        for x in items
    ))

__all__=["apply_regime_flags"]
