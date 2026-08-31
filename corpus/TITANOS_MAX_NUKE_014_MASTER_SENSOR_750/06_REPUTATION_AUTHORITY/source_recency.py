"""Bounded TitanOS sensor scaffold: source_recency."""
def observe_source_recency(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"OBSERVED","sensor":"source_recency","evidence":None}
