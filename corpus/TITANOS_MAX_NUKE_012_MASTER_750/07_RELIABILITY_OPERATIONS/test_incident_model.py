def test_incident_model_contract():
    from titanos_stub import validate_incident_model
    assert validate_incident_model({})["status"] == "PROPOSED"
