"""Bounded TitanOS stack scaffold: agent_capability."""
def validate_agent_capability(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status": "PROPOSED", "component": "agent_capability"}
