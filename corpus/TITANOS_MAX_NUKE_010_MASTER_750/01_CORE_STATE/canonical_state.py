"""TitanOS canonical_state bounded interface scaffold.

This file is intentionally conservative: it defines an interface and does not
claim that the underlying production capability already exists.
"""
from dataclasses import dataclass
from typing import Any

@dataclass
class CanonicalStateResult:
    status: str
    result: Any = None
    evidence: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

def execute_canonical_state(inputs: dict[str, Any]) -> CanonicalStateResult:
    if not isinstance(inputs, dict):
        return CanonicalStateResult(status="REJECT", errors=("inputs_must_be_mapping",))
    return CanonicalStateResult(status="PROPOSED")
