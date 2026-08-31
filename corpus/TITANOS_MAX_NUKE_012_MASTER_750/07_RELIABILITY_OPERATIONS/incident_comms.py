"""TitanOS bounded scaffold: incident_comms."""
def validate_incident_comms(payload):
    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping")
    return {"status":"PROPOSED","topic":"incident_comms"}
