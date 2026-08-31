def test_portal_api_contract():
    from titanos_stub import validate_portal_api
    assert validate_portal_api({})["status"] == "PROPOSED"
