def test_api_timeout_contract():
    from titanos_stub import execute_api_timeout
    assert execute_api_timeout(None).status == "REJECT"
    assert execute_api_timeout({}).status == "PROPOSED"
