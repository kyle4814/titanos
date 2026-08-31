"""TitanOS bounded scaffold: locking."""
def validate_locking(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"PROPOSED","topic":"locking"}
