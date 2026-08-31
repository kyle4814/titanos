"""Bounded TitanOS sensor scaffold: search_signal."""
def observe_search_signal(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"OBSERVED","sensor":"search_signal","evidence":None}
