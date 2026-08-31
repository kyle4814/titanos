"""TitanOS bounded scaffold: ownership_law."""
def validate_ownership_law(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"PROPOSED","topic":"ownership_law"}
