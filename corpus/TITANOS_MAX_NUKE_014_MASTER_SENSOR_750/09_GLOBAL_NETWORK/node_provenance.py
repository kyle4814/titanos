"""Bounded TitanOS sensor scaffold: node_provenance."""
def observe_node_provenance(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"OBSERVED","sensor":"node_provenance","evidence":None}
