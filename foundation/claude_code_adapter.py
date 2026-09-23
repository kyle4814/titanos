"""Claude Code workforce adapter.

Produces deterministic, bounded invocation envelopes for an external Claude Code
runner. This module never executes shell commands or grants authority.
"""
from __future__ import annotations
from dataclasses import dataclass
from foundation.worker_execution_contract import WorkerExecutionContract
from foundation.workforce_dispatcher import DispatchItem

@dataclass(frozen=True)
class ClaudeCodeInvocation:
    worker_id: str
    prompt: str
    tools: tuple[str, ...]
    authority_ceiling: str

def build_invocation(item: DispatchItem, contract: WorkerExecutionContract) -> ClaudeCodeInvocation:
    if item.worker_id != contract.worker_id:
        raise ValueError("dispatch worker and contract worker mismatch")
    prompt = "
".join((
        "TITANOS WORK ORDER",
        f"WORKER: {contract.worker_id}",
        f"OPPORTUNITY: {contract.opportunity_id}",
        f"OBJECTIVE: {contract.objective}",
        f"ALLOWED TOOLS: {', '.join(contract.allowed_tools) or 'none'}",
        f"ALLOWED ACTIONS: {', '.join(contract.allowed_actions) or 'none'}",
        f"FORBIDDEN ACTIONS: {', '.join(contract.forbidden_actions) or 'none'}",
        f"REQUIRED EVIDENCE: {', '.join(contract.required_evidence) or 'none'}",
        f"STOP CONDITIONS: {', '.join(contract.stop_conditions) or 'none'}",
        f"ESCALATION CONDITIONS: {', '.join(contract.escalation_conditions) or 'none'}",
        f"AUTHORITY CEILING: {contract.authority_ceiling}",
        f"RECEIPT SCHEMA: {contract.receipt_schema}",
        "Return a structured worker result. Do not claim completion without required evidence.",
    ))
    return ClaudeCodeInvocation(contract.worker_id, prompt, contract.allowed_tools, contract.authority_ceiling)

__all__ = ["ClaudeCodeInvocation", "build_invocation"]
