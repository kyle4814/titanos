"""TitanOS bounded scaffold: value_loop."""
def validate_value_loop(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"PROPOSED","topic":"value_loop"}
