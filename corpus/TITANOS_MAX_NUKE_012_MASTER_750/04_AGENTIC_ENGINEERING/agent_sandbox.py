"""TitanOS bounded scaffold: agent_sandbox."""
def validate_agent_sandbox(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"PROPOSED","topic":"agent_sandbox"}
