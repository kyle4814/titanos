"""Bounded TitanOS sensor scaffold: entity_conflict."""
def observe_entity_conflict(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"OBSERVED","sensor":"entity_conflict","evidence":None}
