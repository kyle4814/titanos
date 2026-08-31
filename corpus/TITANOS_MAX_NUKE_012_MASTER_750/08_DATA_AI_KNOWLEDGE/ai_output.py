"""TitanOS bounded scaffold: ai_output."""
def validate_ai_output(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"PROPOSED","topic":"ai_output"}
