"""Persistent, restart-safe swarm state for TitanOS."""
from __future__ import annotations
from dataclasses import dataclass, asdict
import json
from pathlib import Path

@dataclass(frozen=True)
class SwarmState:
    swarm_id: str
    active: tuple[str, ...] = ()
    queued: tuple[str, ...] = ()
    completed: tuple[str, ...] = ()
    failed: tuple[str, ...] = ()

class SwarmStateStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def save(self, state: SwarmState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(asdict(state), sort_keys=True), encoding="utf-8")
        tmp.replace(self.path)

    def load(self, swarm_id: str) -> SwarmState:
        if not self.path.exists():
            return SwarmState(swarm_id)
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if data.get("swarm_id") != swarm_id:
            raise ValueError("swarm identity mismatch")
        return SwarmState(
            swarm_id=swarm_id,
            active=tuple(data.get("active", ())),
            queued=tuple(data.get("queued", ())),
            completed=tuple(data.get("completed", ())),
            failed=tuple(data.get("failed", ())),
        )

__all__ = ["SwarmState", "SwarmStateStore"]
