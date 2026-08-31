def test_api_timeout_contract():
    from titanos_stub import validate_api_timeout
    assert validate_api_timeout({})["status"] == "PROPOSED"
