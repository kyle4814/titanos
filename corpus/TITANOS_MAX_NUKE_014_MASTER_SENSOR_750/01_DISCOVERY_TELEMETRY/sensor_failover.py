"""Bounded TitanOS sensor scaffold: sensor_failover."""
def observe_sensor_failover(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"OBSERVED","sensor":"sensor_failover","evidence":None}
