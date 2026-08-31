"""TitanOS brick_subscription bounded interface scaffold.

This file is intentionally conservative: it defines an interface and does not
claim that the underlying production capability already exists.
"""
from dataclasses import dataclass
from typing import Any

@dataclass
class BrickSubscriptionResult:
    status: str
    result: Any = None
    evidence: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

def execute_brick_subscription(inputs: dict[str, Any]) -> BrickSubscriptionResult:
    if not isinstance(inputs, dict):
        return BrickSubscriptionResult(status="REJECT", errors=("inputs_must_be_mapping",))
    return BrickSubscriptionResult(status="PROPOSED")
