"""Bounded TitanOS sensor scaffold: claim_conflict."""
def observe_claim_conflict(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"OBSERVED","sensor":"claim_conflict","evidence":None}
