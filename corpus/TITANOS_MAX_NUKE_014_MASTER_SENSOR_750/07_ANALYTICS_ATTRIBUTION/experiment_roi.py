"""Bounded TitanOS sensor scaffold: experiment_roi."""
def observe_experiment_roi(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"OBSERVED","sensor":"experiment_roi","evidence":None}
