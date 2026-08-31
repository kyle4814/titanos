"""TitanOS bounded scaffold: margin."""
def validate_margin(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"PROPOSED","topic":"margin"}
