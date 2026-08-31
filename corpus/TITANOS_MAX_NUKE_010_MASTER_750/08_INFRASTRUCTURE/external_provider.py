"""TitanOS external_provider bounded interface scaffold.

This file is intentionally conservative: it defines an interface and does not
claim that the underlying production capability already exists.
"""
from dataclasses import dataclass
from typing import Any

@dataclass
class ExternalProviderResult:
    status: str
    result: Any = None
    evidence: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

def execute_external_provider(inputs: dict[str, Any]) -> ExternalProviderResult:
    if not isinstance(inputs, dict):
        return ExternalProviderResult(status="REJECT", errors=("inputs_must_be_mapping",))
    return ExternalProviderResult(status="PROPOSED")
