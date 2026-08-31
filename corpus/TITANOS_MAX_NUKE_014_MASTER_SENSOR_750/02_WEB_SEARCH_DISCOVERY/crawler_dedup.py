"""Bounded TitanOS sensor scaffold: crawler_dedup."""
def observe_crawler_dedup(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"OBSERVED","sensor":"crawler_dedup","evidence":None}
