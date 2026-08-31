"""TitanOS bounded scaffold: double_count_attack."""
def validate_double_count_attack(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"PROPOSED","topic":"double_count_attack"}
