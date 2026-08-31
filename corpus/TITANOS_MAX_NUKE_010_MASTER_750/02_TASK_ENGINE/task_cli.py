"""TitanOS task_cli bounded interface scaffold.

This file is intentionally conservative: it defines an interface and does not
claim that the underlying production capability already exists.
"""
from dataclasses import dataclass
from typing import Any

@dataclass
class TaskCliResult:
    status: str
    result: Any = None
    evidence: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

def execute_task_cli(inputs: dict[str, Any]) -> TaskCliResult:
    if not isinstance(inputs, dict):
        return TaskCliResult(status="REJECT", errors=("inputs_must_be_mapping",))
    return TaskCliResult(status="PROPOSED")
