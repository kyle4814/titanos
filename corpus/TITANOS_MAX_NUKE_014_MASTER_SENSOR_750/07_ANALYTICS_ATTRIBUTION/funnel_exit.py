"""Bounded TitanOS sensor scaffold: funnel_exit."""
def observe_funnel_exit(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"OBSERVED","sensor":"funnel_exit","evidence":None}
