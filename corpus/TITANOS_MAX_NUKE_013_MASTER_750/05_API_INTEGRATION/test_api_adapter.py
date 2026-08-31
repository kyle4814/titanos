def test_api_adapter_contract():
    from titanos_stub import validate_api_adapter
    assert validate_api_adapter({})["status"] == "PROPOSED"
