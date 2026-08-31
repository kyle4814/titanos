"""TitanOS bounded scaffold: agent_output."""
def validate_agent_output(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"PROPOSED","topic":"agent_output"}
