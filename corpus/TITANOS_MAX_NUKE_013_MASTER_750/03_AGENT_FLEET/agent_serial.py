"""Bounded TitanOS stack scaffold: agent_serial."""
def validate_agent_serial(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status": "PROPOSED", "component": "agent_serial"}
