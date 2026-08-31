"""Bounded TitanOS sensor scaffold: content_draft."""
def observe_content_draft(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"OBSERVED","sensor":"content_draft","evidence":None}
