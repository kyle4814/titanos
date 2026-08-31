def test_risk_register_contract():
    from titanos_stub import validate_risk_register
    assert validate_risk_register({})["status"] == "PROPOSED"
