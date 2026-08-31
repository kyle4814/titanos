def test_incident_postmortem_contract():
    from titanos_stub import validate_incident_postmortem
    assert validate_incident_postmortem({})["status"] == "PROPOSED"
