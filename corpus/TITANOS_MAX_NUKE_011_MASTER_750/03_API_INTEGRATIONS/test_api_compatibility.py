def test_api_compatibility_contract():
    from titanos_stub import execute_api_compatibility
    assert execute_api_compatibility(None).status == "REJECT"
    assert execute_api_compatibility({}).status == "PROPOSED"
