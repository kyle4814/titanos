"""Bounded TitanOS sensor scaffold: metric_actual."""
def observe_metric_actual(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"OBSERVED","sensor":"metric_actual","evidence":None}
