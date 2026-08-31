"""TitanOS bounded scaffold: research_result."""
def validate_research_result(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"PROPOSED","topic":"research_result"}
