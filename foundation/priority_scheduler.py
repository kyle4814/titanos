"""Priority/utility scheduling for bounded TitanOS workforce capacity.

Scores are explicit opportunity metadata, not autonomous authority. Ties are
deterministic. The scheduler selects what to attempt; human authority still
controls consequential transitions.
"""
from __future__ import annotations
from dataclasses import dataclass
from foundation.batch_planner import BatchPlan, plan_batch
from foundation.worker_health import WorkerHealthBook
from foundation.specialization import SpecializationBook
from foundation.workforce_registry import WorkforceRegistry

@dataclass(frozen=True)
class OpportunityPriority:
    opportunity_id: str
    priority: float = 0.0
    urgency: float = 0.0
    evidence_strength: float = 0.0
    expected_value: float = 0.0

    @property
    def utility(self) -> float:
        return self.priority + self.urgency + self.evidence_strength + self.expected_value

def prioritize(items: tuple[OpportunityPriority, ...]) -> tuple[OpportunityPriority, ...]:
    return tuple(sorted(items, key=lambda x: (-x.utility, x.opportunity_id)))

def plan_prioritized(registry: WorkforceRegistry, health: WorkerHealthBook,
                     specialization: SpecializationBook,
                     opportunities: tuple[tuple[str,str,set[str]], ...],
                     priorities: tuple[OpportunityPriority, ...],
                     max_active: int) -> BatchPlan:
    order={x.opportunity_id:i for i,x in enumerate(prioritize(priorities))}
    ranked=tuple(sorted(opportunities,key=lambda x:(order.get(x[0],len(order)),x[0])))
    return plan_batch(registry,health,specialization,ranked,max_active)

__all__=["OpportunityPriority","prioritize","plan_prioritized"]
