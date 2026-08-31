"""TitanOS brick_api bounded interface scaffold.

This file is intentionally conservative: it defines an interface and does not
claim that the underlying production capability already exists.
"""
from dataclasses import dataclass
from typing import Any

@dataclass
class BrickApiResult:
    status: str
    result: Any = None
    evidence: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

def execute_brick_api(inputs: dict[str, Any]) -> BrickApiResult:
    if not isinstance(inputs, dict):
        return BrickApiResult(status="REJECT", errors=("inputs_must_be_mapping",))
    return BrickApiResult(status="PROPOSED")
