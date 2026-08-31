"""Bounded TitanOS stack scaffold: integration_adapter."""
def validate_integration_adapter(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status": "PROPOSED", "component": "integration_adapter"}
