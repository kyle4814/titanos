"""Bounded TitanOS stack scaffold: compliance_register."""
def validate_compliance_register(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status": "PROPOSED", "component": "compliance_register"}
