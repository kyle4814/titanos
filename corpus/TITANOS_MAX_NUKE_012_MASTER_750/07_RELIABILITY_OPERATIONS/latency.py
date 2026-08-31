"""TitanOS bounded scaffold: latency."""
def validate_latency(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"PROPOSED","topic":"latency"}
