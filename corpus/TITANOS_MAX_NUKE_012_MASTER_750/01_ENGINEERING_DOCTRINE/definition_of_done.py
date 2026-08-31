"""TitanOS bounded scaffold: definition_of_done."""
def validate_definition_of_done(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"PROPOSED","topic":"definition_of_done"}
