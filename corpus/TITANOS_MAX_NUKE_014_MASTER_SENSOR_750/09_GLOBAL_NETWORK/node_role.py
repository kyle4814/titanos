"""Bounded TitanOS sensor scaffold: node_role."""
def observe_node_role(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"OBSERVED","sensor":"node_role","evidence":None}
