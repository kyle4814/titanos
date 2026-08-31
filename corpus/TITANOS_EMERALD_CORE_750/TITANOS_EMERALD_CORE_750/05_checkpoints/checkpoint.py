from dataclasses import dataclass, asdict
import json, hashlib
@dataclass(frozen=True)
class Checkpoint:
    task_id: str
    state: str
    repo_revision: str
    config_hash: str
    receipt_head: str
    next_action: str
    def digest(self):
        raw = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()
