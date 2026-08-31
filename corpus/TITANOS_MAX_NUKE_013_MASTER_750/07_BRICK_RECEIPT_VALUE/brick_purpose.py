"""Bounded TitanOS stack scaffold: brick_purpose."""
def validate_brick_purpose(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status": "PROPOSED", "component": "brick_purpose"}
