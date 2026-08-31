"""Bounded TitanOS sensor scaffold: launch_rollback."""
def observe_launch_rollback(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"OBSERVED","sensor":"launch_rollback","evidence":None}
