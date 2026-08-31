"""Bounded TitanOS sensor scaffold: cohort_value."""
def observe_cohort_value(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"OBSERVED","sensor":"cohort_value","evidence":None}
