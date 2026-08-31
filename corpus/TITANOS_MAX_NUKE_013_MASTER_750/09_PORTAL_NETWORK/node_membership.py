"""Bounded TitanOS stack scaffold: node_membership."""
def validate_node_membership(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status": "PROPOSED", "component": "node_membership"}
