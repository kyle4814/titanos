"""TitanOS bounded scaffold: merge_bundle."""
def validate_merge_bundle(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"PROPOSED","topic":"merge_bundle"}
