"""TitanOS receipt_runbook bounded interface scaffold.

This file is intentionally conservative: it defines an interface and does not
claim that the underlying production capability already exists.
"""
from dataclasses import dataclass
from typing import Any

@dataclass
class ReceiptRunbookResult:
    status: str
    result: Any = None
    evidence: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

def execute_receipt_runbook(inputs: dict[str, Any]) -> ReceiptRunbookResult:
    if not isinstance(inputs, dict):
        return ReceiptRunbookResult(status="REJECT", errors=("inputs_must_be_mapping",))
    return ReceiptRunbookResult(status="PROPOSED")
