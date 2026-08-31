def test_api_external_provider_contract():
    from titanos_stub import execute_api_external_provider
    assert execute_api_external_provider(None).status == "REJECT"
    assert execute_api_external_provider({}).status == "PROPOSED"
