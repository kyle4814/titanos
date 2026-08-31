"""Bounded TitanOS stack scaffold: evaluation_case."""
def validate_evaluation_case(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status": "PROPOSED", "component": "evaluation_case"}
