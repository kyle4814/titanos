def test_calibration_contract():
    from titanos_stub import validate_calibration
    assert validate_calibration({})["status"] == "PROPOSED"
