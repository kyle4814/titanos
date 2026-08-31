"""TitanOS bounded scaffold: metrics."""
def validate_metrics(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"PROPOSED","topic":"metrics"}
