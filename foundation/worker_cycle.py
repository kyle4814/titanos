"""End-to-end bounded worker cycle for TitanOS.

Coordinates claim, bounded invocation construction, result application and
lease release. External execution is supplied by the caller/Claude Code
adapter; this function never executes arbitrary commands itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from foundation.claude_code_adapter import ClaudeCodeInvocation, build_invocation
from foundation.next_kernel import OpportunityStore
from foundation.next_leases import claim
from foundation.worker_execution_contract import WorkerExecutionContract
from foundation.worker_lifecycle import complete_worker
from foundation.worker_result import WorkerResult
from foundation.authority_result import apply_worker_result
from foundation.workforce_dispatcher import DispatchItem

@dataclass(frozen=True)
class WorkerCycle:
    invocation: ClaudeCodeInvocation
    result: WorkerResult

def prepare_worker_cycle(store: OpportunityStore, item: DispatchItem,
                         contract: WorkerExecutionContract) -> ClaudeCodeInvocation:
    if item.worker_id != contract.worker_id:
        raise ValueError("worker/contract mismatch")
    claim(store, contract.opportunity_id, contract.worker_id)
    return build_invocation(item, contract)

def ingest_worker_cycle(store: OpportunityStore, result: WorkerResult):
    item = complete_worker(store, result.opportunity_id, result.worker_id, result)
    return apply_worker_result(store, result)

__all__ = ["WorkerCycle", "prepare_worker_cycle", "ingest_worker_cycle"]
