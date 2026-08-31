"""TitanOS base_case bounded interface scaffold.

This file is intentionally conservative: it defines an interface and does not
claim that the underlying production capability already exists.
"""
from dataclasses import dataclass
from typing import Any

@dataclass
class BaseCaseResult:
    status: str
    result: Any = None
    evidence: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

def execute_base_case(inputs: dict[str, Any]) -> BaseCaseResult:
    if not isinstance(inputs, dict):
        return BaseCaseResult(status="REJECT", errors=("inputs_must_be_mapping",))
    return BaseCaseResult(status="PROPOSED")
