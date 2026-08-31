"""TitanOS bounded scaffold: task_handoff."""
def validate_task_handoff(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"PROPOSED","topic":"task_handoff"}
