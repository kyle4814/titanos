"""Bounded TitanOS sensor scaffold: network_identity."""
def observe_network_identity(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"OBSERVED","sensor":"network_identity","evidence":None}
