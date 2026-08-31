"""TitanOS bounded scaffold: agent_capabilities."""
def validate_agent_capabilities(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"PROPOSED","topic":"agent_capabilities"}
