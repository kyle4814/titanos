"""Bounded TitanOS sensor scaffold: crawler_search."""
def observe_crawler_search(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"OBSERVED","sensor":"crawler_search","evidence":None}
