from dataclasses import dataclass
from enum import Enum

class State(str, Enum):
    QUEUED="QUEUED"; CLAIMED="CLAIMED"; RUNNING="RUNNING"
    VERIFYING="VERIFYING"; BLUE_TEAM="BLUE_TEAM"
    CHECKPOINTING="CHECKPOINTING"; COMPLETE="COMPLETE"
    FAILED="FAILED"; BLOCKED="BLOCKED"; ROLLED_BACK="ROLLED_BACK"

TRANSITIONS = {
    State.QUEUED:{State.CLAIMED},
    State.CLAIMED:{State.RUNNING,State.QUEUED},
    State.RUNNING:{State.VERIFYING,State.FAILED,State.BLOCKED},
    State.VERIFYING:{State.BLUE_TEAM,State.FAILED},
    State.BLUE_TEAM:{State.CHECKPOINTING,State.FAILED},
    State.CHECKPOINTING:{State.COMPLETE,State.FAILED},
    State.FAILED:{State.QUEUED,State.ROLLED_BACK},
    State.BLOCKED:{State.QUEUED},
    State.ROLLED_BACK:{State.QUEUED},
    State.COMPLETE:set(),
}

class KernelViolation(RuntimeError): pass

def transition(current: State, target: State) -> State:
    if target not in TRANSITIONS.get(current, set()):
        raise KernelViolation(f"illegal state transition: {current}->{target}")
    return target

@dataclass(frozen=True)
class Authorization:
    task_id: str
    actor: str
    capability: str
    write_scope: tuple
    max_requests: int
    max_bytes: int
    max_wall_seconds: int

def authorize(a: Authorization, requested_scope: str) -> None:
    if requested_scope not in a.write_scope:
        raise KernelViolation("write scope denied")
    if a.max_requests < 0 or a.max_bytes < 0 or a.max_wall_seconds < 0:
        raise KernelViolation("invalid resource budget")
