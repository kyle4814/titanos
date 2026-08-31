def test_measurement_contract():
    from titanos_stub import validate_measurement
    assert validate_measurement({})["status"] == "PROPOSED"
