"""TitanOS task_fanin bounded interface scaffold.

This file is intentionally conservative: it defines an interface and does not
claim that the underlying production capability already exists.
"""
from dataclasses import dataclass
from typing import Any

@dataclass
class TaskFaninResult:
    status: str
    result: Any = None
    evidence: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

def execute_task_fanin(inputs: dict[str, Any]) -> TaskFaninResult:
    if not isinstance(inputs, dict):
        return TaskFaninResult(status="REJECT", errors=("inputs_must_be_mapping",))
    return TaskFaninResult(status="PROPOSED")
