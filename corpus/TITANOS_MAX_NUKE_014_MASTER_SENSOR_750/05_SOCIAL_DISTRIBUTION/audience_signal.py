"""Bounded TitanOS sensor scaffold: audience_signal."""
def observe_audience_signal(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"OBSERVED","sensor":"audience_signal","evidence":None}
