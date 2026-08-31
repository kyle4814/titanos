def test_quarantine_model_contract():
    from titanos_stub import validate_quarantine_model
    assert validate_quarantine_model({})["status"] == "PROPOSED"
