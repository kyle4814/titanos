"""TitanOS bounded scaffold: canonicalization."""
def validate_canonicalization(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"PROPOSED","topic":"canonicalization"}
