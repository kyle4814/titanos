"""Bounded TitanOS sensor scaffold: network_api."""
def observe_network_api(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"OBSERVED","sensor":"network_api","evidence":None}
