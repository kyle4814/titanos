"""Bounded TitanOS stack scaffold: resource_lock."""
def validate_resource_lock(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status": "PROPOSED", "component": "resource_lock"}
