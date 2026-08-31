"""TitanOS bounded scaffold: compute_policy."""
def validate_compute_policy(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"PROPOSED","topic":"compute_policy"}
