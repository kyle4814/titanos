"""Bounded TitanOS stack scaffold: value_compute."""
def validate_value_compute(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status": "PROPOSED", "component": "value_compute"}
