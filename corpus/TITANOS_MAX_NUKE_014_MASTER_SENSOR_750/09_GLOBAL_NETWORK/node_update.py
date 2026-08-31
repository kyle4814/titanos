"""Bounded TitanOS sensor scaffold: node_update."""
def observe_node_update(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"OBSERVED","sensor":"node_update","evidence":None}
