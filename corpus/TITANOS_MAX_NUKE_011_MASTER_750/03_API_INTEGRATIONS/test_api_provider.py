def test_api_provider_contract():
    from titanos_stub import execute_api_provider
    assert execute_api_provider(None).status == "REJECT"
    assert execute_api_provider({}).status == "PROPOSED"
