def test_timeouts_contract():
    from titanos_stub import validate_timeouts
    assert validate_timeouts({})["status"] == "PROPOSED"
