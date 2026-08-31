def test_api_search_contract():
    from titanos_stub import execute_api_search
    assert execute_api_search(None).status == "REJECT"
    assert execute_api_search({}).status == "PROPOSED"
