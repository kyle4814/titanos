def test_rate_control_contract():
    from titanos_stub import validate_rate_control
    assert validate_rate_control({})["status"] == "PROPOSED"
