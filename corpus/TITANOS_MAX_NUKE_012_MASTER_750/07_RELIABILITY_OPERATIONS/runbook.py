"""TitanOS bounded scaffold: runbook."""
def validate_runbook(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"PROPOSED","topic":"runbook"}
