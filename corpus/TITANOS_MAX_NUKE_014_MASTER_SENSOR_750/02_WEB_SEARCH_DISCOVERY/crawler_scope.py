"""Bounded TitanOS sensor scaffold: crawler_scope."""
def observe_crawler_scope(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"OBSERVED","sensor":"crawler_scope","evidence":None}
