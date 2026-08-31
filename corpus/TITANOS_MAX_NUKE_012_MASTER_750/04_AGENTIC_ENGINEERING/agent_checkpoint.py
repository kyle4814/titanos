"""TitanOS bounded scaffold: agent_checkpoint."""
def validate_agent_checkpoint(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"PROPOSED","topic":"agent_checkpoint"}
