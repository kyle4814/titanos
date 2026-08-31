from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib, json
@dataclass(frozen=True)
class Receipt:
    receipt_id: str
    task_id: str
    action: str
    status: str
    evidence: list
    changed_files: list
    previous_hash: str = ""
    timestamp: str = ""
    def canonical(self):
        d = asdict(self)
        d["timestamp"] = d["timestamp"] or datetime.now(timezone.utc).isoformat()
        return json.dumps(d, sort_keys=True, separators=(",", ":"))
    def digest(self):
        return hashlib.sha256(self.canonical().encode()).hexdigest()
