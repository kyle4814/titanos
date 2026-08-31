"""Bounded TitanOS sensor scaffold: sensor_source."""
def observe_sensor_source(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"OBSERVED","sensor":"sensor_source","evidence":None}
