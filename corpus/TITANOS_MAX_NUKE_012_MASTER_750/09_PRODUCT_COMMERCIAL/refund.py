"""TitanOS bounded scaffold: refund."""
def validate_refund(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"PROPOSED","topic":"refund"}
