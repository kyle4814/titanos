"""Bounded TitanOS sensor scaffold: search_adr."""
def observe_search_adr(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"OBSERVED","sensor":"search_adr","evidence":None}
