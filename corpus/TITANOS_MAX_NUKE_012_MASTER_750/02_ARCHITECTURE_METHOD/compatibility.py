"""TitanOS bounded scaffold: compatibility."""
def validate_compatibility(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"PROPOSED","topic":"compatibility"}
