"""Public workforce facade over registry, swarm planning and NEXT acquisition."""

from foundation.next_acquire import acquire_next
from foundation.next_kernel import Opportunity, OpportunityStore
from foundation.worker_execution_contract import WorkerExecutionContract
from foundation.workforce_registry import WorkerSpec, WorkforceRegistry
from foundation.swarm_plan import SwarmAssignment, SwarmPlan, WorkRequirement, plan_swarm

__all__ = [
    "Opportunity", "OpportunityStore", "acquire_next",
    "WorkerExecutionContract", "WorkerSpec", "WorkforceRegistry",
    "SwarmAssignment", "SwarmPlan", "WorkRequirement", "plan_swarm",
]
