"""TitanOS brick_runbook bounded interface scaffold.

This file is intentionally conservative: it defines an interface and does not
claim that the underlying production capability already exists.
"""
from dataclasses import dataclass
from typing import Any

@dataclass
class BrickRunbookResult:
    status: str
    result: Any = None
    evidence: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

def execute_brick_runbook(inputs: dict[str, Any]) -> BrickRunbookResult:
    if not isinstance(inputs, dict):
        return BrickRunbookResult(status="REJECT", errors=("inputs_must_be_mapping",))
    return BrickRunbookResult(status="PROPOSED")
