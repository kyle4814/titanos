"""TitanOS bounded scaffold: rollback."""
def validate_rollback(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"PROPOSED","topic":"rollback"}
